"""Civitai API client + response shaping.

Reads CIVITAI_API_KEY from env, falling back to ~/.civitai_token. All functions
return lean dicts shaped for agent consumption — see _lean_item / _lean_detail /
_lean_version. The full Civitai response shape is bloated (21 top-level keys per
item, 28KB HTML descriptions); shipping it raw burns the agent's context window.

Safety rails:
  - Items where `minor=true` are dropped at every layer (never surface or download)
  - NSFW is opt-in via `nsfw=True`; default is SFW-only
  - Downloads are two-call: first call returns a preview, second call with
    `confirm=True` performs the write. Auto-routes to the correct ComfyUI
    subdir based on the model's type field.

The exploration in .scratch/explore_civitai.py established two non-obvious facts:
  - Default sort "Highest Rated" returns zero results for non-LoRA types.
    Default to "Most Downloaded" — universal across all types.
  - Civitai's declared trainedWords are often empty or wrong; the safetensors
    metadata in the downloaded file itself is canonical. We re-read after
    download and surface those instead.
"""
from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Any

import httpx

BASE = "https://civitai.com/api/v1"
DEFAULT_TIMEOUT = 30.0
DEFAULT_DOWNLOAD_TIMEOUT = 600.0  # streaming 250MB on a slow link

# Valid type strings accepted by Civitai's /models?types= filter.
VALID_TYPES = {
    "LORA", "Checkpoint", "Controlnet", "Upscaler", "TextualInversion",
    "VAE", "Hypernetwork", "MotionModule", "Poses", "Wildcards",
    "Workflows", "LoCon", "AestheticGradient", "Other",
}

# Civitai model type → ComfyUI models/ subdir. Auto-routes downloads.
_TYPE_TO_SUBDIR = {
    "LORA": "loras",
    "LoCon": "loras",
    "Checkpoint": "checkpoints",
    "Controlnet": "controlnet",
    "Upscaler": "upscale_models",
    "TextualInversion": "embeddings",
    "VAE": "vae",
    "Hypernetwork": "hypernetworks",
    "MotionModule": "animatediff_models",
}

# Allowed file format → file_type pairs per model type. Civitai bundles training
# data ZIPs and example images alongside the actual model file; we filter to
# what's actually loadable into ComfyUI.
_ACCEPTABLE_FILE = {
    "LORA":             {("Model", "SafeTensor")},
    "LoCon":            {("Model", "SafeTensor")},
    "Checkpoint":       {("Model", "SafeTensor"), ("Model", "PickleTensor")},
    "Controlnet":       {("Model", "SafeTensor"), ("Model", "PickleTensor")},
    "Upscaler":         {("Model", "SafeTensor"), ("Model", "PickleTensor"),
                         ("Model", "Other")},  # .pth is "Other" in Civitai's format enum
    "TextualInversion": {("Model", "SafeTensor"), ("Model", "PickleTensor")},
    "VAE":              {("Model", "SafeTensor"), ("Model", "PickleTensor")},
    "Hypernetwork":     {("Model", "SafeTensor"), ("Model", "PickleTensor")},
    "MotionModule":     {("Model", "SafeTensor"), ("Model", "PickleTensor")},
}


def _token() -> str | None:
    """Resolve API token: env var first, then ~/.civitai_token file."""
    tok = (os.environ.get("CIVITAI_API_KEY") or "").strip()
    if tok:
        return tok
    tf = Path.home() / ".civitai_token"
    if tf.is_file():
        try:
            tok = tf.read_text().strip()
            if tok:
                return tok
        except OSError:
            pass
    return None


def _headers() -> dict[str, str]:
    h = {"User-Agent": "comfyui-mcp/0.1"}
    tok = _token()
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def _html_strip(html: str, max_chars: int = 500) -> str:
    """Strip HTML tags + decode common entities, then truncate. Civitai descriptions
    are HTML; we surface a plain-text summary, not the markup."""
    if not html:
        return ""
    text = re.sub(r"<[^>]+>", " ", html)
    text = (text
            .replace("&nbsp;", " ").replace("&amp;", "&")
            .replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#39;", "'"))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def _is_minor(item: dict[str, Any]) -> bool:
    """Civitai marks content depicting minors with `minor=true`. Always filter these."""
    return bool(item.get("minor"))


def _primary_file(version: dict[str, Any], model_type: str) -> dict[str, Any] | None:
    """Pick the actual loadable model file from a modelVersion's files list.
    Civitai bundles training_data ZIPs, example images, etc — we filter to the
    type/format pairs ComfyUI can load for this model_type."""
    files = version.get("files") or []
    acceptable = _ACCEPTABLE_FILE.get(model_type, {("Model", "SafeTensor")})
    for f in files:
        ftype = f.get("type")
        fmt = (f.get("metadata") or {}).get("format")
        if (ftype, fmt) in acceptable:
            return f
    # No acceptable file — return None so caller can error cleanly.
    return None


def _lean_version(version: dict[str, Any], model_type: str) -> dict[str, Any]:
    """Compact a modelVersion to the fields the agent uses."""
    pf = _primary_file(version, model_type)
    images = version.get("images") or []
    primary_image = None
    if images:
        img = images[0]
        primary_image = {
            "url": img.get("url"),
            "nsfw_level": img.get("nsfwLevel"),
            "width": img.get("width"),
            "height": img.get("height"),
        }
    return {
        "version_id": version.get("id"),
        "version_name": version.get("name"),
        "base_model": version.get("baseModel"),
        "base_model_type": version.get("baseModelType"),
        "trained_words": version.get("trainedWords") or [],
        "file": (
            {
                "name": pf.get("name"),
                "size_kb": pf.get("sizeKB"),
                "size_mb": round((pf.get("sizeKB") or 0) / 1024, 1),
                "type": pf.get("type"),
                "format": (pf.get("metadata") or {}).get("format"),
                "download_url": pf.get("downloadUrl"),
            }
            if pf
            else None
        ),
        "no_acceptable_file": pf is None,
        "primary_image": primary_image,
        "published_at": version.get("publishedAt"),
    }


def _lean_item(item: dict[str, Any]) -> dict[str, Any]:
    """Compact a search-result item. Drops license flags, internal toggles, etc."""
    stats = item.get("stats") or {}
    creator = item.get("creator") or {}
    versions = item.get("modelVersions") or []
    model_type = item.get("type") or "Other"
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "type": model_type,
        "tags": (item.get("tags") or [])[:8],
        "creator": creator.get("username"),
        "nsfw": item.get("nsfw"),
        "poi": item.get("poi"),  # person-of-interest (celebrity likeness LoRA)
        "downloads": stats.get("downloadCount"),
        "thumbs_up": stats.get("thumbsUpCount"),
        "rating": stats.get("rating"),
        "versions": [_lean_version(v, model_type) for v in versions],
    }


def _lean_detail(item: dict[str, Any]) -> dict[str, Any]:
    """Compact /models/{id}. Same as _lean_item but adds plain-text description."""
    out = _lean_item(item)
    out["description"] = _html_strip(item.get("description") or "", max_chars=800)
    return out


async def search(
    query: str,
    types: str | list[str] = "LORA",
    base_model: str | list[str] | None = None,
    nsfw: bool = False,
    sort: str = "Most Downloaded",
    limit: int = 10,
    api_token_required: bool = False,
) -> dict[str, Any]:
    """Search Civitai for models. See module docstring for safety rails.

    `types` accepts a single value or list. Civitai's API takes comma-separated
    but httpx will encode a list as repeated params, which Civitai also accepts.
    """
    types_list = [types] if isinstance(types, str) else list(types)
    bad = [t for t in types_list if t not in VALID_TYPES]
    if bad:
        return {"ok": False, "error": f"unknown type(s) {bad}; valid: {sorted(VALID_TYPES)}"}

    params: list[tuple[str, str]] = []
    if query:
        params.append(("query", query))
    for t in types_list:
        params.append(("types", t))
    params.append(("limit", str(limit)))
    params.append(("sort", sort))
    params.append(("nsfw", "true" if nsfw else "false"))
    if base_model:
        bms = [base_model] if isinstance(base_model, str) else list(base_model)
        for bm in bms:
            params.append(("baseModels", bm))

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as c:
            r = await c.get(f"{BASE}/models", params=params, headers=_headers())
            if r.status_code == 401:
                return {"ok": False, "error": "401 Unauthorized — CIVITAI_API_KEY missing or invalid",
                        "hint": "set CIVITAI_API_KEY env var or write to ~/.civitai_token"}
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        return {"ok": False, "error": f"HTTP error: {e}"}

    raw_items = data.get("items") or []
    items = [_lean_item(i) for i in raw_items if not _is_minor(i)]
    dropped_minor = sum(1 for i in raw_items if _is_minor(i))

    result: dict[str, Any] = {
        "ok": True,
        "query": query,
        "types": types_list,
        "base_model": base_model,
        "sort": sort,
        "nsfw": nsfw,
        "count": len(items),
        "items": items,
    }
    if dropped_minor:
        result["dropped_minor"] = dropped_minor
    cursor = (data.get("metadata") or {}).get("nextCursor")
    if cursor:
        result["next_cursor"] = cursor
    return result


async def describe(model_id: int) -> dict[str, Any]:
    """Fetch full model detail by ID. Returns lean shape with plain-text description."""
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as c:
            r = await c.get(f"{BASE}/models/{model_id}", headers=_headers())
            if r.status_code == 401:
                return {"ok": False, "error": "401 Unauthorized — CIVITAI_API_KEY missing or invalid"}
            if r.status_code == 404:
                return {"ok": False, "error": f"model {model_id} not found"}
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        return {"ok": False, "error": f"HTTP error: {e}"}

    if _is_minor(data):
        return {"ok": False, "error": f"model {model_id} marked as involving a minor; refusing to surface"}

    return {"ok": True, **_lean_detail(data)}


def _resolve_target_path(
    comfy_root: Path,
    model_type: str,
    filename: str,
    subdir: str | None,
) -> tuple[Path | None, str | None]:
    """Compute the on-disk target path. Returns (path, error). Path is None on error."""
    base_subdir = _TYPE_TO_SUBDIR.get(model_type)
    if base_subdir is None:
        return None, f"no auto-route for Civitai type {model_type!r}; pass subdir explicitly"
    target_dir = comfy_root / "models" / base_subdir
    if subdir:
        # Defensive: prevent path traversal escaping models/<base_subdir>/
        sd = Path(subdir)
        if sd.is_absolute() or ".." in sd.parts:
            return None, f"invalid subdir {subdir!r}: must be a relative path with no '..'"
        target_dir = target_dir / sd
    # Defensive: filename must be a bare filename, not a path
    if "/" in filename or "\\" in filename:
        return None, f"invalid filename {filename!r}: must contain no path separators"
    return target_dir / filename, None


async def download(
    model_id: int,
    version_id: int | None = None,
    subdir: str | None = None,
    confirm: bool = False,
    overwrite: bool = False,
    comfy_root: Path | None = None,
) -> dict[str, Any]:
    """Two-call confirm-gated download.

    First call (confirm=False, the default): returns a preview dict with the
    target path, file size, and download URL. Nothing written.

    Second call (confirm=True): streams the file to disk. Auto-routes by model
    type. Refuses to overwrite existing files unless `overwrite=True`.

    If `version_id` is None, uses the model's first (newest) version.
    """
    if comfy_root is None:
        # Lazy import — core resolves cwd / port-listener etc on first call
        from .core import _comfy_root
        comfy_root = _comfy_root()

    # Fetch the model detail to know type, filename, size, URL
    detail = await describe(model_id)
    if not detail.get("ok"):
        return detail
    model_type = detail.get("type")
    versions = detail.get("versions") or []
    if not versions:
        return {"ok": False, "error": f"model {model_id} has no versions"}

    version = None
    if version_id is None:
        version = versions[0]
    else:
        for v in versions:
            if v.get("version_id") == version_id:
                version = v
                break
        if version is None:
            return {"ok": False, "error": f"version {version_id} not found on model {model_id}",
                    "available_versions": [v.get("version_id") for v in versions]}

    if version.get("no_acceptable_file"):
        return {"ok": False, "error": f"no acceptable file (type=Model, format=SafeTensor/PickleTensor/Other) "
                                       f"in version {version.get('version_id')} of model {model_id}",
                "hint": "this version may have only training-data ZIPs or example images"}

    file_info = version["file"]
    download_url = file_info.get("download_url")
    if not download_url:
        return {"ok": False, "error": "version's file has no downloadUrl"}

    target_path, err = _resolve_target_path(
        comfy_root=comfy_root,
        model_type=model_type,
        filename=file_info["name"],
        subdir=subdir,
    )
    if err:
        return {"ok": False, "error": err}

    preview = {
        "model_id": model_id,
        "model_name": detail.get("name"),
        "version_id": version.get("version_id"),
        "version_name": version.get("version_name"),
        "base_model": version.get("base_model"),
        "type": model_type,
        "would_download_mb": file_info.get("size_mb"),
        "filename": file_info["name"],
        "to_path": str(target_path),
        "download_url": download_url,
        "trained_words_declared": version.get("trained_words") or [],
        "trained_words_note": "declared on Civitai — often empty/outdated; the actual "
                              "safetensors metadata is canonical and will be re-read post-download",
        "exists_already": target_path.exists(),
    }

    if not confirm:
        return {"ok": True, "preview": preview,
                "next_step": "call again with confirm=True to perform the download"}

    if target_path.exists() and not overwrite:
        return {"ok": False, "error": f"file already exists at {target_path}; pass overwrite=True to replace"}

    # Stream to disk
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_suffix(target_path.suffix + ".part")
    bytes_written = 0
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_DOWNLOAD_TIMEOUT, follow_redirects=True) as c:
            async with c.stream("GET", download_url, headers=_headers()) as r:
                if r.status_code == 401:
                    return {"ok": False, "error": "401 Unauthorized on download — token required for this file"}
                r.raise_for_status()
                with tmp_path.open("wb") as out:
                    async for chunk in r.aiter_bytes(chunk_size=1 << 20):  # 1MB
                        out.write(chunk)
                        bytes_written += len(chunk)
    except httpx.HTTPError as e:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        return {"ok": False, "error": f"download failed: {e}"}

    # Atomic-ish rename so a partial file doesn't masquerade as complete
    shutil.move(str(tmp_path), str(target_path))

    # Re-read the canonical trigger words from the downloaded file's metadata
    canonical_trigger_words: list[str] = []
    safetensors_meta_summary: dict[str, Any] | None = None
    if target_path.suffix.lower() == ".safetensors":
        try:
            from .model_meta import _read_safetensors_metadata, _top_training_tags
            sf = _read_safetensors_metadata(target_path)
            if "error" not in sf:
                meta = sf.get("metadata") or {}
                trigger_phrase = meta.get("modelspec.trigger_phrase")
                if trigger_phrase:
                    canonical_trigger_words.append(trigger_phrase)
                top_tags = _top_training_tags(meta, limit=10)
                if top_tags:
                    safetensors_meta_summary = {
                        "trigger_phrase": trigger_phrase,
                        "top_training_tags": top_tags,
                        "architecture": meta.get("modelspec.architecture") or meta.get("ss_base_model_version"),
                    }
        except Exception as e:
            safetensors_meta_summary = {"error": f"metadata read failed: {e}"}

    return {
        "ok": True,
        "downloaded": True,
        "path": str(target_path),
        "bytes_written": bytes_written,
        "size_mb": round(bytes_written / 1_048_576, 1),
        "model_id": model_id,
        "version_id": version.get("version_id"),
        "type": model_type,
        "base_model": version.get("base_model"),
        "filename": file_info["name"],
        "trained_words_declared": version.get("trained_words") or [],
        "trained_words_canonical": canonical_trigger_words,
        "safetensors_metadata_summary": safetensors_meta_summary,
        "hint": "use add_lora_to_workflow(filename) to inject into the open workflow",
    }
