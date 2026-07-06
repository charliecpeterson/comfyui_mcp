"""Workflow summarization helpers: notes/model-ref extraction, top-types ranking,
graph structure description, file-based workflow describe, and the shared body builder."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import (
    _NOTE_NODE_TYPES,
    _MODEL_FILE_EXTS,
    _all_nodes,
    _combo_options,
    _comfy_root,
    _detect_format,
    _subgraph_def,
)


def _extract_notes(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract Note/MarkdownNote text from UI-format workflows, including nodes inside
    subgraph definitions. (API format doesn't carry these.)"""
    out: list[dict[str, Any]] = []
    if not isinstance(workflow.get("nodes"), list):
        return out
    for n in _all_nodes(workflow):
        t = n.get("type")
        if t not in _NOTE_NODE_TYPES:
            continue
        for v in n.get("widgets_values") or []:
            if isinstance(v, str) and v.strip():
                out.append({"type": t, "id": n.get("id"), "text": v.strip()})
    return out


def _extract_model_refs(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    """Find every widget value that looks like a model file (by extension), including
    inside subgraph definitions for UI-format workflows."""
    out: list[dict[str, Any]] = []
    if isinstance(workflow.get("nodes"), list):
        for n in _all_nodes(workflow):
            for v in n.get("widgets_values") or []:
                if isinstance(v, str) and v.lower().endswith(_MODEL_FILE_EXTS):
                    out.append({"node_id": n.get("id"), "node_type": n.get("type"), "value": v})
    elif isinstance(workflow, dict):
        for nid, nd in workflow.items():
            if not isinstance(nd, dict):
                continue
            for k, v in (nd.get("inputs") or {}).items():
                if isinstance(v, str) and v.lower().endswith(_MODEL_FILE_EXTS):
                    out.append(
                        {"node_id": nid, "node_type": nd.get("class_type"), "input": k, "value": v}
                    )
    return out


def _extract_model_widget_refs(workflow: dict[str, Any], fmt: str) -> list[dict[str, Any]]:
    """Like `_extract_model_refs` but always returns {node_id, class_type, input_name, value}
    regardless of UI vs API format. For UI format, maps positional widgets_values to
    input names via /object_info — but we can't do an async lookup here, so we fall back
    to a heuristic: emit each model-extension widget value with input_name=None when we
    can't infer it. Caller resolves names later as needed.

    For API format we already have explicit {input_name: value} mappings — much cleaner.
    """
    out: list[dict[str, Any]] = []
    if fmt == "api":
        for nid, nd in workflow.items():
            if not isinstance(nd, dict):
                continue
            class_type = nd.get("class_type")
            for k, v in (nd.get("inputs") or {}).items():
                if isinstance(v, str) and v.lower().endswith(_MODEL_FILE_EXTS):
                    out.append({"node_id": nid, "class_type": class_type, "input_name": k, "value": v})
        return out

    # UI format: walk nodes incl. subgraph contents. We don't know widget names without
    # /object_info, so use _ui_widget_order_aligned at validate-time to map them. Here
    # we just collect raw values; caller does the name resolution.
    if isinstance(workflow.get("nodes"), list):
        for n in _all_nodes(workflow):
            class_type = n.get("type")
            if not class_type:
                continue
            for v in n.get("widgets_values") or []:
                if isinstance(v, str) and v.lower().endswith(_MODEL_FILE_EXTS):
                    out.append({"node_id": n.get("id"), "class_type": class_type,
                                "input_name": None, "value": v})
    return out


def _required_inputs_with_defaults(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Every required-input name for a node class, per /object_info, with its declared
    type and default (when the schema provides one). Used to catch the "workflow saved
    against an older node version that lacked a since-added required input" class of
    bug — e.g. ImageScaleToTotalPixels gaining a required `resolution_steps` param — which
    only otherwise surfaces as a rejected /prompt after a full queue round-trip."""
    out: dict[str, dict[str, Any]] = {}
    inputs = spec.get("input", {}) if isinstance(spec, dict) else {}
    for name, decl in (inputs.get("required") or {}).items():
        t = decl[0] if isinstance(decl, (list, tuple)) and decl else decl
        opts = decl[1] if isinstance(decl, (list, tuple)) and len(decl) > 1 else {}
        opts = opts if isinstance(opts, dict) else {}
        out[name] = {
            "type": "ENUM" if _combo_options(decl) is not None else t,
            "default": opts.get("default"),
        }
    return out


def _valid_values_for_input(spec: dict[str, Any], input_name: str | None) -> Any:
    """Pull the valid_values list (the combo list) for a named input from /object_info.
    Returns the list, or None if not a combo. With input_name=None (UI-format fallback
    where we couldn't determine the name), scans all combo inputs and returns the first
    one that contains a model-extension entry — a reasonable approximation."""
    inputs = spec.get("input", {}) if isinstance(spec, dict) else {}
    for section in ("required", "optional"):
        decls = (inputs.get(section) or {})
        if input_name and input_name in decls:
            return _combo_options(decls[input_name])
        if input_name is None:
            for _name, decl in decls.items():
                t = _combo_options(decl)
                if t and isinstance(t[0], str) and t[0].lower().endswith(_MODEL_FILE_EXTS):
                    return t
    return None


def _top_node_types(workflow: dict[str, Any], n: int = 8) -> list[str]:
    counts: dict[str, int] = {}
    if isinstance(workflow.get("nodes"), list):
        for nd in _all_nodes(workflow):
            t = nd.get("type")
            # Skip subgraph instance "types" (UUIDs) — count their inner contents instead
            if t and not _subgraph_def(workflow, t):
                counts[t] = counts.get(t, 0) + 1
    elif isinstance(workflow, dict):
        for nd in workflow.values():
            if isinstance(nd, dict):
                t = nd.get("class_type")
                if t:
                    counts[t] = counts.get(t, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: -x[1])[:n]
    return [f"{t}×{c}" if c > 1 else t for t, c in ranked]


def _describe_graph(workflow: dict[str, Any]) -> dict[str, Any]:
    """Distill a UI-format workflow (with subgraphs) to its connection structure.

    Inner-subgraph nodes get path-style ids like '<outer>/<inner>'. Links are scoped to
    their container — outer-scope link refs use bare ids; inner-scope links reference
    other inner nodes via the same path prefix.
    """
    out_nodes: list[dict[str, Any]] = []
    orphans: list[str] = []
    total_links = 0

    def visit(scope_wf: dict[str, Any], path_prefix: str) -> None:
        nonlocal total_links
        scope_nodes = scope_wf.get("nodes") or []
        scope_links = scope_wf.get("links") or []
        total_links += len(scope_links)

        link_map: dict[Any, dict[str, Any]] = {}
        for ln in scope_links:
            if isinstance(ln, list) and len(ln) >= 6:
                # Top-level array format: [id, from_node, from_slot, to_node, to_slot, type]
                link_map[ln[0]] = {
                    "from_node": ln[1], "from_slot": ln[2],
                    "to_node": ln[3], "to_slot": ln[4], "type": ln[5],
                }
            elif isinstance(ln, dict) and ln.get("id") is not None:
                # Subgraph-definition dict format: {id, origin_id, origin_slot, target_id, target_slot, type}
                link_map[ln["id"]] = {
                    "from_node": ln.get("origin_id"), "from_slot": ln.get("origin_slot"),
                    "to_node": ln.get("target_id"), "to_slot": ln.get("target_slot"),
                    "type": ln.get("type"),
                }
        outgoing: dict[tuple[Any, int], list[Any]] = {}
        for lid, ln in link_map.items():
            outgoing.setdefault((ln["from_node"], ln["from_slot"]), []).append(lid)

        def to_path(local_id: Any) -> str:
            return f"{path_prefix}/{local_id}" if path_prefix else str(local_id)

        for n in scope_nodes:
            if not isinstance(n, dict):
                continue
            nid = n.get("id")
            ntype = n.get("type")
            path_id = to_path(nid)

            ins: list[dict[str, Any]] = []
            any_in = False
            for inp in n.get("inputs") or []:
                entry: dict[str, Any] = {"name": inp.get("name"), "type": inp.get("type")}
                lid = inp.get("link")
                if lid is not None and lid in link_map:
                    ln = link_map[lid]
                    entry["from"] = {"node": to_path(ln["from_node"]), "slot": ln["from_slot"]}
                    any_in = True
                ins.append(entry)

            outs: list[dict[str, Any]] = []
            any_out = False
            for i, out in enumerate(n.get("outputs") or []):
                tos = []
                for lid in outgoing.get((nid, i), []):
                    ln = link_map.get(lid)
                    if ln:
                        tos.append({"node": to_path(ln["to_node"]), "slot": ln["to_slot"]})
                if tos:
                    any_out = True
                outs.append({"name": out.get("name"), "type": out.get("type"), "to": tos})

            if not any_in and not any_out and (n.get("inputs") or n.get("outputs")):
                orphans.append(path_id)

            entry = {
                "id": path_id,
                "type": ntype,
                "pos": n.get("pos"),
                "inputs": ins,
                "outputs": outs,
            }
            sg = _subgraph_def(workflow, ntype)
            if sg is not None:
                entry["subgraph"] = {
                    "definition_id": sg.get("id"),
                    "name": sg.get("name"),
                    "inner_node_count": len(sg.get("nodes") or []),
                    "inputs": [i.get("name") for i in (sg.get("inputs") or []) if isinstance(i, dict)],
                    "outputs": [o.get("name") for o in (sg.get("outputs") or []) if isinstance(o, dict)],
                }
            out_nodes.append(entry)

            if sg is not None:
                visit(sg, path_id)

    visit(workflow, "")

    return {
        "node_count": len(out_nodes),
        "link_count": total_links,
        "orphans": orphans,
        "nodes": out_nodes,
    }


def _summarize_workflow_body(wf: dict[str, Any], summary_only: bool) -> dict[str, Any]:
    """Build the format/node_count/top_types/notes/refs body shared by both
    describe_workflow branches (tab and file). Subgraph-aware via _all_nodes."""
    fmt, count = _detect_format(wf)
    if fmt == "ui":
        count = sum(1 for _ in _all_nodes(wf))
    out: dict[str, Any] = {"format": fmt, "node_count": count, "top_types": _top_node_types(wf, n=8)}
    notes = _extract_notes(wf)
    if notes:
        out["notes_in_canvas"] = (
            [n["text"][:200] for n in notes[:3]] if summary_only else notes
        )
    refs = _extract_model_refs(wf)
    if refs:
        out["model_references"] = (
            [{"node_type": r["node_type"], "value": r["value"]} for r in refs]
            if summary_only else refs
        )
    if summary_only:
        out.pop("node_count", None)
    return out


def _describe_workflow_file(path: str, summary_only: bool = False) -> dict[str, Any]:
    """Sync helper for the file-path branch of describe_workflow. Used by catalog_workflows."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        try:
            root = _comfy_root() / "user" / "default" / "workflows"
            cand = root / path
            if cand.exists():
                p = cand
        except RuntimeError:
            pass
    p = p.resolve()
    if not p.is_file():
        return {"error": "not a file", "resolved_path": str(p)}

    try:
        wf = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        return {"error": f"invalid json: {e}", "path": str(p)}

    out: dict[str, Any] = {"path": str(p), **_summarize_workflow_body(wf, summary_only)}

    sidecar = p.with_suffix(".md")
    if sidecar.is_file():
        try:
            text = sidecar.read_text(errors="replace")
            out["sidecar_md_path"] = str(sidecar)
            out["sidecar_md"] = text[:6000]
        except OSError:
            pass

    folder_notes = p.parent / "_NOTES.md"
    if folder_notes.is_file():
        try:
            text = folder_notes.read_text(errors="replace")
            out["folder_notes_path"] = str(folder_notes)
            out["folder_notes"] = text[:4000]
        except OSError:
            pass

    return out
