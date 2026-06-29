# comfyui_mcp — Suggested Improvements

## Status — 2026-06-29 (co-located on the RTX 4090 box, ComfyUI 0.26.2)

The split-host topology this doc was written from no longer applies; the MCP now runs
next to ComfyUI, which is section 1's recommendation. That re-sorted the rest. Done:

- **§1 deployment** — satisfied by co-location. `_comfy_root()` resolves locally, full
  filesystem tool surface works, no tunnel.
- **§4 token efficiency** — `get_open_workflow` now defaults to `summary`; `batch_run`
  sweeps the open tab by reference when no `workflow` is passed. (commits `e897f40`, `b9a7bf1`)
- **§2 bridge flakiness** — `bridge_op` retries once on a transient "no tabs connected".
  The *headless edit path* turned out to already exist: a singleton `batch_run` patches
  the open tab's API graph and queues with no live-canvas dependency, which is strictly
  more robust than `bridge_op` for the flap case. Documented rather than rebuilt.
- **§3 HTTP-ify filesystem tools** — **deferred.** Its value was split-host robustness,
  which no longer applies. The routes were verified to exist on 0.26.2 if revived:
  `GET /userdata?dir=workflows&recurse=true&split=false&full_info=true` (list),
  `GET /userdata/<urlencoded-path>` (read), `GET /internal/logs/raw` (logs),
  `GET /object_info` (node classes). Build only as a fallback gated on `_comfy_root()`
  failing, and only if split-host returns.

The original notes below are kept as the source analysis.

---

Context: these notes come from a working session that used this MCP heavily from a
**split-host setup** (MCP running on a Mac, ComfyUI running on a DGX Spark over an SSH
tunnel). That topology surfaced the rough edges below. This doc is written for a coding
agent (Claude on the Spark, where the code lives) to act on.

**Already done** (commit `0bb4219` on `main`, "Clarify split-host and tab-disconnect
errors"): the root-not-found error now names the remote-host/SSH-tunnel case, and tab-op
failures carry a shared `TAB_DISCONNECT_HINT`. Don't redo that. Build on it.

**Guiding principle — the MCP is two tools in one coat.** It is (a) an HTTP client that
talks to ComfyUI over the network (host-agnostic, works from anywhere) and (b) a filesystem
agent that reads ComfyUI's directories directly (`list_custom_nodes`, `catalog_workflows`,
`list_workflows`, `copy_to_input`, log tailing in `logs.py`, snapshots). Only (b) needs to
sit on the ComfyUI host. Every painful failure this session was a filesystem tool invoked
from the wrong host. Keep this split in mind when prioritizing.

**Do NOT restructure wholesale.** The code is already cleanly factored: `core.py`
foundation, `comfy.py` HTTP client, `tabs.py` bridge glue, one concern per module
(`widgets`, `summarize`, `search`, `snapshots`, `logs`, `images`, `model_meta`). That is in
good shape. The only structural smell is `server.py` (~2,700 lines), but it is almost all
thin `@mcp.tool()` registrations delegating to the modules, which is fine for an MCP. Leave
it unless it grows; if it does, split registrations into `tools_*.py` files that register
against the shared `mcp` instance.

---

## 1. Deployment: run the MCP on the ComfyUI host (highest leverage, do first)

This is ops/config, not code, but it fixes the most for the least effort.

- Run the MCP **on the Spark, next to ComfyUI.** Then `COMFYUI_ROOT` resolves for free (the
  cwd / via-port detection in `core.py::_comfy_root` works), no tunnel, and the entire
  filesystem tool surface lights up.
- The browser-canvas bridge is a ComfyUI custom_node (`custom_nodes/comfyui-mcp-bridge`), so
  it always lives with ComfyUI regardless of where the MCP runs. Co-locating the MCP does
  **not** cost the live-canvas feature.
- Transport options:
  - Driving Claude from a terminal **on the Spark**: stdio MCP local to the Spark. Simplest.
  - Driving Claude from the **Mac** while working in the browser: run the MCP as an HTTP/SSE
    server on the Spark and register it as a remote MCP in the Mac's Claude config.
- Document this in the README as the supported topology, with split-host explicitly called
  out as "HTTP tools only."

---

## 2. Reduce the live-tab bridge dependency

Problem: `set_widget` (and other `bridge_op`-based ops) require a live, focused browser tab.
Backgrounded tabs drop the bridge websocket, so an op succeeds and the next one reports zero
tabs. This was the single flakiest part of the session. Meanwhile `queue_workflow(workflow=...)`
and `batch_run` ran headless with no issue.

Suggested changes:
- Add a **headless edit path**: a `set_widget`-equivalent that patches the API-format graph
  (fetched once, or cached) and re-queues, with no canvas dependency. `edit_workflow` already
  patches API/UI graphs; wire a tool around it that targets the open tab's *last fetched* API
  workflow so simple value changes don't need a live socket.
- Prefer the headless path internally for anything that doesn't need to be visible on the
  user's canvas.
- Optional: a short single retry with backoff inside `comfy.py::bridge_op` on transient
  "no tabs connected", to ride out the flap. Keep it short so it doesn't mask a genuinely
  closed tab.

---

## 3. HTTP-ify the most painful filesystem tools (topology robustness)

Even after co-locating, make "what's installed" and "browse my workflows" work over HTTP so
they survive remote/split-host use and degrade gracefully instead of erroring.

- **Node availability** (`list_custom_nodes` / `list_failed_imports`): derive what you can
  from `/object_info`, which you already call in `tabs.py::_enrich_node_errors`. Installed
  node *classes* are visible over HTTP even when the filesystem isn't.
- **Workflow listing/reading** (`list_workflows` / `catalog_workflows` / `read_workflow`):
  recent ComfyUI exposes a userdata/workflows HTTP API. Route through it when the local FS
  isn't reachable.
- **Logs** (`logs.py` tailing): recent ComfyUI has an internal logs HTTP endpoint; use it as
  a fallback to reading the file.

Caveat: I am not certain of the exact ComfyUI route names (they have changed across
versions). **Verify against the installed ComfyUI version before implementing** rather than
trusting these from memory. Where no HTTP equivalent exists (e.g. copying output->input,
which `copy_to_input` does on disk), keep the filesystem path but have it return a clear
"needs local FS access on the ComfyUI host" message when the root isn't found (the
`_url_looks_remote` helper added in commit `0bb4219` is a starting point for detecting this).

---

## 4. Token efficiency

These bit during heavy automation:

- **`batch_run` ferries the full API workflow JSON in and out.** Add a mode that sweeps a
  param grid over the **open tab's** workflow server-side (by reference), so the client
  doesn't have to send the whole graph for every batch. Big saving for seed/param sweeps.
- **Default `get_open_workflow` to `format="summary"`.** The docstring already steers callers
  there; the `ui`/`api` modes routinely produce 50-200KB payloads. Make the cheap, safe
  option the default and require opt-in for the full JSON.

---

## Priority order

1. Move the MCP onto the Spark (section 1). Fixes the most, costs the least.
2. Default `get_open_workflow` to summary + the `batch_run` open-tab mode (section 4). Cheap, high value.
3. HTTP-ify node/workflow/log tools (section 3). Makes it robust to any topology.
4. Headless edit path / bridge retry (section 2). Removes the last fragile dependency.

Everything here is incremental on a tool that already works. No rewrite warranted.
