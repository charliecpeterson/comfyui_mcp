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

# Live-edit ops (set_widget, add_node, ...) and tab reads need an open browser tab whose
# bridge websocket is alive. Browsers suspend that socket in backgrounded tabs, so an op
# can succeed and the very next call report zero tabs. Attached to every such failure.
TAB_DISCONNECT_HINT = (
    "A ComfyUI browser tab must be open AND focused — browsers suspend the bridge "
    "websocket in backgrounded tabs, so calls can flap to zero tabs between requests. "
    "Open the ComfyUI tab, hard-refresh it, and keep it the active foreground tab."
)


def _url_looks_remote(url: str) -> bool:
    """True if COMFYUI_URL points at a host other than this machine. The filesystem tools
    read ComfyUI's disk directly, so they only work when the MCP is co-located with it."""
    from urllib.parse import urlparse
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False
    return host not in ("", "127.0.0.1", "localhost", "::1", "0.0.0.0")


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

    url = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
    if _url_looks_remote(url):
        raise RuntimeError(
            f"ComfyUI root not found, and COMFYUI_URL ({url}) points at a remote host. The "
            f"filesystem tools (list_custom_nodes, catalog/list_workflows, log tailing, "
            f"snapshots) read ComfyUI's disk directly, so they only work when this MCP runs "
            f"on the same machine as ComfyUI. Run the MCP on that host, or set COMFYUI_ROOT "
            f"if the install is mounted locally. HTTP tools (generation, model listing, "
            f"set_widget, queueing) work fine over the network."
        )
    raise RuntimeError(
        f"ComfyUI root not found. Set COMFYUI_ROOT env var, or launch the MCP from the "
        f"ComfyUI dir. Note: if you reach ComfyUI through an SSH tunnel or it runs on "
        f"another host, the filesystem tools can't work from here even though the HTTP "
        f"tools (generation, model listing, set_widget, queueing) will — run the MCP on "
        f"the ComfyUI host. (COMFYUI_URL={url}, cwd={cwd})"
    )


def _model_search_paths(category: str) -> list[Path]:
    """Every directory ComfyUI searches for `category`: the built-in models/<category>
    plus each block in extra_model_paths.yaml. Tools that hit ComfyUI's HTTP API
    (list_models) already see these; this is for the tools that read model files off
    disk directly (LoRA scan, metadata reads), which would otherwise miss a NAS library
    registered only via extra_model_paths. Returns existing dirs, deduped, local-first.
    """
    root = _comfy_root()
    paths: list[Path] = []
    seen: set[str] = set()

    def add(p: Path) -> None:
        key = str(p)
        if key not in seen and p.is_dir():
            seen.add(key)
            paths.append(p)

    add(root / "models" / category)

    cfg = root / "extra_model_paths.yaml"
    if cfg.is_file():
        try:
            import yaml
            data = yaml.safe_load(cfg.read_text()) or {}
        except Exception:
            data = {}
        if isinstance(data, dict):
            for block in data.values():
                if not isinstance(block, dict) or not block.get(category):
                    continue
                base = Path(str(block.get("base_path") or root)).expanduser()
                for line in str(block[category]).splitlines():
                    line = line.strip()
                    if line:
                        add((base / line).expanduser())
    return paths


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
