from __future__ import annotations

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

import httpx
import websockets

from .core import TAB_DISCONNECT_HINT

DEFAULT_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
DEFAULT_TIMEOUT = float(os.environ.get("COMFYUI_TIMEOUT", "30"))


def _extract_execution_error(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Pull the execution_error payload out of a /history entry's status.messages.

    History entries store terminal events as [event_type, payload] pairs under
    status.messages. When status_str is "error" the payload we want is the
    "execution_error" one — same shape (node_id/exception_type/exception_message/
    traceback/current_inputs/current_outputs) as the live WS execution_error event,
    so callers get a consistent `error` field regardless of which path caught it.
    """
    messages = (entry.get("status") or {}).get("messages") or []
    for msg in messages:
        if isinstance(msg, (list, tuple)) and len(msg) == 2 and msg[0] == "execution_error":
            return msg[1] if isinstance(msg[1], dict) else None
    return None


class ComfyClient:
    def __init__(self, base_url: str = DEFAULT_URL, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)

    async def system_stats(self) -> dict[str, Any]:
        async with self._client() as c:
            r = await c.get("/system_stats")
            r.raise_for_status()
            return r.json()

    async def object_info(self, node_class: str | None = None) -> dict[str, Any]:
        path = f"/object_info/{node_class}" if node_class else "/object_info"
        async with self._client() as c:
            r = await c.get(path)
            r.raise_for_status()
            return r.json()

    async def queue(
        self,
        workflow: dict[str, Any],
        client_id: str | None = None,
        prompt_id: str | None = None,
        extra_data: dict[str, Any] | None = None,
        partial_execution_targets: list[str] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        payload: dict[str, Any] = {"prompt": workflow}
        if client_id:
            payload["client_id"] = client_id
        if prompt_id:
            payload["prompt_id"] = prompt_id
        if extra_data:
            payload["extra_data"] = extra_data
        # Top-level key on /prompt (sibling of prompt/client_id), consumed by
        # execution.validate_prompt to restrict the run to these output nodes.
        if partial_execution_targets:
            payload["partial_execution_targets"] = partial_execution_targets
        async with self._client() as c:
            r = await c.post("/prompt", json=payload)
            return r.status_code, r.json()

    async def free(self, unload_models: bool = False, free_memory: bool = False) -> dict[str, Any]:
        """POST /free — request ComfyUI drop cached models / free VRAM. The server sets a
        queue flag consumed on the next worker cycle; it returns 200 with an empty body
        immediately, so this doesn't block on the actual unload."""
        async with self._client() as c:
            r = await c.post("/free", json={"unload_models": unload_models, "free_memory": free_memory})
            return {"ok": r.status_code == 200, "status": r.status_code}

    async def workflow_templates(self) -> dict[str, Any]:
        """GET /api/workflow_templates — {package_name: [template_name, ...]} for
        templates shipped by installed custom_node packages."""
        async with self._client() as c:
            r = await c.get("/api/workflow_templates")
            r.raise_for_status()
            return r.json()

    async def workflow_template(self, package: str, name: str) -> dict[str, Any]:
        """GET one custom_node template's UI-format JSON."""
        async with self._client() as c:
            r = await c.get(f"/api/workflow_templates/{package}/{name}.json")
            r.raise_for_status()
            return r.json()

    async def core_templates(self) -> list[dict[str, Any]]:
        """GET /templates/index.json — the core Comfy-Org template catalog, a list of
        categories each with a `templates` array of {name, title, description, models, ...}."""
        async with self._client() as c:
            r = await c.get("/templates/index.json")
            r.raise_for_status()
            return r.json()

    async def core_template(self, name: str) -> dict[str, Any]:
        """GET one core template's UI-format JSON by its `name`."""
        async with self._client() as c:
            r = await c.get(f"/templates/{name}.json")
            r.raise_for_status()
            return r.json()

    async def history(
        self, prompt_id: str | None = None, max_items: int | None = None
    ) -> dict[str, Any]:
        if prompt_id:
            path = f"/history/{prompt_id}"
            params = None
        else:
            path = "/history"
            params = {"max_items": max_items} if max_items else None
        async with self._client() as c:
            r = await c.get(path, params=params)
            r.raise_for_status()
            return r.json()

    async def queue_state(self) -> dict[str, Any]:
        async with self._client() as c:
            r = await c.get("/queue")
            r.raise_for_status()
            return r.json()

    async def interrupt(self, prompt_id: str | None = None) -> dict[str, Any]:
        body = {"prompt_id": prompt_id} if prompt_id else {}
        async with self._client() as c:
            r = await c.post("/interrupt", json=body)
            return {"ok": r.status_code == 200, "status": r.status_code}

    async def delete_from_queue(self, prompt_ids: list[str]) -> dict[str, Any]:
        async with self._client() as c:
            r = await c.post("/queue", json={"delete": prompt_ids})
            return {"ok": r.status_code == 200, "status": r.status_code, "deleted": prompt_ids}

    async def models(self, folder: str | None = None) -> list[str] | dict[str, Any]:
        path = f"/models/{folder}" if folder else "/models"
        async with self._client() as c:
            r = await c.get(path)
            r.raise_for_status()
            return r.json()

    async def view(self, filename: str, subfolder: str = "", folder_type: str = "output") -> tuple[bytes, str]:
        params = {"filename": filename, "type": folder_type}
        if subfolder:
            params["subfolder"] = subfolder
        async with self._client() as c:
            r = await c.get("/view", params=params)
            r.raise_for_status()
            return r.content, r.headers.get("content-type", "application/octet-stream")

    async def upload(
        self,
        file_path: str,
        name: str | None = None,
        subfolder: str = "",
        overwrite: bool = False,
    ) -> dict[str, Any]:
        p = Path(file_path).expanduser()
        if not p.is_file():
            raise FileNotFoundError(f"not a file: {p}")
        files = {"image": (name or p.name, p.read_bytes())}
        data: dict[str, str] = {"overwrite": "true" if overwrite else "false"}
        if subfolder:
            data["subfolder"] = subfolder
        async with self._client() as c:
            r = await c.post("/upload/image", files=files, data=data)
            r.raise_for_status()
            return r.json()

    async def manager_node_mappings(self) -> dict[str, Any] | None:
        """GET ComfyUI-Manager's node→package map: {install_id_or_url: [[class_names...],
        {title_aux, ...}]}. Returns None if Manager isn't installed (404) or errors —
        callers degrade to "can't identify the provider" rather than failing."""
        try:
            async with self._client() as c:
                r = await c.get("/customnode/getmappings", params={"mode": "local"})
                if r.status_code != 200:
                    return None
                return r.json()
        except httpx.HTTPError:
            return None

    async def bridge_debug(self) -> dict[str, Any]:
        async with self._client() as c:
            r = await c.get("/mcp_bridge/debug")
            if r.status_code == 404:
                return {"error": "bridge_not_installed"}
            r.raise_for_status()
            return r.json()

    async def bridge_state(self, tab_id: str | None = None) -> dict[str, Any]:
        params = {"tab_id": tab_id} if tab_id else None
        async with self._client() as c:
            r = await c.get("/mcp_bridge/current", params=params)
            if r.status_code == 404:
                if tab_id:
                    return r.json()
                return {"error": "bridge_not_installed"}
            r.raise_for_status()
            return r.json()

    async def bridge_op(
        self,
        op: dict[str, Any],
        tab_id: str | None = None,
        timeout: float = 10.0,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"op": op, "timeout": timeout}
        if tab_id:
            body["tab_id"] = tab_id
        # A backgrounded tab can momentarily drop its bridge socket, so an op lands
        # as "no tabs connected" a beat before the tab re-registers. One short retry
        # rides out that flap; kept to a single brief wait so a genuinely closed tab
        # still fails fast.
        for attempt in range(2):
            async with httpx.AsyncClient(base_url=self.base_url, timeout=timeout + 5) as c:
                r = await c.post("/mcp_bridge/op", json=body)
            if r.status_code == 404 and not tab_id:
                return {"ok": False, "error": "bridge_not_installed"}
            result = r.json()
            disconnected = (
                isinstance(result, dict)
                and not result.get("ok")
                and "connected" in str(result.get("error", ""))
            )
            if disconnected and attempt == 0:
                await asyncio.sleep(0.4)
                continue
            if disconnected and "hint" not in result:
                result["hint"] = TAB_DISCONNECT_HINT
            return result

    async def bridge_screenshot(self, tab_id: str | None = None, timeout: float = 10.0) -> dict[str, Any]:
        body: dict[str, Any] = {"timeout": timeout}
        if tab_id:
            body["tab_id"] = tab_id
        async with httpx.AsyncClient(base_url=self.base_url, timeout=timeout + 5) as c:
            r = await c.post("/mcp_bridge/screenshot/request", json=body)
            if r.status_code == 404:
                if tab_id:
                    return r.json()
                return {"ok": False, "error": "bridge_not_installed"}
            return r.json()

    async def bridge_load(
        self,
        workflow: dict[str, Any],
        tab_id: str | None = None,
        confirm: bool = True,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"workflow": workflow, "confirm": confirm}
        if tab_id:
            body["tab_id"] = tab_id
        async with self._client() as c:
            r = await c.post("/mcp_bridge/load", json=body)
            if r.status_code == 404:
                if tab_id:
                    return r.json()
                return {"ok": False, "error": "bridge_not_installed"}
            r.raise_for_status()
            return r.json()

    def _ws_url(self) -> str:
        if self.base_url.startswith("https://"):
            return "wss://" + self.base_url[len("https://"):] + "/ws"
        if self.base_url.startswith("http://"):
            return "ws://" + self.base_url[len("http://"):] + "/ws"
        return self.base_url + "/ws"

    async def poll_events(self, timeout: float = 1.0) -> list[dict[str, Any]]:
        """Open the ComfyUI WS for a brief window, collect any messages, return them.
        Used for snapshot-style status checks that don't want to subscribe long-term."""
        events: list[dict[str, Any]] = []
        try:
            async with websockets.connect(self._ws_url(), max_size=10_000_000) as ws:
                deadline = time.monotonic() + timeout
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
                    except asyncio.TimeoutError:
                        break
                    if isinstance(raw, bytes):
                        continue
                    try:
                        events.append(json.loads(raw))
                    except json.JSONDecodeError:
                        continue
        except (websockets.WebSocketException, OSError):
            pass
        return events

    async def wait(
        self,
        prompt_id: str,
        timeout: float = 300.0,
        on_progress=None,
    ) -> dict[str, Any]:
        """Wait for a prompt to finish. Two parallel paths:

        1. WebSocket events — fast wake-up when ComfyUI fires execution_success, IF the
           events reach our connection. They may not: ComfyUI scopes terminal events to
           the submitting client_id, and we forward the BROWSER's client_id at queue time
           so live previews show in the tab. Our WS connection (different client_id)
           may never see the terminal event.

        2. History polling, every HISTORY_POLL_INTERVAL seconds, ALWAYS — regardless of
           WS activity. This is the source of truth: when /history has the prompt_id, the
           run is complete. Without this, jobs that finish via cached/scoped WS events
           hang the wait until timeout.

        A history entry exists whether the run succeeded OR failed — /history doesn't
        distinguish at the polling level, so we have to inspect entry.status.status_str
        ourselves. Without that, a run that fails and is only observed via the history-poll
        path (the common case: the live WS execution_error event is scoped to the browser's
        client_id, same reason as above) gets reported as status="completed" with the actual
        failure buried three levels deep in history.status.messages instead of surfaced.
        """
        HISTORY_POLL_INTERVAL = 2.0

        async def check_history() -> dict[str, Any] | None:
            try:
                h = await self.history(prompt_id)
                if h and prompt_id in h:
                    return h[prompt_id]
            except httpx.HTTPError:
                pass
            return None

        def result_for(entry: dict[str, Any], progress: dict[str, Any] | None) -> dict[str, Any]:
            status_str = (entry.get("status") or {}).get("status_str")
            if status_str == "error":
                out: dict[str, Any] = {"status": "error", "history": entry, "progress": progress}
                err = _extract_execution_error(entry)
                if err is not None:
                    out["error"] = err
                return out
            return {"status": "completed", "history": entry, "progress": progress}

        # Initial check (already done?)
        if (entry := await check_history()) is not None:
            return result_for(entry, None)

        deadline = time.monotonic() + timeout
        last_progress: dict[str, Any] | None = None
        last_history_check = time.monotonic()

        try:
            async with websockets.connect(self._ws_url(), max_size=10_000_000) as ws:
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break

                    # Always-poll safety net: re-check history at the regular interval
                    # regardless of whether WS is delivering events (it may not be —
                    # terminal events can be scoped to a client_id we don't share).
                    now = time.monotonic()
                    if now - last_history_check >= HISTORY_POLL_INTERVAL:
                        last_history_check = now
                        if (entry := await check_history()) is not None:
                            return result_for(entry, last_progress)

                    ws_timeout = min(remaining, HISTORY_POLL_INTERVAL)
                    try:
                        raw = await asyncio.wait_for(ws.recv(), timeout=ws_timeout)
                    except asyncio.TimeoutError:
                        continue

                    if isinstance(raw, bytes):
                        continue  # binary preview frames
                    try:
                        msg = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    t = msg.get("type")
                    payload = msg.get("data", {}) or {}
                    msg_pid = payload.get("prompt_id")

                    if t == "progress":
                        last_progress = {
                            "value": payload.get("value"),
                            "max": payload.get("max"),
                            "node": payload.get("node"),
                        }
                        if on_progress is not None:
                            try:
                                await on_progress(last_progress)
                            except Exception:
                                pass  # a broken progress sink must never abort the wait
                        continue
                    if msg_pid and msg_pid != prompt_id:
                        continue

                    if t == "execution_success":
                        if (entry := await check_history()) is not None:
                            return result_for(entry, last_progress)
                    if t == "execution_error":
                        return {"status": "error", "error": payload, "progress": last_progress}
                    if t == "execution_interrupted":
                        return {"status": "interrupted", "data": payload, "progress": last_progress}
                    if t == "executing" and payload.get("node") is None and msg_pid == prompt_id:
                        # legacy terminal signal on older ComfyUI
                        if (entry := await check_history()) is not None:
                            return result_for(entry, last_progress)
        except (websockets.WebSocketException, OSError):
            # WS connection failed — fall through to history-only polling
            while time.monotonic() < deadline:
                await asyncio.sleep(HISTORY_POLL_INTERVAL)
                if (entry := await check_history()) is not None:
                    return result_for(entry, last_progress)

        return {"status": "timeout", "progress": last_progress}
