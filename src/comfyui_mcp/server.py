from __future__ import annotations

import base64
import copy
import itertools
import json
import re
import time
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP, Image

from .client import comfy
from .images import (
    _resize_image_for_inline,
    _OPENPOSE_LIMB_PAIRS,
    _OPENPOSE_LIMB_COLORS,
    _OPENPOSE_JOINT_COLORS,
)
from .logs import (
    _is_log_noise,
    _strip_history_warnings,
    _extract_traceback_blocks,
    _traceback_block_above,
    _traceback_block_below,
    _walk_traceback,
)
from .search import (
    _SEARCH_STOPWORDS,
    _basename_no_ext,
    _score_query_match,
    _fuzzy_match_list,
    _split_query_tokens,
    _score_model_path,
)
from .model_meta import (
    _classify_model,
    _trim_safetensors_metadata,
    _model_summary,
    _inspect_pytorch_state,
    _upscaler_summary_from_state,
    _read_safetensors_metadata,
)
from .core import (
    _comfy_root,
    _walk_json,
    _detect_format,
    _subgraph_def,
    _resolve_node_path,
    _outputs_to_files,
    TAB_DISCONNECT_HINT,
)
from .widgets import (
    _ui_widget_order_aligned,
    _flatten_inputs,
    _socket_type,
)
from .tabs import _workflow_from_tab, _queue_and_enrich
from .summarize import (
    _extract_model_widget_refs,
    _valid_values_for_input,
    _describe_graph,
    _summarize_workflow_body,
    _describe_workflow_file,
)
from .snapshots import (
    _read_workflow_for_apply,
    _save_pre_apply_snapshot,
)
from . import civitai as _civitai
from . import loras as _loras_mod

mcp = FastMCP("comfyui-mcp")


@mcp.tool()
async def get_system_stats() -> dict[str, Any]:
    """Return ComfyUI system info: device, vram, python/comfy version. Use this as a smoke test."""
    return await comfy.system_stats()


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
        tab_count = state.get("tab_count", 0)
        return {
            "error": "no workflow state available",
            "hint": TAB_DISCONNECT_HINT if tab_count == 0 else
                    "the bridge (custom_nodes/comfyui-mcp-bridge) is reachable but the tab has no graph open",
            "tab_count": tab_count,
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


@mcp.tool()
async def suggest_local_loras(
    intent: str,
    base_model: str = "",
    k: int = 8,
) -> dict[str, Any]:
    """Find LoRAs already downloaded under <COMFYUI_ROOT>/models/loras/ that match an intent.

    Walks the LoRA dir recursively, reads each safetensors header for training tags
    (Kohya's ss_tag_frequency) + author-declared trigger phrase + base model, then
    ranks by tag overlap with `intent`. Returns ready-to-use candidates with their
    real trigger words and a recommended strength.

    Use this BEFORE search_civitai — the LoRA the user wants may already be on disk.

    Args:
      intent: free-text description of what the user wants (e.g. "photographic
              style with film grain", "neon cyberpunk lighting", "muscular fantasy
              warrior"). Tokenized, stopwords dropped.
      base_model: optional family filter. Free-form ("Flux.1 D", "illustrious",
                  "sdxl", "Pony", "Wan 2.6") — normalized internally to a small
                  enum (flux1/flux2/sdxl/sd15/illustrious/pony/qwen/zimage/wan/ltx).
                  LoRAs whose base family is detectably DIFFERENT are filtered out;
                  LoRAs with undetectable base are kept (lenient).
      k: max results.

    Returns: {ok, intent, base_family_normalized, total_scored, returned, candidates}
    where each candidate is {filename, base_model_raw, base_family, trigger_words,
    top_training_tags, recommended_strength, size_mb, score}.
    """
    return _loras_mod.suggest(intent=intent, base_model=base_model or None, k=k)


@mcp.tool()
async def search_civitai(
    query: str,
    types: str = "LORA",
    base_model: str = "",
    nsfw: bool = False,
    sort: str = "Most Downloaded",
    limit: int = 10,
) -> dict[str, Any]:
    """Search Civitai for any model type (LORA, Checkpoint, Controlnet, Upscaler,
    TextualInversion, VAE, Hypernetwork, MotionModule).

    BEFORE REACHING FOR THIS: call suggest_local_loras first. The LoRA the user
    wants may already be downloaded. Only use search_civitai when the local
    catalogue doesn't have what's needed, or the user explicitly asked to search.

    Safety rails baked in: items where Civitai flags `minor=true` are dropped
    silently and never returned. NSFW is opt-in via nsfw=True; default is SFW.

    Defaults:
      - `sort='Most Downloaded'` is intentional: 'Highest Rated' returns ZERO
        results for non-LoRA types (no items meet the rating threshold).
      - `nsfw=False` — only flip when the user explicitly asks for NSFW content.

    Args:
      query: free-text search terms (e.g. "neon noir", "openpose").
      types: model type — one of LORA, Checkpoint, Controlnet, Upscaler,
             TextualInversion, VAE, Hypernetwork, MotionModule, LoCon, MotionModule.
             Pass a comma-separated list to query multiple types in one call
             (e.g. "LORA,Checkpoint"). Defaults to LORA.
      base_model: filter by base model — Civitai uses strings like 'Flux.1 D',
                  'SDXL 1.0', 'Illustrious', 'Pony', 'SD 1.5'. Critical for not
                  surfacing cross-base-model results (an SDXL LoRA in a Flux
                  workflow is useless). When in doubt, omit and filter client-side.
      nsfw: include NSFW results. Default False. Never auto-flip — the user must
            explicitly ask.
      sort: 'Most Downloaded' (default), 'Highest Rated', 'Newest'.
      limit: max results. Default 10. Civitai paginates via nextCursor (returned
             in response when available).

    Returns: {ok, count, items: [{id, name, type, tags, creator, downloads, nsfw,
    versions: [{version_id, base_model, trained_words, file: {name, size_mb, ...},
    primary_image: {url, ...}}]}]}. Item shape is lean (~10 fields) — full
    description and license info live in describe_civitai_model.
    """
    types_arg: str | list[str] = types
    if "," in types:
        types_arg = [t.strip() for t in types.split(",") if t.strip()]
    return await _civitai.search(
        query=query,
        types=types_arg,
        base_model=base_model or None,
        nsfw=nsfw,
        sort=sort,
        limit=limit,
    )


@mcp.tool()
async def describe_civitai_model(model_id: int) -> dict[str, Any]:
    """Fetch full detail for a Civitai model by ID. Use after search_civitai when
    the user picks one and you need version list / declared trigger words /
    description before downloading.

    HTML in the description is stripped and truncated to ~800 chars. Full version
    list is returned with every file's size, format, and download URL. Trigger
    words returned here are Civitai-DECLARED — often empty or out of date; the
    canonical trigger words come from the file's own safetensors metadata after
    download (download_civitai_model returns them).

    Items where Civitai flags `minor=true` are refused outright.

    Returns: {ok, id, name, type, description, tags, creator, downloads, versions: [...]}
    """
    return await _civitai.describe(model_id=model_id)


@mcp.tool()
async def download_civitai_model(
    model_id: int,
    version_id: int = 0,
    subdir: str = "",
    confirm: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Download a Civitai model into the correct ComfyUI models/ subdir.

    TWO-CALL CONFIRMATION (this writes hundreds of MB to disk):
      1. First call with confirm=False (DEFAULT) returns a PREVIEW: target path,
         filesize, base model. Nothing is written.
      2. Show the preview to the user. If they approve, call AGAIN with confirm=True.

    Auto-routes by Civitai type → ComfyUI subdir:
      LORA / LoCon → models/loras/
      Checkpoint → models/checkpoints/
      Controlnet → models/controlnet/
      Upscaler → models/upscale_models/
      TextualInversion → models/embeddings/
      VAE → models/vae/
      Hypernetwork → models/hypernetworks/
      MotionModule → models/animatediff_models/

    File-type filtered: picks the actual loadable .safetensors / .ckpt / .pth from
    the version's files list (Civitai bundles training-data ZIPs and example
    images alongside; those are skipped).

    Refuses to overwrite existing files unless overwrite=True. Items where
    Civitai flags `minor=true` are refused outright.

    After successful download, re-reads the file's actual safetensors metadata
    and returns the CANONICAL trigger words (Civitai's declared words are
    often empty or wrong; the file's own header is authoritative).

    Args:
      model_id: Civitai model id (from search_civitai).
      version_id: specific version (from describe_civitai_model). Default 0 = newest.
      subdir: optional sub-path under the auto-routed type dir (e.g. "flux/" to
              go under models/loras/flux/). Relative paths only; no '..' allowed.
      confirm: must be True to actually download. Default False = preview only.
      overwrite: replace an existing file at the target path. Default False.

    Returns (preview): {ok, preview: {...}, next_step: "..."}
    Returns (downloaded): {ok, downloaded: true, path, size_mb, trained_words_canonical,
                          safetensors_metadata_summary, hint}
    """
    return await _civitai.download(
        model_id=model_id,
        version_id=version_id if version_id else None,
        subdir=subdir or None,
        confirm=confirm,
        overwrite=overwrite,
    )


@mcp.tool()
async def add_lora_to_workflow(
    filename: str,
    strength: float = 0.75,
    append_trigger_words: bool = True,
    tab_id: str = "",
) -> dict[str, Any]:
    """Add a LoRA to the open ComfyUI tab's workflow + optionally append its trigger
    words to the positive CLIPTextEncode.

    What this does:
      1. Pulls the open tab's UI workflow via the bridge.
      2. Reads the LoRA's safetensors metadata to extract canonical trigger words
         and the recommended strength (overridden by the `strength` arg).
      3. Adds a LoraLoader node to the canvas (it's NOT auto-wired — the agent
         must connect MODEL and CLIP to it via connect_nodes, OR the user may
         prefer to wire it manually).
      4. If `append_trigger_words=True` AND a positive CLIPTextEncode is found,
         appends the LoRA's trigger words to its prompt text via set_widget.
         Skips trigger words already present (case-insensitive substring check).

    Returns context the agent needs to finish the job: the new LoraLoader's node
    id, the existing CheckpointLoader's id (so the agent can wire MODEL+CLIP
    through the LoraLoader), and the existing LoRA loaders if any (so the agent
    can decide whether to delete the new one and reuse an existing slot).

    Args:
      filename: LoRA filename relative to models/loras/ (e.g. "illustrious/foo.safetensors").
                Use suggest_local_loras to get this.
      strength: LoRA strength (typically 0.4–1.0). Defaults to 0.75. The LoRA's
                metadata-recommended strength is included in the response.
      append_trigger_words: if True (default), the LoRA's trigger words are
                            appended to the positive prompt.
      tab_id: target a specific tab; defaults to the most-recent.

    Returns: {ok, lora_added: {node_id, filename, strength}, trigger_words_appended,
              trigger_words: [...], hint, existing_lora_loaders, checkpoint_loader_id?}
    """
    # 1. Pull workflow + read LoRA metadata in parallel-ish
    wf, _state, err = await _workflow_from_tab(tab_id=tab_id, want_api=False)
    if err:
        return {"ok": False, **err}

    # 2. Resolve LoRA file path and read its metadata
    try:
        loras_root = _comfy_root() / "models" / "loras"
    except RuntimeError as e:
        return {"ok": False, "error": str(e)}
    lora_path = loras_root / filename
    if not lora_path.is_file():
        return {"ok": False, "error": f"LoRA file not found: {lora_path}",
                "hint": "filename must be relative to models/loras/ (use suggest_local_loras)"}
    sf = _read_safetensors_metadata(lora_path)
    if "error" in sf:
        return {"ok": False, "error": f"could not read LoRA metadata: {sf['error']}"}
    meta = sf.get("metadata") or {}
    trigger_words = _loras_mod._extract_trigger_words(meta)
    metadata_strength = _loras_mod._recommended_strength(meta)

    # 3. Inspect existing graph: find LoRA loaders + positive text encode + checkpoint loader
    existing_loaders = _loras_mod.find_lora_loader_nodes(wf)
    positive_id = _loras_mod.find_positive_clip_text_encode(wf)
    checkpoint_id: int | None = None
    for n in wf.get("nodes") or []:
        if isinstance(n, dict) and n.get("type") in {"CheckpointLoaderSimple", "CheckpointLoader",
                                                       "Load Checkpoint", "ECHO Checkpoint Loader",
                                                       "UnetLoaderGGUF", "UNETLoader"}:
            checkpoint_id = n.get("id")
            break

    # 4. Add the LoraLoader node. Don't auto-wire; surface what's needed instead.
    add_result = await comfy.bridge_op(
        {
            "op": "add_node",
            "class_type": "LoraLoader",
            "pos": [0, 0],
            "widget_values": {"lora_name": filename, "strength_model": strength, "strength_clip": strength},
        },
        tab_id=tab_id or None,
    )
    if not add_result.get("ok"):
        return {"ok": False, "error": "add_node failed",
                "details": add_result, "trigger_words": trigger_words}
    new_node_id = (add_result.get("node") or {}).get("id")

    # 5. Append trigger words to positive CLIPTextEncode if requested
    trigger_words_appended = False
    append_error: str | None = None
    if append_trigger_words and trigger_words and positive_id is not None:
        positive_node = next(
            (n for n in wf.get("nodes") or [] if isinstance(n, dict) and n.get("id") == positive_id),
            None,
        )
        if positive_node:
            widgets = positive_node.get("widgets_values") or []
            current_text = widgets[0] if widgets and isinstance(widgets[0], str) else ""
            new_text = _loras_mod.append_to_prompt(current_text, trigger_words)
            if new_text != current_text:
                widget_name = _loras_mod.positive_text_widget_name(positive_node.get("type") or "")
                set_result = await comfy.bridge_op(
                    {"op": "set_widget", "node_id": positive_id, "name": widget_name, "value": new_text},
                    tab_id=tab_id or None,
                )
                if set_result.get("ok"):
                    trigger_words_appended = True
                else:
                    append_error = f"set_widget failed: {set_result.get('error', set_result)}"

    return {
        "ok": True,
        "lora_added": {
            "node_id": new_node_id,
            "filename": filename,
            "strength": strength,
            "metadata_recommended_strength": metadata_strength,
        },
        "trigger_words": trigger_words,
        "trigger_words_appended": trigger_words_appended,
        "trigger_words_append_error": append_error,
        "positive_text_encode_id": positive_id,
        "checkpoint_loader_id": checkpoint_id,
        "existing_lora_loaders": existing_loaders,
        "hint": (
            "The LoraLoader is on the canvas but NOT wired. Connect "
            f"MODEL and CLIP from checkpoint (node {checkpoint_id}) → "
            f"LoraLoader (node {new_node_id}) via connect_nodes, then wire "
            "LoraLoader's MODEL output to wherever the checkpoint's MODEL was "
            "going (sampler or another LoRA), and similarly for CLIP."
            if checkpoint_id is not None and new_node_id is not None
            else "Manually wire the LoraLoader's MODEL + CLIP inputs to your "
                 "model source, and route its outputs to the rest of the graph."
        ),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
