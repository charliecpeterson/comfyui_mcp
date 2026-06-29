# comfyui-mcp

A Model Context Protocol server that lets a coding agent (Claude Code, Codex, qwen-code, etc.) read, edit, run, and visually co-edit ComfyUI workflows on a local machine.

Works in two modes:

- **API-only**: queue workflows, watch progress, view outputs, debug failures. No browser required.
- **Live co-editing** (with the optional bridge custom_node): the agent and you can both modify the workflow open in your ComfyUI tab — add nodes, change widget values, rewire connections, and watch the changes appear on the canvas in real time.

## Architecture

```
┌──────────────┐    stdio JSON-RPC    ┌────────────────────┐    HTTP/WS    ┌──────────────┐
│ Claude Code  │◄────────────────────►│ comfyui-mcp server │◄─────────────►│   ComfyUI    │
│   (or any    │       (47 tools)     │  (this package)    │  127.0.0.1    │   :8188      │
│  MCP client) │                      │                    │     :8188     │              │
└──────────────┘                      └────────────────────┘               └──────┬───────┘
                                                                                   │
                                                                                   │ aiohttp routes
                                                                                   │ + JS extension
                                                                                   ▼
                                                              ┌─────────────────────────────────┐
                                                              │ comfyui-mcp-bridge (custom_node)│
                                                              │  - per-tab state via long-poll  │
                                                              │  - granular ops on LiteGraph    │
                                                              │  - canvas screenshot + apply    │
                                                              └─────────────────────────────────┘
                                                                                   │
                                                                                   ▼ JS in browser
                                                                            (your ComfyUI tab)
```

The MCP server is **stdio**-based (single-user, local). The bridge is a regular ComfyUI custom_node that registers HTTP routes on the running ComfyUI server and serves a JS extension to the editor.

## Install

### 1. The MCP server

```bash
cd comfyui-mcp
uv pip install -e .
# or: pip install -e .
```

This installs the `comfyui-mcp` console script (a stdio MCP server entry point).

### 2. The bridge custom_node (optional, for live co-edit)

The bridge lives at `<ComfyUI>/custom_nodes/comfyui-mcp-bridge/`. A vendored copy ships in this repo under `custom_nodes/comfyui-mcp-bridge/` — symlink it into your ComfyUI install:

```bash
ln -s /path/to/comfyui-mcp/custom_nodes/comfyui-mcp-bridge \
      /path/to/ComfyUI/custom_nodes/comfyui-mcp-bridge
```

Restart ComfyUI. In its startup log you should see:

```
[mcp_bridge] no-cache middleware installed for /extensions/comfyui-mcp-bridge/
[mcp_bridge] routes registered: /mcp_bridge/{state,heartbeat,disconnect,...}
```

Open the ComfyUI editor in a browser; in the JS console you should see:

```
[mcp_bridge] v0.9.0 ready (tab_id=..., comfy_client_id=..., trust=true)
```

Verify with:

```bash
curl -s http://127.0.0.1:8188/mcp_bridge/debug | jq '{tab_count: (.tabs|length)}'
```

### 3. Wire into Claude Code

Point at the entry-point script directly — **not** `uv run`, which prints status to stdout and corrupts the JSON-RPC stream.

**Recommended: project-scoped `.mcp.json`** in your ComfyUI directory. Loads only when you start Claude Code from inside `<ComfyUI>/`, keeps the global config clean:

```bash
cat > /path/to/ComfyUI/.mcp.json <<'EOF'
{
  "mcpServers": {
    "comfyui": {
      "type": "stdio",
      "command": "/path/to/comfyui-mcp/venv/bin/comfyui-mcp",
      "args": [],
      "env": {}
    }
  }
}
EOF
```

(Use the conda env's `comfyui-mcp` binary instead if you installed there.)

First time you start Claude Code in `<ComfyUI>/`, it will prompt you to approve the project MCP servers — accept once.

**Alternative: user-scope** if you want comfyui-mcp available everywhere:

```bash
claude mcp add comfyui -s user -- /path/to/comfyui-mcp/venv/bin/comfyui-mcp
```

In both cases, restart Claude Code. `/mcp` should show `comfyui · ✔ connected`.

## Configuration

Environment variables read by the MCP server:

| Var | Default | Purpose |
|---|---|---|
| `COMFYUI_URL` | `http://127.0.0.1:8188` | base URL of the running ComfyUI |
| `COMFYUI_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `COMFYUI_ROOT` | (cwd, if it looks like a ComfyUI install) | filesystem root for `list_workflows`, `list_custom_nodes`, `tail_log`, `describe_model` |

The `COMFYUI_ROOT` autodetection looks for `main.py` + `custom_nodes/` in the current working directory. If you launch Claude Code from your ComfyUI directory, it just works; otherwise set the env var explicitly.

## Quick start

Once everything's wired:

```
> can you run my open workflow?
[agent calls run_workflow() (no args = pulls from open tab) → returns output_files → view_file]

> add a fun lora that I have and re-run
[agent calls list_models("loras") → describe_model on a few → set_widget on the
 LoRA stack node → run_workflow]

> the workflow won't queue — fix it
[agent calls resolve_missing_models → set_widget for each path-prefix issue →
 run_workflow]

> clean up my graph and arrange it nicely
[agent calls describe_graph → delete_node on dead Reroutes → arrange_layout]

> the face looks different from the body skin
[agent uses /comfyui-image-quality skill — diagnose + apply Recipe A
 (FaceDetailer tune + ColorMatchV2)]

> mask just the arms and inpaint leather sleeves
[agent uses /comfyui-mask-strategy skill — picks DWPose-keypoint approach,
 draws polyline mask, inpaints once]
```

## Tool surface (47 tools)

### Discovery

| Tool | Purpose |
|---|---|
| `search_nodes(query, input_type?, output_type?)` | Smart, ranked search across installed nodes. Multi-token, scores name > category > description. |
| `list_models(category?)` | List models registered with ComfyUI (respects `extra_model_paths.yaml`). |
| `find_model(query, category?)` | Fuzzy basename lookup across all model categories. |
| `describe_model(path, category?)` | Read safetensors header + sidecars + folder notes. Catches corrupted files before queueing. |
| `list_workflows(dir?)` | Recursive .json walk under `<COMFYUI_ROOT>/user/default/workflows`. |
| `list_custom_nodes()` | Enumerate `custom_nodes/` packages. |
| `read_workflow(path)` | Read + format-detect (UI vs API) a workflow file. |
| `get_system_stats()` | Smoke test: device, vram, comfy version. |

### Run / queue / status

| Tool | Purpose |
|---|---|
| `run_workflow(workflow?, tab_id?)` | Daily driver: queue + wait + return output file refs. No-args queues the open tab. |
| `queue_workflow(workflow?, tab_id?, client_id?)` | Submit. No-args queues the open tab and forwards the tab's client_id for live previews. |
| `validate_workflow(workflow)` | Dry-run: queue + immediate cancel. Returns enriched `node_errors`. |
| `resolve_missing_models(workflow?)` | One-call diagnose: validate + fuzzy-match every missing model reference, returns a fix plan with `auto_fix` candidates. |
| `wait_for_completion(prompt_id, timeout, compact?)` | Block until done. Always-poll history fallback so it doesn't hang on missed WS events. `compact=True` (default) drops verbose history echo. |
| `get_current_execution(timeout?)` | Snapshot: running prompt, current node + class, latest step progress. Non-blocking. |
| `get_queue(compact?)` | List running + pending jobs. |
| `cancel_job(prompt_id?)` | Remove from pending queue + interrupt if running. |
| `get_history(prompt_id?, max_items?)` | Past runs with outputs. |
| `batch_run(workflow, params_grid)` | Cartesian-product or zip parameter sweeps. |

### Outputs / I/O

| Tool | Purpose |
|---|---|
| `view_file(filename, ...)` | Inline image (auto-thumbnails 18MB+ outputs via PIL) OR metadata for video/audio. |
| `view_image(...)` | Thin alias for `view_file` (image-only). |
| `compare_images([{filename, ...}, ...])` | PIL composite of N images side-by-side / vertical / grid. A/B verification. |
| `upload_input(path)` | Push a local file into ComfyUI's `input/` for LoadImage etc. |
| `copy_to_input(filename, source_type=output)` | Copy from output/temp into input/ for chained inpaint passes. |
| `tail_log(lines?)` | Tail `<COMFYUI_ROOT>/user/comfyui.log`. |

### Editing (offline JSON, subgraph-aware)

| Tool | Purpose |
|---|---|
| `edit_workflow(workflow, edits)` | Multi-node patcher. Path syntax `"59/68"` for inner subgraph nodes. Auto-detects UI vs API format. |
| `save_workflow(path, workflow)` | Write JSON to disk. |
| `describe_graph(workflow?, tab_id?)` | Token-efficient connection summary; flags orphans. Recurses into subgraphs (path-style ids). |
| `describe_workflow(path?, tab_id?, summary_only?)` | Workflow file summary: notes_in_canvas, sidecar_md, folder_notes, model_references, top_types. Pass nothing → describes the open tab. |
| `catalog_workflows(dir?, query?, type_contains?, model_contains?, limit?)` | Bulk describe across a directory. Server-side filters keep responses small on big libraries. |

### Live co-edit (requires bridge)

| Tool | Purpose |
|---|---|
| `get_open_workflow(format?, tab_id?)` | Defaults to a compact `summary` (~1-2KB). `format="ui"`/`"api"` returns the full JSON — **token-expensive**; prefer `describe_graph` / `get_node_widgets` for inspection. |
| `get_node_widgets(node_id, tab_id?)` | Token-cheap: one node's widgets, name-resolved (handles seed_control_after_generate). Path syntax for subgraphs. |
| `apply_workflow(workflow, tab_id?, confirm?)` | Replace the graph in a tab (UI format). |
| `add_node(class_type, x, y, widget_values?)` | Surgical: insert one node. Validates class_type against /object_info; suggests fuzzy matches on miss. |
| `delete_node(node_id)` | Surgical: remove one node. |
| `connect_nodes(from_id, from_slot, to_id, to_slot)` | Wire output → input (slots can be name or index). |
| `connect_many([{...}])` | Batch wire — single round-trip for N connections. |
| `disconnect_input(to_id, to_slot)` | Break the link feeding an input. |
| `set_widget(node_id, name, value)` | Change a widget. Type-checked: string widgets reject non-strings cleanly. After set, fresh state is pushed before the call returns (no race with subsequent queue). |
| `move_node(node_id, x, y)` | Reposition. |
| `arrange_layout()` | Auto-arrange via LiteGraph (best-effort, depends on ComfyUI version). |
| `screenshot_canvas(tab_id?)` | Inline PNG of the visual graph. |
| `bridge_debug()` | Diagnostic dump: live tabs, pending events, sockets. |

### LoRA / Civitai discovery

Find a model for a job — prefer files already on disk, fall back to Civitai, then inject into the open tab. Driven end-to-end by the `find-loras` skill, but each tool is usable on its own.

| Tool | Purpose |
|---|---|
| `suggest_local_loras(intent, base_model?, k?)` | Rank LoRAs already under `<COMFYUI_ROOT>/models/loras/` against a free-text `intent`. Reads each safetensors header for training tags + trigger phrase + base family; filters out cross-base mismatches. Returns candidates with real trigger words and a recommended strength. **Try this BEFORE `search_civitai`** — it may already be on disk. |
| `search_civitai(query, types?, base_model?, nsfw?, sort?, limit?)` | Search Civitai for any model type (`LORA`, `Checkpoint`, `Controlnet`, `Upscaler`, `TextualInversion`, `VAE`, ...). SFW-default (`nsfw=False`), minor-filtered, lean response shape. `sort` defaults to `Most Downloaded` (universal across types). |
| `describe_civitai_model(model_id)` | Full detail for one Civitai model: versions, declared trigger words, base model, file sizes — without the bloated raw API payload. |
| `download_civitai_model(model_id, version_id?, subdir?, confirm?, overwrite?)` | **Two-call confirmation** (writes hundreds of MB): first call returns a preview, second with `confirm=True` writes. Auto-routes to the correct `models/` subdir by model type. Re-reads the downloaded file's safetensors metadata for canonical trigger words. |
| `add_lora_to_workflow(filename, strength?, append_trigger_words?, tab_id?)` | Inject a LoRA into the open tab: inserts/extends the LoRA-loader chain and (by default) appends its trigger words to the positive `CLIPTextEncode`. |

## Common recipes

### Run the open workflow and show me the result
```
"run_workflow then view_file the first output"
```

### Fix a workflow shared from another machine
```
"resolve_missing_models, set_widget on each auto_fix, run_workflow"
```

### Clean up a spaghetti graph
```
"describe_graph, delete_node on every Reroute in orphans, arrange_layout"
```

### Sweep a parameter
```
"run batch_run with seed=[1,2,3,4] and cfg=[5,7,9], queue=true"
```

### Pick a fun LoRA and run
```
"list_models('loras'), describe_model on three from the pony folder, pick the
 one whose tags look most fun, set_widget into the LoRA stack, run_workflow"
```

### Find a LoRA for a look (local first, Civitai fallback)
```
"suggest_local_loras intent='neon cyberpunk lighting' — if nothing local fits,
 search_civitai, describe_civitai_model the top hit, download_civitai_model with
 confirm, then add_lora_to_workflow"  (or just: /find-loras)
```

### Watch a long run without blocking
```
"queue_workflow (no args), then call get_current_execution every few seconds"
```

### Find a starting workflow from your library
```
"catalog_workflows with model_contains='illustrious' and type_contains='ControlNet',
 then describe_workflow on the most relevant one"
```

### Inpaint a region from an existing output
```
"copy_to_input the latest output PNG, then build a face detailer pass on top of it"
```

## Troubleshooting

### MCP shows ✘ failed in `/mcp`

Most likely you used `uv run` in the launch command — it prints status messages to stdout that corrupt JSON-RPC framing. Use the entry-point script directly:

```bash
claude mcp remove comfyui -s user
claude mcp add comfyui -s user -- /path/to/comfyui-mcp/.venv/bin/comfyui-mcp
```

### Bridge tab_count stuck at 1 (or 0) after restart

Browser cached the old bridge JS. The bridge installs a no-cache middleware for `/extensions/comfyui-mcp-bridge/*` so future loads are clean, but a tab loaded *before* the middleware was installed may still have stale JS. In that tab: F12 → Network tab → check "Disable cache" → Ctrl+F5. Console should show `[mcp_bridge] v0.X.Y ready`.

### `tab_count` doesn't increase when you open a second tab

ComfyUI persists `clientId` in `localStorage`, so multiple tabs in the same browser share it — and ComfyUI's WebSocket layer kicks the older tab out of its `sockets` dict when the second connects. The bridge works around this with a per-tab `tab_id` in `sessionStorage` and a `boot_id` collision detector. If you still see only one tab after a hard reload of each:

- Did you open the second tab via "duplicate tab"? sessionStorage gets *copied*. The bridge will detect this within a few seconds and regenerate the duplicate's `tab_id` automatically (look for `[mcp_bridge] tab_id collision` in the duplicate tab's console).
- Otherwise, paste this in the duplicate tab's console:
  ```js
  sessionStorage.removeItem("mcp_bridge.tab_id"); location.reload()
  ```

### Workflow won't queue, error in stderr but truncated

ComfyUI's stderr printer truncates long valid-value lists to `(list of length 75)`. The MCP's `validate_workflow` and `queue_workflow` automatically backfill the full lists from `/object_info`, so the **complete** list is always available in the structured `node_errors` response.

### Long workflow appears to hang

`wait_for_completion` blocks until the run finishes — the user sees no progress mid-call. The implementation polls `/history` every 2s as a safety net so it always exits within ~2s of completion (even when ComfyUI's WebSocket events miss our connection because they're scoped to the browser tab's client_id). If you want progress visibility:

- Use `get_current_execution` to poll (non-blocking, ~1 second per call).
- Split into `queue_workflow` then `wait_for_completion`, with the wait running in the background.
- Use `run_workflow` for short runs only.

### Edit isn't visible in browser tab until I refresh

The bridge JS pushes state on every `app.graph.onAfterChange` event, but that hook misses some edit types (notably widget value tweaks) on certain ComfyUI versions. A 3-second polling fallback re-checks the graph and pushes if changed; if you can't wait, refresh the tab manually.

### My ComfyUI is on a remote machine

The MCP needs to reach `COMFYUI_URL`. The bridge's `screenshot_canvas` and `apply_workflow` need a browser to actually be open. If the agent runs on the same machine as ComfyUI (the typical setup), everything works. If they're separate, set `COMFYUI_URL` and the bridge still works as long as you have the editor open somewhere.

## Caveats and known limits

- **Subgraphs (offline tools support; live ops don't)**: `describe_graph`, `edit_workflow`, `get_node_widgets`, `describe_workflow`, and `_extract_model_refs` recurse into subgraph definitions and accept path-style ids like `"59/68"` (node 68 inside subgraph instance 59). Live ops via the bridge (`add_node`, `connect_nodes`, `set_widget`) currently address top-level only — for inner-subgraph live edits, edit offline via path syntax then `apply_workflow` to push the updated graph back. Inner-node mutations affect the SHARED subgraph definition (all instances see the change).
- **UI ↔ API conversion**: the MCP doesn't currently convert UI-format workflows to API format. ComfyUI does this in browser JS only. To queue a UI-format file, open it in the editor and `run_workflow()` (bridge has the API form), or export "Save (API Format)" first.
- **Browser-driven cancels**: if you hit the Cancel button in ComfyUI mid-run, the MCP doesn't get notified in real time. `wait_for_completion` catches it via WS events; `get_history(prompt_id)` afterwards shows status `error` with `execution_interrupted`.
- **`arrange_layout`**: depends on `LGraph.arrange()` existing in your ComfyUI build. On older versions you'll get a clear error; in that case compute positions yourself and call `move_node` per node.
- **Concurrent MCP edits + manual edits**: the bridge debounces background pushes (800ms) but explicit ops push synchronously before responding (so `set_widget` → `run_workflow` is race-free). Multi-agent simultaneous writes can still race for last-writer-wins.
- **`screenshot_canvas`**: requires a real, currently-rendered canvas. Background tabs with paused rendering may return a blank frame.
- **`describe_model` for `.pth` files** (upscalers): requires `torch` in the MCP's venv to inspect tensor shapes. Without it, `.pth` returns a clean fallback message; safetensors models work without torch.

## Bundled skills

The repo ships Claude Code Skills under `skills/`. Two flavors:

**Prompt-enhancement skills** (model-specific) — turn a basic description into a high-quality, model-aware prompt. Distilled from prompting guides + a curated 2.5K-tag danbooru reference for the tag-based one.

| Skill | Purpose | Output |
|---|---|---|
| `prompt-flux` | Prompts for Flux 1 (Dev/Pro/Schnell), Flux 2 (Pro/Max/Flex/Dev/Klein), and Flux NSFW LoRAs. Includes **Enhance Mode** with a structured rubric (named-reference anchor + off-center detail + scene-typed enrichment palette) for turning thin seeds like *"a girl in a forest"* into specific, non-generic prompts. | natural-language prompt (no negatives) |
| `prompt-illustrious` | Prompts for Illustrious XL, Pony Diffusion V6 XL, NoobAI, Hassaku XL, generic SDXL danbooru fine-tunes. Backed by a snapshot of high-post-count danbooru general tags. | comma-separated tag prompt + negative |
| `prompt-qwen` | Prompts for Qwen Image 1.0 / 2.0 / Edit. Excellent text rendering (English + Chinese) and unified gen+edit. | natural-language prompt + negative |
| `prompt-zimage` | Prompts for Z-Image base / Turbo / Omni / Edit. Bilingual, retro/synthwave-friendly. Turbo ignores negatives — the skill handles that. | long camera-style prose |
| `prompt-wan` | Prompts for Wan 2.1 → 2.7 (Alibaba video). Handles the structural shift between Wan 2.2 (single-sentence) and Wan 2.6+ (shot-block with timecodes), plus 2.7 multi-reference / brand-color placement. | structured video prompt |
| `prompt-ltx` | Prompts for LTX Video 2B/13B, LTX-2, LTX-2.3 (Lightricks). Uses the official 7-component structure; handles A2V audio-locking and the divisible-by-32 resolution constraint. | structured video prompt |

**Workflow-engineering skills** — diagnose and fix image quality issues, with concrete recipes from real iteration sessions.

| Skill | Purpose |
|---|---|
| `comfyui-image-quality` | Diagnose + fix face/body color mismatch, broken hands, AI-looking skin, anatomy artifacts. Diagnostic checklist, 5 validated fix recipes (FaceDetailer tune, hand detailer, anti-AI postprocess, single-KSampler collapse, UltimateSDUpscale), and an inpaint failure-mode checklist. Forces verification BEFORE declaring success. |
| `comfyui-mask-strategy` | Pick the right mask source BEFORE wiring up an inpaint pass. Decision table across YOLO bbox / SEGS combined / CLIPSeg / pose-keypoint polyline / manual paint. Includes the keypoint→polyline recipe (with PIL code), CLIPSeg pitfalls, and the mask-batch-vs-mask gotcha. |
| `comfyui-pose-editing` | Recipes for changing or repairing a subject's pose using ControlNet / OpenPose preprocessors + inpaint, including keypoint hand-edit patterns. |

### Install (symlink so edits flow through immediately)

**Recommended: project-scoped** — pairs with the project `.mcp.json` so skills and MCP both load only when you start Claude Code in `<ComfyUI>/`. One symlink covers every current and future skill in the repo:

```bash
mkdir -p /path/to/ComfyUI/.claude
ln -s /path/to/comfyui-mcp/skills /path/to/ComfyUI/.claude/skills
```

**Alternative: user-scope** — makes the skills available everywhere (not just in `<ComfyUI>/`):

```bash
mkdir -p ~/.claude/skills
for d in /path/to/comfyui-mcp/skills/*/; do
    ln -s "$d" ~/.claude/skills/
done
```

After either, restart Claude Code. The skills are invokable as `/prompt-flux`, `/prompt-illustrious`, etc.

### Usage

```
> /prompt-flux a girl in a forest at dawn
> /prompt-illustrious pony, muscular girl with red skin and glasses
> /prompt-qwen vintage cafe with bilingual sign
> /prompt-zimage athletic woman running at sunrise
> /prompt-wan a sword fight under autumn maples, Wan 2.6 shot-block
> /prompt-ltx an espresso machine pulling a shot, LTX-2.3 with audio
```

The skill returns a ready-to-paste prompt (and negative if applicable). Combine with the MCP tools:

```
> /prompt-illustrious pony, cyberpunk samurai
> ... agent returns positive + negative ...
> "now set_widget on my open workflow's CLIPTextEncode positive node and the negative one, then run_workflow"
```

That's the prompt-enhance → live-edit → run loop in three turns.

### Re-curating tags.txt

The tag list at `skills/prompt-illustrious/tags.txt` was generated from a snapshot of the danbooru tags database (`tags.json`, ~41 MB). To refresh:

```bash
python -c "
import json
with open('/path/to/tags.json') as f: tags = json.load(f)
gen = [t for t in tags if t.get('category')==0 and t['post_count'] >= 10000]
gen.sort(key=lambda x: -x['post_count'])
with open('skills/prompt-illustrious/tags.txt','w') as f:
    f.write('# Top danbooru general tags by post_count >= 10000\n#\n')
    for t in gen: f.write(f\"{t['name']}\t{t['post_count']}\n\")
"
```

## File layout

```
comfyui-mcp/
├── pyproject.toml
├── README.md            # this file
├── CLAUDE.md            # agent-facing context for Claude Code
├── src/comfyui_mcp/
│   ├── __init__.py
│   ├── server.py        # all 47 @mcp.tool() entry points
│   ├── client.py        # shared singleton ComfyClient
│   ├── comfy.py         # httpx + websockets wrapper over ComfyUI REST/WS
│   ├── core.py          # _comfy_root, _detect_format, _resolve_node_path, _subgraph_def
│   ├── tabs.py          # _workflow_from_tab, _queue_and_enrich (open-tab path)
│   ├── widgets.py       # widget read/write helpers
│   ├── summarize.py     # graph-summary helpers
│   ├── snapshots.py     # pre-apply snapshot save/restore
│   ├── search.py        # search_nodes, search-related helpers
│   ├── model_meta.py    # describe_model, model metadata
│   ├── images.py        # image / preview helpers
│   └── logs.py          # tail_log, log helpers
├── custom_nodes/comfyui-mcp-bridge/
│   ├── __init__.py      # registers HTTP routes + middleware on ComfyUI
│   └── web/mcp_bridge.js  # ComfyUI editor extension (JS, v0.9.0)
└── skills/              # Claude Code Skills — symlink into <ComfyUI>/.claude/skills/
    ├── prompt-flux/{SKILL.md, references/*.md}
    ├── prompt-illustrious/{SKILL.md, SKILL-pony.md, tags.txt, refs/, extract_danbooru_tag.py}
    ├── prompt-qwen/{SKILL.md, references/*.md}
    ├── prompt-zimage/{SKILL.md, references/*.md}
    ├── prompt-wan/{SKILL.md, references/*.md}
    ├── prompt-ltx/{SKILL.md, references/*.md}
    ├── comfyui-image-quality/SKILL.md
    ├── comfyui-mask-strategy/SKILL.md
    └── comfyui-pose-editing/SKILL.md
```

## License

(Whatever you want — currently unspecified.)
