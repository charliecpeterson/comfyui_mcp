"""comfyui-mcp-bridge: lets the comfyui-mcp server see and modify the workflows
open in the editor.

Per-tab state keyed by a sessionStorage-scoped tab_id (NOT ComfyUI's clientId,
which is shared across tabs in the same browser). Event delivery to tabs uses
HTTP long-polling rather than ComfyUI's WS, because the WS slot is overwritten
when a second tab connects with the same clientId — making WS-based routing to
older tabs impossible.
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any

from aiohttp import web
from server import PromptServer

HEARTBEAT_TIMEOUT_MS = 30_000
LONGPOLL_TIMEOUT_S = 25.0

_tabs: dict[str, dict[str, Any]] = {}
_pending_events: dict[str, list[dict]] = {}
_waiters: dict[str, list[asyncio.Future]] = {}
_pending_screenshots: dict[str, asyncio.Future] = {}
_pending_ops: dict[str, asyncio.Future] = {}

routes = PromptServer.instance.routes


@web.middleware
async def _bridge_no_cache(request: web.Request, handler) -> web.StreamResponse:
    response = await handler(request)
    if request.path.startswith("/extensions/comfyui-mcp-bridge/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


try:
    PromptServer.instance.app.middlewares.append(_bridge_no_cache)
    print("[mcp_bridge] no-cache middleware installed for /extensions/comfyui-mcp-bridge/")
except Exception as e:
    print(f"[mcp_bridge] WARNING: could not install no-cache middleware: {e}")


def _now_ms() -> int:
    return int(time.time() * 1000)


def _gc_dead_tabs() -> None:
    cutoff = _now_ms() - HEARTBEAT_TIMEOUT_MS
    dead = [tid for tid, t in _tabs.items() if t.get("updated_at", 0) < cutoff]
    for tid in dead:
        _tabs.pop(tid, None)
        _pending_events.pop(tid, None)
        for fut in _waiters.pop(tid, []):
            if not fut.done():
                fut.set_result(None)


def _push_event(tab_id: str, event: dict) -> None:
    _pending_events.setdefault(tab_id, []).append(event)
    waiters = _waiters.pop(tab_id, [])
    for fut in waiters:
        if not fut.done():
            fut.set_result(None)


async def _read_json_or_beacon(request: web.Request) -> dict:
    try:
        return await request.json()
    except Exception:
        raw = await request.read()
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}


@routes.post("/mcp_bridge/state")
async def push_state(request: web.Request) -> web.Response:
    data = await _read_json_or_beacon(request)
    tab_id = data.get("tab_id")
    boot_id = data.get("boot_id")
    if not tab_id:
        return web.json_response({"ok": False, "error": "missing tab_id"}, status=400)

    existing = _tabs.get(tab_id)
    if existing and existing.get("boot_id") and boot_id and existing["boot_id"] != boot_id:
        return web.json_response(
            {"ok": False, "regenerate": True, "reason": "tab_id collision (duplicated sessionStorage)"},
            status=409,
        )

    _tabs[tab_id] = {
        "tab_id": tab_id,
        "boot_id": boot_id,
        "comfy_client_id": data.get("comfy_client_id"),
        "workflow": data.get("workflow"),
        "api_workflow": data.get("api_workflow"),
        "label": data.get("label"),
        "updated_at": _now_ms(),
    }
    return web.json_response({"ok": True})


@routes.post("/mcp_bridge/heartbeat")
async def heartbeat(request: web.Request) -> web.Response:
    data = await _read_json_or_beacon(request)
    tab_id = data.get("tab_id")
    boot_id = data.get("boot_id")
    if not tab_id or tab_id not in _tabs:
        return web.json_response({"ok": True, "known": False})

    existing = _tabs[tab_id]
    if existing.get("boot_id") and boot_id and existing["boot_id"] != boot_id:
        return web.json_response({"ok": False, "regenerate": True})

    existing["updated_at"] = _now_ms()
    return web.json_response({"ok": True, "known": True})


@routes.post("/mcp_bridge/disconnect")
async def disconnect(request: web.Request) -> web.Response:
    data = await _read_json_or_beacon(request)
    tab_id = data.get("tab_id")
    if tab_id:
        _tabs.pop(tab_id, None)
        _pending_events.pop(tab_id, None)
        for fut in _waiters.pop(tab_id, []):
            if not fut.done():
                fut.set_result(None)
    return web.json_response({"ok": True})


@routes.get("/mcp_bridge/current")
async def current(request: web.Request) -> web.Response:
    _gc_dead_tabs()
    tab_id = request.query.get("tab_id")
    if tab_id:
        if tab_id not in _tabs:
            return web.json_response({"error": "tab not connected", "tab_id": tab_id}, status=404)
        t = _tabs[tab_id]
        return web.json_response({
            "tab_id": tab_id,
            "workflow": t["workflow"],
            "api_workflow": t["api_workflow"],
            "comfy_client_id": t.get("comfy_client_id"),
            "label": t.get("label"),
            "updated_at": t["updated_at"],
            "tab_count": len(_tabs),
        })
    if not _tabs:
        return web.json_response({"workflow": None, "tab_count": 0, "tabs": []})
    latest_id = max(_tabs, key=lambda k: _tabs[k]["updated_at"])
    t = _tabs[latest_id]
    warning = f"{len(_tabs)} live tabs; returning the most-recently-edited. Pass tab_id= to target a specific one." if len(_tabs) > 1 else None
    return web.json_response({
        "tab_id": latest_id,
        "workflow": t["workflow"],
        "api_workflow": t["api_workflow"],
        "comfy_client_id": t.get("comfy_client_id"),
        "label": t.get("label"),
        "updated_at": t["updated_at"],
        "tab_count": len(_tabs),
        "tabs": [
            {
                "tab_id": tid,
                "comfy_client_id": _tabs[tid].get("comfy_client_id"),
                "label": _tabs[tid].get("label"),
                "updated_at": _tabs[tid]["updated_at"],
            }
            for tid in sorted(_tabs, key=lambda k: -_tabs[k]["updated_at"])
        ],
        "warning": warning,
    })


@routes.get("/mcp_bridge/debug")
async def debug(request: web.Request) -> web.Response:
    _gc_dead_tabs()
    server = PromptServer.instance
    sockets = getattr(server, "sockets", None)
    return web.json_response({
        "now_ms": _now_ms(),
        "heartbeat_timeout_ms": HEARTBEAT_TIMEOUT_MS,
        "tabs": {
            tid: {k: v for k, v in t.items() if k not in ("workflow", "api_workflow")}
            for tid, t in _tabs.items()
        },
        "pending_events_per_tab": {tid: len(evs) for tid, evs in _pending_events.items()},
        "waiters_per_tab": {tid: len(ws) for tid, ws in _waiters.items()},
        "pending_screenshots": list(_pending_screenshots.keys()),
        "comfy_sockets_keys": list(sockets.keys()) if isinstance(sockets, dict) else None,
    })


@routes.get("/mcp_bridge/poll")
async def poll(request: web.Request) -> web.Response:
    """Long-poll for events targeted at a specific tab."""
    tab_id = request.query.get("tab_id")
    if not tab_id:
        return web.json_response({"events": []})

    events = _pending_events.pop(tab_id, [])
    if events:
        return web.json_response({"events": events})

    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    _waiters.setdefault(tab_id, []).append(fut)
    try:
        await asyncio.wait_for(fut, timeout=LONGPOLL_TIMEOUT_S)
    except asyncio.TimeoutError:
        pass
    finally:
        waiters = _waiters.get(tab_id)
        if waiters and fut in waiters:
            waiters.remove(fut)

    events = _pending_events.pop(tab_id, [])
    return web.json_response({"events": events})


@routes.post("/mcp_bridge/load")
async def load_workflow(request: web.Request) -> web.Response:
    data = await request.json()
    target = data.get("tab_id")
    workflow = data.get("workflow")
    confirm = bool(data.get("confirm", True))
    if workflow is None:
        return web.json_response({"ok": False, "error": "missing workflow"}, status=400)

    _gc_dead_tabs()
    if target:
        if target not in _tabs:
            return web.json_response({"ok": False, "error": f"tab {target!r} not connected"}, status=404)
        targets = [target]
    else:
        targets = list(_tabs.keys())
    if not targets:
        return web.json_response({"ok": False, "error": "no tabs connected"}, status=503)

    event = {"type": "load", "id": uuid.uuid4().hex, "workflow": workflow, "confirm": confirm}
    for tid in targets:
        _push_event(tid, event)
    return web.json_response({"ok": True, "queued_to": targets})


@routes.post("/mcp_bridge/screenshot/request")
async def request_screenshot(request: web.Request) -> web.Response:
    data = await request.json()
    target = data.get("tab_id")
    timeout = float(data.get("timeout", 10))

    _gc_dead_tabs()
    if target:
        if target not in _tabs:
            return web.json_response({"ok": False, "error": f"tab {target!r} not connected"}, status=404)
        targets = [target]
    else:
        targets = list(_tabs.keys())
    if not targets:
        return web.json_response({"ok": False, "error": "no tabs connected"}, status=503)

    rid = uuid.uuid4().hex
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    _pending_screenshots[rid] = fut

    event = {"type": "screenshot", "id": uuid.uuid4().hex, "request_id": rid}
    for tid in targets:
        _push_event(tid, event)

    try:
        result = await asyncio.wait_for(fut, timeout=timeout)
        return web.json_response({"ok": True, **result})
    except asyncio.TimeoutError:
        return web.json_response(
            {"ok": False, "error": "no tab responded in time"},
            status=504,
        )
    finally:
        _pending_screenshots.pop(rid, None)


@routes.post("/mcp_bridge/op")
async def submit_op(request: web.Request) -> web.Response:
    data = await request.json()
    op = data.get("op")
    target = data.get("tab_id")
    timeout = float(data.get("timeout", 10))
    if not op:
        return web.json_response({"ok": False, "error": "missing op"}, status=400)

    _gc_dead_tabs()
    if target:
        if target not in _tabs:
            return web.json_response({"ok": False, "error": f"tab {target!r} not connected"}, status=404)
        targets = [target]
    else:
        targets = list(_tabs.keys())
    if not targets:
        return web.json_response({"ok": False, "error": "no tabs connected"}, status=503)
    if len(targets) > 1:
        latest = max(_tabs, key=lambda k: _tabs[k]["updated_at"])
        targets = [latest]

    rid = uuid.uuid4().hex
    loop = asyncio.get_running_loop()
    fut: asyncio.Future = loop.create_future()
    _pending_ops[rid] = fut

    event = {"type": "op", "id": uuid.uuid4().hex, "request_id": rid, "op": op}
    for tid in targets:
        _push_event(tid, event)

    try:
        result = await asyncio.wait_for(fut, timeout=timeout)
        return web.json_response(result)
    except asyncio.TimeoutError:
        return web.json_response({"ok": False, "error": "tab did not respond in time"}, status=504)
    finally:
        _pending_ops.pop(rid, None)


@routes.post("/mcp_bridge/op/response")
async def op_response(request: web.Request) -> web.Response:
    data = await request.json()
    rid = data.get("request_id")
    fut = _pending_ops.get(rid)
    if fut and not fut.done():
        fut.set_result({k: v for k, v in data.items() if k != "request_id"})
    return web.json_response({"ok": True})


@routes.post("/mcp_bridge/screenshot/response")
async def screenshot_response(request: web.Request) -> web.Response:
    data = await request.json()
    rid = data.get("request_id")
    fut = _pending_screenshots.get(rid)
    if fut and not fut.done():
        fut.set_result({
            "data_url": data.get("data_url"),
            "width": data.get("width"),
            "height": data.get("height"),
            "tab_id": data.get("tab_id"),
        })
    return web.json_response({"ok": True})


print("[mcp_bridge] routes registered: /mcp_bridge/{state,heartbeat,disconnect,current,debug,poll,load,op,op/response,screenshot/{request,response}}")

NODE_CLASS_MAPPINGS: dict[str, Any] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}
WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
