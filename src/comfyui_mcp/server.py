from __future__ import annotations

import base64
import copy
import itertools
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP, Image

from .comfy import ComfyClient

mcp = FastMCP("comfyui-mcp")
comfy = ComfyClient()


@mcp.tool()
async def get_system_stats() -> dict[str, Any]:
    """Return ComfyUI system info: device, vram, python/comfy version. Use this as a smoke test."""
    return await comfy.system_stats()


_SEARCH_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "for", "with", "in", "on",
    "is", "are", "from", "by", "this", "that", "node", "nodes",
}


def _score_query_match(name: str, category: str, description: str, tokens: list[str]) -> int:
    """All tokens must match somewhere; score by where (name>category>description)."""
    name_l = name.lower()
    cat_l = (category or "").lower()
    desc_l = (description or "").lower()
    total = 0
    for t in tokens:
        ts = 0
        if t == name_l:
            ts = 200
        elif t in name_l:
            ts = 80
        if t in cat_l:
            ts = max(ts, 60)
        if t in desc_l:
            ts = max(ts, 40)
        if ts == 0:
            return 0
        total += ts
    return total


@mcp.tool()
async def search_nodes(
    query: str = "",
    input_type: str = "",
    output_type: str = "",
    limit: int = 30,
) -> list[dict[str, Any]]:
    """Smart search across installed ComfyUI nodes by free-text query and/or socket types.

    BEFORE REACHING FOR THIS: building workflows from scratch via search_nodes is rare
    and expensive. Most tasks should start from an existing workflow:
      • catalog_workflows() — see what's already in the user's library
      • get_open_workflow() / describe_graph() — see what's open in their tab
      • Then modify it via set_widget / add_node / connect_nodes
    Use search_nodes when you need to ADD a specific capability (a detailer, an
    upscaler, a controlnet preprocessor) to an existing workflow — not as the
    first step of "build me a workflow that does X."

    Multi-word queries: every non-stopword token must match somewhere in the node's name,
    category, OR description. Results ranked by where the match occurred (name > category
    > description) and by exact-match strength.

    Examples:
      search_nodes("upscale image with model") → finds ImageUpscaleWithModel etc.
      search_nodes("ksampler", output_type="LATENT")
      search_nodes(input_type="CONDITIONING", output_type="CONDITIONING")  # conditioning ops

    Args:
        query: free text. Whitespace-split. Stopwords ignored: with/a/the/for/to/of...
        input_type: socket type a node must accept (case-insensitive). E.g. "IMAGE".
        output_type: socket type a node must produce.
        limit: max results.

    Returns: list of {name, category, description, inputs, outputs, score}.
    Description truncated to 200 chars; call get_object_info(class_name) for the full record.
    """
    info = await comfy.object_info()
    in_t = input_type.upper()
    out_t = output_type.upper()
    tokens = [t for t in query.lower().split() if t and t not in _SEARCH_STOPWORDS]

    scored: list[tuple[int, dict[str, Any]]] = []
    for name, node in info.items():
        category = node.get("category") or ""
        description = node.get("description") or ""

        score = _score_query_match(name, category, description, tokens) if tokens else 1
        if score == 0:
            continue

        inputs = _flatten_inputs(node.get("input", {}))
        outputs = list(node.get("output", []) or [])

        if in_t and not any(_socket_type(t) == in_t for _, t in inputs):
            continue
        if out_t and out_t not in (_socket_type(t) for t in outputs):
            continue

        scored.append(
            (
                score,
                {
                    "name": name,
                    "category": category,
                    "description": description[:200] if description else "",
                    "inputs": [{"name": n, "type": _socket_type(t)} for n, t in inputs],
                    "outputs": [_socket_type(t) for t in outputs],
                    "score": score,
                },
            )
        )

    scored.sort(key=lambda x: (-x[0], x[1]["name"]))
    return [r for _, r in scored[:limit]]


@mcp.tool()
async def get_current_execution(timeout: int = 1) -> dict[str, Any]:
    """Snapshot of what ComfyUI is doing right now, for non-blocking progress checks.

    Reads /queue for running + pending counts, then briefly subscribes to the WebSocket
    (~timeout seconds) to capture in-flight progress and executing-node events.

    Returns:
      {running: [{prompt_id, number, node_count}],
       pending_count: N,
       current_node: <id or null>,
       current_class_type: <str or null>,
       progress: {value, max, node} | null,
       last_executed_node: <id or null>}

    Use during a long run to confirm "still alive, sampler is on step 12/25" without
    blocking with wait_for_completion. Call repeatedly to watch progress.
    """
    queue = await comfy.queue_state()
    running_raw = queue.get("queue_running") or []
    pending_count = len(queue.get("queue_pending") or [])

    running_pid: str | None = None
    running_graph: dict[str, Any] | None = None
    running_compact: list[dict[str, Any]] = []
    for entry in running_raw:
        if isinstance(entry, list) and len(entry) >= 3:
            number, pid, graph = entry[0], entry[1], entry[2]
            if running_pid is None:
                running_pid = pid
                running_graph = graph if isinstance(graph, dict) else None
            running_compact.append(
                {
                    "prompt_id": pid,
                    "number": number,
                    "node_count": len(graph) if isinstance(graph, dict) else None,
                }
            )

    progress: dict[str, Any] | None = None
    executing_node = None
    last_executed = None
    if running_pid:
        events = await comfy.poll_events(timeout=float(timeout))
        for ev in events:
            t = ev.get("type")
            payload = ev.get("data") or {}
            if t == "progress":
                progress = {
                    "value": payload.get("value"),
                    "max": payload.get("max"),
                    "node": payload.get("node"),
                }
            elif t == "executing":
                if not payload.get("prompt_id") or payload.get("prompt_id") == running_pid:
                    executing_node = payload.get("node")
            elif t == "executed":
                if not payload.get("prompt_id") or payload.get("prompt_id") == running_pid:
                    last_executed = payload.get("node")

    current_class_type = None
    if executing_node and running_graph:
        node = running_graph.get(str(executing_node)) or running_graph.get(executing_node)
        if isinstance(node, dict):
            current_class_type = node.get("class_type")

    return {
        "running": running_compact,
        "pending_count": pending_count,
        "current_node": executing_node,
        "current_class_type": current_class_type,
        "progress": progress,
        "last_executed_node": last_executed,
    }


@mcp.tool()
async def queue_workflow(
    workflow: dict[str, Any] | None = None,
    tab_id: str = "",
    client_id: str = "",
) -> dict[str, Any]:
    """Submit a workflow for execution. Prefer the no-args form when possible.

    PREFERRED: omit `workflow=`. Queues whatever is open in the user's ComfyUI tab,
    forwards the tab's ComfyUI client_id so live PreviewImage events stream back to
    them. The user sees what's running on their canvas.

    `workflow=` is for headless/batch only. The submitted graph won't appear in the
    user's tab and they have no UI-side visibility into it. Most flows that reach
    for `workflow=` are reconstructing a graph the user already has — check
    catalog_workflows() first, or modify the open tab via set_widget instead.

    On success returns {ok: true, prompt_id, number, node_errors}. On validation
    failure returns {ok: false, error, node_errors} (with valid_values backfilled
    from /object_info).
    """
    effective_client_id: str | None = client_id or None
    if workflow is None:
        wf, state, err = await _workflow_from_tab(tab_id=tab_id, want_api=True)
        if err:
            return err
        workflow = wf  # type: ignore[assignment]
        if not effective_client_id:
            effective_client_id = state.get("comfy_client_id") if state else None
    elif "nodes" in workflow and "links" in workflow:
        return {
            "ok": False,
            "error": "workflow appears to be UI format; need API format",
            "node_errors": {},
        }
    return await _queue_and_enrich(workflow, client_id=effective_client_id)


@mcp.tool()
async def get_history(
    prompt_id: str = "",
    max_items: int = 10,
    compact: bool = True,
) -> dict[str, Any]:
    """Retrieve execution history. With prompt_id, returns just that run; otherwise the most recent runs.

    Each run includes status and outputs. Output entries from image-saving nodes have
    {filename, subfolder, type} — pass those to view_image to see the result.

    Args:
        prompt_id: specific run to fetch; if empty, list recent runs.
        max_items: max entries when listing (ignored when prompt_id is set).
        compact: drop the verbose original prompt graph from each entry to save tokens.
    """
    raw = await comfy.history(prompt_id=prompt_id or None, max_items=max_items if not prompt_id else None)
    if not compact:
        return raw
    out: dict[str, Any] = {}
    for pid, entry in raw.items():
        out[pid] = {
            "status": entry.get("status"),
            "outputs": entry.get("outputs"),
            "meta": entry.get("meta"),
        }
    return out


@mcp.tool()
async def view_image(filename: str, subfolder: str = "", type: str = "output") -> Any:
    """Image-only alias for view_file. Returns inline Image content for png/jpg/webp/gif;
    errors on non-image content types. Prefer view_file for general use (handles video/audio
    too). Type must be one of: "output" (default), "input", "temp".
    """
    return await view_file(filename, subfolder=subfolder, type=type)


@mcp.tool()
async def edit_workflow(
    workflow: dict[str, Any],
    edits: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Patch one or more nodes in a workflow without re-sending the whole graph.

    Auto-detects API vs UI format and routes accordingly.
    - API format: directly sets workflow[node_id]["inputs"][input_name] = value.
    - UI format: maps input name -> widget index via /object_info, edits widgets_values[i].

    Args:
        workflow: API or UI format (returned by read_workflow / get_open_workflow).
        edits: {node_id: {input_name: value, ...}, ...}. node_id is a string.
               For nodes inside subgraphs (UI format), use path syntax: '<outer_id>/<inner_id>',
               e.g. '59/65' for inner node 65 inside subgraph instance 59. Get the paths from
               describe_graph (which now recurses into subgraphs and emits path-style ids).
               NOTE: editing an inner node mutates the SHARED subgraph definition — all
               outer instances of that subgraph type will see the change.
               value can be a literal (int/float/str/bool/list) OR a socket reference like
               ["3", 0] (output 0 of node 3) for API format.

    Returns: {workflow, format, applied: [{node_id, inputs}], errors: [...]}.
    Errors do not abort: edits that work succeed, edits that fail are reported.
    """
    fmt, _ = _detect_format(workflow)
    if fmt == "api":
        return await _edit_api(workflow, edits)
    if fmt == "ui":
        return await _edit_ui(workflow, edits)
    return {"error": "workflow is not a recognizable format", "format": fmt}


@mcp.tool()
async def batch_run(
    workflow: dict[str, Any],
    params_grid: dict[str, list[Any]],
    mode: str = "grid",
    max_runs: int = 16,
    queue: bool = True,
) -> dict[str, Any]:
    """Sweep a workflow across parameter combinations and queue each run.

    Args:
        workflow: API-format workflow (use convert tools or save with format="api").
        params_grid: {"<node_id>.<input_name>": [v1, v2, ...]}. Example:
                     {"3.seed": [1,2,3], "5.cfg": [3.0, 7.5]}.
        mode: "grid" — cartesian product (3 seeds × 2 cfgs = 6 runs).
              "zip"  — parallel arrays of equal length (3 runs, paired).
        max_runs: hard cap to prevent runaway sweeps. Raise explicitly if you want more.
        queue: True submits each variant to ComfyUI immediately and returns prompt_ids.
               False is dry-run: returns the generated workflows for inspection without queueing.

    Returns: {mode, count, runs: [{params, prompt_id?, queued|workflow, error?}]}.
    Pair with wait_for_completion(prompt_id) per run, or get_queue() to monitor progress.
    """
    fmt, _ = _detect_format(workflow)
    if fmt != "api":
        return {"error": f"batch_run requires API-format workflow; got {fmt}"}

    parsed: list[tuple[str, str, list[Any]]] = []
    for key, values in params_grid.items():
        if "." not in key:
            return {"error": f"key {key!r} must be 'node_id.input_name'"}
        node_id, input_name = key.split(".", 1)
        parsed.append((node_id, input_name, list(values)))

    if mode == "grid":
        combos = list(itertools.product(*[v for _, _, v in parsed]))
    elif mode == "zip":
        lengths = {len(v) for _, _, v in parsed}
        if len(lengths) > 1:
            return {"error": f"zip mode needs equal-length lists; got {lengths}"}
        combos = list(zip(*[v for _, _, v in parsed]))
    else:
        return {"error": f"unknown mode {mode!r}; use 'grid' or 'zip'"}

    if not combos:
        return {"error": "no parameter combinations generated"}
    if len(combos) > max_runs:
        return {
            "error": f"{len(combos)} runs exceeds max_runs={max_runs}; raise the limit explicitly",
            "count": len(combos),
        }

    runs: list[dict[str, Any]] = []
    for combo in combos:
        wf = copy.deepcopy(workflow)
        params: dict[str, Any] = {}
        for (node_id, input_name, _), value in zip(parsed, combo):
            wf.setdefault(node_id, {}).setdefault("inputs", {})[input_name] = value
            params[f"{node_id}.{input_name}"] = value
        entry: dict[str, Any] = {"params": params}
        if queue:
            status, body = await comfy.queue(wf)
            if status == 200:
                entry["queued"] = True
                entry["prompt_id"] = body.get("prompt_id")
            else:
                entry["queued"] = False
                entry["error"] = body
        else:
            entry["workflow"] = wf
        runs.append(entry)

    return {"mode": mode, "count": len(runs), "runs": runs}


@mcp.tool()
async def describe_workflow(
    path: str = "",
    summary_only: bool = False,
    tab_id: str = "",
) -> dict[str, Any]:
    """Structured summary of a workflow: in-canvas Note/MarkdownNote text, sidecar `.md`
    next to it, parent folder's `_NOTES.md`, top node types, model references, orphans.
    Mirrors describe_model for workflows. Subgraph-aware (recurses into subgraph
    definitions for top_types, model_refs, and notes).

    With no `path`, describes the workflow open in the most-recently-edited tab (no
    sidecar/folder_notes available in that case — the tab's workflow isn't on disk).
    Pass `path` to describe a file on disk; pass `tab_id` to target a specific tab.

    Returns:
      {path?|tab_id?, format, node_count, top_types, notes_in_canvas, sidecar_md?,
       folder_notes?, model_references: [{node_type, value}, ...], orphans?}
    With summary_only=True, drops node_count details and trims notes — for catalog use.
    """
    if not path:
        wf, state, err = await _workflow_from_tab(tab_id=tab_id, want_api=False)
        if err:
            return err
        out = _summarize_workflow_body(wf, summary_only)
        out["tab_id"] = state.get("tab_id") if state else None
        return out

    return _describe_workflow_file(path, summary_only)


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


@mcp.tool()
def catalog_workflows(
    dir: str = "",
    recursive: bool = True,
    query: str = "",
    type_contains: str = "",
    model_contains: str = "",
    limit: int = 0,
) -> dict[str, Any]:
    """Bulk describe_workflow over a tree. Returns compact per-file summaries the agent
    can scan to answer "which workflow should I use for X?" without reading every JSON.

    Defaults to <COMFYUI_ROOT>/user/default/workflows (follows symlinks; handles dangling
    symlinks gracefully). Each entry has {rel_path, top_types, notes_in_canvas (top 3,
    truncated), sidecar_md (first 800 chars), model_references, error?}.

    Server-side filtering (case-insensitive, all optional, AND-combined):
      query: substring match against rel_path / notes / sidecar / top_types names.
             Pre-prune the catalog to only workflows that look relevant.
      type_contains: only entries whose top_types include this substring
                     (e.g. "ControlNet", "FaceDetailer", "LoraLoader").
      model_contains: only entries whose model_references include this substring
                      (e.g. "illustrious", "flux", "z_image").
      limit: cap returned entries (0 = all).

    Use these to keep responses under a few KB even on large libraries.
    """
    base = Path(dir) if dir else _comfy_root() / "user" / "default" / "workflows"
    if not base.exists():
        return {"root": str(base), "error": "not found (broken symlink?)", "entries": []}
    if not base.is_dir():
        return {"root": str(base), "error": "not a directory"}

    q = query.lower()
    type_q = type_contains.lower()
    model_q = model_contains.lower()

    entries: list[dict[str, Any]] = []
    folder_notes_seen: dict[str, str] = {}
    total_scanned = 0

    iterator = base.rglob("*.json") if recursive else base.glob("*.json")
    for jf in sorted(iterator):
        if not jf.is_file():
            continue
        total_scanned += 1
        summary = _describe_workflow_file(str(jf), summary_only=True)
        if "sidecar_md" in summary:
            summary["sidecar_md"] = summary["sidecar_md"][:800]

        rel_path = str(jf.relative_to(base))
        top_types_str = " ".join(summary.get("top_types") or []).lower()
        model_refs_str = " ".join(
            (m.get("value", "") or "")
            for m in (summary.get("model_references") or [])
        ).lower()
        notes_str = " ".join(
            (n if isinstance(n, str) else (n.get("text", "") if isinstance(n, dict) else ""))
            for n in (summary.get("notes_in_canvas") or [])
        ).lower()
        sidecar_str = (summary.get("sidecar_md") or "").lower() if isinstance(summary.get("sidecar_md"), str) else ""

        if q:
            if q not in rel_path.lower() and q not in top_types_str \
               and q not in notes_str and q not in sidecar_str:
                continue
        if type_q and type_q not in top_types_str:
            continue
        if model_q and model_q not in model_refs_str:
            continue

        folder_dir = str(jf.parent)
        if folder_dir not in folder_notes_seen and "folder_notes" in summary:
            folder_notes_seen[folder_dir] = summary["folder_notes"][:600]
        summary.pop("folder_notes", None)
        summary.pop("folder_notes_path", None)

        entry = {"rel_path": rel_path, **summary}
        entry.pop("path", None)
        entries.append(entry)
        if limit and len(entries) >= limit:
            break

    return {
        "root": str(base),
        "count": len(entries),
        "scanned": total_scanned,
        "filters": {"query": query, "type_contains": type_contains, "model_contains": model_contains, "limit": limit},
        "folder_notes": folder_notes_seen,
        "entries": entries,
    }


@mcp.tool()
async def describe_graph(
    workflow: dict[str, Any] | None = None,
    tab_id: str = "",
    include_widgets: bool = False,
) -> dict[str, Any]:
    """Compact, token-efficient structural summary of a UI-format workflow.

    Per node: {id, type, pos, inputs: [{name, type, from?: {node, slot}}],
                                outputs: [{name, type, to: [{node, slot}, ...]}]}.
    Strips widget values, sizes, colors, and other UI cruft. Purpose-built for cleanup
    reasoning ("find dead Reroutes", "which CLIPTextEncode is unused", "trace the model
    path") without paying for the full workflow JSON.

    With no arguments, describes the workflow open in the most-recently-edited tab.
    Pass `workflow` to describe an arbitrary UI-format workflow (from read_workflow).
    Pass `tab_id` to target a specific tab.

    With `include_widgets=True`, every node also gets a `widgets: [{name, value}, ...]`
    field with name-resolved widget values (same alignment-fallback as get_node_widgets).
    Replaces the "fan out N parallel get_node_widgets calls" pattern when the agent
    wants whole-workflow values inline. Adds one /object_info call per unique class_type.

    SUBGRAPHS: recursively descends into subgraph definitions. Inner nodes get path-style
    ids like '59/65'. Subgraph instance nodes are tagged with `subgraph: {name, ...}`.
    """
    if workflow is None:
        wf, state, err = await _workflow_from_tab(tab_id=tab_id, want_api=False)
        if err:
            return err
        summary = _describe_graph(wf)
        if include_widgets:
            await _attach_widgets(summary, wf)
        summary["tab_id"] = state.get("tab_id") if state else None
        summary["label"] = state.get("label") if state else None
        return summary
    summary = _describe_graph(workflow)
    if include_widgets:
        await _attach_widgets(summary, workflow)
    return summary


async def _attach_widgets(summary: dict[str, Any], workflow: dict[str, Any]) -> None:
    """Mutate `summary` in place: each node entry gets a `widgets: [{name, value}]` list."""
    # Build a quick lookup: path_id → node from the original workflow
    path_to_raw_values: dict[str, list[Any]] = {}
    path_to_class: dict[str, str] = {}
    for entry in summary.get("nodes") or []:
        path_id = entry.get("id")
        if not path_id:
            continue
        node, _ = _resolve_node_path(workflow, path_id)
        if node is None:
            continue
        path_to_raw_values[path_id] = list(node.get("widgets_values") or [])
        ct = node.get("type")
        if ct:
            path_to_class[path_id] = ct

    # Resolve widget orders (cache per class_type)
    order_cache: dict[str, tuple[list[str], str]] = {}
    for entry in summary.get("nodes") or []:
        path_id = entry.get("id")
        class_type = path_to_class.get(path_id)
        raw = path_to_raw_values.get(path_id, [])
        if not class_type or not raw:
            continue
        cache_key = f"{class_type}:{len(raw)}"
        if cache_key not in order_cache:
            try:
                order_cache[cache_key] = await _ui_widget_order_aligned(class_type, len(raw))
            except Exception:
                order_cache[cache_key] = ([], "")
        order, confidence = order_cache[cache_key]
        if order:
            entry["widgets"] = [
                {"name": order[i] if i < len(order) else f"<idx_{i}>",
                 "value": raw[i] if i < len(raw) else None}
                for i in range(min(len(order), len(raw)))
            ]
            if confidence == "best_guess":
                entry["alignment_warning"] = "widget names may not align with values"
        elif raw:
            entry["widgets_values"] = raw  # raw fallback when no schema available


@mcp.tool()
async def describe_subgraph(
    definition_id: str = "",
    tab_id: str = "",
    workflow: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Structural summary of a subgraph DEFINITION (the reusable template).

    Like describe_graph but scoped to one subgraph: lists inner nodes, exposed
    inputs/outputs, and proxy widgets that surface inner widgets at the instance
    level. Replaces the "read raw JSON to find proxy widgets" workflow.

    Args:
        definition_id: the subgraph type UUID (from describe_graph's subgraph.definition_id
                       or get_open_workflow(format="summary").subgraph_ids).
        tab_id: target a specific tab; defaults to most-recently-edited.
        workflow: explicit UI-format workflow to read from (e.g. via read_workflow).
                  Skips the bridge round-trip.

    Returns:
      {definition_id, name, inner_node_count, inner_link_count,
       inputs:  [{name, type, exposed_at_instance: bool}, ...],
       outputs: [{name, type, exposed_at_instance: bool}, ...],
       widget_proxies: [{instance_widget_name, target_inner_node_id,
                         target_inner_widget_name}, ...],
       inner_nodes: [{id, type, pos, ...same shape as describe_graph}, ...]}
       or {error}.
    """
    if workflow is None:
        wf, _state, err = await _workflow_from_tab(tab_id=tab_id, want_api=False)
        if err:
            return err
        workflow = wf  # type: ignore[assignment]

    if not isinstance(workflow, dict):
        return {"error": "no workflow available"}
    if not definition_id:
        defs = (workflow.get("definitions") or {}).get("subgraphs") or []
        return {
            "error": "definition_id required",
            "available": [{"definition_id": d.get("id"), "name": d.get("name")}
                          for d in defs if isinstance(d, dict)],
        }

    sg = _subgraph_def(workflow, definition_id)
    if sg is None:
        return {"error": f"no subgraph definition found with id {definition_id!r}"}

    # Inner graph structure: reuse _describe_graph by treating sg as a top-level workflow
    inner_summary = _describe_graph({"nodes": sg.get("nodes") or [], "links": sg.get("links") or []})

    # Exposed inputs/outputs: the subgraph's own "inputs"/"outputs" arrays. These are the
    # slots the instance node shows externally.
    sg_inputs = [
        {"name": s.get("name"), "type": s.get("type"),
         "exposed_at_instance": True}
        for s in (sg.get("inputs") or []) if isinstance(s, dict)
    ]
    sg_outputs = [
        {"name": s.get("name"), "type": s.get("type"),
         "exposed_at_instance": True}
        for s in (sg.get("outputs") or []) if isinstance(s, dict)
    ]

    # Widget proxies: ComfyUI uses different shapes across versions. Look for any of:
    #   sg["widgets"] = [{name, type, link?}, ...]   — recent format
    #   sg nodes with type "PrimitiveNode"/"PrimitiveString"/"PrimitiveInt" wired into
    #     real nodes' widget slots — the "publish a widget" pattern
    # Prefer the explicit array if present; fall back to scanning Primitives.
    proxies: list[dict[str, Any]] = []
    explicit = sg.get("widgets") if isinstance(sg.get("widgets"), list) else None
    if explicit:
        for w in explicit:
            if not isinstance(w, dict):
                continue
            proxies.append({
                "instance_widget_name": w.get("name"),
                "type": w.get("type"),
                "target_inner_node_id": w.get("node_id") or w.get("target_id"),
                "target_inner_widget_name": w.get("widget") or w.get("target_widget"),
            })
    else:
        # Heuristic fallback: PrimitiveNodes wired to widget inputs of inner nodes
        for n in sg.get("nodes") or []:
            if not isinstance(n, dict):
                continue
            if str(n.get("type", "")).startswith("Primitive"):
                # Find what inner node consumes this primitive's output
                outs = n.get("outputs") or []
                exposed_name = (n.get("title") or
                                (outs[0].get("name") if outs and isinstance(outs[0], dict) else None))
                proxies.append({
                    "instance_widget_name": exposed_name,
                    "type": "primitive",
                    "target_inner_node_id": n.get("id"),
                    "target_inner_widget_name": "value",
                    "note": "heuristic: PrimitiveNode wired into a real node",
                })

    return {
        "definition_id": sg.get("id"),
        "name": sg.get("name"),
        "inner_node_count": inner_summary.get("node_count"),
        "inner_link_count": inner_summary.get("link_count"),
        "inputs": sg_inputs,
        "outputs": sg_outputs,
        "widget_proxies": proxies,
        "inner_nodes": inner_summary.get("nodes"),
    }


@mcp.tool()
async def inspect_subgraph_instance(
    node_id: int,
    tab_id: str = "",
    workflow: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Inspect an INSTANCE of a subgraph: which definition it points to, what it's
    wired to externally, and (via describe_subgraph) the inner structure.

    Args:
        node_id: the top-level node id of the subgraph instance (the box on the canvas).
        tab_id: target a specific tab; defaults to most-recently-edited.
        workflow: explicit UI-format workflow; skips the bridge round-trip.

    Returns:
      {node_id, type (definition_id), pos, instance_inputs, instance_outputs,
       definition: <full describe_subgraph result>}
       or {error}.
    """
    if workflow is None:
        wf, _state, err = await _workflow_from_tab(tab_id=tab_id, want_api=False)
        if err:
            return err
        workflow = wf  # type: ignore[assignment]

    node, _ = _resolve_node_path(workflow, node_id)
    if node is None:
        return {"error": f"node {node_id} not found"}

    definition_id = node.get("type")
    if not _subgraph_def(workflow, definition_id):
        return {"error": f"node {node_id} is type {definition_id!r} which is not a subgraph definition"}

    # Use describe_subgraph for the inner detail
    inner = await describe_subgraph(definition_id=str(definition_id), workflow=workflow)

    return {
        "node_id": node_id,
        "type": definition_id,
        "pos": node.get("pos"),
        "instance_inputs": node.get("inputs"),
        "instance_outputs": node.get("outputs"),
        "instance_widgets_values": node.get("widgets_values"),
        "definition": inner,
    }


@mcp.tool()
async def add_node(
    class_type: str,
    x: int = 0,
    y: int = 0,
    widget_values: dict[str, Any] | None = None,
    connections: list[dict[str, Any]] | None = None,
    tab_id: str = "",
) -> dict[str, Any]:
    """Add a node to the live ComfyUI tab. Visible immediately on the canvas.

    Validates `class_type` against /object_info BEFORE dispatching to the bridge —
    on a typo'd or non-existent class, returns a clear error with fuzzy-matched
    suggestions instead of silently creating a red-error node on the canvas.

    Args:
        class_type: e.g. "KSampler", "CheckpointLoaderSimple". Use search_nodes to discover.
        x, y: canvas position. Defaults to 0,0; use move_node afterward if needed.
        widget_values: optional initial widget settings, e.g. {"seed": 42, "steps": 20}.
        connections: optional list wired up immediately after the node is created.
                     Each entry is {from_node_id, from_slot, to_node_id, to_slot},
                     same shape as connect_many. Use the literal string "$new" for
                     either node id to refer to the just-created node — typically you
                     pass {from_node_id: <existing>, to_node_id: "$new", ...} for
                     incoming wires, or the reverse for outgoing. Slots may be int
                     indices or string names. Halves round-trips when dropping in
                     a new node and wiring it up.
        tab_id: target a specific tab; defaults to the most-recently-edited tab.

    Returns: {ok, node: {id, type, pos, size, widgets}, connections?: {count, results: [...]}}
    so you can use the assigned id in subsequent set_widget calls. On unknown
    class_type: {ok: false, error, suggestions: [{name, score}, ...]}.
    """
    # Validate class_type against the running ComfyUI's installed nodes
    try:
        info = await comfy.object_info(class_type)
    except Exception as e:
        return {"ok": False, "error": f"object_info lookup failed: {e}", "class_type": class_type}
    if not info or class_type not in info:
        # Fuzzy-suggest similar class names. Don't use _fuzzy_match_list — it's
        # path-aware and splits on '/' which is meaningless for node class names.
        suggestions: list[dict[str, Any]] = []
        try:
            import difflib
            full = await comfy.object_info()
            close = difflib.get_close_matches(class_type, list(full.keys()), n=5, cutoff=0.5)
            suggestions = [{"name": n, "category": (full.get(n) or {}).get("category", "")} for n in close]
        except Exception:
            pass
        return {
            "ok": False,
            "error": f"unknown node class_type {class_type!r}; not registered with this ComfyUI",
            "suggestions": suggestions,
            "hint": "use search_nodes() to find the right name; check spelling/case",
        }

    op: dict[str, Any] = {"op": "add_node", "class_type": class_type}
    if x or y:
        op["pos"] = [x, y]
    if widget_values:
        op["widget_values"] = widget_values
    result = await comfy.bridge_op(op, tab_id=tab_id or None)

    if not connections or not result.get("ok"):
        return result

    new_id = (result.get("node") or {}).get("id")
    if new_id is None:
        # add_node succeeded but didn't surface an id — can't substitute "$new".
        # Surface the omission rather than silently dropping the connections list.
        return {**result, "connections_skipped": connections,
                "connections_error": "bridge did not return new node id; cannot substitute $new"}

    resolved: list[dict[str, Any]] = []
    for c in connections:
        if not isinstance(c, dict):
            resolved.append({"ok": False, "error": "connection entry must be a dict", "raw": c})
            continue
        rc = dict(c)
        for key in ("from_node_id", "to_node_id"):
            if rc.get(key) == "$new":
                rc[key] = new_id
        resolved.append(rc)

    well_formed = [c for c in resolved if "from_node_id" in c and "to_node_id" in c]
    if not well_formed:
        return {**result, "connections": {"count": 0, "results": resolved}}
    conn_result = await comfy.bridge_op(
        {"op": "connect_many", "connections": well_formed},
        tab_id=tab_id or None,
    )
    return {**result, "connections": conn_result}


@mcp.tool()
async def delete_node(node_id: int, tab_id: str = "") -> dict[str, Any]:
    """Delete a node from the live ComfyUI tab. Auto-disconnects its links."""
    return await comfy.bridge_op({"op": "delete_node", "node_id": node_id}, tab_id=tab_id or None)


@mcp.tool()
async def connect_nodes(
    from_node_id: int,
    from_slot: Any,
    to_node_id: int,
    to_slot: Any,
    tab_id: str = "",
) -> dict[str, Any]:
    """Wire one node's output to another node's input in the live tab.

    Slots can be either an integer index (0,1,2,...) OR a string name ("MODEL", "CLIP",
    "image", etc.). Names are resolved against the node's outputs/inputs. If LiteGraph
    rejects the connection (type mismatch), you'll get an error explaining which types.
    """
    op = {
        "op": "connect",
        "from_node_id": from_node_id,
        "from_slot": from_slot,
        "to_node_id": to_node_id,
        "to_slot": to_slot,
    }
    return await comfy.bridge_op(op, tab_id=tab_id or None)


@mcp.tool()
async def connect_many(
    connections: list[dict[str, Any]],
    tab_id: str = "",
) -> dict[str, Any]:
    """Wire many connections in one round trip — much cheaper than N connect_nodes calls
    when wiring up a new pipeline (e.g. dropping in a Detailer + Detector pass).

    Each connection entry: {from_node_id, from_slot, to_node_id, to_slot}.
    Slots may be int indices or string names. Failures are reported per-connection
    rather than aborting the batch — agent can re-issue just the failed ones.

    Returns {count, results: [{ok, error?, ...connection}, ...]}.
    """
    return await comfy.bridge_op({"op": "connect_many", "connections": connections}, tab_id=tab_id or None)


@mcp.tool()
async def disconnect_input(to_node_id: int, to_slot: Any, tab_id: str = "") -> dict[str, Any]:
    """Break the link feeding a specific input slot. to_slot is an int index or string name."""
    return await comfy.bridge_op(
        {"op": "disconnect", "to_node_id": to_node_id, "to_slot": to_slot},
        tab_id=tab_id or None,
    )


@mcp.tool()
async def lock_seed(
    node_id: int,
    value: int = -1,
    lock: bool = True,
    seed_widget: str = "seed",
    tab_id: str = "",
) -> dict[str, Any]:
    """Lock or unlock a node's seed for A/B comparison runs. Two coupled ops in one tool:
    sets the seed value AND flips its `*_control_after_generate` widget to fixed/randomize.

    Use when iterating: lock the seed so prompt/widget changes are isolated from
    seed-roll variance. Unlock to randomize again when you want exploration.

    Args:
        node_id: KSampler / KSamplerAdvanced / FaceDetailer / etc.
        value: explicit seed integer. -1 (default) keeps the current seed value
               and only flips the control mode.
        lock: True (default) → control = "fixed"; False → "randomize".
        seed_widget: widget name (defaults to "seed"; some nodes use "noise_seed").
        tab_id: target a specific tab; empty = most-recently-edited.

    Returns: {ok, seed_value, control_mode} or {ok: false, error}.
    """
    control_widget = f"{seed_widget}_control_after_generate"
    control_mode = "fixed" if lock else "randomize"

    if value >= 0:
        r1 = await comfy.bridge_op(
            {"op": "set_widget", "node_id": node_id, "name": seed_widget, "value": value},
            tab_id=tab_id or None,
        )
        if not r1.get("ok"):
            return {"ok": False, "error": "failed to set seed value", "raw": r1}

    r2 = await comfy.bridge_op(
        {"op": "set_widget", "node_id": node_id, "name": control_widget, "value": control_mode},
        tab_id=tab_id or None,
    )
    if not r2.get("ok"):
        return {
            "ok": False,
            "error": f"failed to set {control_widget}; this node may not have a control widget",
            "raw": r2,
        }
    return {
        "ok": True,
        "node_id": node_id,
        "seed_value": value if value >= 0 else "(unchanged)",
        "control_mode": control_mode,
    }


@mcp.tool()
async def set_widget(node_id: int, name: str, value: Any, tab_id: str = "") -> dict[str, Any]:
    """Change a single widget value on a live node (text, number, combo, boolean).

    Faster + more visible than swapping the entire workflow. Use this for prompt edits,
    sampler/cfg/steps tuning, model switches, etc. Triggers the widget's callback so
    derived UI updates (e.g., conditional widgets) fire correctly.

    VALUE TYPE MUST MATCH the existing widget's type:
      • Prompt text (CLIPTextEncode.text, PrimitiveStringMultiline.value, ...)
        → JSON string. e.g. value="1girl, solo, masterpiece" — NOT 12345.
      • Numeric widgets (seed, cfg, steps) → number. String-numeric ("42") is coerced.
      • Boolean widgets → bool. "true"/"false" strings are coerced.
    Mismatched types now raise a clear error rather than silently corrupting the
    widget. Common mistake: passing a number where a prompt string was meant.
    """
    return await comfy.bridge_op(
        {"op": "set_widget", "node_id": node_id, "name": name, "value": value},
        tab_id=tab_id or None,
    )


@mcp.tool()
async def move_node(node_id: int, x: int, y: int, tab_id: str = "") -> dict[str, Any]:
    """Reposition a node on the canvas. Useful for cleanup passes."""
    return await comfy.bridge_op(
        {"op": "move_node", "node_id": node_id, "x": x, "y": y},
        tab_id=tab_id or None,
    )


@mcp.tool()
async def arrange_layout(tab_id: str = "") -> dict[str, Any]:
    """Auto-arrange the graph using LiteGraph's built-in layout. Returns an error on
    older ComfyUI builds where graph.arrange() is unavailable; in that case, compute
    positions yourself and use move_node per node."""
    return await comfy.bridge_op({"op": "arrange_layout"}, tab_id=tab_id or None)


@mcp.tool()
async def screenshot_canvas(tab_id: str = "", timeout: int = 10) -> Any:
    """Capture the LiteGraph canvas of an open ComfyUI tab as a PNG, returned inline.

    Lets the agent see the visual graph layout (node positions, groupings, the actual
    spaghetti) instead of just the JSON. Requires the bridge custom_node and an open tab.

    With tab_id, captures that specific tab; otherwise targets all live tabs and uses
    the first response. Times out at `timeout` seconds if no browser responds.
    Get tab_ids from get_open_workflow() — they are sessionStorage-scoped, NOT
    ComfyUI's clientId (which is shared across tabs in the same browser).
    """
    result = await comfy.bridge_screenshot(tab_id=tab_id or None, timeout=float(timeout))
    if not result.get("ok"):
        return {"error": result.get("error", "screenshot failed"), "raw": result}
    data_url = result.get("data_url") or ""
    if not data_url.startswith("data:image/"):
        return {"error": "browser returned no image", "raw": result}
    b64 = data_url.split(",", 1)[1]
    return Image(data=base64.b64decode(b64), format="png")


@mcp.tool()
def save_workflow(
    path: str,
    workflow: dict[str, Any],
    overwrite: bool = False,
) -> dict[str, Any]:
    """Save a workflow JSON to disk. Detects UI vs API format and reports it.

    Refuses to overwrite an existing file unless overwrite=True. Creates parent
    directories as needed. Pretty-prints with 2-space indent (matches ComfyUI's
    own saved format).

    Returns {path, format, node_count, bytes_written} on success or {error, path}.
    """
    p = Path(path).expanduser().resolve()
    if p.exists() and not overwrite:
        return {"error": "file exists; pass overwrite=True to replace", "path": str(p)}
    fmt, count = _detect_format(workflow)
    if fmt == "unknown":
        return {"error": "workflow doesn't look like UI or API format", "path": str(p)}
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(workflow, indent=2)
    p.write_text(text)
    return {"path": str(p), "format": fmt, "node_count": count, "bytes_written": len(text.encode("utf-8"))}


@mcp.tool()
async def cancel_job(prompt_id: str = "") -> dict[str, Any]:
    """Cancel a queued or running ComfyUI job.

    With prompt_id: removes the ID from the pending queue AND interrupts the running
    job if it matches (both are no-ops if not applicable, so it's safe).
    Without: interrupts whatever is currently executing.
    """
    out: dict[str, Any] = {}
    if prompt_id:
        out["delete"] = await comfy.delete_from_queue([prompt_id])
    out["interrupt"] = await comfy.interrupt(prompt_id or None)
    return out


@mcp.tool()
async def get_queue(compact: bool = True) -> dict[str, Any]:
    """List ComfyUI's running and pending jobs.

    With compact=True (default), strips the full prompt graph from each entry to
    save tokens. Set compact=False to inspect the full submitted graph.
    """
    raw = await comfy.queue_state()
    running_raw = raw.get("queue_running", []) or []
    pending_raw = raw.get("queue_pending", []) or []

    def shape(entry: Any, position: int) -> dict[str, Any]:
        if not isinstance(entry, list) or len(entry) < 3:
            return {"raw": entry, "position": position}
        number, pid, prompt = entry[0], entry[1], entry[2]
        extra = entry[3] if len(entry) > 3 else None
        out: dict[str, Any] = {
            "number": number,
            "prompt_id": pid,
            "node_count": len(prompt) if isinstance(prompt, dict) else None,
            "position": position,
        }
        if not compact:
            out["prompt"] = prompt
            out["extra_data"] = extra
        return out

    return {
        "running": [shape(e, i) for i, e in enumerate(running_raw)],
        "pending": [shape(e, i) for i, e in enumerate(pending_raw)],
        "running_count": len(running_raw),
        "pending_count": len(pending_raw),
    }


@mcp.tool()
async def compare_images(
    files: list[dict[str, str]],
    layout: str = "horizontal",
    max_long_edge: int = 1024,
    label: bool = True,
) -> Any:
    """Composite N images side-by-side and return inline. The agent gets a true visual
    A/B (or A/B/C/...) instead of holding both images in memory across separate calls.

    Each entry in `files` is {filename, subfolder?, type?} (same shape as get_history
    output entries). Type defaults to "output". Pulls each via /view, resizes to
    `max_long_edge`, and pastes into a composite image.

    Args:
        files: list of {filename, subfolder, type}. Up to ~6 images.
        layout: "horizontal" (default) or "vertical" or "grid" (square-ish).
        max_long_edge: resize each input so its long edge ≤ this, before compositing.
        label: write a small "A", "B", "C", ... label in each panel.

    Returns: inline JPEG of the composite, or {error} on failure.
    """
    if not files:
        return {"error": "no files provided"}
    if len(files) > 8:
        return {"error": f"too many files ({len(files)}); max 8 for one composite"}
    try:
        from PIL import Image as PILImage, ImageDraw, ImageFont  # type: ignore
        import io
    except ImportError:
        return {"error": "Pillow not installed in MCP venv"}

    panels: list[Any] = []
    for entry in files:
        if not isinstance(entry, dict) or "filename" not in entry:
            return {"error": f"each file must be a dict with 'filename'; got {entry!r}"}
        try:
            data, _ = await comfy.view(
                entry["filename"],
                subfolder=entry.get("subfolder", ""),
                folder_type=entry.get("type", "output"),
            )
            img = PILImage.open(io.BytesIO(data))
            if img.mode != "RGB":
                img = img.convert("RGB")
            w, h = img.size
            long_edge = max(w, h)
            if long_edge > max_long_edge:
                scale = max_long_edge / long_edge
                img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
            panels.append(img)
        except Exception as e:
            return {"error": f"failed to load {entry.get('filename')!r}: {e}"}

    if label:
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None
        for i, p in enumerate(panels):
            draw = ImageDraw.Draw(p)
            tag = chr(ord("A") + i)
            # Drop-shadow + bright fill for legibility on any background
            for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                draw.text((10 + dx, 10 + dy), tag, fill=(0, 0, 0), font=font)
            draw.text((10, 10), tag, fill=(255, 255, 0), font=font)

    n = len(panels)
    if layout == "vertical":
        cols, rows = 1, n
    elif layout == "grid":
        cols = int(n ** 0.5) if n ** 0.5 == int(n ** 0.5) else int(n ** 0.5) + 1
        rows = (n + cols - 1) // cols
    else:
        cols, rows = n, 1

    cell_w = max(p.width for p in panels)
    cell_h = max(p.height for p in panels)
    composite = PILImage.new("RGB", (cols * cell_w, rows * cell_h), (16, 16, 16))
    for i, p in enumerate(panels):
        col = i % cols
        row = i // cols
        x = col * cell_w + (cell_w - p.width) // 2
        y = row * cell_h + (cell_h - p.height) // 2
        composite.paste(p, (x, y))

    buf = io.BytesIO()
    composite.save(buf, format="JPEG", quality=85, optimize=True)
    return Image(data=buf.getvalue(), format="jpeg")


@mcp.tool()
async def view_file(
    filename: str,
    subfolder: str = "",
    type: str = "output",
    max_inline_bytes: int = 5_000_000,
) -> Any:
    """View a file from ComfyUI's input/output/temp folders.

    Behavior:
      - Images (png/jpg/jpeg/webp/gif) under max_inline_bytes: returned inline.
      - Images OVER max_inline_bytes: auto-resized via PIL to fit (max 2048px on
        the long edge, JPEG quality 85). Agent gets a viewable thumbnail instead
        of a metadata-only response — useful for the 4x upscaler output case.
      - Non-image (mp4/webm/wav/...): returns {filename, ..., size, path} so the
        user/agent can open the file externally.

    Pair with get_history outputs to render still frames inline and surface paths
    for video/audio results from animatediff/ltxvideo/melband-roformer workflows.
    """
    image_exts = {"png", "jpg", "jpeg", "webp", "gif"}
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    data, content_type = await comfy.view(filename, subfolder=subfolder, folder_type=type)

    if ext in image_exts:
        if len(data) <= max_inline_bytes:
            fmt = "jpeg" if ext == "jpg" else ext
            return Image(data=data, format=fmt)
        # Too big — auto-resize to a viewable thumbnail. Quality 92 preserves skin
        # texture / fine artifacts important for quality evaluation; 85 hid them.
        thumb = _resize_image_for_inline(data, max_long_edge=2048, quality=92)
        if thumb is not None:
            return Image(data=thumb, format="jpeg")
        # PIL unavailable or resize failed — fall through to metadata response

    local_path: str | None = None
    try:
        candidate = _comfy_root() / type / subfolder / filename
        if candidate.exists():
            local_path = str(candidate)
    except RuntimeError:
        pass

    return {
        "filename": filename,
        "subfolder": subfolder,
        "type": type,
        "size": len(data),
        "mime_type": content_type,
        "path": local_path,
        "note": (
            "exceeded max_inline_bytes and resize was unavailable, OR file is non-image. "
            "Use the path to open externally."
        ),
    }


def _resize_image_for_inline(data: bytes, max_long_edge: int = 2048, quality: int = 85) -> bytes | None:
    """Resize an image so its long edge is ≤ max_long_edge, encode as JPEG.
    Returns None if PIL unavailable or resize fails; caller falls back to metadata."""
    try:
        from PIL import Image as PILImage  # type: ignore[import-not-found]
        import io
    except ImportError:
        return None
    try:
        img = PILImage.open(io.BytesIO(data))
        if img.mode in ("RGBA", "LA", "P"):
            # JPEG can't carry alpha; flatten onto white
            bg = PILImage.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        w, h = img.size
        long_edge = max(w, h)
        if long_edge > max_long_edge:
            scale = max_long_edge / long_edge
            img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        return buf.getvalue()
    except Exception:
        return None


@mcp.tool()
async def get_node_widgets(node_id: str, tab_id: str = "") -> dict[str, Any]:
    """Token-efficient: read just one node's widget values from the open tab.

    Use instead of get_open_workflow when you only need to know what a single node
    is set to (e.g. "what model does the UNETLoader currently load?"). Resolves
    widget names via /object_info so values come back as {name: value} not as a
    raw positional list.

    `node_id` accepts subgraph paths: '59' for top-level, '59/68' for inner.
    """
    wf, _state, err = await _workflow_from_tab(tab_id=tab_id, want_api=False)
    if err:
        return err
    node, _scope = _resolve_node_path(wf, node_id)
    if node is None:
        return {"error": f"node {node_id} not found", "hint": "use '<outer>/<inner>' for subgraph nodes"}
    class_type = node.get("type")
    raw_values = list(node.get("widgets_values") or [])
    out: dict[str, Any] = {
        "node_id": node_id,
        "type": class_type,
        "title": node.get("title"),
    }
    try:
        order, confidence = (
            await _ui_widget_order_aligned(class_type, len(raw_values))
            if class_type else ([], "")
        )
    except Exception:
        order, confidence = [], ""
    if order:
        widgets = []
        for i, name in enumerate(order):
            val = raw_values[i] if i < len(raw_values) else None
            widgets.append({"name": name, "value": val})
        out["widgets"] = widgets
        if len(raw_values) > len(order):
            out["extra_widget_values"] = raw_values[len(order):]
        if confidence == "best_guess":
            out["alignment_warning"] = (
                f"name/value alignment is uncertain — INPUT_TYPES suggests "
                f"{len(order)} widgets but widgets_values has {len(raw_values)}. "
                f"Treat names as approximate; raw widgets_values is authoritative."
            )
            out["widgets_values"] = raw_values  # always include raw on uncertain alignment
    else:
        out["widgets_values"] = raw_values
    return out


@mcp.tool()
async def get_open_workflow(format: str = "ui", tab_id: str = "") -> dict[str, Any]:
    """Read the FULL workflow currently open in the user's ComfyUI browser tab(s).

    ⚠️ TOKEN-EXPENSIVE in "ui"/"api" mode: a typical workflow is 5-50KB; complex
    ones (with subgraphs, rgthree power-loaders, etc.) can exceed 200KB. Most agent
    use cases want one of these instead:

      - format="summary" — node_count, top_types, model_refs, subgraph_ids, notes.
        ~1-2KB. Use to answer "what's open right now?" without paying for the JSON.
      - `describe_graph()` — structural summary (id/type/connections), ~1-5KB.
      - `get_node_widgets(node_id)` — one node's settings only.
      - `describe_workflow()` — high-level summary with notes, model refs, top types.

    Reach for "ui"/"api" mode only when you genuinely need the entire JSON
    (e.g. to clone, edit, and apply_workflow back). Requires the bridge custom_node
    + a browser tab open.

    Args:
        format: "ui" (editable; what read_workflow returns), "api" (queue-able), or
                "summary" (compact metadata-only response, no full JSON).
        tab_id: optional, target a specific tab. If omitted, returns the most recently
                edited tab. tab_id is per-tab (sessionStorage-scoped); NOT ComfyUI's
                clientId, which is shared across tabs in the same browser.

    Returns:
      For "ui"/"api": {workflow, format, tab_id, comfy_client_id, updated_at, tab_count, tabs?, warning?}
      For "summary":  {format, node_count, top_types, model_references, notes_in_canvas,
                       subgraph_ids, tab_id, comfy_client_id, label, updated_at, tab_count, tabs?}
      or {error}. The "tabs" list (when multiple are open) gives all tab_ids so you
      can disambiguate.
    """
    state = await comfy.bridge_state(tab_id=tab_id or None)
    if state.get("error"):
        return state
    if state.get("workflow") is None:
        return {
            "error": "no workflow state available",
            "hint": "is the bridge installed (custom_nodes/comfyui-mcp-bridge) and is a browser tab open?",
            "tab_count": state.get("tab_count", 0),
        }

    common_meta = {
        "tab_id": state.get("tab_id"),
        "comfy_client_id": state.get("comfy_client_id"),
        "label": state.get("label"),
        "updated_at": state.get("updated_at"),
        "tab_count": state.get("tab_count"),
        "tabs": state.get("tabs"),
        "warning": state.get("warning"),
    }

    if format == "summary":
        wf = state["workflow"]
        body = _summarize_workflow_body(wf, summary_only=False)
        # Pull out subgraph definition ids/names from the workflow — the agent needs these
        # to follow up with describe_subgraph.
        sg_defs = (wf.get("definitions") or {}).get("subgraphs") or []
        body["subgraph_ids"] = [
            {"definition_id": d.get("id"), "name": d.get("name"),
             "inner_node_count": len(d.get("nodes") or [])}
            for d in sg_defs if isinstance(d, dict)
        ]
        return {"format": "summary", **body, **common_meta}

    chosen = state["api_workflow"] if format == "api" else state["workflow"]
    return {"workflow": chosen, "format": format, **common_meta}


@mcp.tool()
async def bridge_debug() -> dict[str, Any]:
    """Diagnostic dump of the comfyui-mcp-bridge state.

    Returns: live tabs (with labels showing workflow type / prompt preview / node count),
    pending events per tab, ComfyUI WebSocket sockets dict, server timestamps. Use this
    when tabs aren't being seen, to confirm which tabs have the new bridge JS loaded.
    """
    return await comfy.bridge_debug()


@mcp.tool()
async def apply_workflow(
    workflow: dict[str, Any] | None = None,
    path: str = "",
    tab_id: str = "",
    confirm: bool = True,
    snapshot: bool = True,
) -> dict[str, Any]:
    """Replace the graph in open ComfyUI browser tab(s) with a UI-format workflow.

    Two ways to supply the workflow:
      • path=<file>     — server-side reads the JSON. Use this for workflows >50KB
                          where the inline payload would exceed safe MCP limits.
                          Resolves relative to <COMFYUI_ROOT>/user/default/workflows
                          if not absolute.
      • workflow={...}  — inline JSON. Fine for small/programmatically-built graphs.

    Auto-snapshot: by default the current tab's workflow is saved to
    <COMFYUI_ROOT>/output/_snapshots/<tab_id>_<timestamp>.json before the swap, so you
    can `restore_snapshot()` if the apply was a mistake (e.g. stub workflow clears
    canvas). Last 5 snapshots per tab are retained; older ones are pruned.

    The browser will prompt the user to confirm before swapping, unless
    confirm=False (and only if the user has set localStorage trust flag).

    Args:
        workflow: UI-format workflow JSON. Mutually exclusive with `path`.
        path:     filesystem path to a UI-format workflow JSON. Mutually exclusive with `workflow`.
        tab_id:   optional, target a specific tab. Empty broadcasts to all live tabs.
        confirm:  ask the user in-browser before applying. Default true; set false only for
                  fully-trusted automation.
        snapshot: save the pre-apply state. Default true. Set false to skip (e.g. when
                  applying a workflow you JUST snapshotted).

    Returns: {ok, queued_to: [<tab_id>, ...], snapshot_path?, snapshot_warning?}
             or {ok: false, error}.
    """
    if path and workflow is not None:
        return {"ok": False, "error": "pass either `path` or `workflow`, not both"}
    if path:
        loaded, load_err = _read_workflow_for_apply(path)
        if load_err:
            return load_err
        workflow = loaded

    if not isinstance(workflow, dict) or "nodes" not in workflow:
        return {
            "ok": False,
            "error": "workflow must be UI format (top-level 'nodes' key); for API format, save via save_workflow and queue with queue_workflow",
        }

    snapshot_meta: dict[str, Any] = {}
    if snapshot:
        snapshot_meta = await _save_pre_apply_snapshot(tab_id=tab_id or None)

    result = await comfy.bridge_load(workflow, tab_id=tab_id or None, confirm=confirm)
    if isinstance(result, dict):
        if snapshot_meta.get("path"):
            result["snapshot_path"] = snapshot_meta["path"]
        if snapshot_meta.get("warning"):
            result["snapshot_warning"] = snapshot_meta["warning"]
    return result


def _read_workflow_for_apply(raw_path: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Resolve + read a workflow JSON for apply_workflow's path= branch.
    Returns (workflow, error). Exactly one is non-None."""
    p = Path(raw_path).expanduser()
    if not p.is_absolute():
        try:
            base = _comfy_root() / "user" / "default" / "workflows"
            cand = base / raw_path
            if cand.exists():
                p = cand
        except RuntimeError:
            pass
    p = p.resolve()
    if not p.is_file():
        return None, {"ok": False, "error": "not a file", "resolved_path": str(p)}
    try:
        wf = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return None, {"ok": False, "error": f"could not read JSON: {e}", "path": str(p)}
    return wf, None


_SNAPSHOT_RETENTION = 5


async def _save_pre_apply_snapshot(tab_id: str | None) -> dict[str, Any]:
    """Save the current tab's workflow to output/_snapshots/. Best-effort: any failure
    is reported via the returned dict but never raises.

    Returns {path?, warning?}. An empty dict means no tab to snapshot or root resolution
    failed — caller treats this as "no snapshot saved" without surfacing an error since
    the apply itself can still succeed.
    """
    state = await comfy.bridge_state(tab_id=tab_id)
    if state.get("error") or state.get("workflow") is None:
        return {"warning": "no current workflow available to snapshot"}

    actual_tab = state.get("tab_id") or "unknown"
    safe_tab = re.sub(r"[^A-Za-z0-9_-]", "_", str(actual_tab))[:40]
    try:
        root = _comfy_root()
    except RuntimeError as e:
        return {"warning": f"snapshot skipped: {e}"}
    snap_dir = root / "output" / "_snapshots"
    try:
        snap_dir.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        target = snap_dir / f"{safe_tab}_{ts}.json"
        target.write_text(json.dumps(state["workflow"], indent=2))
    except OSError as e:
        return {"warning": f"snapshot write failed: {e}"}

    # Prune old snapshots for this tab — keep last N
    try:
        existing = sorted(snap_dir.glob(f"{safe_tab}_*.json"))
        for old in existing[:-_SNAPSHOT_RETENTION]:
            try:
                old.unlink()
            except OSError:
                pass
    except OSError:
        pass

    return {"path": str(target)}


@mcp.tool()
async def restore_snapshot(
    tab_id: str = "",
    index: int = 0,
    confirm: bool = True,
) -> dict[str, Any]:
    """Restore the most recent pre-apply snapshot for a tab.

    Use immediately after a bad apply_workflow (e.g. stub workflow that wiped the canvas).
    Snapshots are saved in <COMFYUI_ROOT>/output/_snapshots/<tab_id>_<ts>.json.

    Args:
        tab_id: target tab; defaults to most-recently-edited tab.
        index:  0 (default) = most recent; 1 = previous; up to 4. Use list_snapshots
                if you're unsure which one to restore.
        confirm: ask the user in-browser before applying (default true).

    Returns: {ok, restored_from, queued_to: [<tab_id>], available_snapshots: [...]}
             or {ok: false, error}.
    """
    state = await comfy.bridge_state(tab_id=tab_id or None)
    if state.get("error"):
        return {"ok": False, **state}
    actual_tab = state.get("tab_id") or tab_id
    if not actual_tab:
        return {"ok": False, "error": "no tab to restore into; pass tab_id or open ComfyUI"}

    safe_tab = re.sub(r"[^A-Za-z0-9_-]", "_", str(actual_tab))[:40]
    try:
        root = _comfy_root()
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}
    snap_dir = root / "output" / "_snapshots"
    snaps = sorted(snap_dir.glob(f"{safe_tab}_*.json"), reverse=True) if snap_dir.exists() else []
    if not snaps:
        return {"ok": False, "error": f"no snapshots found for tab {actual_tab}",
                "snap_dir": str(snap_dir)}
    if index < 0 or index >= len(snaps):
        return {"ok": False, "error": f"index {index} out of range (have {len(snaps)} snapshots)",
                "available": [s.name for s in snaps]}

    target = snaps[index]
    try:
        wf = json.loads(target.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return {"ok": False, "error": f"could not read snapshot: {e}", "path": str(target)}

    # Use snapshot=False to avoid snapshotting the broken state we're undoing
    result = await comfy.bridge_load(wf, tab_id=actual_tab, confirm=confirm)
    if isinstance(result, dict):
        result["restored_from"] = str(target)
        result["available_snapshots"] = [s.name for s in snaps]
    return result


@mcp.tool()
def list_snapshots(tab_id: str = "") -> dict[str, Any]:
    """List available pre-apply snapshots, optionally for one tab.

    Returns: {snap_dir, snapshots: [{tab_id, filename, path, age_seconds, size}, ...]}.
    Sorted newest-first. Use to identify the right index to pass to restore_snapshot.
    """
    try:
        root = _comfy_root()
    except RuntimeError as e:
        return {"error": str(e)}
    snap_dir = root / "output" / "_snapshots"
    if not snap_dir.exists():
        return {"snap_dir": str(snap_dir), "snapshots": [], "note": "no snapshots yet"}

    pattern = "*.json"
    if tab_id:
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", str(tab_id))[:40]
        pattern = f"{safe}_*.json"

    now = time.time()
    out: list[dict[str, Any]] = []
    for p in sorted(snap_dir.glob(pattern), reverse=True):
        # filename is <safe_tab>_<ts>.json — pull tab back out
        name_root = p.stem
        # Last underscore separates ts; everything before is the safe_tab portion
        tab_part, _, _ = name_root.rpartition("_")
        try:
            st = p.stat()
            out.append({
                "tab_id": tab_part,
                "filename": p.name,
                "path": str(p),
                "size": st.st_size,
                "age_seconds": int(now - st.st_mtime),
            })
        except OSError:
            continue
    return {"snap_dir": str(snap_dir), "count": len(out), "snapshots": out}


@mcp.tool()
async def wait_for_completion(
    prompt_id: str,
    timeout: int = 300,
    compact: bool = True,
    strip_warnings: bool = False,
) -> dict[str, Any]:
    """Wait for a queued workflow to finish via ComfyUI's WebSocket stream.

    Returns {status, output_files?, history?, error?, progress?} where status is one of:
      "completed" — finished successfully; `output_files` is a flat list of
                    {node_id, kind, filename, subfolder, type} that you can pass
                    directly to view_file/view_image without a separate get_history.
      "error"     — runtime failure; error holds node_id/exception_type/exception_message/traceback.
      "interrupted" — user/agent cancelled.
      "timeout"   — deadline hit; progress holds the last (value, max, node) seen.

    Args:
        prompt_id: the id returned by queue_workflow.
        timeout: max seconds to wait (default 300).
        compact: True (default) drops the verbose original prompt graph + extra_data
                 from history. Saves significant tokens across many inpaint iterations.
                 Set False if you actually need the submitted graph for inspection.
        strip_warnings: drop HuggingFace weight-list spam, transformer "Some weights of"
                        warnings, and tqdm progress noise from history.status.messages.
                        Set when a custom node logs the entire Gemma3 weight list
                        (~70KB) and the wait result becomes unreadable.
    """
    result = await comfy.wait(prompt_id, timeout=float(timeout))
    if result.get("status") == "completed":
        history = result.get("history") or {}
        result["output_files"] = _outputs_to_files(history)
        if compact:
            # Strip the verbose echo fields — output_files has the actionable info
            history = {
                k: v for k, v in history.items()
                if k not in ("prompt", "extra_data", "current_inputs", "current_outputs")
            }
        if strip_warnings:
            history = _strip_history_warnings(history)
        result["history"] = history
    elif strip_warnings and result.get("status") == "error":
        # Errors carry their own message field; if it ever embeds noise, scrub there too
        err = result.get("error")
        if isinstance(err, dict) and isinstance(err.get("traceback"), list):
            err = {**err, "traceback": [ln for ln in err["traceback"] if not _is_log_noise(ln)]}
            result["error"] = err
    return result


def _strip_history_warnings(history: dict[str, Any]) -> dict[str, Any]:
    """Drop noise lines from history.status.messages. ComfyUI structures these as
    [event_type, payload_dict] pairs; messages of type 'logs' or with a nested 'entries'
    list are the heaviest. Mutates a shallow copy."""
    status = history.get("status")
    if not isinstance(status, dict):
        return history
    messages = status.get("messages")
    if not isinstance(messages, list):
        return history

    cleaned: list[Any] = []
    for msg in messages:
        if not isinstance(msg, list) or len(msg) < 2:
            cleaned.append(msg)
            continue
        ev_type, payload = msg[0], msg[1]
        if isinstance(payload, dict) and isinstance(payload.get("entries"), list):
            kept = [e for e in payload["entries"]
                    if not isinstance(e, str) or not _is_log_noise(e)]
            if kept:
                cleaned.append([ev_type, {**payload, "entries": kept}])
            continue
        if isinstance(payload, dict) and isinstance(payload.get("message"), str):
            if _is_log_noise(payload["message"]):
                continue
        cleaned.append(msg)

    return {**history, "status": {**status, "messages": cleaned}}


@mcp.tool()
def copy_to_input(
    filename: str,
    subfolder: str = "",
    source_type: str = "output",
    dest_name: str = "",
) -> dict[str, Any]:
    """Copy a file from ComfyUI's output/temp folder into input/ so it can be loaded by
    LoadImage in a follow-up workflow. Common pattern for chained inpaint passes:
    generate → run face detailer → copy result to input → run sleeve detailer → ...

    Args:
        filename: source file basename (e.g. "warrior_pose_00001_.png").
        subfolder: optional subfolder within the source folder.
        source_type: "output" (default), "temp", or "input" (no-op).
        dest_name: optional new name in input/. Defaults to the same basename.

    Returns: {dest_name, dest_path, source_path, bytes}.
    """
    import shutil
    if source_type not in ("output", "temp", "input"):
        return {"error": f"source_type must be output/temp/input; got {source_type!r}"}
    try:
        root = _comfy_root()
    except RuntimeError as e:
        return {"error": str(e)}
    src = root / source_type / subfolder / filename
    if not src.is_file():
        return {"error": "source file not found", "resolved_path": str(src)}
    dest_dir = root / "input"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / (dest_name or src.name)
    try:
        shutil.copy2(src, dest)
    except OSError as e:
        return {"error": f"copy failed: {e}", "source_path": str(src), "dest_path": str(dest)}
    return {
        "dest_name": dest.name,
        "dest_path": str(dest),
        "source_path": str(src),
        "bytes": dest.stat().st_size,
    }


# OpenPose 18-keypoint connections (1-indexed in original; 0-indexed here).
# Standard COCO_18 / BODY_25 layout — first 18 indices are body, then optional ears.
_OPENPOSE_LIMB_PAIRS = [
    (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7),  # arms
    (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),  # legs
    (1, 0), (0, 14), (14, 16), (0, 15), (15, 17),  # head/face
]
_OPENPOSE_LIMB_COLORS = [
    (255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0),
    (170, 255, 0), (85, 255, 0), (0, 255, 0), (0, 255, 85),
    (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
    (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255),
    (255, 0, 170),
]
_OPENPOSE_JOINT_COLORS = [
    (255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0),
    (170, 255, 0), (85, 255, 0), (0, 255, 0), (0, 255, 85),
    (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255),
    (0, 0, 255), (85, 0, 255), (170, 0, 255), (255, 0, 255),
    (255, 0, 170), (255, 0, 85),
]


@mcp.tool()
def render_pose_skeleton(
    keypoints: dict[str, Any],
    width: int = 0,
    height: int = 0,
    save_as: str = "",
    confidence_threshold: float = 0.05,
) -> dict[str, Any]:
    """Draw an OpenPose-format skeleton image from numerical keypoints, save to ComfyUI's
    input/ folder so it can be loaded with LoadImage and fed to a ControlNet OpenPose.

    Use after `extract_pose_keypoints` (potentially with intermediate Python edits to
    move/rotate/mirror joints) to produce the conditioning image for ControlNet runs.

    Args:
        keypoints: dict with `people: [{pose_keypoints_2d: [x,y,c, ...], hand_left_*,
                   hand_right_*, face_*}]` shape — exactly what extract_pose_keypoints
                   returns. Coordinates may be normalized (0-1) or pixel-space; auto-detected.
        width, height: output canvas size. Defaults pulled from `keypoints.canvas_width/height`,
                       falling back to 1024×1024.
        save_as: filename to save in input/. Default: pose_skeleton_<timestamp>.png.
        confidence_threshold: skip joints with confidence below this (default 0.05).

    Returns: {ok, filename, path, size, person_count}.

    Standard OpenPose 18-keypoint indices:
      0: nose, 1: neck, 2: r_shoulder, 3: r_elbow, 4: r_wrist,
      5: l_shoulder, 6: l_elbow, 7: l_wrist, 8: r_hip, 9: r_knee, 10: r_ankle,
      11: l_hip, 12: l_knee, 13: l_ankle,
      14: r_eye, 15: l_eye, 16: r_ear, 17: l_ear
    """
    try:
        from PIL import Image as PILImage, ImageDraw  # type: ignore[import-not-found]
    except ImportError:
        return {"ok": False, "error": "Pillow not installed in MCP venv"}

    canvas_w = width or keypoints.get("canvas_width") or 1024
    canvas_h = height or keypoints.get("canvas_height") or 1024
    canvas_w = int(canvas_w)
    canvas_h = int(canvas_h)

    img = PILImage.new("RGB", (canvas_w, canvas_h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    people = keypoints.get("people") or []
    if not people:
        return {"ok": False, "error": "keypoints.people is empty — nothing to render"}

    for person in people:
        body = person.get("pose_keypoints_2d") or []
        if len(body) < 3:
            continue
        # Detect normalized vs pixel coords by checking max value
        max_xy = max((max(body[i], body[i + 1]) for i in range(0, len(body), 3) if i + 1 < len(body)), default=0)
        normalized = max_xy <= 1.5

        def coord(idx: int) -> tuple[float, float, float] | None:
            base = idx * 3
            if base + 2 >= len(body):
                return None
            x, y, c = body[base], body[base + 1], body[base + 2]
            if c < confidence_threshold:
                return None
            if normalized:
                x *= canvas_w
                y *= canvas_h
            return (x, y, c)

        # Draw limbs (lines)
        for limb_idx, (a, b) in enumerate(_OPENPOSE_LIMB_PAIRS):
            pa = coord(a)
            pb = coord(b)
            if pa is None or pb is None:
                continue
            color = _OPENPOSE_LIMB_COLORS[limb_idx % len(_OPENPOSE_LIMB_COLORS)]
            draw.line([(pa[0], pa[1]), (pb[0], pb[1])], fill=color, width=4)

        # Draw joints (circles)
        joint_count = max(18, len(body) // 3)
        for j in range(joint_count):
            p = coord(j)
            if p is None:
                continue
            color = _OPENPOSE_JOINT_COLORS[j % len(_OPENPOSE_JOINT_COLORS)]
            r = 4
            draw.ellipse([(p[0] - r, p[1] - r), (p[0] + r, p[1] + r)], fill=color)

        # Hands and face — draw as small white dots if present
        for kp_key in ("hand_left_keypoints_2d", "hand_right_keypoints_2d", "face_keypoints_2d"):
            arr = person.get(kp_key) or []
            for i in range(0, len(arr), 3):
                if i + 2 >= len(arr):
                    break
                x, y, c = arr[i], arr[i + 1], arr[i + 2]
                if c < confidence_threshold:
                    continue
                if normalized:
                    x *= canvas_w
                    y *= canvas_h
                draw.ellipse([(x - 1.5, y - 1.5), (x + 1.5, y + 1.5)], fill=(255, 255, 255))

    try:
        root = _comfy_root()
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}

    if not save_as:
        save_as = f"pose_skeleton_{int(time.time())}.png"
    if not save_as.lower().endswith((".png", ".jpg", ".jpeg")):
        save_as += ".png"
    dest_dir = root / "input"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / save_as
    try:
        img.save(dest)
    except OSError as e:
        return {"ok": False, "error": f"save failed: {e}", "dest_path": str(dest)}

    return {
        "ok": True,
        "filename": dest.name,
        "path": str(dest),
        "size": [canvas_w, canvas_h],
        "person_count": len(people),
    }


@mcp.tool()
async def extract_pose_keypoints(
    image_filename: str,
    preprocessor: str = "DWPreprocessor",
) -> dict[str, Any]:
    """Extract numerical OpenPose keypoints from an image already in ComfyUI's input/ folder.

    Runs a small headless workflow: LoadImage → DWPreprocessor (or OpenposePreprocessor)
    → SavePoseKpsAsJsonFile → PreviewImage. Returns parsed keypoints (BODY_18/25 + face +
    hands per person) AND the saved skeleton image filename.

    Combine with `render_pose_skeleton` to modify and re-render, or pass the skeleton
    image directly to a ControlNet OpenPose workflow.

    Args:
        image_filename: file in ComfyUI's input/ folder (use upload_input or copy_to_input
                        first if the image is elsewhere).
        preprocessor: "DWPreprocessor" (default, faster + more accurate) or
                      "OpenposePreprocessor" (older, sometimes more compatible).

    Returns:
      {ok, keypoints: {version, people: [{pose_keypoints_2d, face_keypoints_2d,
        hand_left_keypoints_2d, hand_right_keypoints_2d}], canvas_width, canvas_height},
       skeleton_image: <filename>, skeleton_path}
       Each *_keypoints_2d is a flat [x, y, confidence, ...] list.

    On empty pose detection (`people: []`), the source image's body wasn't detected.
    Common cause: image was masked/clipspaced before passing in. Try a clean copy.
    """
    if preprocessor not in ("DWPreprocessor", "OpenposePreprocessor"):
        return {"ok": False, "error": f"preprocessor must be DWPreprocessor or OpenposePreprocessor; got {preprocessor!r}"}

    prefix = f"mcp_pose_{int(time.time())}"
    workflow = {
        "1": {"class_type": "LoadImage", "inputs": {"image": image_filename}},
        "2": {
            "class_type": preprocessor,
            "inputs": {
                "image": ["1", 0],
                "detect_hand": "enable",
                "detect_body": "enable",
                "detect_face": "enable",
                "resolution": 512,
                "bbox_detector": "yolox_l.onnx",
                "pose_estimator": "dw-ll_ucoco_384.onnx",
            },
        },
        "3": {
            "class_type": "SavePoseKpsAsJsonFile",
            "inputs": {"pose_kps": ["2", 1], "filename_prefix": prefix},
        },
        "4": {
            "class_type": "PreviewImage",
            "inputs": {"images": ["2", 0]},
        },
    }

    queued = await _queue_and_enrich(workflow)
    if not queued.get("ok"):
        return {"ok": False, "error": "extraction workflow failed validation", **queued}

    prompt_id = queued.get("prompt_id")
    result = await comfy.wait(prompt_id, timeout=60.0)
    if result.get("status") != "completed":
        return {"ok": False, "error": f"extraction did not complete: {result.get('status')}", "raw": result}

    # Find the JSON file written by SavePoseKpsAsJsonFile (in output/)
    try:
        root = _comfy_root()
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}
    output_dir = root / "output"
    json_candidates = sorted(output_dir.glob(f"{prefix}*.json"))
    if not json_candidates:
        return {"ok": False, "error": f"no pose JSON found at {output_dir}/{prefix}*.json"}
    json_path = json_candidates[-1]
    try:
        with json_path.open() as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return {"ok": False, "error": f"could not parse {json_path}: {e}"}

    # SavePoseKpsAsJsonFile writes a list with one entry per frame; for a single image
    # we typically have one entry. Normalize to that single dict.
    keypoints = data[0] if isinstance(data, list) and data else data

    # Skeleton preview image is in output_files (PreviewImage saves to temp/)
    skeleton_filename = None
    skeleton_subfolder = ""
    skeleton_type = "temp"
    for entry in _outputs_to_files(result.get("history") or {}):
        if entry.get("kind") == "images":
            skeleton_filename = entry.get("filename")
            skeleton_subfolder = entry.get("subfolder", "")
            skeleton_type = entry.get("type", "temp")
            break

    out: dict[str, Any] = {
        "ok": True,
        "keypoints": keypoints,
        "json_path": str(json_path),
        "person_count": len(keypoints.get("people", [])) if isinstance(keypoints, dict) else 0,
    }
    if skeleton_filename:
        out["skeleton_image"] = {
            "filename": skeleton_filename,
            "subfolder": skeleton_subfolder,
            "type": skeleton_type,
        }
    return out


@mcp.tool()
async def upload_input(
    path: str,
    name: str = "",
    subfolder: str = "",
    overwrite: bool = False,
) -> dict[str, Any]:
    """Upload a local file into ComfyUI's input/ folder for use by LoadImage etc.

    Returns {name, subfolder, type} — plug those values into a LoadImage node's
    "image" input (the format LoadImage expects is just the saved name string).
    """
    return await comfy.upload(path, name=name or None, subfolder=subfolder, overwrite=overwrite)


@mcp.tool()
def tail_log(
    lines: int = 200,
    path: str = "",
    strip_noise: bool = False,
    errors_only: bool = False,
    max_tracebacks: int = 5,
) -> dict[str, Any]:
    """Tail the last N lines of ComfyUI's log file (default <COMFYUI_ROOT>/user/comfyui.log).

    When a workflow fails at runtime (OOM, missing model, custom-node bug), the actionable
    error usually lives here, not in the API response.

    Args:
        lines: how many lines to return (after filtering).
        path: override log path.
        strip_noise: drop HuggingFace transformer weight-list lines, progress bars,
                     and similar high-volume diagnostic spam that can bury the real
                     error 60KB deep. Always-applied lookback so the "interesting"
                     stuff isn't trimmed by `lines` cap.
        errors_only: return only the last N traceback blocks + their preceding error
                     line. Bypasses the line-count tail entirely. Best for "what just
                     broke?" without scrolling through model-loading log spam.
        max_tracebacks: when errors_only=True, cap how many traceback blocks to return.
    """
    p = Path(path) if path else _comfy_root() / "user" / "comfyui.log"
    if not p.is_file():
        return {"path": str(p), "error": "not found"}
    try:
        size = p.stat().st_size
        # When extracting tracebacks, read more — they often live before the recent tail.
        read_window = 4_000_000 if errors_only else 1_000_000
        with p.open("rb") as f:
            if size > read_window:
                f.seek(size - read_window)
                content = f.read()
                truncated = True
            else:
                content = f.read()
                truncated = False
        text = content.decode("utf-8", errors="replace")
        all_lines = text.splitlines()

        if errors_only:
            blocks = _extract_traceback_blocks(all_lines, max_tracebacks)
            return {
                "path": str(p),
                "size": size,
                "truncated": truncated,
                "mode": "errors_only",
                "traceback_count": len(blocks),
                "tracebacks": blocks,
            }

        if strip_noise:
            kept = [ln for ln in all_lines if not _is_log_noise(ln)]
            return {
                "path": str(p),
                "size": size,
                "truncated": truncated,
                "mode": "strip_noise",
                "stripped": len(all_lines) - len(kept),
                "lines": kept[-lines:],
            }

        return {
            "path": str(p),
            "size": size,
            "truncated": truncated,
            "lines": all_lines[-lines:],
        }
    except OSError as e:
        return {"path": str(p), "error": str(e)}


# Noise patterns: HF/transformers weight printouts, common progress bars, and lines
# that are pure metadata. Compiled once at module import.
_NOISE_PATTERNS = [
    # HuggingFace transformers weight enumeration: ".language_model.layers.0.mlp.weight"
    re.compile(r"^\s*(model\.)?(language_model|vision_model|text_encoder|encoder|decoder|transformer)\..*\.(weight|bias|gamma|beta|running_mean|running_var)\s*$"),
    re.compile(r"^\s*[\w.]+\.layers\.\d+\..*\.(weight|bias)\s*$"),
    # tqdm-style progress bars (Unicode-block AND ASCII-hash variants)
    re.compile(r"^\s*\d+%\|[█▌▏#=\- ]*\|\s*\d+/\d+"),
    re.compile(r"^\s*\d+it \[\d+:\d+, "),
    # ComfyUI per-token sampler progress (a single line that gets cleared via \r in TTYs but
    # ends up as separate lines in file logs)
    re.compile(r"^\s*\d+%\|.* it/s\]"),
]


def _is_log_noise(line: str) -> bool:
    return any(p.match(line) for p in _NOISE_PATTERNS)


def _extract_traceback_blocks(all_lines: list[str], limit: int) -> list[dict[str, Any]]:
    """Extract the last `limit` traceback blocks from log lines.

    A block runs from a 'Traceback (most recent call last):' marker through the
    last indented frame and the final exception line (typically un-indented and
    starting with the exception class name + ':').
    """
    blocks: list[dict[str, Any]] = []
    i = 0
    n = len(all_lines)
    while i < n:
        if "Traceback (most recent call last):" in all_lines[i]:
            start = i
            j = i + 1
            # Walk forward over indented frame lines + a trailing un-indented exception line.
            # Stop when we hit a line that's neither indented nor matches the exception pattern.
            exception_line_idx = None
            while j < n:
                ln = all_lines[j]
                if ln.startswith((" ", "\t")):
                    j += 1
                    continue
                # Un-indented line: the exception terminator if it looks like "Foo: msg"
                if exception_line_idx is None and re.match(r"^[A-Z][\w.]*(Error|Exception|Warning|Interrupt|Failed|NotImplemented)[\w.]*: ", ln):
                    exception_line_idx = j
                    j += 1
                    break
                if exception_line_idx is None and re.match(r"^[\w.]+: \S", ln):
                    exception_line_idx = j
                    j += 1
                    break
                # End of block without classic terminator
                break
            end = j
            preceding = all_lines[max(0, start - 1)] if start > 0 else ""
            blocks.append({
                "start_line": start,
                "preceding_line": preceding[-300:],
                "lines": all_lines[start:end],
                "exception": all_lines[exception_line_idx][:500] if exception_line_idx is not None else None,
            })
            i = end
            continue
        i += 1
    return blocks[-limit:] if limit > 0 else blocks


async def _enrich_node_errors(
    node_errors: dict[str, Any], workflow: dict[str, Any]
) -> dict[str, Any]:
    """Backfill `valid_values` on value_not_in_list errors where ComfyUI returned a null
    input_config (happens for dynamically-populated combos like model lists)."""
    if not node_errors:
        return node_errors
    out: dict[str, Any] = {}
    for node_id, info in node_errors.items():
        info_copy = dict(info)
        errs_out: list[dict[str, Any]] = []
        for err in info.get("errors", []) or []:
            err_copy = dict(err)
            if err.get("type") == "value_not_in_list":
                extra = err.get("extra_info") or {}
                input_name = extra.get("input_name")
                input_config = extra.get("input_config")
                already_have_list = (
                    isinstance(input_config, list)
                    and input_config
                    and isinstance(input_config[0], list)
                )
                if input_name and not already_have_list:
                    class_type = info.get("class_type") or (
                        workflow.get(node_id, {}).get("class_type")
                        if isinstance(node_id, str)
                        else None
                    )
                    if class_type:
                        try:
                            oi = await comfy.object_info(class_type)
                            spec = (oi.get(class_type, {}) or {}).get("input", {}) or {}
                            for section in ("required", "optional"):
                                decl = (spec.get(section) or {}).get(input_name)
                                if decl:
                                    t = (
                                        decl[0]
                                        if isinstance(decl, (list, tuple)) and decl
                                        else None
                                    )
                                    if isinstance(t, list):
                                        err_copy["valid_values"] = t
                                    break
                        except Exception:
                            pass
            errs_out.append(err_copy)
        info_copy["errors"] = errs_out
        out[node_id] = info_copy
    return out


def _fuzzy_match_list(needle: str, haystack: list) -> list[dict[str, Any]]:
    """Find candidates in haystack that resemble needle by basename (sans dir + ext)."""
    if not isinstance(needle, str) or not isinstance(haystack, list):
        return []
    needle_base = _basename_no_ext(needle).lower()
    out: list[dict[str, Any]] = []
    for item in haystack:
        if not isinstance(item, str):
            continue
        item_base = _basename_no_ext(item).lower()
        if item_base == needle_base:
            out.append({"value": item, "score": 100, "reason": "exact basename match"})
        elif item_base.startswith(needle_base) or needle_base.startswith(item_base):
            out.append({"value": item, "score": 80, "reason": "prefix"})
        elif needle_base in item_base or item_base in needle_base:
            out.append({"value": item, "score": 50, "reason": "substring"})
    out.sort(key=lambda m: -m["score"])
    return out


@mcp.tool()
async def resolve_missing_models(
    workflow: dict[str, Any] | None = None,
    tab_id: str = "",
) -> dict[str, Any]:
    """One-call diagnosis for the "workflow from another machine" case: validate, find
    substitutes for every missing model reference, return an actionable plan.

    Combines validate_workflow + find_model + fuzzy basename matching against the
    actual valid lists from ComfyUI's installed models. Use this before set_widget
    when fixing a workflow that was exported on a different setup.

    With no args, uses the workflow open in the most-recently-edited tab. Pass
    `workflow` (API format) for an offline check or `tab_id` for a specific tab.

    Returns:
      {
        ok: false if missing references exist (true if all valid),
        missing: [
          {
            node_id, class_type, input_name, received,
            auto_fix: <value> when an exact-basename match exists in valid list,
            suggestions: [{value, score, reason}, ...] (top 5),
            valid_values_count: N,
          }, ...
        ],
        node_errors: <full enriched node_errors>,
      }

    The agent can then call set_widget(node_id, input_name, auto_fix) for each
    auto_fix, and surface `suggestions` to the user for the rest.
    """
    if workflow is None:
        wf, _state, err = await _workflow_from_tab(tab_id=tab_id, want_api=True)
        if err:
            return err
        workflow = wf  # type: ignore[assignment]

    fmt, _ = _detect_format(workflow)
    if fmt != "api":
        return {"ok": False, "error": f"resolve_missing_models needs API format; got {fmt}"}

    queued = await _queue_and_enrich(workflow)
    if queued.get("ok"):
        prompt_id = queued.get("prompt_id")
        if prompt_id:
            await comfy.delete_from_queue([prompt_id])
            await comfy.interrupt(prompt_id)
        return {"ok": True, "missing": [], "message": "all references valid"}

    node_errors = queued.get("node_errors") or {}
    missing: list[dict[str, Any]] = []
    for node_id, info in node_errors.items():
        for err in info.get("errors", []) or []:
            if err.get("type") != "value_not_in_list":
                continue
            extra = err.get("extra_info") or {}
            input_name = extra.get("input_name")
            received = extra.get("received_value")
            if not (input_name and received):
                continue
            valid = err.get("valid_values")
            if valid is None:
                ic = extra.get("input_config")
                valid = ic[0] if isinstance(ic, list) and ic and isinstance(ic[0], list) else []
            suggestions = _fuzzy_match_list(received, valid or [])
            top = suggestions[0] if suggestions else None
            auto_fix = top["value"] if (top and top["score"] == 100) else None
            missing.append(
                {
                    "node_id": node_id,
                    "class_type": info.get("class_type"),
                    "input_name": input_name,
                    "received": received,
                    "auto_fix": auto_fix,
                    "suggestions": suggestions[:5],
                    "valid_values_count": len(valid) if isinstance(valid, list) else 0,
                }
            )

    return {
        "ok": len(missing) == 0,
        "error": queued.get("error"),
        "missing": missing,
        "node_errors": node_errors,
    }


@mcp.tool()
def describe_model(path: str, category: str = "") -> dict[str, Any]:
    """Read metadata from a local model file without loading it.

    Detects the model kind (lora/checkpoint/upscaler/controlnet/other) and returns
    a compact, type-aware summary at top level — trigger words for LoRAs, scale
    factor for upscalers, etc. Strips noisy raw fields (ss_tag_frequency,
    ss_dataset_dirs, ...) that bloat token usage; the useful distillations are
    in `summary`.

    Supports .safetensors (full metadata), .pth/.pt (tensor-shape inspection for
    upscalers — torch.load with weights_only=True for safety).

    Surfaces:
      - Type-aware `summary`: per-kind structured fields.
      - Sidecar files (<name>.json/.md/.txt/.civitai.info), folder _NOTES.md,
        preview image path.
      - Header validation — corrupted/truncated files fail here cleanly before
        wasting a queue.

    Args:
        path: relative-to-models (e.g. "loras/pony/style.safetensors") or absolute.
        category: when path is just a filename, look in this models subdir.
    """
    root = _comfy_root() / "models"
    if Path(path).is_absolute():
        full = Path(path)
    elif category:
        full = root / category / path
    else:
        full = root / path
    full = full.resolve()

    if not full.is_file():
        return {"error": "not a file", "resolved_path": str(full)}

    stat = full.stat()
    suffix = full.suffix.lower()
    kind = _classify_model(full, category)
    out: dict[str, Any] = {
        "path": str(full),
        "kind": kind,
        "size": stat.st_size,
        "modified": int(stat.st_mtime),
    }

    if suffix == ".safetensors":
        sf = _read_safetensors_metadata(full)
        meta = (sf or {}).get("metadata") or {}
        # Strip noisy raw fields — distilled bits are in summary
        if meta:
            sf = {**sf, "metadata": _trim_safetensors_metadata(meta)}
        out["safetensors"] = sf
        out["summary"] = _model_summary(kind, meta, sf)
    elif suffix in (".pth", ".pt"):
        info = _inspect_pytorch_state(full)
        out["state_dict"] = info
        out["summary"] = _upscaler_summary_from_state(info) if kind == "upscaler" else {
            "shape_info": "unknown kind for .pth — pass category to disambiguate"
        }

    # Sidecars + folder notes + preview (unchanged)
    sidecars: dict[str, Any] = {}
    for sc in (
        full.with_suffix(".json"),
        full.with_suffix(".md"),
        full.with_suffix(".txt"),
        full.parent / (full.stem + ".civitai.info"),
        full.parent / (full.name + ".civitai.info"),
    ):
        if sc.is_file():
            try:
                content = sc.read_text(errors="replace")
                if sc.suffix in (".json", ".info"):
                    try:
                        content = json.loads(content)
                    except Exception:
                        pass
                sidecars[sc.name] = content if not isinstance(content, str) else content[:6000]
            except OSError:
                pass
    if sidecars:
        out["sidecars"] = sidecars

    notes = full.parent / "_NOTES.md"
    if notes.is_file():
        try:
            out["folder_notes_path"] = str(notes)
            out["folder_notes"] = notes.read_text(errors="replace")[:6000]
        except OSError:
            pass

    for ext in (".preview.png", ".preview.jpg", ".png", ".jpg", ".webp"):
        candidate = full.parent / (full.stem + ext)
        if candidate.is_file():
            out["preview_path"] = str(candidate)
            break

    return out


@mcp.tool()
async def run_workflow(
    workflow: dict[str, Any] | None = None,
    tab_id: str = "",
    wait_seconds: int = 300,
    strip_warnings: bool = False,
) -> dict[str, Any]:
    """Daily-driver: queue + wait + return output file references in one call.

    PREFERRED PATTERN — modify the workflow already open in the user's ComfyUI tab,
    then run with no args:

        get_open_workflow / describe_graph   # see what's there
        set_widget(node_id, name, value)     # tweak settings
        run_workflow()                        # queues the open tab's graph

    This is fast, token-cheap, and the user sees what's happening in their editor.

    The `workflow=` argument should be your LAST RESORT. It's for headless / batch
    use only. When you pass an explicit workflow:
      • The graph is NOT shown in the user's editor (no canvas update, no node refs).
      • Live PreviewImage events go to no one — user has no visibility into progress.
      • The submitted JSON is auto-saved to <COMFYUI_ROOT>/output/_runs/<prompt_id>.json
        so the user can manually load it via ComfyUI's "Load" button if needed.

    Before reaching for `workflow=`, consider:
      • catalog_workflows() — your user likely has dozens of working workflows already.
        Pick the closest, apply_workflow it to the tab, then set_widget your tweaks.
      • Use the prompt-* skills (prompt-flux, prompt-illustrious, prompt-qwen,
        prompt-zimage) to generate prompts that follow each model's conventions.
        These exist precisely so you don't construct workflows from prompting first
        principles.

    Returns:
      {prompt_id, status, elapsed_seconds, output_files: [{node_id, kind, filename,
        subfolder, type}, ...], history?, error?, saved_workflow_path?}
      where status is "completed" | "error" | "interrupted" | "timeout".
      saved_workflow_path is set only when `workflow=` was passed explicitly.

    Long runs (>30s): this tool blocks. Either run in the background or split into
    queue_workflow() + wait_for_completion() so the user sees progress.
    """
    effective_client_id: str | None = None
    saved_workflow_path: str | None = None
    if workflow is None:
        wf, state, err = await _workflow_from_tab(tab_id=tab_id, want_api=True)
        if err:
            return err
        workflow = wf  # type: ignore[assignment]
        effective_client_id = state.get("comfy_client_id") if state else None

    fmt, _ = _detect_format(workflow)
    if fmt != "api":
        return {"ok": False, "error": f"workflow must be API format; got {fmt}"}

    queued = await _queue_and_enrich(workflow, client_id=effective_client_id)
    if not queued.get("ok"):
        return queued

    prompt_id = queued.get("prompt_id")
    if not prompt_id:
        return {"ok": False, "error": "queued but server returned no prompt_id", "raw": queued}

    # Fix A: when an explicit workflow was passed (no tab pulled), save the JSON
    # to a known path so the user can load it manually. The agent has constructed
    # something the user otherwise has no way to see.
    if effective_client_id is None:
        try:
            runs_dir = _comfy_root() / "output" / "_runs"
            runs_dir.mkdir(parents=True, exist_ok=True)
            target = runs_dir / f"{prompt_id}.json"
            target.write_text(json.dumps(workflow, indent=2))
            saved_workflow_path = str(target)
        except (RuntimeError, OSError):
            pass

    t0 = time.monotonic()
    result = await comfy.wait(prompt_id, timeout=float(wait_seconds))
    elapsed = round(time.monotonic() - t0, 1)

    out: dict[str, Any] = {
        "prompt_id": prompt_id,
        "status": result.get("status"),
        "elapsed_seconds": elapsed,
    }
    if saved_workflow_path:
        out["saved_workflow_path"] = saved_workflow_path
        out["note"] = (
            "explicit `workflow=` was supplied — the graph was NOT applied to any "
            "browser tab. Saved API-format JSON to saved_workflow_path so the user "
            "can drag/load it into ComfyUI manually."
        )
    if result.get("status") == "completed":
        history = result.get("history") or {}
        out["output_files"] = _outputs_to_files(history)
        # Compact: only keep status + outputs from history; drop prompt/extra_data echoes
        compact_history = {"status": history.get("status"), "outputs": history.get("outputs")}
        if strip_warnings:
            compact_history = _strip_history_warnings(compact_history)
        out["history"] = compact_history
    elif result.get("status") == "error":
        out["error"] = result.get("error")
        out["progress"] = result.get("progress")
    elif result.get("status") == "interrupted":
        out["interrupted"] = True
        out["progress"] = result.get("progress")
    elif result.get("status") == "timeout":
        out["timeout"] = True
        out["progress"] = result.get("progress")
    return out


@mcp.tool()
async def find_model(query: str, category: str = "", limit: int = 20) -> dict[str, Any]:
    """Fuzzy-find an installed model by filename across model categories.

    Multi-token search: split on whitespace/underscore/dash; ALL tokens must appear
    somewhere in the candidate path (case-insensitive). Score combines exact-basename
    bonus, prefix match, and the fraction of tokens that landed in the basename
    (vs. dir components). So "gemma 12B fp8" picks gemma_3_12B_it_fp8_e4m3fn over
    gemma_3_12B_it.

    Strips path components and the file extension when matching, so "qwen_image_vae"
    finds "qwen/qwen_image_vae.safetensors" in the vae category.

    Args:
        query: free-text. Whitespace/underscore/dash split. Single-token queries fall
               back to substring scoring (preserves prior behavior).
        category: restrict to one category (checkpoints, vae, loras, ...). Empty searches all.
        limit: max matches.

    Returns: {query, tokens, matches: [{category, path, score, matched_in_basename}, ...],
              categories_searched, match_count}.
    """
    q_full = _basename_no_ext(query).lower()
    tokens = [t for t in _split_query_tokens(query) if t]

    if category:
        categories = [category]
    else:
        cats = await comfy.models()
        categories = [c for c in (cats if isinstance(cats, list) else []) if isinstance(c, str)]

    results: list[dict[str, Any]] = []
    for cat in categories:
        try:
            files = await comfy.models(cat)
        except Exception:
            continue
        if not isinstance(files, list):
            continue
        for path in files:
            if not isinstance(path, str):
                continue
            scored = _score_model_path(path, q_full, tokens)
            if scored is None:
                continue
            results.append({"category": cat, "path": path, **scored})

    results.sort(key=lambda r: (-r["score"], r["path"]))
    return {
        "query": query,
        "tokens": tokens,
        "categories_searched": categories,
        "matches": results[:limit],
        "match_count": len(results),
    }


def _split_query_tokens(query: str) -> list[str]:
    """Lowercase + split on whitespace/underscore/dash. Drops empties."""
    return [t for t in re.split(r"[\s_\-]+", query.lower()) if t]


def _score_model_path(path: str, q_full: str, tokens: list[str]) -> dict[str, Any] | None:
    """Score a candidate model path against the query.

    Single-token: legacy substring scoring (100=exact, 80=prefix, 50=substring).
    Multi-token: every token must appear somewhere in the path. Score is the sum of
    per-token bonuses, weighted toward basename matches over directory matches, plus
    a small bonus when ALL tokens land in the basename (the "right one" signal).
    """
    base_no_ext = _basename_no_ext(path).lower()
    path_l = path.lower()

    if len(tokens) <= 1:
        # Legacy single-token mode — preserves existing callers
        if q_full == base_no_ext:
            return {"score": 100, "matched_in_basename": True}
        if base_no_ext.startswith(q_full):
            return {"score": 80, "matched_in_basename": True}
        if q_full in base_no_ext:
            return {"score": 50, "matched_in_basename": True}
        return None

    score = 0
    in_base = 0
    for tok in tokens:
        if tok in base_no_ext:
            score += 30
            in_base += 1
        elif tok in path_l:
            score += 10  # matched in directory only — weaker signal
        else:
            return None  # AND-semantics: every token must appear

    # Bonuses for fully-in-basename hits and for full string match
    if in_base == len(tokens):
        score += 20
    if base_no_ext == q_full:
        score += 50
    elif base_no_ext.startswith(q_full):
        score += 20

    return {"score": score, "matched_in_basename": in_base == len(tokens)}


@mcp.tool()
async def validate_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    """Dry-run an API-format workflow through ComfyUI's validator without running it.

    If invalid, returns {ok: false, error, node_errors: {<node_id>: {errors: [...], class_type}}}
    where each error includes the input name, the offending value, and the list of valid
    values. If valid, the workflow gets queued and then immediately cancelled —
    returns {ok: true, cancelled: true}.

    For workflows that reference missing models, the structured node_errors gives you
    the COMPLETE valid list (not the truncated "list of length 27" you see in stderr).
    """
    fmt, _ = _detect_format(workflow)
    if fmt != "api":
        return {"ok": False, "error": f"validate_workflow needs API format; got {fmt}"}
    queued = await _queue_and_enrich(workflow)
    if not queued.get("ok"):
        return queued
    prompt_id = queued.get("prompt_id")
    if prompt_id:
        await comfy.delete_from_queue([prompt_id])
        await comfy.interrupt(prompt_id)
    return {
        "ok": True,
        "prompt_id": prompt_id,
        "cancelled": True,
        "node_errors": queued.get("node_errors") or {},
    }


@mcp.tool()
async def validate_workflow_models(
    workflow: dict[str, Any] | None = None,
    tab_id: str = "",
) -> dict[str, Any]:
    """Pre-flight every model widget in a workflow against ComfyUI's installed lists.

    Faster than `resolve_missing_models` (which submits + cancels a queue trip): walks
    the workflow's model references and asks /object_info directly for each loader's
    valid_values list. No queue side-effects, no race against currently-running jobs.

    Use BEFORE queue_workflow to catch path issues like the "ltx2/<file>" subfolder
    case — every node_id, slot, value, and resolution status in one pass.

    With no args, validates the workflow open in the most-recently-edited tab.
    Pass `workflow` (UI or API format) for an offline check or `tab_id` for a specific tab.

    Returns:
      {
        ok: false if any reference is unresolved (true if all resolve),
        format,
        checked: <count>,
        resolved: [{node_id, class_type, input_name, value}, ...],
        unresolved: [{node_id, class_type, input_name, value, suggestions: [...],
                      valid_values_count}, ...],
        unknown_loader: [{node_id, class_type, value, reason}, ...]
            — references where /object_info had no valid-values list (custom node we
              can't introspect, or the input type isn't a combo).
      }
    """
    if workflow is None:
        wf, _state, err = await _workflow_from_tab(tab_id=tab_id, want_api=False)
        if err:
            return err
        workflow = wf  # type: ignore[assignment]

    fmt, _ = _detect_format(workflow)
    if fmt == "unknown":
        return {"ok": False, "error": "workflow is not a recognizable format", "format": fmt}

    refs = _extract_model_widget_refs(workflow, fmt)
    if not refs:
        return {"ok": True, "format": fmt, "checked": 0, "resolved": [], "unresolved": [],
                "note": "no model widget references found"}

    info_cache: dict[str, Any] = {}
    resolved: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    unknown_loader: list[dict[str, Any]] = []

    for ref in refs:
        class_type = ref["class_type"]
        if class_type not in info_cache:
            try:
                oi = await comfy.object_info(class_type)
                info_cache[class_type] = oi.get(class_type) if isinstance(oi, dict) else None
            except Exception as e:
                info_cache[class_type] = None
                unknown_loader.append({**ref, "reason": f"object_info failed: {e}"})
                continue

        spec = info_cache.get(class_type) or {}
        valid = _valid_values_for_input(spec, ref["input_name"])
        if not isinstance(valid, list):
            unknown_loader.append({**ref, "reason": "input has no combo valid_values list"})
            continue

        if ref["value"] in valid:
            resolved.append(ref)
            continue

        # Try basename-only match (handles loras/foo.safetensors vs foo.safetensors)
        suggestions = _fuzzy_match_list(ref["value"], valid)
        unresolved.append({
            **ref,
            "valid_values_count": len(valid),
            "suggestions": suggestions[:5],
            "auto_fix": (suggestions[0]["value"] if suggestions and suggestions[0]["score"] == 100 else None),
        })

    return {
        "ok": len(unresolved) == 0,
        "format": fmt,
        "checked": len(refs),
        "resolved": resolved,
        "unresolved": unresolved,
        "unknown_loader": unknown_loader,
    }


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


def _valid_values_for_input(spec: dict[str, Any], input_name: str | None) -> Any:
    """Pull the valid_values list (the combo list) for a named input from /object_info.
    Returns the list, or None if not a combo. With input_name=None (UI-format fallback
    where we couldn't determine the name), scans all combo inputs and returns the first
    one that contains a model-extension entry — a reasonable approximation."""
    inputs = spec.get("input", {}) if isinstance(spec, dict) else {}
    for section in ("required", "optional"):
        decls = (inputs.get(section) or {})
        if input_name and input_name in decls:
            decl = decls[input_name]
            t = decl[0] if isinstance(decl, (list, tuple)) and decl else None
            return t if isinstance(t, list) else None
        if input_name is None:
            for _name, decl in decls.items():
                t = decl[0] if isinstance(decl, (list, tuple)) and decl else None
                if isinstance(t, list) and t and isinstance(t[0], str) \
                        and t[0].lower().endswith(_MODEL_FILE_EXTS):
                    return t
    return None


@mcp.tool()
async def list_models(category: str = "") -> dict[str, Any]:
    """List models registered with ComfyUI (respects extra_model_paths.yaml).

    With no category, returns the list of available categories (checkpoints, loras, vae, ...).
    With a category, returns the file list within that category.

    This hits ComfyUI's /models API rather than walking the filesystem, so it matches what
    the running server actually sees.
    """
    data = await comfy.models(category or None)
    return {"category": category or None, "items": data}


@mcp.tool()
def list_workflows(dir: str = "") -> dict[str, Any]:
    """Recursively list .json workflow files under a directory.

    Defaults to <COMFYUI_ROOT>/user/default/workflows. Follows symlinks (your workflows dir
    is a NAS symlink); reports a clear error instead of silently returning [] if the target
    is missing or unreadable.
    """
    base = Path(dir) if dir else _comfy_root() / "user" / "default" / "workflows"
    return _walk_json(base)


@mcp.tool()
def read_workflow(path: str) -> dict[str, Any]:
    """Read a workflow JSON file and detect its format.

    Returns {path, format: "api"|"ui"|"unknown", node_count, workflow}.
    - "api" is the flat {<id>: {class_type, inputs}} shape that queue_workflow accepts.
    - "ui" is the editor's saved shape (top-level "nodes"/"links"); not directly runnable —
      open in ComfyUI and "Save (API Format)" to convert.
    """
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        return {"path": str(p), "error": "not a file"}
    try:
        wf = json.loads(p.read_text())
    except json.JSONDecodeError as e:
        return {"path": str(p), "error": f"invalid json: {e}"}

    fmt, count = _detect_format(wf)
    return {"path": str(p), "format": fmt, "node_count": count, "workflow": wf}


@mcp.tool()
def list_failed_imports(path: str = "", with_tracebacks: bool = True) -> dict[str, Any]:
    """Surface custom_node packages that failed to import during ComfyUI startup.

    When a custom_node silently fails to import (missing dependency, removed module,
    breaking ComfyUI core change), the only signal at runtime is "missing class_type"
    when you try to queue a workflow that uses it. This tool parses comfyui.log for
    the actual import errors so you can fix the root cause.

    Detected patterns:
      • "(IMPORT FAILED): /path/to/custom_nodes/<name>"  ← ComfyUI startup line
      • "Cannot import <path> module for custom nodes: <reason>"
      • "[ComfyUI-Manager] Failed to import: <name>" + traceback
      • Traceback blocks where any frame's file path lives in custom_nodes/

    Args:
        path: override comfyui.log location.
        with_tracebacks: include the full traceback per failure (default true).

    Returns: {log_path, failed: [{name, path?, reason?, traceback?}, ...], unique_count}.
    """
    p = Path(path) if path else _comfy_root() / "user" / "comfyui.log"
    if not p.is_file():
        return {"log_path": str(p), "error": "not found"}

    try:
        size = p.stat().st_size
        with p.open("rb") as f:
            # Custom node imports happen at startup — usually within first ~10MB of log,
            # but to handle long-running daemons that have rotated, scan up to 20MB.
            window = min(size, 20_000_000)
            f.seek(size - window)
            content = f.read()
    except OSError as e:
        return {"log_path": str(p), "error": str(e)}

    lines = content.decode("utf-8", errors="replace").splitlines()
    failures: dict[str, dict[str, Any]] = {}

    re_import_failed = re.compile(r"^\s*[\d.]+\s*seconds?\s*\(IMPORT FAILED\):\s*(.+)$")
    re_cannot_import = re.compile(r"^Cannot import (.+) module for custom nodes:\s*(.*)$")
    re_manager_failed = re.compile(r"^\[ComfyUI-Manager\]\s+Failed to import:\s*(.+)$")
    re_custom_node_in_traceback = re.compile(r'File\s+"([^"]*custom_nodes/[^"]+)"')

    for i, ln in enumerate(lines):
        m = re_import_failed.match(ln)
        if m:
            full_path = m.group(1).strip()
            name = full_path.rstrip("/").rsplit("/", 1)[-1]
            entry = failures.setdefault(name, {"name": name, "path": full_path,
                                               "reason": None, "traceback": None})
            entry["path"] = full_path
            # Look back for the prior Traceback block — typically right above
            if with_tracebacks and entry.get("traceback") is None:
                tb = _traceback_block_above(lines, i)
                if tb:
                    entry["traceback"] = tb
                    entry["reason"] = (tb[-1][:300] if tb else None)
            continue

        m = re_cannot_import.match(ln)
        if m:
            module_path = m.group(1).strip()
            reason = m.group(2).strip()
            name = module_path.rstrip("/").rsplit("/", 1)[-1]
            failures.setdefault(name, {"name": name, "path": module_path,
                                       "reason": reason, "traceback": None})
            continue

        m = re_manager_failed.match(ln)
        if m:
            name = m.group(1).strip()
            entry = failures.setdefault(name, {"name": name, "path": None,
                                               "reason": None, "traceback": None})
            if with_tracebacks and entry.get("traceback") is None:
                tb = _traceback_block_below(lines, i)
                if tb:
                    entry["traceback"] = tb
                    entry["reason"] = (tb[-1][:300] if tb else None)

    # Catch unaffiliated tracebacks that mention custom_nodes/<X>/...
    if with_tracebacks:
        for i, ln in enumerate(lines):
            if "Traceback (most recent call last):" not in ln:
                continue
            block = _walk_traceback(lines, i)
            if not block:
                continue
            for f_ln in block:
                m = re_custom_node_in_traceback.search(f_ln)
                if not m:
                    continue
                # Extract the custom_nodes/<name>/ portion
                path_in_tb = m.group(1)
                after = path_in_tb.split("custom_nodes/", 1)[1]
                name = after.split("/", 1)[0]
                if not name or name in failures:
                    break
                failures[name] = {
                    "name": name,
                    "path": path_in_tb.split("/" + name, 1)[0] + "/" + name,
                    "reason": block[-1][:300] if block else None,
                    "traceback": block,
                }
                break

    failed_list = [
        {k: v for k, v in entry.items() if (with_tracebacks or k != "traceback")}
        for entry in failures.values()
    ]
    failed_list.sort(key=lambda e: e["name"].lower())
    return {
        "log_path": str(p),
        "scanned_bytes": len(content),
        "unique_count": len(failed_list),
        "failed": failed_list,
    }


def _traceback_block_above(lines: list[str], idx: int, max_lookback: int = 200) -> list[str] | None:
    """Walk backward from idx looking for the most recent 'Traceback (most recent call last):'
    marker, then return that block (forward-walked from there). None if not found nearby."""
    start_search = max(0, idx - max_lookback)
    for j in range(idx - 1, start_search - 1, -1):
        if "Traceback (most recent call last):" in lines[j]:
            return _walk_traceback(lines, j)
    return None


def _traceback_block_below(lines: list[str], idx: int, max_lookahead: int = 200) -> list[str] | None:
    """Walk forward from idx looking for the next 'Traceback (most recent call last):' marker."""
    end = min(len(lines), idx + max_lookahead)
    for j in range(idx + 1, end):
        if "Traceback (most recent call last):" in lines[j]:
            return _walk_traceback(lines, j)
    return None


def _walk_traceback(lines: list[str], start: int) -> list[str]:
    """Forward-walk an intact traceback block starting at `start`. Includes the
    Traceback marker, indented frames, and the final exception-class line if present."""
    if start >= len(lines):
        return []
    out = [lines[start]]
    j = start + 1
    while j < len(lines):
        ln = lines[j]
        if ln.startswith((" ", "\t")):
            out.append(ln)
            j += 1
            continue
        # Un-indented terminator: classic "ClassName: message" or "ClassName"
        if re.match(r"^[A-Z][\w.]*(Error|Exception|Warning|Interrupt|Failed|NotImplemented)[\w.]*(:\s|$)", ln):
            out.append(ln)
            break
        if re.match(r"^[\w.]+: \S", ln):
            out.append(ln)
            break
        break
    return out


@mcp.tool()
def list_custom_nodes() -> dict[str, Any]:
    """List custom_node packages installed under <COMFYUI_ROOT>/custom_nodes.

    Returns {root, count, packages: [{name, path, has_git, has_pyproject, has_init}]}.
    Useful before recommending a workflow — many in-the-wild graphs reference nodes
    that may not be installed locally.
    """
    root = _comfy_root() / "custom_nodes"
    if not root.exists():
        return {"root": str(root), "error": "not found"}

    packages = []
    for entry in sorted(root.iterdir()):
        if entry.name.startswith((".", "__")) or entry.name.endswith(".py.example"):
            continue
        if entry.is_file() and entry.suffix == ".py":
            packages.append({"name": entry.name, "path": str(entry), "kind": "single_file"})
            continue
        if not entry.is_dir():
            continue
        packages.append(
            {
                "name": entry.name,
                "path": str(entry),
                "kind": "package",
                "has_git": (entry / ".git").exists(),
                "has_pyproject": (entry / "pyproject.toml").exists(),
                "has_init": (entry / "__init__.py").exists(),
            }
        )
    return {"root": str(root), "count": len(packages), "packages": packages}


_comfy_root_cache: Path | None = None


def _comfy_root() -> Path:
    """Locate the ComfyUI installation root in priority order:
      1. COMFYUI_ROOT env var
      2. Current working directory if it looks like a ComfyUI install
      3. The cwd of the process listening on COMFYUI_URL's port (via psutil) —
         catches the common case where Claude Code runs from /home/charlie but
         ComfyUI is running from /home/charlie/projects/.../ComfyUI.
    Result is cached after first successful resolution.
    """
    global _comfy_root_cache
    if _comfy_root_cache is not None:
        return _comfy_root_cache

    env = os.environ.get("COMFYUI_ROOT")
    if env:
        _comfy_root_cache = Path(env).expanduser().resolve()
        return _comfy_root_cache

    cwd = Path.cwd()
    if (cwd / "main.py").exists() and (cwd / "custom_nodes").exists():
        _comfy_root_cache = cwd
        return cwd

    detected = _detect_comfy_root_via_port()
    if detected is not None:
        _comfy_root_cache = detected
        return detected

    raise RuntimeError(
        f"ComfyUI root not found. Set COMFYUI_ROOT env var, launch from the ComfyUI dir, "
        f"or ensure ComfyUI is running on {os.environ.get('COMFYUI_URL', 'http://127.0.0.1:8188')} "
        f"(current cwd: {cwd})"
    )


def _detect_comfy_root_via_port() -> Path | None:
    """Find the process listening on the ComfyUI port and use its cwd. Returns None on
    any failure (no psutil, no listener, perms, etc) — caller falls back to error."""
    try:
        import psutil
        from urllib.parse import urlparse
    except ImportError:
        return None
    url = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
    try:
        port = urlparse(url).port or 8188
    except Exception:
        return None
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.status != psutil.CONN_LISTEN:
                continue
            if conn.laddr and conn.laddr.port == port and conn.pid:
                try:
                    proc = psutil.Process(conn.pid)
                    cwd = Path(proc.cwd())
                    if (cwd / "main.py").exists() and (cwd / "custom_nodes").exists():
                        return cwd
                except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
                    continue
    except (psutil.AccessDenied, OSError):
        return None
    return None


def _walk_json(base: Path) -> dict[str, Any]:
    if not base.exists():
        return {"root": str(base), "error": "not found (broken symlink?)", "files": []}
    if not base.is_dir():
        return {"root": str(base), "error": "not a directory", "files": []}
    files = []
    try:
        for p in sorted(base.rglob("*.json")):
            if p.is_file():
                st = p.stat()
                files.append(
                    {
                        "path": str(p),
                        "rel": str(p.relative_to(base)),
                        "size": st.st_size,
                        "mtime": int(st.st_mtime),
                    }
                )
    except OSError as e:
        return {"root": str(base), "error": str(e), "files": files}
    return {"root": str(base), "count": len(files), "files": files}


_WIDGET_TYPES = {"STRING", "INT", "FLOAT", "BOOLEAN"}


async def _edit_api(workflow: dict[str, Any], edits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    wf = copy.deepcopy(workflow)
    applied: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for node_id, inputs in edits.items():
        if node_id not in wf:
            errors.append({"node_id": node_id, "error": "not in workflow"})
            continue
        node = wf[node_id]
        node.setdefault("inputs", {})
        for name, value in inputs.items():
            node["inputs"][name] = value
        applied.append({"node_id": node_id, "inputs": list(inputs.keys())})
    return {"workflow": wf, "format": "api", "applied": applied, "errors": errors}


async def _ui_widget_order_aligned(class_type: str, actual_len: int) -> tuple[list[str], str]:
    """Pick the widget-name order that matches the actual widgets_values length.

    Different ComfyUI nodes follow different conventions for the seed_control_after_generate
    synthetic widget — most stock nodes have it, but custom nodes (Impact Pack's FaceDetailer,
    UltimateSDUpscale, etc.) often don't, even when their seed widget declares
    control_after_generate: True. Trying both variants and picking the matching length is
    the only robust resolution without per-node hardcoding.

    Returns (order, confidence) where confidence ∈ {"with_control", "without_control",
    "best_guess"} — agents/UI can surface "best_guess" cases as a warning.
    """
    with_control = await _ui_widget_order(class_type)
    if len(with_control) == actual_len:
        return with_control, "with_control"
    without_control = [n for n in with_control if not n.endswith("_control_after_generate")]
    if len(without_control) == actual_len:
        return without_control, "without_control"
    # Neither matches — return whichever is closer in length, with low confidence
    diff_with = abs(len(with_control) - actual_len)
    diff_without = abs(len(without_control) - actual_len)
    return (with_control if diff_with <= diff_without else without_control), "best_guess"


async def _ui_widget_order(class_type: str) -> list[str]:
    """Map widget input names to their positional index in widgets_values for a node class.

    Critical: accounts for synthetic *_control_after_generate widgets that ComfyUI's
    frontend injects right after any widget with `control_after_generate: True` in its
    options (most commonly `seed` on KSampler). Without this, the position-to-name
    mapping silently shifts after the seed and corrupts edits/reads from that point on.
    """
    info = await comfy.object_info(class_type)
    spec = info.get(class_type, {}).get("input", {})
    order: list[str] = []
    for section in ("required", "optional"):
        for name, decl in (spec.get(section) or {}).items():
            t = decl[0] if isinstance(decl, (list, tuple)) and decl else decl
            opts = decl[1] if isinstance(decl, (list, tuple)) and len(decl) > 1 else {}
            opts = opts if isinstance(opts, dict) else {}
            is_widget = False
            if isinstance(t, list):
                if not opts.get("forceInput"):
                    order.append(name)  # COMBO[...]
                    is_widget = True
            elif isinstance(t, str) and t in _WIDGET_TYPES:
                if not opts.get("forceInput"):
                    order.append(name)
                    is_widget = True
            # Frontend-injected control widget for INT seed-style inputs
            if is_widget and opts.get("control_after_generate"):
                order.append(f"{name}_control_after_generate")
    return order


async def _edit_ui(workflow: dict[str, Any], edits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    wf = copy.deepcopy(workflow)
    applied: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for node_id, inputs in edits.items():
        node, _scope = _resolve_node_path(wf, node_id)
        if node is None:
            errors.append({
                "node_id": node_id,
                "error": "node not found (use '<outer>/<inner>' for nodes inside subgraphs)",
            })
            continue
        class_type = node.get("type")
        if not class_type:
            errors.append({"node_id": node_id, "error": "node missing 'type'"})
            continue
        wv = list(node.get("widgets_values") or [])
        try:
            order, confidence = await _ui_widget_order_aligned(class_type, len(wv))
        except Exception as e:
            errors.append({"node_id": node_id, "error": f"object_info lookup failed: {e}"})
            continue

        ok_inputs: list[str] = []
        for name, value in inputs.items():
            if name not in order:
                errors.append({"node_id": node_id, "input": name, "error": "not a widget on this node (socket-only or unknown)"})
                continue
            idx = order.index(name)
            while len(wv) <= idx:
                wv.append(None)
            wv[idx] = value
            ok_inputs.append(name)
        node["widgets_values"] = wv
        if ok_inputs:
            entry = {"node_id": node_id, "inputs": ok_inputs, "class_type": class_type}
            if confidence == "best_guess":
                entry["alignment_warning"] = (
                    "widget alignment uncertain — edit may have landed at wrong index. "
                    "Verify with get_node_widgets and the agent's expectation."
                )
            applied.append(entry)

    return {"workflow": wf, "format": "ui", "applied": applied, "errors": errors}


def _read_safetensors_metadata(path: Path) -> dict[str, Any]:
    """Read the JSON header from a .safetensors file. Cheap (reads at most ~100MB,
    typically <2MB), and fails fast on truncation/corruption — exactly what catches
    incomplete downloads before they hit a runtime crash."""
    try:
        size = path.stat().st_size
        with path.open("rb") as f:
            head = f.read(8)
            if len(head) < 8:
                return {"error": "file too short to contain a header"}
            header_len = int.from_bytes(head, "little")
            if header_len <= 0:
                return {"error": f"non-positive header length {header_len}"}
            if header_len > 100_000_000:
                return {"error": f"absurd header length {header_len} (file likely not safetensors)"}
            if 8 + header_len > size:
                return {
                    "error": "header truncated — file is incomplete (partial download?)",
                    "expected_at_least_bytes": 8 + header_len,
                    "actual_bytes": size,
                }
            body = f.read(header_len)
            if len(body) < header_len:
                return {"error": "could not read full header"}
        try:
            hdr = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as e:
            return {"error": f"invalid JSON header: {e}"}
        except UnicodeDecodeError as e:
            return {"error": f"header is not UTF-8: {e}"}
        meta = hdr.get("__metadata__") or {}
        tensor_count = sum(1 for k in hdr if k != "__metadata__")

        # Check tensor data isn't truncated. Header lists each tensor's data_offsets
        # [start, end] relative to the start of the data block (which begins at
        # byte 8 + header_len). If the highest 'end' exceeds the file's actual
        # remaining bytes, the safetensors is corrupted — even if the header
        # itself parses cleanly. This is the "file not fully covered" case.
        max_end = 0
        for k, v in hdr.items():
            if k == "__metadata__" or not isinstance(v, dict):
                continue
            offsets = v.get("data_offsets")
            if isinstance(offsets, list) and len(offsets) >= 2 and isinstance(offsets[1], int):
                if offsets[1] > max_end:
                    max_end = offsets[1]
        expected_total = 8 + header_len + max_end
        if expected_total > size:
            return {
                "error": "tensor data truncated — file is incomplete (partial download?)",
                "expected_bytes": expected_total,
                "actual_bytes": size,
                "shortfall_bytes": expected_total - size,
                "metadata": meta,
                "tensor_count": tensor_count,
            }

        return {
            "metadata": meta,
            "tensor_count": tensor_count,
            "header_bytes": header_len,
            "tensor_data_bytes": max_end,
        }
    except OSError as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# describe_model helpers
# ---------------------------------------------------------------------------

# Kind classification: by category subdir first, then heuristic from filename + suffix
_LORA_CATEGORIES = {"loras", "lycoris"}
_CHECKPOINT_CATEGORIES = {"checkpoints", "diffusion_models", "diffusers"}
_UPSCALER_CATEGORIES = {"upscale_models"}
_CONTROLNET_CATEGORIES = {"controlnet"}
_VAE_CATEGORIES = {"vae", "vae_approx"}
_CLIP_CATEGORIES = {"text_encoders", "clip", "clip_vision"}

# Noisy safetensors metadata keys we drop — useful distillations end up in summary anyway
_NOISY_META_KEYS = {
    "ss_tag_frequency", "ss_dataset_dirs", "ss_datasets", "ss_bucket_info",
    "ss_session_id", "ss_training_started_at", "ss_training_finished_at",
    "ss_sd_scripts_commit_hash", "ss_steps", "ss_epoch",
    "ss_training_comment", "ss_full_fp16", "ss_seed", "ss_v2",
    "ss_face_crop_aug_range", "ss_random_crop", "ss_keep_tokens",
    "ss_max_grad_norm", "ss_max_token_length", "ss_min_snr_gamma",
    "ss_caption_dropout_rate", "ss_caption_dropout_every_n_epochs",
    "ss_caption_tag_dropout_rate", "ss_color_aug", "ss_flip_aug",
    "ss_gradient_accumulation_steps", "ss_gradient_checkpointing",
    "ss_huber_c", "ss_huber_schedule", "ss_loss_type",
    "ss_lr_scheduler", "ss_lr_warmup_steps", "ss_max_train_steps",
    "ss_mixed_precision", "ss_multires_noise_discount",
    "ss_multires_noise_iterations", "ss_network_alpha",
    "ss_network_args", "ss_network_dropout", "ss_network_module",
    "ss_new_sd_model_hash", "ss_noise_offset", "ss_noise_offset_random_strength",
    "ss_num_batches_per_epoch", "ss_num_epochs", "ss_num_reg_images",
    "ss_num_train_images", "ss_optimizer", "ss_prior_loss_weight",
    "ss_resolution", "ss_scale_weight_norms", "ss_sd_model_hash",
    "ss_text_encoder_lr", "ss_unet_lr", "ss_zero_terminal_snr",
    "ss_ip_noise_gamma", "ss_ip_noise_gamma_random_strength",
    "ss_debiased_estimation", "ss_lowram", "ss_clip_skip",
    "ss_cache_latents", "ss_adaptive_noise_scale",
    "sshs_model_hash", "sshs_legacy_hash",
    "ss_sd_model_name",  # often huge path strings
}


def _classify_model(path: Path, category: str) -> str:
    """Classify model kind from category + filename + suffix."""
    cat = (category or "").lower()
    if cat in _LORA_CATEGORIES or "lora" in path.parts or "lora" in path.stem.lower():
        return "lora"
    if cat in _CHECKPOINT_CATEGORIES:
        return "checkpoint"
    if cat in _UPSCALER_CATEGORIES or path.suffix.lower() in (".pth", ".pt"):
        # .pth/.pt typically upscalers; safetensors in upscale_models also valid
        return "upscaler"
    if cat in _CONTROLNET_CATEGORIES:
        return "controlnet"
    if cat in _VAE_CATEGORIES:
        return "vae"
    if cat in _CLIP_CATEGORIES:
        return "text_encoder"
    # Heuristic fallback: try to infer from path components
    parts_lower = {p.lower() for p in path.parts}
    if parts_lower & _LORA_CATEGORIES:
        return "lora"
    if parts_lower & _CHECKPOINT_CATEGORIES:
        return "checkpoint"
    if parts_lower & _UPSCALER_CATEGORIES:
        return "upscaler"
    if parts_lower & _CONTROLNET_CATEGORIES:
        return "controlnet"
    return "other"


def _trim_safetensors_metadata(meta: dict[str, Any]) -> dict[str, Any]:
    """Drop noisy raw fields from kohya-style safetensors metadata. The useful bits
    (top tags, trigger phrase, architecture) are extracted into `summary` separately."""
    return {k: v for k, v in meta.items() if k not in _NOISY_META_KEYS}


def _model_summary(kind: str, meta: dict[str, Any], sf: dict[str, Any] | None) -> dict[str, Any]:
    """Build the type-aware, structured summary the agent actually needs."""
    summary: dict[str, Any] = {
        "kind": kind,
        "title": meta.get("modelspec.title"),
        "description": (meta.get("modelspec.description") or "")[:500] or None,
        "architecture": meta.get("modelspec.architecture") or meta.get("ss_base_model_version"),
    }
    if kind == "lora":
        summary["trigger_phrase"] = meta.get("modelspec.trigger_phrase")
        summary["output_name"] = meta.get("ss_output_name")
        summary["training_top_tags"] = _top_training_tags(meta, limit=15)
        summary["recommended_strength_range"] = "0.4-0.7 (typical)"
    elif kind == "checkpoint":
        summary["embedded_vae"] = meta.get("modelspec.has_vae")
        summary["sai_resolution"] = meta.get("modelspec.resolution")
    elif kind == "controlnet":
        summary["controlnet_type"] = meta.get("modelspec.implementation") or "(check filename for hint: depth/canny/openpose/tile/...)"
    return {k: v for k, v in summary.items() if v is not None}


def _top_training_tags(meta: dict[str, Any], limit: int = 15) -> list[str]:
    """Extract the most-frequent training tags from kohya's ss_tag_frequency JSON."""
    tags = meta.get("ss_tag_frequency")
    if not isinstance(tags, str):
        return []
    try:
        tag_dict = json.loads(tags)
    except (json.JSONDecodeError, TypeError):
        return []
    flat: dict[str, int] = {}
    for _ds, counts in tag_dict.items():
        if isinstance(counts, dict):
            for tag, count in counts.items():
                flat[tag] = flat.get(tag, 0) + (count if isinstance(count, int) else 1)
    return [t for t, _ in sorted(flat.items(), key=lambda x: -x[1])[:limit]]


def _inspect_pytorch_state(path: Path) -> dict[str, Any]:
    """Read a .pth/.pt PyTorch state dict safely (weights_only=True). Returns key stats
    the agent can reason about without loading the full model: tensor count, common
    shape patterns, key prefixes (which hint at architecture)."""
    try:
        import torch  # type: ignore[import-untyped]
    except ImportError:
        return {"error": "torch not available; install for .pth inspection"}
    try:
        # weights_only=True since 2.4 — safely reject pickled callables
        state = torch.load(str(path), map_location="cpu", weights_only=True)
    except Exception as e:
        return {"error": f"torch.load failed: {e}"}

    if isinstance(state, dict) and not all(hasattr(v, "shape") for v in state.values()):
        # nested format — drill in if a 'model'/'state_dict' wrapper is present
        for key in ("model", "state_dict", "params"):
            if key in state and isinstance(state[key], dict):
                state = state[key]
                break

    if not isinstance(state, dict):
        return {"error": f"unexpected state type: {type(state).__name__}"}

    keys = list(state.keys())
    # Common architecture key prefixes
    key_prefixes: dict[str, int] = {}
    for k in keys:
        prefix = str(k).split(".", 1)[0]
        key_prefixes[prefix] = key_prefixes.get(prefix, 0) + 1
    top_prefixes = sorted(key_prefixes.items(), key=lambda x: -x[1])[:5]
    return {
        "tensor_count": len(keys),
        "top_key_prefixes": [{"prefix": p, "count": c} for p, c in top_prefixes],
        "first_keys": keys[:5],
    }


def _upscaler_summary_from_state(info: dict[str, Any]) -> dict[str, Any]:
    """Infer scale factor + architecture flavor from a torch state dict's key shapes.
    Best-effort — covers the common ESRGAN / Real-ESRGAN / SwinIR / SRVGGNet patterns."""
    if "error" in info:
        return {"error": info["error"]}
    prefixes = {p["prefix"]: p["count"] for p in info.get("top_key_prefixes", [])}
    summary: dict[str, Any] = {"kind": "upscaler", "tensor_count": info.get("tensor_count")}
    if "RRDB_trunk" in prefixes or "RRDB" in str(info.get("first_keys", [])):
        summary["architecture"] = "ESRGAN (RRDB trunk)"
    elif "body" in prefixes and "conv_first" in prefixes:
        summary["architecture"] = "Real-ESRGAN / SRResNet variant"
    elif "layers" in prefixes:
        summary["architecture"] = "SwinIR (transformer)"
    elif "head" in prefixes and "body" in prefixes:
        summary["architecture"] = "SRVGGNet (Real-ESRGAN compact)"
    else:
        summary["architecture"] = "unknown (inspect first_keys for clues)"
    summary["note"] = "scale factor not auto-detected; check filename (e.g. '4x-AnimeSharp' = 4x)"
    return summary


_NOTE_NODE_TYPES = {"Note", "MarkdownNote", "Note Plus (mtb)", "PrimitiveNode", "easy showAnything"}
_MODEL_FILE_EXTS = (".safetensors", ".ckpt", ".pth", ".gguf", ".bin", ".pt", ".onnx")


def _subgraph_def(workflow: dict[str, Any], type_id: Any) -> dict[str, Any] | None:
    """Find the subgraph definition with the given UUID/type. Returns the def dict or None."""
    if not isinstance(type_id, str):
        return None
    defs = (workflow.get("definitions") or {}).get("subgraphs") or []
    for d in defs:
        if isinstance(d, dict) and d.get("id") == type_id:
            return d
    return None


def _all_nodes(workflow: dict[str, Any], top: dict[str, Any] | None = None):
    """Yield every node dict in the workflow, recursing into subgraph definitions."""
    if top is None:
        top = workflow
    for n in workflow.get("nodes") or []:
        if not isinstance(n, dict):
            continue
        yield n
        sg = _subgraph_def(top, n.get("type"))
        if sg is not None:
            yield from _all_nodes(sg, top)


def _resolve_node_path(workflow: dict[str, Any], node_id: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Resolve a path-style node_id to (node, container_scope). Path syntax: '<outer>/<inner>'
    or '<outer>/<inner>/<inner_inner>' for nested subgraphs. Plain ints/strings work for
    top-level nodes. Returns (None, None) if not found."""
    parts = str(node_id).split("/")
    current = workflow
    found_node = None
    for i, part in enumerate(parts):
        try:
            nid_int = int(part)
        except (ValueError, TypeError):
            nid_int = None
        match = None
        for n in current.get("nodes") or []:
            if not isinstance(n, dict):
                continue
            n_id = n.get("id")
            if n_id == nid_int or str(n_id) == part:
                match = n
                break
        if match is None:
            return None, None
        found_node = match
        if i < len(parts) - 1:
            sg = _subgraph_def(workflow, match.get("type"))
            if sg is None:
                return None, None
            current = sg
    return found_node, current


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


def _detect_format(wf: Any) -> tuple[str, int]:
    if isinstance(wf, dict) and isinstance(wf.get("nodes"), list) and "links" in wf:
        return "ui", len(wf["nodes"])
    if isinstance(wf, dict) and wf and all(
        isinstance(v, dict) and "class_type" in v for v in wf.values()
    ):
        return "api", len(wf)
    return "unknown", 0


def _flatten_inputs(spec: dict[str, Any]) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []
    for section in ("required", "optional"):
        for n, v in (spec.get(section) or {}).items():
            out.append((n, v[0] if isinstance(v, (list, tuple)) and v else v))
    return out


def _socket_type(t: Any) -> str:
    if isinstance(t, str):
        return t.upper()
    if isinstance(t, list):
        return "ENUM"
    return str(t).upper()


# ---------------------------------------------------------------------------
# Refactor helpers (Dec 2025)
# ---------------------------------------------------------------------------


def _basename_no_ext(s: str) -> str:
    """Strip directory and extension. 'foo/bar.safetensors' → 'bar'."""
    base = s.rsplit("/", 1)[-1]
    return base.rsplit(".", 1)[0] if "." in base else base


def _outputs_to_files(history_entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten a history entry's outputs dict to a list of {node_id, kind, ...file fields}.
    `history_entry` is the per-prompt dict with shape {prompt, outputs, status, ...}."""
    outputs = (history_entry or {}).get("outputs") or {}
    files: list[dict[str, Any]] = []
    for node_id, node_out in outputs.items():
        if not isinstance(node_out, dict):
            continue
        for kind in ("images", "gifs", "audio", "videos"):
            for entry in node_out.get(kind, []) or []:
                if isinstance(entry, dict):
                    files.append({"node_id": node_id, "kind": kind, **entry})
    return files


async def _workflow_from_tab(
    tab_id: str = "", want_api: bool = False
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    """Pull workflow from the bridge for a tab. Returns (workflow, state, error_response).
    Exactly one of workflow/error_response is non-None on success/failure."""
    state = await comfy.bridge_state(tab_id=tab_id or None)
    if state.get("error"):
        return None, state, state
    wf = state.get("api_workflow" if want_api else "workflow")
    if wf is None:
        fmt_label = "api-format" if want_api else "ui-format"
        return None, state, {
            "error": f"no {fmt_label} workflow available",
            "hint": "is the bridge installed and a browser tab open with a valid graph?",
            "tab_count": state.get("tab_count", 0),
        }
    return wf, state, None


async def _queue_and_enrich(
    workflow: dict[str, Any], client_id: str | None = None
) -> dict[str, Any]:
    """Submit a workflow and shape the response uniformly: {ok, prompt_id?, error?, node_errors?}.
    On validation failure, node_errors are enriched with valid_values from /object_info."""
    status, body = await comfy.queue(workflow, client_id=client_id)
    if status == 200:
        return {"ok": True, **body}
    if "node_errors" in body:
        body = {**body, "node_errors": await _enrich_node_errors(body["node_errors"] or {}, workflow)}
    return {"ok": False, **body}


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


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
