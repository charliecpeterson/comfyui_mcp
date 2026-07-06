"""Offline tests for the core vocabulary helpers — no running ComfyUI required."""
import json
from pathlib import Path

from comfyui_mcp.core import (
    _combo_options,
    _detect_format,
    _subgraph_def,
    _resolve_node_path,
    _all_nodes,
    _outputs_to_files,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _subgraph_workflow():
    return json.loads((FIXTURES / "subgraph_zimage_t2i.json").read_text())


def test_detect_format_ui():
    assert _detect_format({"nodes": [], "links": []}) == ("ui", 0)
    assert _detect_format({"nodes": [{"id": 1}], "links": []})[0] == "ui"


def test_detect_format_api():
    wf = {"1": {"class_type": "KSampler", "inputs": {}}, "2": {"class_type": "VAEDecode", "inputs": {}}}
    assert _detect_format(wf) == ("api", 2)


def test_detect_format_unknown():
    assert _detect_format({})[0] == "unknown"
    assert _detect_format({"foo": "bar"})[0] == "unknown"
    assert _detect_format([1, 2, 3])[0] == "unknown"


def test_combo_options_classic_shape():
    # Classic: the type IS the options list.
    assert _combo_options([["euler", "dpmpp_2m"], {}]) == ["euler", "dpmpp_2m"]


def test_combo_options_v3_shape():
    # Newer COMBO shape: options nested in the second element.
    decl = ["COMBO", {"options": ["nearest", "bilinear"], "default": "nearest"}]
    assert _combo_options(decl) == ["nearest", "bilinear"]


def test_combo_options_not_a_combo():
    assert _combo_options(["INT", {"default": 0}]) is None
    assert _combo_options(["STRING", {}]) is None


def test_combo_options_degenerate():
    assert _combo_options([]) is None
    assert _combo_options("INT") is None
    assert _combo_options(["COMBO", {}]) is None  # COMBO but no options list


def test_subgraph_def_lookup():
    wf = _subgraph_workflow()
    def_id = wf["definitions"]["subgraphs"][0]["id"]
    assert _subgraph_def(wf, def_id)["name"] == "Text to Image"
    assert _subgraph_def(wf, "no-such-id") is None
    assert _subgraph_def(wf, None) is None
    assert _subgraph_def(wf, 123) is None


def test_resolve_node_path_top_level():
    wf = _subgraph_workflow()
    node, scope = _resolve_node_path(wf, 59)
    assert node is not None and node["id"] == 59


def test_resolve_node_path_nested():
    wf = _subgraph_workflow()
    # 63 is an inner node of the subgraph instance 59
    node, scope = _resolve_node_path(wf, "59/63")
    assert node is not None and node["id"] == 63


def test_resolve_node_path_missing():
    wf = _subgraph_workflow()
    assert _resolve_node_path(wf, 99999) == (None, None)
    assert _resolve_node_path(wf, "59/99999") == (None, None)


def test_all_nodes_recurses_into_subgraph():
    wf = _subgraph_workflow()
    top_count = len(wf["nodes"])
    inner_count = len(wf["definitions"]["subgraphs"][0]["nodes"])
    assert len(list(_all_nodes(wf))) == top_count + inner_count


def test_outputs_to_files_flattens_kinds():
    history = {
        "outputs": {
            "9": {"images": [{"filename": "a.png", "subfolder": "", "type": "output"}]},
            "12": {"gifs": [{"filename": "b.gif", "subfolder": "clips", "type": "output"}]},
        }
    }
    files = _outputs_to_files(history)
    kinds = {(f["node_id"], f["kind"], f["filename"]) for f in files}
    assert ("9", "images", "a.png") in kinds
    assert ("12", "gifs", "b.gif") in kinds


def test_outputs_to_files_empty():
    assert _outputs_to_files({}) == []
    assert _outputs_to_files({"outputs": {}}) == []
