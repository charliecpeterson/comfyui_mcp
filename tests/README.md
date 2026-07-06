# tests

Offline unit tests for the pure helpers — no running ComfyUI, no network. They pin the
mechanical logic that's easy to break silently: format detection, the COMBO dual-shape
sniff, subgraph path addressing, UI→API subgraph flattening, and PNG metadata extraction.

Tools that need a live server (queueing, the bridge, `/object_info` widget alignment) are
exercised by hand against a real ComfyUI, not here.

```bash
pip install -e ".[dev]"    # pulls in pytest
pytest tests/ -q
```

`fixtures/subgraph_zimage_t2i.json` is a real saved workflow with one subgraph instance —
the flattener tests run against it so they track ComfyUI's actual data model, not a mock.
