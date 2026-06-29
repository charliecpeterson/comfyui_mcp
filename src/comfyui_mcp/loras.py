"""Local LoRA discovery + ranking + graph-injection helpers.

Two halves:

  1. `suggest(intent, base_model, k)` — walks <COMFYUI_ROOT>/models/loras/
     (recursively), reads each safetensors header via model_meta._read_safetensors_metadata,
     scores by tag overlap with `intent`, returns top-k candidates with trigger
     words and recommended strength.

  2. Pure graph-inspection helpers — find existing LoRA-loader nodes and the
     positive CLIPTextEncode in a UI-format workflow. The actual injection
     (add_node / set_widget / connect_nodes bridge ops) lives in server.py
     because it needs the live bridge client; this module returns plans.

Trigger-word resolution priority (per LoRA):
  modelspec.trigger_phrase > ss_output_name > top-3 training tags

Base-model normalization: Civitai uses strings like "Flux.1 D", "SDXL 1.0",
"Illustrious". Kohya safetensors metadata uses ss_base_model_version with
values like "sdxl_base_v1-0" / "flux_dev" / etc. We canonicalize to a small
family-level enum so the agent can match across these conventions.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

from .core import _comfy_root
from .model_meta import _read_safetensors_metadata, _top_training_tags


# --- base-model family normalization ---------------------------------------

# Family enum: "flux1", "flux2", "sdxl", "sd15", "illustrious", "pony",
# "qwen", "zimage", "wan", "ltx", "unknown"

_BASE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"flux[\.\-_ ]?2", re.I), "flux2"),
    (re.compile(r"flux[\.\-_ ]?1|flux\.?d|flux\.?dev|flux\.?pro|flux\.?schnell", re.I), "flux1"),
    (re.compile(r"\bflux\b", re.I), "flux1"),  # bare "flux" → 1.x (the older default)
    (re.compile(r"illustrious|noobai", re.I), "illustrious"),
    (re.compile(r"\bpony\b", re.I), "pony"),
    (re.compile(r"sdxl|sd[\.\-_ ]?xl", re.I), "sdxl"),
    (re.compile(r"sd[\.\-_ ]?1\.?5|sd15|stable.?diffusion.?1", re.I), "sd15"),
    (re.compile(r"qwen", re.I), "qwen"),
    (re.compile(r"\bz[\-_ ]?image\b", re.I), "zimage"),
    (re.compile(r"\bwan\b", re.I), "wan"),
    (re.compile(r"\bltx\b|lightricks", re.I), "ltx"),
]


def normalize_base_model(s: str | None) -> str:
    """Map a free-form base-model string (Civitai or Kohya format) to a family enum."""
    if not s:
        return "unknown"
    for pat, fam in _BASE_PATTERNS:
        if pat.search(s):
            return fam
    return "unknown"


# --- safetensors metadata extraction ---------------------------------------

def _extract_trigger_words(meta: dict[str, Any]) -> list[str]:
    """Trigger-word resolution per the priority order in the module docstring.

    1. modelspec.trigger_phrase (explicit author-declared) — split on , and ;
    2. Top training tags (kohya bakes them in; the top frequency tag is almost
       always the real trigger concept the LoRA learned)
    3. ss_output_name as last resort (often just the filename, e.g. "Amy_Rose_IL"
       when the real trigger is "amy rose")
    """
    tp = meta.get("modelspec.trigger_phrase")
    if isinstance(tp, str) and tp.strip():
        out: list[str] = []
        for piece in re.split(r"[,;]", tp):
            p = piece.strip()
            if p:
                out.append(p)
        if out:
            return out
    top = _top_training_tags(meta, limit=3)
    if top:
        return top
    on = meta.get("ss_output_name")
    if isinstance(on, str) and on.strip():
        return [on.strip()]
    return []


def _recommended_strength(meta: dict[str, Any]) -> float:
    """Heuristic strength based on network dim. Higher rank = lower recommended
    strength (more powerful — over-fires at 1.0). LoRAs with no rank info default
    to 0.75."""
    try:
        dim = int(meta.get("ss_network_dim") or 0)
    except (TypeError, ValueError):
        dim = 0
    if dim >= 128:
        return 0.55
    if dim >= 32:
        return 0.7
    if dim >= 8:
        return 0.8
    return 0.75


# --- intent tokenization + scoring -----------------------------------------

_INTENT_STOPWORDS = {
    "a", "an", "the", "of", "for", "with", "to", "and", "or", "but", "in",
    "on", "at", "by", "as", "is", "it", "be", "are", "was", "were", "this",
    "that", "these", "those", "i", "we", "you", "they", "he", "she", "his",
    "her", "their", "our", "my", "your", "lora", "style", "concept", "model",
}


def _tokenize(text: str) -> set[str]:
    """Lowercase + split on non-alphanumeric. Drop stopwords + very short tokens."""
    if not text:
        return set()
    toks = re.split(r"[^a-z0-9]+", text.lower())
    return {t for t in toks if len(t) >= 3 and t not in _INTENT_STOPWORDS}


def _score(intent_tokens: set[str], lora_tokens: set[str], tag_freq: dict[str, int]) -> int:
    """Score a LoRA against the intent. Each overlapping token contributes 1 base
    point plus min(log2(frequency), 4) bonus when the matched token has a known
    training frequency. Without the bonus, a single rare tag matches as well as
    a hugely-represented one."""
    import math
    score = 0
    for tok in intent_tokens & lora_tokens:
        score += 1
        freq = tag_freq.get(tok, 0)
        if freq > 0:
            score += min(int(math.log2(freq + 1)), 4)
    return score


# --- public: suggest -------------------------------------------------------

def _iter_lora_paths(loras_root: Path) -> Iterable[Path]:
    """Yield safetensors files under the LoRA dir, recursing. Silently skip
    unreadable subtrees (broken symlinks etc.)."""
    if not loras_root.exists():
        return
    try:
        for p in loras_root.rglob("*.safetensors"):
            if p.is_file():
                yield p
    except OSError:
        return


def _candidate_record(path: Path, loras_root: Path) -> dict[str, Any] | None:
    """Read metadata + build a candidate dict. Returns None on read failure
    (corrupt file, broken symlink) — failures are not fatal at the listing level."""
    sf = _read_safetensors_metadata(path)
    if "error" in sf:
        return None
    meta = sf.get("metadata") or {}

    # Tag frequency dict for scoring
    import json
    tag_freq_raw = meta.get("ss_tag_frequency")
    tag_freq: dict[str, int] = {}
    if isinstance(tag_freq_raw, str):
        try:
            parsed = json.loads(tag_freq_raw)
            if isinstance(parsed, dict):
                for _ds, counts in parsed.items():
                    if isinstance(counts, dict):
                        for tag, count in counts.items():
                            if isinstance(count, int):
                                tag_freq[tag.lower()] = tag_freq.get(tag.lower(), 0) + count

        except (json.JSONDecodeError, TypeError):
            pass

    top_tags = _top_training_tags(meta, limit=12)
    triggers = _extract_trigger_words(meta)
    base_model = meta.get("modelspec.architecture") or meta.get("ss_base_model_version")
    # Try metadata first, fall back to path component. Path is often more reliable
    # for organized libraries — Kohya's `stable-diffusion-xl-v1-base/lora` won't
    # tell us "this is an Illustrious LoRA" even though the path /loras/illustrious/
    # makes it obvious.
    base_family = normalize_base_model(base_model)
    if base_family == "unknown":
        base_family = normalize_base_model(str(path))

    # Tokens this LoRA "knows": filename, path, training tags
    rel = path.relative_to(loras_root) if loras_root in path.parents or loras_root == path.parent else path
    tokens = _tokenize(path.stem) | _tokenize(str(rel.parent)) | {t.lower() for t in top_tags}
    return {
        "filename": str(rel),
        "abs_path": str(path),
        "base_model_raw": base_model,
        "base_family": base_family,
        "trigger_words": triggers,
        "top_training_tags": top_tags,
        "recommended_strength": _recommended_strength(meta),
        "_tokens": tokens,
        "_tag_freq": tag_freq,
        "size_mb": round(path.stat().st_size / 1_048_576, 1),
    }


def suggest(
    intent: str,
    base_model: str | None = None,
    k: int = 8,
    loras_root: Path | None = None,
) -> dict[str, Any]:
    """Return top-k local LoRAs matching `intent`, optionally filtered by base model
    family (free-form input is normalized via normalize_base_model)."""
    if loras_root is None:
        try:
            loras_root = _comfy_root() / "models" / "loras"
        except RuntimeError as e:
            return {"ok": False, "error": str(e)}

    target_family = normalize_base_model(base_model) if base_model else None
    intent_tokens = _tokenize(intent)
    if not intent_tokens:
        return {"ok": False, "error": "intent must contain at least one meaningful token (3+ chars)"}

    candidates: list[dict[str, Any]] = []
    skipped_unreadable = 0
    skipped_base_mismatch = 0
    for p in _iter_lora_paths(loras_root):
        c = _candidate_record(p, loras_root)
        if c is None:
            skipped_unreadable += 1
            continue
        if target_family and target_family != "unknown" and c["base_family"] != "unknown":
            if c["base_family"] != target_family:
                skipped_base_mismatch += 1
                continue
        score = _score(intent_tokens, c["_tokens"], c["_tag_freq"])
        if score == 0:
            continue
        candidates.append({**c, "score": score})

    candidates.sort(key=lambda x: (-x["score"], x["filename"]))
    top = candidates[:k]
    # Strip internal fields before returning
    for c in top:
        c.pop("_tokens", None)
        c.pop("_tag_freq", None)

    return {
        "ok": True,
        "intent": intent,
        "base_model_requested": base_model,
        "base_family_normalized": target_family,
        "loras_root": str(loras_root),
        "total_scored": len(candidates),
        "returned": len(top),
        "skipped_base_mismatch": skipped_base_mismatch,
        "skipped_unreadable": skipped_unreadable,
        "candidates": top,
    }


# --- graph-inspection helpers (pure functions on UI workflow dicts) --------

# Node class_types we treat as "LoRA loaders" — covers stock + popular custom_nodes
_LORA_LOADER_TYPES = {
    "LoraLoader",
    "LoraLoaderModelOnly",
    "Power Lora Loader (rgthree)",
    "LoraStack",
    "LoraTagLoader",
    "Lora Loader Stack (rgthree)",
    "CR LoRA Stack",
    "Efficient Loader",  # has embedded LoRA stack via lora_name fields
}

# CLIPTextEncode-like classes that hold prompts. The "positive" one is identified
# by being downstream of the SAMPLER positive input, not by class name.
_TEXT_ENCODE_TYPES = {
    "CLIPTextEncode",
    "CLIPTextEncodeSDXL",
    "CLIPTextEncodeFlux",
    "BNK_CLIPTextEncodeAdvanced",
    "smZ CLIPTextEncode",
}


def find_lora_loader_nodes(graph_ui: dict[str, Any]) -> list[dict[str, Any]]:
    """Locate existing LoRA-loader-like nodes in a UI-format workflow.
    Returns a list of {id, class_type, lora_name_slots: [widget_names]} so the
    caller can decide whether to fill an empty slot or insert a new node."""
    nodes = graph_ui.get("nodes") or []
    found: list[dict[str, Any]] = []
    for n in nodes:
        if not isinstance(n, dict):
            continue
        cls = n.get("type")
        if cls not in _LORA_LOADER_TYPES:
            continue
        widgets = n.get("widgets_values") or []
        # Most loaders have widget order: [lora_name, strength_model, strength_clip]
        # or for stacks: [lora_name_1, strength_1, ..., lora_name_2, ...]
        found.append({
            "id": n.get("id"),
            "class_type": cls,
            "widget_count": len(widgets),
            "pos": n.get("pos"),
        })
    return found


def find_positive_clip_text_encode(graph_ui: dict[str, Any]) -> int | None:
    """Find the node feeding the sampler's `positive` input.

    Walks the graph's `links` array (UI format: [link_id, from_node, from_slot,
    to_node, to_slot, type]) to identify which CLIPTextEncode is wired into a
    sampler node's positive input.

    Returns the node_id (int) or None if undetectable."""
    nodes_by_id = {n.get("id"): n for n in (graph_ui.get("nodes") or []) if isinstance(n, dict)}
    links = graph_ui.get("links") or []

    sampler_types = {
        "KSampler", "KSamplerAdvanced", "SamplerCustom", "SamplerCustomAdvanced",
        "KSampler (Efficient)", "KSamplerSelect",
    }
    # Find sampler nodes
    sampler_ids = [nid for nid, n in nodes_by_id.items() if n.get("type") in sampler_types]
    if not sampler_ids:
        return None

    # For each link: if its to_node is a sampler and the to_input is named "positive"
    # (or slot index matches the sampler's positive input position), return from_node.
    for link in links:
        if not (isinstance(link, list) and len(link) >= 6):
            continue
        _link_id, from_node, _from_slot, to_node, to_slot, _link_type = link[:6]
        if to_node not in sampler_ids:
            continue
        # Determine if to_slot is the positive slot on this sampler. UI format
        # uses an `inputs` array on the node with named entries.
        sampler = nodes_by_id.get(to_node)
        if not sampler:
            continue
        inputs = sampler.get("inputs") or []
        if to_slot < len(inputs) and isinstance(inputs[to_slot], dict):
            if inputs[to_slot].get("name") == "positive":
                src = nodes_by_id.get(from_node)
                if src and src.get("type") in _TEXT_ENCODE_TYPES:
                    return from_node
    return None


def positive_text_widget_index(graph_ui: dict[str, Any], node_id: int) -> int | None:
    """Index into widgets_values where the prompt text lives. For all
    CLIPTextEncode-family nodes, this is 0 (the first widget)."""
    node = next(
        (n for n in graph_ui.get("nodes") or [] if isinstance(n, dict) and n.get("id") == node_id),
        None,
    )
    if not node:
        return None
    if (node.get("type") or "") not in _TEXT_ENCODE_TYPES:
        return None
    widgets = node.get("widgets_values") or []
    if widgets:
        return 0
    return None


def positive_text_widget_name(class_type: str) -> str:
    """The widget name (for set_widget calls) where prompt text lives, by class.
    Stock CLIPTextEncode uses 'text'; specialized variants may differ."""
    if class_type == "CLIPTextEncodeFlux":
        return "clip_l"  # Flux dual-encoder; clip_l is the main prompt slot
    return "text"


def append_to_prompt(existing: str, trigger_words: list[str]) -> str:
    """Append trigger words to an existing prompt string without duplicating ones
    already present (case-insensitive substring check)."""
    if not trigger_words:
        return existing
    existing_lc = (existing or "").lower()
    to_add = [t for t in trigger_words if t and t.lower() not in existing_lc]
    if not to_add:
        return existing
    sep = ", " if existing and not existing.rstrip().endswith(",") else ""
    return (existing or "") + sep + ", ".join(to_add)
