"""Offline tests for PNG-embedded workflow extraction."""
import io
import json

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from comfyui_mcp.images import _extract_embedded_workflow

_API_GRAPH = {"3": {"class_type": "KSampler", "inputs": {"seed": 42}}}
_UI_GRAPH = {"nodes": [{"id": 3, "type": "KSampler"}], "links": []}


def _png_with(chunks: dict[str, str]) -> bytes:
    info = PngInfo()
    for k, v in chunks.items():
        info.add_text(k, v)
    buf = io.BytesIO()
    Image.new("RGB", (8, 8)).save(buf, format="PNG", pnginfo=info)
    return buf.getvalue()


def test_extract_prompt_only():
    data = _png_with({"prompt": json.dumps(_API_GRAPH)})
    out = _extract_embedded_workflow(data)
    assert out["found"] == ["prompt"]
    assert out["prompt"] == _API_GRAPH
    assert "workflow" not in out


def test_extract_prompt_and_workflow():
    data = _png_with({"prompt": json.dumps(_API_GRAPH), "workflow": json.dumps(_UI_GRAPH)})
    out = _extract_embedded_workflow(data)
    assert set(out["found"]) == {"prompt", "workflow"}
    assert out["workflow"] == _UI_GRAPH


def test_extract_no_metadata():
    data = _png_with({})
    out = _extract_embedded_workflow(data)
    assert out["found"] == []


def test_extract_ignores_malformed_json():
    data = _png_with({"prompt": "{not valid json"})
    out = _extract_embedded_workflow(data)
    assert out["found"] == []
