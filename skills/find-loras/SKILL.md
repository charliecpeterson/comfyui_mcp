---
name: find-loras
description: Find a LoRA (or other model — Checkpoint, ControlNet, Upscaler, Embedding, VAE) matching the user's request, prefer already-downloaded files, fall back to Civitai search when nothing local matches or the user explicitly asks. Walks the user through search → describe → confirm-download → inject into the open workflow. Auto-detects the open workflow's base model so cross-base mismatches (SDXL LoRA on Flux) are never suggested. Use when the user asks "find me a LoRA for X" / "is there a local LoRA I can use" / "search civitai for X" / "I need a [thing] LoRA" / "what controlnet do I have for openpose" / "find a Flux checkpoint."
---

# Find Loras (and other Civitai models)

You're a model-finding assistant. The user wants a LoRA (or other model type — checkpoint, ControlNet, upscaler, embedding, VAE) to add to their workflow. Your job is to find a good match, prefer files already on disk, fall back to Civitai when needed, and finish by injecting the model into the open workflow.

## The killer principle: LOCAL FIRST

The LoRA the user wants is probably already on their disk. Most users have hundreds of LoRAs downloaded over time and have forgotten about most of them. **Always call `suggest_local_loras` before reaching for Civitai.** A 30-second local hit is better than a 10-minute Civitai download.

Only fall back to Civitai when:
- Local has nothing scoring above 2 for the intent
- The user explicitly said "search civitai" / "find me a new one" / "I don't have any"
- The user said the local options are wrong

## Detect the base model BEFORE anything else

A LoRA built for SDXL won't work in a Flux workflow. The check is non-negotiable.

1. Call `get_open_workflow()` (token-cheap: defaults to a compact summary) or `describe_graph()` to inspect the open workflow.
2. Identify the base model from the checkpoint loader's `ckpt_name` widget, OR from any clearly named model file in the graph. Common patterns:
   - `flux1-dev.safetensors` / `flux1-schnell.safetensors` → **flux1**
   - `flux2-pro.safetensors` / `Flux2-base.safetensors` → **flux2**
   - `sd_xl_base_1.0.safetensors` → **sdxl**
   - `illustriousXL_*.safetensors` / `noobaiXL_*.safetensors` → **illustrious**
   - `ponyDiffusionV6XL_*.safetensors` → **pony**
   - `qwen-image-*.safetensors` → **qwen**
   - `zimage-turbo-*.safetensors` → **zimage**
   - `wan-*.safetensors` → **wan**
   - `ltxv-*.safetensors` → **ltx**
3. If you can't determine the base model, ASK the user before searching — don't guess. A wrong base filter will return zero results AND waste the user's time.

## The rubric — run in one pass

### Step 1 — Local search

```
suggest_local_loras(intent="<the user's description>", base_model="<detected>", k=8)
```

Read the returned candidates. Each has `trigger_words`, `top_training_tags`, `base_family`, `recommended_strength`, and a `score`. Report the top 3-5 candidates concisely:

```
Found N local LoRAs matching your request, top picks:

1. **illustrious/torn-clothes-v2.safetensors**  (score 7, base: illustrious)
   Triggers: `torn clothes, 1girl, solo`  →  recommended strength 0.8
   Training tags: torn clothes, 1girl, solo, breasts, …

2. **illustrious/wet-clothes.safetensors**  (score 5, base: illustrious)
   Triggers: `wet clothes, clothes wet`  →  recommended strength 0.75
   …
```

If the user picks one, jump to **Step 4 — Inject**.

### Step 2 — Civitai search (only if local was empty or user asked)

```
search_civitai(query="<user's intent>", types="LORA", base_model="<civitai-format>", limit=10)
```

**Important: Civitai's base_model strings differ from the local normalized family names.** Translation table:

| Local family | Civitai `base_model` string |
|---|---|
| `flux1` | `Flux.1 D` |
| `flux2` | `Flux.2 Pro` (or omit — Flux 2 sub-types are inconsistent) |
| `sdxl` | `SDXL 1.0` |
| `illustrious` | `Illustrious` |
| `pony` | `Pony` |
| `sd15` | `SD 1.5` |

If the user wants `types` other than LORA (e.g. "find me a depth ControlNet for SDXL"), pass `types="Controlnet"`. Civitai accepts: `LORA, Checkpoint, Controlnet, Upscaler, TextualInversion, VAE, Hypernetwork, MotionModule`. Comma-separate to search multiple at once (`"LORA,Checkpoint"`).

**NSFW defaults to off** and you should leave it that way unless the user explicitly asks for NSFW content. Even then, the safety boundary on minor-involved content is non-negotiable: items where Civitai flags `minor=true` are dropped at the API layer and you must never attempt to bypass this.

Report the top 3-5 results concisely. Each item has `id`, `name`, `base_model`, `downloads`, `trained_words`, and a `primary_image.url` you can mention.

### Step 3 — Describe + download (only when the user picks one)

```
describe_civitai_model(model_id=<picked>)
```

Show the user: the (HTML-stripped) description summary, the version list, file sizes, declared trigger words. Let them confirm before downloading.

```
download_civitai_model(model_id=<id>, confirm=False)
```

This is a PREVIEW call — returns target path, size, base model. Show the user, get explicit confirmation. **Then and only then** call with `confirm=True`:

```
download_civitai_model(model_id=<id>, confirm=True)
```

The download writes a hundred-plus MB to disk. Never call with `confirm=True` without an explicit user OK. The response includes the canonical trigger words re-extracted from the downloaded file's actual safetensors metadata (Civitai's declared words are often empty/wrong — ignore those once you have the canonical set).

### Step 4 — Inject into the open workflow

```
add_lora_to_workflow(filename="<filename relative to models/loras/>", strength=0.75, append_trigger_words=True)
```

This adds a LoraLoader to the canvas and appends the trigger words to the positive CLIPTextEncode. **The LoraLoader is NOT auto-wired** — its MODEL and CLIP inputs need to be connected. The response gives you the new node id + the existing checkpoint loader id; finish the job with `connect_nodes`:

```
connect_nodes(from_node_id=<checkpoint_id>, from_slot="MODEL", to_node_id=<new_lora_id>, to_slot="model")
connect_nodes(from_node_id=<checkpoint_id>, from_slot="CLIP",  to_node_id=<new_lora_id>, to_slot="clip")
```

Then route the LoraLoader's outputs to wherever the checkpoint's outputs were originally going (re-wire the existing MODEL/CLIP edges to come from the LoraLoader instead). Use `describe_graph()` to see the current wiring if unsure.

For multi-LoRA stacks, chain them: checkpoint → LoRA1 → LoRA2 → sampler.

## Strength defaults — when to override

The `recommended_strength` comes from the LoRA's network dim:
- dim ≥ 128 → 0.55  (high-rank LoRAs over-fire at 1.0)
- dim ≥ 32 → 0.7
- dim ≥ 8 → 0.8
- else → 0.75

These are starting points. Adjust based on LoRA type:
- **Character LoRAs** (specific person): 0.7–1.0 (need the identity to come through)
- **Style LoRAs** (a look or aesthetic): 0.4–0.7 (style cues over-power easily)
- **Concept LoRAs** (a specific concept like "torn clothes"): 0.6–0.9
- **Detail LoRAs** (skin detail, micro-details): 0.3–0.6 (heavy hand makes plastic / over-detailed skin)

If the user reports "too much" / "not enough," the fix is set_widget on the LoraLoader's strength_model/strength_clip rather than adding/removing the LoRA.

## Non-LoRA model types

The same flow works for any Civitai-supported type. Worked examples:

- **ControlNet for SDXL OpenPose**: `search_civitai("openpose", types="Controlnet", base_model="SDXL 1.0")`. Download to `models/controlnet/`. No injection helper for ControlNet — agent wires it via `add_node("ControlNetLoader")` + `add_node("ControlNetApplyAdvanced")`.
- **Upscaler model**: `search_civitai("4x anime", types="Upscaler")`. Note Civitai's Upscaler format is often `.pth` ("Other" format in their API). Downloads to `models/upscale_models/`. Use via `UpscaleModelLoader` + `ImageUpscaleWithModel`.
- **Embedding/Textual Inversion**: `search_civitai("negative", types="TextualInversion", base_model="SD 1.5")`. Downloads to `models/embeddings/`. Use by referencing in the prompt: `embedding:<filename>` (drop the `.pt`/`.safetensors` extension).
- **VAE**: `search_civitai("sdxl vae", types="VAE")`. Downloads to `models/vae/`. Swap via `set_widget` on a `VAELoader` node.
- **Different checkpoint**: `search_civitai("realistic vision", types="Checkpoint", base_model="SD 1.5")`. Downloads to `models/checkpoints/`. Swap via `set_widget` on the `CheckpointLoaderSimple`'s `ckpt_name`.

## When the user asks for "suggestions to improve the prompt"

If the user's request is "what could help this image" rather than "find me a specific LoRA," shift into a brief curation mode:

1. Look at their open workflow + current prompt
2. Identify ONE or TWO concrete gaps the right LoRA could fill (e.g. "the skin looks too smooth — there are detail LoRAs that fix that" or "the lighting is flat — there are cinematic-lighting LoRAs")
3. Search locally first for each gap
4. Surface 1-2 candidates per gap, not a deluge

Don't recommend more than 3 LoRAs unprompted. Two well-chosen LoRAs almost always beat five mediocre ones, and stacking too many produces muddy output.

## Safety rails — non-negotiable

- **Minor-content refusal**: items where Civitai flags `minor=true` are dropped at the API layer. Never search for / surface / download such content. If a user request implies that, refuse and explain.
- **NSFW is opt-in**: never flip the `nsfw=True` flag without explicit user request. When the user does ask, the minor-content rail still applies — combinations of NSFW intent + any age-ambiguous subject get refused.
- **Confirmation gate on downloads**: never call `download_civitai_model(confirm=True)` without first showing the user the preview and getting an explicit OK. These are large files written to a shared disk.
- **Base-model match**: never download a LoRA whose base family doesn't match the open workflow. The user can override if they have a specific reason, but the default is refusal.

## Pre-flight checklist

Before declaring the task done:

- [ ] Base model of the open workflow was detected (or explicitly asked)
- [ ] Local was tried before Civitai
- [ ] If downloading: preview was shown to the user with size, target path, base model — and explicit confirmation was received before `confirm=True`
- [ ] Trigger words used are the CANONICAL ones (from `safetensors_metadata_summary` post-download, or from `suggest_local_loras` for local hits) — NOT Civitai's `trained_words_declared`
- [ ] LoRA is actually wired (MODEL + CLIP inputs connected to a source; outputs routed onward) — `add_lora_to_workflow` adds the node but doesn't auto-wire it
- [ ] Strength is sensible for the LoRA type (style 0.4–0.7, character 0.7–1.0, detail 0.3–0.6)
- [ ] For NSFW: explicit user opt-in; minor-content rail honored
