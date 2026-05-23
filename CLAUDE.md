# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A stdio MCP server (`comfyui-mcp` console script) that lets an agent inspect, edit, and run ComfyUI workflows on a local machine. Two interaction modes:

- **API-only** — talks to ComfyUI over HTTP/WS (`/prompt`, `/history`, `/object_info`, `/queue`, etc.).
- **Live co-edit** — also talks to the bundled `comfyui-mcp-bridge` custom_node, which serves per-tab graph state from the actual browser editor over HTTP long-poll.

The README at the repo root is the authoritative user-facing reference for the tool surface (42 tools) and bridge protocol. Read it before adding/changing tools.

## Install / run

```bash
uv pip install -e .              # or: pip install -e .
comfyui-mcp                      # stdio entry point (see pyproject.toml [project.scripts])
```

There are **no tests, no linter config, no build step**. Iteration loop is: edit → restart the MCP client (Claude Code) → invoke the tool → observe.

When wiring into Claude Code, point at the venv's `comfyui-mcp` binary directly. **Never use `uv run`** — it prints to stdout and corrupts the JSON-RPC stream. (This bites every new contributor; preserve it in any install docs you touch.)

## Architecture — the parts that need cross-file context

### Module layout (`src/comfyui_mcp/`)

`server.py` is the only file with `@mcp.tool()` decorators (~2700 lines, all 42 tools). Pure helpers were extracted into focused modules to keep server.py navigable:

- `client.py` — shared singleton `ComfyClient` (avoids server.py ↔ helpers import cycle). All helpers import `from .client import comfy`.
- `comfy.py` — thin httpx/websockets wrapper over the ComfyUI REST + WS surface.
- `core.py` — `_comfy_root()`, `_detect_format()`, `_resolve_node_path()`, `_subgraph_def()`, `_outputs_to_files()`. The shared vocabulary every other module uses.
- `tabs.py` — `_workflow_from_tab()` and `_queue_and_enrich()`: the canonical "pull workflow from the open browser tab via the bridge, queue it, shape the response" path. Used by every tool whose default behavior is "operate on the open tab."
- `widgets.py`, `summarize.py`, `snapshots.py`, `search.py`, `model_meta.py`, `images.py`, `logs.py` — domain helpers. The names match their imports in `server.py`.

When adding a new tool that operates on the open tab, reuse `_workflow_from_tab` + `_queue_and_enrich` — don't reimplement the state-fetch + error-shape contract.

### Two workflow formats

ComfyUI has **two** JSON shapes; tools must handle both or document which they accept:

- **UI format** — what the editor reads/writes: top-level `{nodes: [...], links: [...], definitions: {subgraphs: [...]}}`. Includes layout, subgraph definitions, widget order.
- **API format** — what `/prompt` accepts: `{node_id: {class_type, inputs: {...}}, ...}`. No layout, no subgraphs.

`_detect_format()` in `core.py` is the canonical sniff. **The MCP does NOT convert UI → API** — that conversion lives in ComfyUI's browser JS. When the user has a UI-format file, route them through `run_workflow()` (the bridge already holds the API form) or ask them to "Save (API Format)".

### Subgraph addressing

Offline tools (`describe_graph`, `edit_workflow`, `get_node_widgets`, `describe_workflow`) recurse into subgraph definitions and accept **path-style ids like `"59/68"`** (node 68 inside subgraph instance 59). `_resolve_node_path()` and `_all_nodes()` in `core.py` are the helpers.

**Live ops via the bridge (`add_node`, `connect_nodes`, `set_widget`) currently address top-level only.** For inner-subgraph live edits, edit offline via path syntax then `apply_workflow` to push the updated graph back. Inner-node mutations affect the SHARED subgraph definition — every instance sees the change.

### The bridge (`custom_nodes/comfyui-mcp-bridge/`)

A vendored ComfyUI custom_node. It registers aiohttp routes on the running ComfyUI server (`/mcp_bridge/state`, `/heartbeat`, `/disconnect`, ...) and serves a JS extension (`web/mcp_bridge.js`) that runs in every editor tab.

Key constraints baked into its design — preserve them:

- **Per-tab state is keyed by a sessionStorage `tab_id`, NOT ComfyUI's `clientId`.** ComfyUI persists `clientId` in localStorage, so all tabs in the same browser share it, and ComfyUI's WS layer evicts the older tab on a clientId collision. Don't "simplify" by switching to clientId.
- **Event delivery is HTTP long-poll, not WS.** Same reason — the WS slot is single-occupant per clientId.
- A `boot_id` collision detector + a 3-second graph-poll fallback exist because `app.graph.onAfterChange` misses widget tweaks on some ComfyUI versions. If edits stop appearing live, suspect those hooks first.
- The bridge installs a no-cache middleware for `/extensions/comfyui-mcp-bridge/*` to prevent stale-JS issues. Don't remove it — browser caching was the #1 ghost bug here.

### Queue + wait semantics

- `wait_for_completion` polls `/history` every 2s as a safety net **in addition to** WS events, because WS messages are scoped to the browser tab's clientId and our connection won't see them otherwise. Don't refactor to "WS only".
- `set_widget` synchronously pushes fresh state before returning, so `set_widget` → `run_workflow` is race-free. Multi-agent simultaneous writes are still last-writer-wins.
- Validation errors from `/prompt` get enriched in `tabs.py::_enrich_node_errors` — ComfyUI returns `null` `input_config` for dynamically-populated combos (model lists), so we re-fetch `/object_info` and backfill the valid-value list. Keep this path intact when touching error shaping.

### Snapshots before apply

`apply_workflow` saves the current tab graph to `<COMFYUI_ROOT>/output/_snapshots/<tab_id>_<ts>.json` (last 5 per tab) before swapping. Implemented in `snapshots.py`. If you add another mutator that replaces the whole graph, route it through `_save_pre_apply_snapshot` too.

### `_comfy_root()` resolution

Three-tier (in `core.py`): `COMFYUI_ROOT` env → cwd if it looks like a ComfyUI install → **psutil-based discovery** of the cwd of the process listening on `COMFYUI_URL`'s port. The third tier catches the common case where the agent runs from a different directory than ComfyUI. Cached after first hit.

## Skills (`skills/`)

Two kinds, both Claude Code Skills. Not loaded by the MCP server — installed via symlink. Two install patterns (README §Bundled skills has the commands):

- **Project-scoped** (recommended, pairs with project `.mcp.json`): one symlink `<ComfyUI>/.claude/skills` → `<repo>/skills`. Loads only when Claude Code starts in `<ComfyUI>/`. Every current + future skill auto-shows-up.
- **User-scope**: per-skill symlinks into `~/.claude/skills/`. Available globally.

Two skill families:

- **Prompt-enhancement skills** (`prompt-flux`, `prompt-illustrious`, `prompt-qwen`, `prompt-zimage`, `prompt-ltx`, `prompt-wan`) — model-specific prompt builders. `prompt-illustrious` is backed by `tags.txt`, a snapshot of high-post-count danbooru general tags (README has the regeneration one-liner). `prompt-flux` has an **Enhance Mode** rubric (named-reference anchor + off-center detail + scene-typed enrichment palette in `references/enrichment-palette.md`) for turning thin seeds into specific prompts; this pattern is the template to replicate to other prose-model skills (qwen, zimage) when extending.
- **Workflow-engineering skills** (`comfyui-image-quality`, `comfyui-mask-strategy`, `comfyui-pose-editing`) — diagnostic recipes for quality/inpaint/pose problems. They reference MCP tools by name; keep them in sync when tool names or signatures change.

## When editing tools

- Keep `@mcp.tool()` docstrings *agent-facing*: tell the model when to use the tool, when **not** to (see `search_nodes`'s "BEFORE REACHING FOR THIS" preamble as the template), and what the output shape is.
- Token-efficiency matters. `get_open_workflow` is flagged "token-expensive" for a reason — prefer adding narrow inspectors (`describe_graph`, `get_node_widgets`) over returning whole-graph JSON.
- Errors should be structured dicts (`{"ok": False, "error": "...", "hint": "..."}`), not raised exceptions, so the agent gets a parseable message.

## Caveats list (from README — re-read when in doubt)

- No UI → API converter
- Live ops are top-level only (use offline edit + `apply_workflow` for subgraphs)
- Browser-driven cancels aren't pushed to the MCP in real time
- `arrange_layout` depends on `LGraph.arrange()` existing in the user's ComfyUI build
- `screenshot_canvas` needs a foreground/rendering tab
- `describe_model` for `.pth` upscalers requires `torch` in the MCP venv
