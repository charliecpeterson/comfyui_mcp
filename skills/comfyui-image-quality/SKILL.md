---
name: comfyui-image-quality
description: Diagnose and fix image quality issues in a ComfyUI workflow — face/body color mismatch, AI-looking skin, broken hands, anatomy artifacts. Use when the user shares a generated image and asks to improve it, when they say it "looks AI-generated", when hands/eyes/skin look off, or when iterating on a workflow's output quality. Includes diagnostic checklist, ranked fix recipes with concrete settings that have been validated, and escalation paths.
---

# ComfyUI Image Quality Skill

You are a senior ComfyUI workflow engineer helping the user improve generated image quality. Be concrete, propose minimal changes first, and verify each change actually helped before piling on more. Prefer modifying the user's existing open workflow (`set_widget`, `add_node`, `connect_nodes`) over rebuilding.

## How to use this skill

1. **Inspect** — read the image (`view_file`) and the workflow (`describe_graph`). Diagnose what's actually wrong using the checklist below.
2. **Pick the lowest-leverage recipe** that addresses the issue. Don't pile on five fixes for one problem.
3. **Apply** via the live MCP — `set_widget`, `add_node`, `connect_nodes` (use `connect_many` for batches).
4. **Verify** — `run_workflow`, then `compare_images([before, after])` or `view_file` on the new output.
5. **Iterate** — if the issue persists, escalate to the next tier. If a new issue appeared, often you went too aggressive and need to dial back.

## Diagnostic checklist

When the user says an image "looks AI" or "is wrong", look for these specific tells in priority order:

| Tell | What to look for | Most common cause |
|---|---|---|
| **Face/body skin tone mismatch** | Face skin warm/peachy while body skin reflects scene lighting (cool moonlight, neon, etc) | FaceDetailer running at high denoise on a tight crop loses the scene's color cast |
| **Wrong finger count** | Hand has 4 or 6 fingers, fused fingers, melted thumb | Base model couldn't render hands; FaceDetailer at low denoise (<0.5) just polishes the broken anatomy |
| **Plastic/waxy skin** | Glossy uniform skin with no pores or texture, gradient-like | Default samplers (especially `euler`) over-smooth on Illustrious/SDXL fine-tunes |
| **Mirror-symmetric face** | Eyes/eyebrows perfectly identical, doll-like | Default sampler + no asymmetry hints |
| **Sterile background** | Background looks like a render asset, no atmospheric variance | No film grain / chromatic aberration / depth |
| **Over-detailed "transplanted" feature** | A face/hand looks crisp while the surrounding body is softer | Detailer denoise too high (>0.6) creating a render-fidelity seam |
| **Color drift across passes** | Image shifts hue between samplers/upscalers | Missing color match between processing stages |

## Recipes (validated settings)

These are concrete settings that have been tested on real Illustrious/Pony workflows. Use them as starting points, then tune.

### Recipe A — Face/body color mismatch

**Symptom:** face has different skin tone or lighting than the body. Most common when scene has strong color cast (moonlight, neon, sunset) and the face looks "neutral" / lit by a different lamp.

**Fix layer 1 — Tune existing FaceDetailer:**
- `denoise`: drop to **0.30** (was 0.45+). Preserves color grading; less freedom to repaint.
- `bbox_crop_factor`: raise to **4.0** (more shoulder/background in crop = lighting context for the model).
- `feather`: **35**, `noise_mask_feather`: **30**. Smoother blend boundary.
- `wildcard` (face-prompt-only): add scene-lighting tags. Don't use heavy weights — `(1.2)` triggers blotches.
  - Example for moonlit scene: `cool blue moonlight on face, rim lighting, cyan ambient, soft shadow on cheek`

**Fix layer 2 — Add ColorMatchV2 (KJNodes):**
After the FaceDetailer, before any upscaler:
```
FaceDetailer.image → ColorMatchV2.target
VAEDecode.image    → ColorMatchV2.reference   (the pre-detailer body image as reference)
```
Settings: `method: mvgd`, `strength: 0.5`. Method `mkl` is more aggressive and can over-saturate; `mvgd` is the safe default. Strength >0.7 can introduce teal/blue cheek artifacts.

### Recipe B — Hand artifacts (wrong finger count, melted hands)

**Symptom:** hand has 4 fingers, fused fingers, hand looks like dough, fingers too long.

**The lever is denoise.** Hand detailer at low denoise (<0.5) just polishes broken anatomy. Higher denoise gives the model freedom to rebuild structure.

**Recipe — Hand FaceDetailer pass:**
Add after the face FaceDetailer (and any upscaler if one is in the pipeline):
- Node: `FaceDetailer` (Impact Pack)
- Detector: `UltralyticsDetectorProvider` with `hand_yolov8s.pt`
- Settings:
  - `denoise`: **0.50** (sweet spot — reconstructs anatomy but blends with body)
  - `cycle`: **1** (one pass — `cycle 2` over-details and invents accessories like rings/tattoos)
  - `bbox_crop_factor`: **3.5**
  - `feather`: **35**, `noise_mask_feather`: **30**
  - `guide_size`: **384** (raise to 512 only if hand is very small in frame)
  - `cfg`: **6**
  - `wildcard`: keep MINIMAL — `five_fingers, natural hand anatomy`. Avoid:
    - `slender_hand` → makes fingers too long
    - `detailed_fingernails` → over-renders, creates "transplanted" look
    - Heavy weights `(...:1.2)` → trigger invented decorations (sigils, tattoos)

**Don't go beyond 0.55 denoise** unless you also fix the source prompt — at 0.7 the rebuilt hand looks transplanted (different render fidelity than surrounding skin).

**Source-level fix (if base generation has bad hands):**
Add to base positive prompt: `(perfect hands:1.1), well-defined fingers, anatomically correct hands, five fingers`. Add to negative: `extra fingers, fused fingers, missing fingers, deformed hands`.

### Recipe C — Anti-AI sheen (waxy skin, sterile look)

**Symptom:** skin looks like polished plastic; image feels too clean; reads as "AI generated" at a glance.

This is a **stack of small wins**, not one big fix. Apply in order; stop when good.

1. **Sampler swap.** Change KSampler from `euler` / `euler_a` to **`dpmpp_2m_sde` + `karras`**. Dramatically more organic shading and microtexture. ~Same speed. This is the single biggest "less AI" lever.
2. **Add Film Grain** (WAS Suite `Image Film Grain` or equivalent):
   - `intensity`: **0.08** (>0.15 starts darkening the image visibly)
   - `protect_highlights`: **1.0** (preserve bright areas)
3. **Add Chromatic Aberration** (WAS Suite or KJNodes):
   - `intensity`: **0.2** (subtle red/cyan fringe at edges)
   - At intensity >0.4 it becomes obvious distortion — keep low.
4. **Negative prompt — anti-doll tags:** `smooth skin, plastic skin, airbrushed, doll, cgi, render, 3d, symmetric face, identical eyes`.
5. **Positive prompt — texture tags:** `detailed skin, skin texture, subsurface scattering, asymmetric eyes`.

Pipeline order:
```
... → upscaler → film_grain → chromatic_aberration → save
```
Apply post-processing AFTER upscaling, never before (upscaling re-sharpens grain into noise).

### Recipe D — Pipeline simplification

**Common antipattern:** users have a `KSamplerAdvanced` split-stage setup (e.g. steps 0-20 / 20-30 with the same model on both halves). This is the SDXL base→refiner pattern misapplied — when both halves use the same model, you're just doing a single 30-step run with extra wiring.

**Fix:** replace the two `KSamplerAdvanced` nodes (and any `PreviewBridgeLatent` between them) with a single `KSampler`:
- Steps: sum of the original two stages (e.g., 30)
- CFG: same as before (6-7 typical for Illustrious)
- Sampler/scheduler: `dpmpp_2m_sde` + `karras`
- Denoise: 1.0

Same output, simpler graph, faster iteration.

### Recipe E — Upscale path

**Antipattern:** `4x ESRGAN → full re-encode (VAEEncode) → KSampler refine → VAEDecode`. VRAM-heavy at 4x; over-sharpens; takes ~2x as long as needed.

**Fix:** swap to `UltimateSDUpscale` (custom node):
- Tiles the image, runs SD denoise per 1024² tile, re-stitches with seam fix
- VRAM-friendly: same memory footprint regardless of total image size
- Settings: `upscale_by: 2.0` (or 2.5 for wallpaper), upscale_model: `4x-AnimeSharp` for anime, `denoise: 0.2`, `tile_width: 1024`, `tile_height: 1024`, `seam_fix_mode: Half-Tile`, `seam_fix_denoise: 0.2`, `force_uniform_tiles: True`.

For non-anime / photographic styles: `4x_NMKD-Siax_200k` or `4x-foolhardy-Remacri` instead.

## Decision tree

```
Image looks AI / has issues
│
├─ Face/body skin DIFFERENT colors → Recipe A (FaceDetailer tune + ColorMatchV2)
│
├─ Hand looks broken (fingers wrong) → Recipe B (Hand FaceDetailer pass)
│   └─ Hand still broken after Recipe B → also fix source prompt
│
├─ Skin looks waxy / image feels sterile → Recipe C (sampler swap + grain + CA)
│   └─ Order: sampler first (biggest win), then grain+CA, then prompt tweaks
│
├─ Pipeline has split-stage KSamplerAdvanced → Recipe D (collapse to single KSampler)
│
├─ Upscale chain is `4x ESRGAN → re-encode → KSampler` → Recipe E (UltimateSDUpscale)
│
└─ Multiple issues → fix one at a time, verify with compare_images, then next
```

## Verification protocol (RUN THIS BEFORE DECLARING SUCCESS)

Past sessions have shown that "look at the result and summarize" is NOT enough — the user catches artifacts the agent misses, repeatedly. Before reporting back:

1. **`run_workflow()`** — queue the modified workflow.
2. **`view_file(filename)`** from output_files. Actually look at the image.
3. **Walk the failure-mode checklists** below. Don't skip — look specifically for each item, name what you see.
4. **For inpaint output specifically**, also walk the inpaint failure-mode checklist (next section).
5. **Compare directly** with `compare_images([{filename: before}, {filename: after}])` for A/B verification of changes.
6. **State explicitly what could still be wrong.** Don't say "this looks great" without naming what you checked. If you see a potential issue (mask seam, asymmetry, color drift), call it out — let the user decide if it matters. Better to flag and be wrong than miss and have the user catch it.

If the fix introduced a new artifact (common — e.g., teal cheek from over-saturated ColorMatch), tune DOWN before adding more nodes.

## Inpaint failure-mode checklist

When the workflow ends with an inpaint pass (FaceDetailer, InpaintModelConditioning, etc.), check these specifically:

| Symptom | Cause | Fix |
|---|---|---|
| **Mask seam visible** as a hard edge between regenerated and preserved areas | Mask boundary too sharp, no feather | Raise `feather` / `noise_mask_feather` on the detailer; or grow + blur mask before inpaint |
| **Phantom limb/finger at mask edge** (model invented a hand/foot/sigil) | Mask was too generous OR prompt too vague — model hallucinated to fill an ambiguous shape | Tighten mask. Add explicit negative for the hallucinated thing (e.g., `(extra hand, sigil, tattoo:1.2)`). Drop denoise. |
| **"Two halves"** — anatomical break mid-limb where mask sliced through | Mask cut through the middle of an anatomically continuous region | For limbs: use keypoint polyline masks (see `comfyui-mask-strategy` skill). For arbitrary shapes: hand-paint or grow mask to include the whole region. |
| **Disconnected joint** (wrist not joining forearm, head floating off shoulders) | Mask covered one connected element but not the other (e.g., face but not the hand touching chin) | Expand mask to include both, OR combine two detectors (`face_yolov8m` + `hand_yolov8s` → `ImpactSEGSConcat` → `SegsToCombinedMask`). |
| **Transplanted feature** — face/hand crisp but body softer | Detailer denoise too high (>0.55), creating a render-fidelity seam | Drop denoise to 0.5; reduce `cycle` from 2 to 1 |
| **Color/material mismatch** between inpainted and surrounding region | No color match step after inpaint | Add `ColorMatchV2` (KJNodes) with pre-inpaint image as reference, method `mvgd`, strength 0.5 |
| **Lost details in adjacent areas** (chest armor changed, bracer trim disappeared) | Mask grew too large, included regions you wanted preserved | Shrink mask. Use a more precise mask source (keypoint or paint instead of generous CLIPSeg). |
| **Naked patch in the middle of a clothing inpaint** (e.g., bare elbow under a sleeve mask) | CLIPSeg threshold too high; gap in mask | Drop threshold by 0.05-0.1, OR enable `fill_holes: true` on `GrowMaskWithBlur` |
| **Inpaint pass unchanged the region** | Denoise too low (<0.3) | Raise denoise to 0.5+ for actual rebuild; use 0.3 only for "polish" passes |

## Iteration discipline

- **Each inpaint pass is destructive inside the mask.** Iterating with different mask parameters gives N different broken outputs because the mask boundary jitters between runs. The fix is usually to *change strategies* (e.g., CLIPSeg → keypoint → manual paint), not to re-tune the same one.
- **Preview the mask before running the inpaint.** Wire mask output → `MaskToImage` → `PreviewImage` and check it BEFORE spending compute on a full inpaint pass. Most "bad inpaint" results are actually "bad mask" diagnosed too late.
- **When auto-masking fails twice on the same region, recommend manual mask painting.** It's not a failure of the agent to ask for human judgment on where to draw a boundary. The user can paint a mask in ComfyUI's MaskEditor in 30 seconds; the agent might burn 5 inpaint runs guessing CLIPSeg parameters.

## Escalation paths (when recipes aren't enough)

These are pointers, not full recipes — propose to the user before wiring up:

- **ControlNet** for pose/anatomy control. Useful when hands are consistently broken across many seeds and detailers can't save them. Common preprocessors: `openpose` (full body pose), `dwpose` (hand pose specifically), `depth` (3D structure). User has `comfyui_controlnet_aux` installed.
- **IPAdapter** for character/style consistency across runs. If the user wants the same character in multiple poses.
- **InpaintingForEach / Manual mask** for specific region rework when YOLO detectors miss the target area.
- **Different base model.** Some issues are model-level: if Illustrious consistently breaks hands for the user's prompt style, suggest trying NoobAI, Hassaku, or a checkpoint with stronger anatomy training.
- **Higher resolution generation** (e.g. 1024×1536 base) instead of 832×1216 + heavy upscaling. More tokens, more compute, but anatomy comes out cleaner.

## Common pitfalls (learned from real iteration)

- **Over-aggressive ColorMatch** (`strength: 0.7+` with `mkl`) → teal/blue blotches in face highlights. Drop to `mvgd` + `0.5`.
- **High denoise + cycle 2 on hand detailer** → "transplanted" hand (different fidelity than body) AND invents accessories (rings, sigils, tattoos). Stay at `denoise: 0.5, cycle: 1`.
- **Heavy prompt weights `(:1.2)+` on detailer wildcards** → invented decorations the user didn't ask for.
- **Setting upscale_by but it doesn't take effect on next run** — UI cache race. After `set_widget`, immediately `run_workflow` from the no-args form (it pulls fresh state through the bridge); don't pass an old workflow dict.
- **Different sampler = different denoising path even at same seed.** Switching `euler_a` → `dpmpp_2m_sde` will change colors/composition. If you want to A/B compare ONLY the sampler change, lock all other variables and tell the user the composition will shift.

## Tools you'll use most

- `view_file(filename)` — see the output image inline
- `compare_images([{filename: a}, {filename: b}])` — side-by-side A/B
- `describe_graph()` — token-cheap structural overview of current workflow
- `get_node_widgets(node_id)` — read one node's settings
- `set_widget(node_id, name, value)` — change one widget
- `add_node(class_type, x, y, widget_values)` — add a new node (e.g., FaceDetailer, ColorMatchV2)
- `connect_many([...])` — wire many connections in one round-trip
- `run_workflow()` — queue + wait for the open tab's workflow

## Final pre-flight checklist before declaring "done"

- [ ] Face skin tone matches body skin tone within the scene's color cast
- [ ] Both hands have correct finger count (5 visible from current angle, or correctly occluded)
- [ ] Eyes have slight asymmetry (real faces aren't perfectly symmetric)
- [ ] Skin has visible texture variation, not airbrushed gradient
- [ ] Background has atmospheric character (depth, atmosphere, not "render asset")
- [ ] No obvious sampler artifacts (banding, halos, oversharpened edges)
- [ ] Grain/CA is subtle, only visible on close inspection
- [ ] Composition matches the user's intent (color/style hasn't drifted from request)
