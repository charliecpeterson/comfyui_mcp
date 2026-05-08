---
name: comfyui-mask-strategy
description: Decide HOW to build a mask before running an inpaint pass. Use when the user wants to inpaint, mask, or regenerate a region of an image, OR when an inpaint failed (mask seam visible, hallucinated body parts, two-halves anatomy). The wrong mask source guarantees a wrong inpaint; this skill picks the right tool for the region BEFORE wiring up nodes.
---

# ComfyUI Mask Strategy Skill

You are picking how to build a mask for an inpainting workflow. The single biggest source of bad inpaint results is reaching for the wrong mask source — usually CLIPSeg-first because it's easy to wire, even when a better tool is right there. This skill exists to short-circuit that instinct.

## The decision table

| Region the user wants masked | Best strategy | Why |
|---|---|---|
| **Face** (1-2 of them) | `face_yolov8m.pt` via `UltralyticsDetectorProvider` → `BboxDetectorSEGS` | Pre-trained, single-shot, deterministic. Converges in 1 pass. |
| **Hands** (1-2) | `hand_yolov8s.pt` via same chain | Same as faces. |
| **Eyes alone** | `Eyeful_v2-Paired.pt` (or face detector + manual crop) | Dedicated bbox model, highest precision. |
| **Multiple of the above in one pass** | Two detectors → `ImpactSEGSConcat` → `SegsToCombinedMask` → grow/blur | Both regions share an inpaint, anatomy stays consistent across them. |
| **Limbs (arms, legs, neck)** | DWPose keypoints → polyline-thickness mask drawn programmatically (Bash + PIL) | Limbs follow keypoint axes; YOLO doesn't have them, CLIPSeg drifts. |
| **Body parts with semantic names** ("hair", "armor", "shadow", "background") | `BatchCLIPSeg` text-prompted segmentation, threshold ~0.3-0.5 | Right tool for vague concepts. **Expect 2-3 iterations.** |
| **Anything you can identify by clicking** | Manual paint via ComfyUI's MaskEditor on a `LoadImage` node | Fastest, most precise, agent can't drive it but USER can. |
| **Specific geometric shape** (tight rectangle, circle, polygon at known coords) | Bash + PIL: draw shape, save PNG, `LoadImage` + `ImageToMask` | When you have coordinates from another step. |

## Decision tree

```
What region needs masking?
│
├─ Face / hand / pre-trained category   →  YOLO bbox detector (1 pass, done)
│
├─ Multiple of the above                 →  YOLO ×N + ImpactSEGSConcat + SegsToCombinedMask
│
├─ Limb (arm, leg, neck)                 →  DWPose keypoints → polyline mask (see "Keypoint masks" below)
│
├─ Vague semantic concept               →  CLIPSeg, BUT preview the mask first.
│   ("hair", "background", "armor")        Be ready to iterate threshold + expand.
│
├─ Specific shape / known coordinates    →  Programmatic PIL draw → ImageToMask
│
└─ User can point at it                  →  Manual paint in MaskEditor (delegate to user)
```

## Keypoint masks (pose → polyline)

When the user asks for a limb mask and you have a pose-conditioned image (or can run DWPose on it):

1. Run `DWPreprocessor` or `OpenposePreprocessor` on the source image to get keypoints. Output is JSON-like: `{people: [{pose_keypoints_2d: [...]}]}`. Coordinates are normalized — you'll need image dimensions.
2. The 18 OpenPose keypoint indices (most common subset):
   - 2 = right shoulder, 3 = right elbow, 4 = right wrist
   - 5 = left shoulder, 6 = left elbow, 7 = left wrist
   - 8 = right hip, 9 = right knee, 10 = right ankle
   - 11 = left hip, 12 = left knee, 13 = left ankle
3. For each limb, draw a thick polyline along the bones using PIL:
   ```python
   from PIL import Image, ImageDraw
   img = Image.new("L", (W, H), 0)
   draw = ImageDraw.Draw(img)
   draw.line([(shoulder_x, shoulder_y), (elbow_x, elbow_y), (wrist_x, wrist_y)],
             fill=255, width=80, joint="curve")
   img.save("/path/to/comfyui/input/arm_mask.png")
   ```
4. Save PNG into ComfyUI's input/ folder (or use a temp path + `LoadImage` if accessible).
5. In the workflow: `LoadImage` (mask file) → `ImageToMask` (channel: red) → `GrowMaskWithBlur` (expand 5-10, blur 6-12) → `InpaintModelConditioning`.

**Width tuning:** ~60-100px for arms in a 1024-tall image. Multiply by image scale. Constant width along the bone is fine for a first pass; taper later if needed.

**Common gotcha:** if the source image was masked/clipspaced before being passed to DWPose, the body detector returns `{people: []}`. Fall back to keypoints from an unmasked copy of the image.

## CLIPSeg pitfalls (read before reaching for it)

CLIPSeg is *attractive* (one node, takes a text prompt) but **noisy** for body anatomy:

- Prompts pull semantically related regions in. "biceps, triceps" pulled the chest into a sleeve mask in one validated session — chest has the muscle-definition cues the model learned.
- Threshold is fragile. Below 0.3 picks up too much; above 0.5 leaves gaps. The right value drifts per image.
- Each inpaint pass is destructive — iterating CLIPSeg gives you THREE different broken outputs because the boundary jitters between runs.

**If CLIPSeg is genuinely the right tool** (the region is vague and semantic, and no detector exists):
1. Always preview the mask BEFORE running the inpaint. Wire `BatchCLIPSeg` → `MaskToImage` → `PreviewImage`. Run that branch alone first.
2. Tune threshold in 0.05 increments based on the preview, not based on the inpaint result.
3. Use simple, anatomically-distinct prompts: `"bare skin upper arms"` — not `"biceps, triceps, deltoids, forearms"` (the latter brings adjacent muscle groups in).
4. `expand` on `GrowMaskWithBlur`: small (5-15) to keep tight boundaries; large (30-50) bridges gaps but starts capturing adjacent regions.

## Mask-batch vs mask gotcha

`ImpactSEGSToMaskBatch` outputs a **batch** of masks (one per detected SEG). When you have multiple detections (e.g., face detector finds 1 face but hand detector finds 2 hands → 3 SEGs total), the downstream node may expect a single MASK and silently fail with shape errors.

**Fix:** use `SegsToCombinedMask` (Impact Pack) — combines all SEGS into one union mask. Required when you `ImpactSEGSConcat` two detectors together.

## Inpaint failure modes (and which mask change fixes them)

| What you see in the output | Mask issue | Fix |
|---|---|---|
| Inpaint region looks crisp; surrounding body looks softer | Mask is right; **denoise too high inside it** (>0.6) — drop to 0.5 |
| "Two halves" — anatomical break mid-limb | Mask sliced through the middle of the limb. Grow expand or use keypoint-line mask that follows the bone. |
| Phantom hand/finger at the mask edge | Model hallucinated to fill an ambiguous shape. Mask was too generous OR prompt too vague. Tighten mask, add explicit negative prompt for the hallucinated thing. |
| Disconnected joint (wrist not joining forearm) | Mask covered face+chin but not the hand that touches the chin. Expand mask to include both, OR use combined-detector mask (face + hand). |
| Color mismatch between inpainted region and rest | Mask is right; missing color match step. Add `ColorMatchV2` (KJNodes) AFTER the inpaint, with the pre-inpaint image as reference. |
| Naked elbow / strip of skin in the middle of a clothing inpaint | CLIPSeg threshold too high; gap in the middle of a roughly-correct mask. Drop threshold by 0.05-0.1 OR add `fill_holes: true` on `GrowMaskWithBlur`. |
| Region you wanted preserved got changed | Mask included it. View `MaskToImage` preview on the pre-inpaint mask BEFORE running. |

## Verification protocol — RUN BEFORE DECLARING SUCCESS

Past sessions have shown that "look at the result and report" is not enough — the user catches artifacts the agent misses. Before reporting back to the user:

1. **`view_file` the generated image** — actually look at it.
2. **Walk the failure-mode checklist above.** For each row, check whether you see it.
3. **`view_file` the mask preview separately** if the result looks weird. The mask explains 80% of inpaint failures.
4. **For limbs/anatomy specifically**, count fingers, trace each limb from shoulder/hip to extremity, look for:
   - Joints that don't connect
   - Hands the model invented at mask edges
   - Two halves of a limb at slightly different fidelities (transplant look)
5. **State explicitly what could still be wrong.** Don't summarize "this looks great" — say "the right arm is clean; left elbow has a small skin patch where the mask had a gap; if it bothers you, fix is X."

## When to recommend manual painting

Auto-masking has a ceiling. After 2 failed CLIPSeg or keypoint attempts, recommend the user paint a mask in ComfyUI's MaskEditor:

1. Right-click the `LoadImage` node showing the source image.
2. Click "Open in MaskEditor".
3. Paint the regions you want regenerated. Use brush + eraser. Save.
4. Wire `LoadImage.MASK` (the alpha channel from MaskEditor) into the inpaint pipeline, replacing the auto-detector chain.

This converges in 1 pass with the user's exact judgment, instead of N passes guessing thresholds. Don't be shy about recommending it — it's not a failure to ask for human input on a fundamentally human task (where to draw the boundary).

## Skills to layer with this one

- **comfyui-image-quality** — once the mask is right, that skill handles the actual inpaint settings (denoise, prompts, post-processing).
- **prompt-illustrious** / **prompt-flux** / etc — the prompt for the inpaint pass should follow the same conventions as the base model.

## Pre-flight before any inpaint attempt

```
list_models("controlnet")           # if pose-conditioned source is needed
search_nodes("UltralyticsDetector") # YOLO bbox path
search_nodes("CLIPSeg")             # text-prompted segmentation
search_nodes("InpaintModelConditioning")  # the inpaint conditioner
search_nodes("MaskEditor")          # availability of paint UI
```

Confirm the nodes you intend to use exist in this ComfyUI install BEFORE wiring them up. The `add_node` tool now validates class_type and suggests fixes, but the pre-flight catches gaps earlier and saves a round-trip.
