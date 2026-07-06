"""Best-effort UI-format -> API-format workflow conversion.

This is deliberately narrow. Full UI -> API conversion (subgraph flattening, exact
frontend widget semantics) lives in ComfyUI's own browser JS and is out of scope here —
see CLAUDE.md. What's common in practice is narrower: an agent has a saved UI-format
workflow it wants to run headlessly with overrides (batch_run/run_workflow's `path=`),
and hand-transcribing node-by-node into API format is slow and error-prone (wrong node
id, wrong input name, a missed link). This module resolves the mechanical part — widget
positions, direct links, and the common indirection nodes (Reroute, PrimitiveNode,
rgthree's GetNode/SetNode) — and surfaces anything it can't confidently resolve as a
warning instead of silently emitting a broken graph.
"""
from __future__ import annotations

import copy
from typing import Any

from .core import _detect_format, _subgraph_def
from .widgets import _ui_widget_order_aligned

_ANNOTATION_ONLY_TYPES = {"Note", "MarkdownNote", "Note Plus (mtb)"}
_PASSTHROUGH_TYPES = {"Reroute", "GetNode", "SetNode", "PrimitiveNode"}

# Virtual node ids ComfyUI assigns to a subgraph's external input/output ports. Inner
# links whose origin is the input port or whose target is the output port cross the
# subgraph boundary and get rewired to the instance's external connections.
_SUBGRAPH_INPUT_NODE = -10
_SUBGRAPH_OUTPUT_NODE = -20


def _expand_subgraphs(workflow: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Inline every subgraph instance into plain top-level nodes + array-form links so a
    UI workflow that uses subgraphs can go through the normal draft path.

    Inner node ids are namespaced as '<instance_id>:<inner_id>' — the same convention
    ComfyUI's own frontend uses when it flattens to API format (see _apply_overrides),
    so overrides/validation on the result line up with real ComfyUI output. Runs to a
    fixpoint, so nested subgraphs expand too (an inner instance surfaces as a namespaced
    top-level node on the next pass). Returns (expanded_workflow, warnings)."""
    wf = copy.deepcopy(workflow)
    warnings: list[dict[str, Any]] = []

    def def_for(node: dict[str, Any]) -> dict[str, Any] | None:
        return _subgraph_def(workflow, node.get("type"))

    # New link ids must not collide with any existing top-level or inner link.
    next_link = [_max_link_id(workflow) + 1]

    def new_link_id() -> int:
        lid = next_link[0]
        next_link[0] += 1
        return lid

    for _ in range(1000):  # fixpoint guard against a malformed self-referential def
        nodes = wf.get("nodes") or []
        inst = next((n for n in nodes if isinstance(n, dict) and def_for(n) is not None), None)
        if inst is None:
            break
        _expand_one_instance(wf, inst, def_for(inst), warnings, new_link_id)
    else:
        warnings.append({"reason": "subgraph expansion did not converge after 1000 passes — "
                                   "possible self-referential subgraph definition"})

    wf.pop("definitions", None)
    return wf, warnings


def _max_link_id(workflow: dict[str, Any]) -> int:
    ids = [0]
    for ln in workflow.get("links") or []:
        if isinstance(ln, list) and ln:
            ids.append(int(ln[0]) if isinstance(ln[0], int) else 0)
    for sg in (workflow.get("definitions") or {}).get("subgraphs") or []:
        for ln in sg.get("links") or []:
            if isinstance(ln, dict) and isinstance(ln.get("id"), int):
                ids.append(ln["id"])
    return max(ids)


def _expand_one_instance(
    wf: dict[str, Any],
    inst: dict[str, Any],
    sg: dict[str, Any],
    warnings: list[dict[str, Any]],
    new_link_id,
) -> None:
    instance_id = inst.get("id")
    links = wf.setdefault("links", [])
    top_link_map = {ln[0]: ln for ln in links if isinstance(ln, list) and len(ln) >= 6}

    def nid(inner_id: Any) -> str:
        return f"{instance_id}:{inner_id}"

    # External source feeding each subgraph input slot (by slot index): (from_node, from_slot)
    # if the instance input is wired to a top-level node, else None (inner node keeps its own
    # widget default — the common case for exposed model/seed widgets).
    inst_inputs = inst.get("inputs") or []
    inst_input_by_name = {s.get("name"): s for s in inst_inputs if isinstance(s, dict)}
    external_source: dict[int, tuple[Any, Any] | None] = {}
    for i, slot in enumerate(sg.get("inputs") or []):
        src = None
        inst_slot = inst_input_by_name.get(slot.get("name")) if isinstance(slot, dict) else None
        lid = inst_slot.get("link") if isinstance(inst_slot, dict) else None
        if lid is not None and lid in top_link_map:
            ln = top_link_map[lid]
            src = (ln[1], ln[2])
        external_source[i] = src

    if sg.get("widgets") and any(inst.get("widgets_values") or []):
        warnings.append({
            "node_id": instance_id, "class_type": sg.get("name"),
            "reason": "subgraph instance overrides exposed widgets via widgets_values — those "
                      "overrides are NOT applied; inner nodes keep their own widget values. "
                      "Verify the flattened inner widgets by hand.",
        })

    inner_links = [ln for ln in (sg.get("links") or []) if isinstance(ln, dict)]

    # What each subgraph output slot is fed by, resolved to a real (namespaced) inner source
    # — or straight back to an external source when the subgraph just passes an input through.
    output_source: dict[Any, tuple[Any, Any] | None] = {}
    for ln in inner_links:
        if ln.get("target_id") == _SUBGRAPH_OUTPUT_NODE:
            origin_id, origin_slot = ln.get("origin_id"), ln.get("origin_slot")
            if origin_id == _SUBGRAPH_INPUT_NODE:
                output_source[ln.get("target_slot")] = external_source.get(origin_slot)
            else:
                output_source[ln.get("target_slot")] = (nid(origin_id), origin_slot)

    # Promote inner nodes; reset their input links (we rebuild every connection below).
    promoted: dict[Any, dict[str, Any]] = {}
    for n in sg.get("nodes") or []:
        if not isinstance(n, dict):
            continue
        c = copy.deepcopy(n)
        c["id"] = nid(n.get("id"))
        for inp in c.get("inputs") or []:
            if isinstance(inp, dict):
                inp["link"] = None
        promoted[n.get("id")] = c

    # Rewire inner links (skip the output-port sinks; those are handled via output_source).
    for ln in inner_links:
        target_id, target_slot = ln.get("target_id"), ln.get("target_slot")
        if target_id == _SUBGRAPH_OUTPUT_NODE:
            continue
        origin_id, origin_slot = ln.get("origin_id"), ln.get("origin_slot")
        if origin_id == _SUBGRAPH_INPUT_NODE:
            src = external_source.get(origin_slot)
        else:
            src = (nid(origin_id), origin_slot)
        if src is None:  # unconnected external input — inner node falls back to its widget default
            continue
        tgt = promoted.get(target_id)
        if tgt is None:
            continue
        lid = new_link_id()
        links.append([lid, src[0], src[1], nid(target_id), target_slot, ln.get("type")])
        tgt_inputs = tgt.get("inputs") or []
        if isinstance(target_slot, int) and 0 <= target_slot < len(tgt_inputs):
            tgt_inputs[target_slot]["link"] = lid

    # Rewire top-level consumers of the instance's outputs to the real inner source.
    for ln in links:
        if isinstance(ln, list) and len(ln) >= 6 and ln[1] == instance_id:
            src = output_source.get(ln[2])
            if src is None:
                warnings.append({"node_id": instance_id, "class_type": sg.get("name"),
                                 "reason": f"subgraph output slot {ln[2]} isn't connected to any "
                                           "inner node; downstream link left dangling"})
                continue
            ln[1], ln[2] = src[0], src[1]

    # Drop the instance node and the now-consumed links feeding its inputs.
    wf["nodes"] = [n for n in (wf.get("nodes") or [])
                   if not (isinstance(n, dict) and n.get("id") == instance_id)]
    wf["nodes"].extend(promoted.values())
    wf["links"] = [ln for ln in links
                   if not (isinstance(ln, list) and len(ln) >= 6 and ln[3] == instance_id)]


def _build_link_map(workflow: dict[str, Any]) -> dict[Any, dict[str, Any]]:
    link_map: dict[Any, dict[str, Any]] = {}
    for ln in workflow.get("links") or []:
        if isinstance(ln, list) and len(ln) >= 6:
            link_map[ln[0]] = {
                "from_node": ln[1], "from_slot": ln[2],
                "to_node": ln[3], "to_slot": ln[4], "type": ln[5],
            }
    return link_map


def _resolve_link_source(
    link_map: dict[Any, dict[str, Any]],
    node_by_id: dict[Any, dict[str, Any]],
    node_id: Any,
    slot: Any,
    seen: frozenset | None = None,
) -> dict[str, Any]:
    """Follow a link backward through Reroute/PrimitiveNode/GetNode/SetNode passthroughs
    to the real source. These node types have no meaningful equivalent in API format —
    they're pure UI organization — so their consumers get rewired straight through.

    Returns one of:
      {"kind": "node", "node_id": ..., "slot": ...}   — a real, emittable source node
      {"kind": "literal", "value": ...}               — inlined from a PrimitiveNode
      {"kind": "unresolved", "reason": ...}            — couldn't confidently resolve
    """
    seen = seen or frozenset()
    key = (node_id, slot)
    if key in seen:
        return {"kind": "unresolved", "reason": f"cycle detected resolving node {node_id}"}
    seen = seen | {key}

    node = node_by_id.get(node_id)
    if node is None:
        return {"kind": "unresolved", "reason": f"node {node_id} not found in workflow"}
    ntype = node.get("type")

    if ntype == "PrimitiveNode":
        wv = node.get("widgets_values") or []
        if wv:
            return {"kind": "literal", "value": wv[0]}
        return {"kind": "unresolved", "reason": f"PrimitiveNode {node_id} has no value set"}

    if ntype in ("Reroute", "SetNode"):
        inputs = node.get("inputs") or []
        if not inputs:
            return {"kind": "unresolved", "reason": f"{ntype} {node_id} has no input socket"}
        lid = inputs[0].get("link")
        if lid is None or lid not in link_map:
            return {"kind": "unresolved", "reason": f"{ntype} {node_id}'s input isn't connected"}
        ln = link_map[lid]
        return _resolve_link_source(link_map, node_by_id, ln["from_node"], ln["from_slot"], seen)

    if ntype == "GetNode":
        wv = node.get("widgets_values") or []
        if not wv:
            return {"kind": "unresolved", "reason": f"GetNode {node_id} has no variable name set"}
        var_name = wv[0]
        set_node_id = None
        for nid2, n2 in node_by_id.items():
            if n2.get("type") == "SetNode" and (n2.get("widgets_values") or [None])[0] == var_name:
                set_node_id = nid2
                break
        if set_node_id is None:
            return {"kind": "unresolved", "reason": f"no SetNode found for variable {var_name!r} (GetNode {node_id})"}
        return _resolve_link_source(link_map, node_by_id, set_node_id, 0, seen)

    # A real node with a registered class_type — terminal.
    return {"kind": "node", "node_id": node_id, "slot": slot}


async def _draft_api_workflow(workflow: dict[str, Any]) -> dict[str, Any]:
    fmt, _ = _detect_format(workflow)
    if fmt != "ui":
        return {"ok": False, "error": f"draft_api_workflow needs UI format; got {fmt}"}

    warnings: list[dict[str, Any]] = []
    has_subgraphs = any(
        isinstance(n, dict) and _subgraph_def(workflow, n.get("type")) is not None
        for n in (workflow.get("nodes") or [])
    )
    if has_subgraphs:
        workflow, warnings = _expand_subgraphs(workflow)

    nodes = [n for n in (workflow.get("nodes") or []) if isinstance(n, dict)]
    node_by_id = {n.get("id"): n for n in nodes}
    link_map = _build_link_map(workflow)

    api: dict[str, Any] = {}
    excluded: list[dict[str, Any]] = []

    for n in nodes:
        ntype = n.get("type")
        nid = n.get("id")

        if ntype in _ANNOTATION_ONLY_TYPES:
            excluded.append({"node_id": nid, "type": ntype, "reason": "annotation-only, no server-side class"})
            continue
        if ntype in _PASSTHROUGH_TYPES:
            excluded.append({"node_id": nid, "type": ntype, "reason": "resolved inline at each consumer"})
            continue

        widgets_values = n.get("widgets_values") or []
        names, confidence = await _ui_widget_order_aligned(ntype, len(widgets_values))

        inputs: dict[str, Any] = {}
        for i, name in enumerate(names):
            if i >= len(widgets_values):
                break
            if not name.endswith("_control_after_generate"):
                inputs[name] = widgets_values[i]
        if confidence != "with_control" and len(names) != len(widgets_values):
            warnings.append({
                "node_id": nid, "class_type": ntype,
                "reason": (
                    f"widget/value count mismatch (confidence={confidence}) — "
                    f"double-check this node's inputs by hand"
                ),
            })

        for inp in (n.get("inputs") or []):
            lid = inp.get("link")
            if lid is None:
                continue
            name = inp.get("name")
            if lid not in link_map:
                warnings.append({
                    "node_id": nid, "class_type": ntype, "input_name": name,
                    "reason": f"link {lid} not found in workflow.links",
                })
                continue
            ln = link_map[lid]
            resolved = _resolve_link_source(link_map, node_by_id, ln["from_node"], ln["from_slot"])
            if resolved["kind"] == "literal":
                inputs[name] = resolved["value"]
            elif resolved["kind"] == "node":
                inputs[name] = [str(resolved["node_id"]), resolved["slot"]]
            else:
                warnings.append({
                    "node_id": nid, "class_type": ntype, "input_name": name,
                    "reason": resolved["reason"],
                })

        api[str(nid)] = {"class_type": ntype, "inputs": inputs}

    return {
        "ok": len(warnings) == 0,
        "workflow": api,
        "node_count": len(api),
        "warnings": warnings,
        "excluded_nodes": excluded,
    }
