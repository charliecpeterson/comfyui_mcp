"""Pre-apply workflow snapshots — save the current tab's graph before swapping it in,
so a bad apply_workflow can be undone via restore_snapshot.

Snapshots live in <COMFYUI_ROOT>/output/_snapshots/<tab_id>_<ts>.json; the last
_SNAPSHOT_RETENTION are kept per tab.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from .client import comfy
from .core import _comfy_root


_SNAPSHOT_RETENTION = 5


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
