"""Offline tests for UI->API conversion helpers, focused on subgraph flattening.

_expand_subgraphs is pure (no network), so it's fully testable against a real saved
workflow. The async _draft_api_workflow (which needs /object_info for widget alignment)
is exercised live elsewhere; here we pin the structural flattening it depends on.
"""
import json
from pathlib import Path

from comfyui_mcp.convert import (
    _build_link_map,
    _resolve_link_source,
    _expand_subgraphs,
    _max_link_id,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _subgraph_workflow():
    return json.loads((FIXTURES / "subgraph_zimage_t2i.json").read_text())


def test_build_link_map():
    wf = {"links": [[5, 1, 0, 2, 0, "MODEL"], [6, 2, 1, 3, 0, "LATENT"]]}
    lm = _build_link_map(wf)
    assert lm[5] == {"from_node": 1, "from_slot": 0, "to_node": 2, "to_slot": 0, "type": "MODEL"}
    assert lm[6]["to_node"] == 3


def test_resolve_link_source_terminal_node():
    node_by_id = {1: {"id": 1, "type": "CheckpointLoaderSimple"}}
    res = _resolve_link_source({}, node_by_id, 1, 0)
    assert res == {"kind": "node", "node_id": 1, "slot": 0}


def test_resolve_link_source_reroute_passthrough():
    # consumer <- Reroute(2) <- real node(1)
    link_map = {10: {"from_node": 1, "from_slot": 0, "to_node": 2, "to_slot": 0, "type": "MODEL"}}
    node_by_id = {
        1: {"id": 1, "type": "UNETLoader"},
        2: {"id": 2, "type": "Reroute", "inputs": [{"link": 10}]},
    }
    res = _resolve_link_source(link_map, node_by_id, 2, 0)
    assert res == {"kind": "node", "node_id": 1, "slot": 0}


def test_resolve_link_source_primitive_literal():
    node_by_id = {3: {"id": 3, "type": "PrimitiveNode", "widgets_values": ["a red car"]}}
    res = _resolve_link_source({}, node_by_id, 3, 0)
    assert res == {"kind": "literal", "value": "a red car"}


def test_resolve_link_source_cycle_is_caught():
    link_map = {1: {"from_node": 2, "from_slot": 0, "to_node": 2, "to_slot": 0, "type": "X"}}
    node_by_id = {2: {"id": 2, "type": "Reroute", "inputs": [{"link": 1}]}}
    res = _resolve_link_source(link_map, node_by_id, 2, 0)
    assert res["kind"] == "unresolved"


def test_max_link_id_spans_top_and_inner():
    wf = _subgraph_workflow()
    top_max = max(ln[0] for ln in wf["links"])
    inner_max = max(l["id"] for l in wf["definitions"]["subgraphs"][0]["links"])
    assert _max_link_id(wf) == max(top_max, inner_max)


def test_expand_subgraphs_strips_definitions():
    wf = _subgraph_workflow()
    expanded, warnings = _expand_subgraphs(wf)
    assert "definitions" not in expanded
    assert warnings == []


def test_expand_subgraphs_namespaces_inner_nodes():
    wf = _subgraph_workflow()
    expanded, _ = _expand_subgraphs(wf)
    ids = [n["id"] for n in expanded["nodes"]]
    # top-level count minus the one instance, plus the 11 inner nodes
    assert len(ids) == len(wf["nodes"]) - 1 + len(wf["definitions"]["subgraphs"][0]["nodes"])
    # every promoted inner node is namespaced under the instance id 59
    assert any(str(i).startswith("59:") for i in ids)
    # the instance node itself is gone
    assert 59 not in ids


def test_expand_subgraphs_no_dangling_links():
    wf = _subgraph_workflow()
    expanded, _ = _expand_subgraphs(wf)
    node_ids = {n["id"] for n in expanded["nodes"]}
    for ln in expanded["links"]:
        assert ln[1] in node_ids, f"link source {ln[1]} missing"
        assert ln[3] in node_ids, f"link target {ln[3]} missing"


def test_expand_subgraphs_rewires_boundary_inputs():
    # The inner KSampler's model/positive/negative/latent all cross internal links; after
    # flattening they must resolve to namespaced inner sources, not the vanished instance.
    wf = _subgraph_workflow()
    expanded, _ = _expand_subgraphs(wf)
    lm = _build_link_map(expanded)
    ksampler = next(n for n in expanded["nodes"] if n["id"] == "59:67")
    linked_inputs = {inp["name"]: inp["link"] for inp in ksampler["inputs"] if inp.get("link") is not None}
    for name in ("model", "positive", "negative", "latent_image"):
        assert name in linked_inputs, f"{name} not wired after flatten"
        src = lm[linked_inputs[name]]["from_node"]
        assert str(src).startswith("59:"), f"{name} sourced from {src}, expected a namespaced inner node"
