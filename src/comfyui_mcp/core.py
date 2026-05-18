"""Foundation helpers shared across tool modules:
- ComfyUI root resolution
- Workflow format detection
- Subgraph-aware node walking and resolution
- Output flattening
- Shared constants
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


_NOTE_NODE_TYPES = {"Note", "MarkdownNote", "Note Plus (mtb)", "PrimitiveNode", "easy showAnything"}
_MODEL_FILE_EXTS = (".safetensors", ".ckpt", ".pth", ".gguf", ".bin", ".pt", ".onnx")


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


def _detect_format(wf: Any) -> tuple[str, int]:
    if isinstance(wf, dict) and isinstance(wf.get("nodes"), list) and "links" in wf:
        return "ui", len(wf["nodes"])
    if isinstance(wf, dict) and wf and all(
        isinstance(v, dict) and "class_type" in v for v in wf.values()
    ):
        return "api", len(wf)
    return "unknown", 0


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
