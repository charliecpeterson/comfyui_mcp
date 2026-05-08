---
name: comfyui-pose-editing
description: Extract, edit, and synthesize OpenPose skeletons for ControlNet conditioning. Use when the user wants a unique/custom pose, wants to modify a pose extracted from a reference image, or wants to escape the "AI default poses" attractor by feeding ControlNet a hand-tuned skeleton. Covers the extract → modify → render → ControlNet pipeline with concrete coordinates and PIL recipes.
---

# ComfyUI Pose Editing Skill

You are helping the user produce a custom OpenPose skeleton image to feed into a ControlNet OpenPose conditioning pass. This is the *most reliable* way to break out of the cliché-pose attractor that danbooru-tag fine-tunes (Pony, Illustrious) fall back to — the model can't render `dynamic_pose` cleanly, but it WILL follow a hand-tuned skeleton from ControlNet.

The workflow is always: **extract numerical keypoints → modify them in Python → render the skeleton image → feed it to ControlNet OpenPose in the generation workflow.**

## Required nodes (verify with `search_nodes` first)

- `DWPreprocessor` (preferred) or `OpenposePreprocessor` — outputs `IMAGE` + `POSE_KEYPOINT`
- `SavePoseKpsAsJsonFile` — writes keypoints to disk as JSON
- `LoadImage` — for loading the rendered skeleton back into the generation workflow
- A ControlNet OpenPose model (e.g., `control_v11p_sd15_openpose`, `noob-sdxl/openpose_pre`) loaded via `ControlNetLoader` + `ControlNetApplyAdvanced`

If `SavePoseKpsAsJsonFile` is not installed, the `extract_pose_keypoints` MCP tool won't work — you'll need to wire the workflow manually and read the JSON via Read tool, or fall back to the keypoint-polyline-mask recipe in `comfyui-mask-strategy`.

## The MCP tools

- **`extract_pose_keypoints(image_filename, preprocessor="DWPreprocessor")`** — runs the full extract workflow headlessly, returns `{keypoints: {...}, skeleton_image: {filename, ...}}`. The image must be in ComfyUI's `input/` folder; use `upload_input` or `copy_to_input` first if needed.
- **`render_pose_skeleton(keypoints, width, height, save_as)`** — PIL renders a keypoints dict to a colored skeleton image, saves to `input/`. Auto-detects normalized (0-1) vs pixel-space coords.

The agent's job between those two calls is to **modify the keypoints** in Python. There's no "edit_pose" tool by design — the modifications are too varied (rotations, mirrors, presets, retargeting). Use Bash + Python.

## OpenPose 18-keypoint index reference

The DWPose / OpenPose preprocessor returns `pose_keypoints_2d` as a flat list `[x1, y1, c1, x2, y2, c2, ...]` — 3 values per joint, in this order:

| Idx | Joint | | Idx | Joint |
|---|---|---|---|---|
| 0 | nose | | 9 | r_knee |
| 1 | neck | | 10 | r_ankle |
| 2 | r_shoulder | | 11 | l_hip |
| 3 | r_elbow | | 12 | l_knee |
| 4 | r_wrist | | 13 | l_ankle |
| 5 | l_shoulder | | 14 | r_eye |
| 6 | l_elbow | | 15 | l_eye |
| 7 | l_wrist | | 16 | r_ear |
| 8 | r_hip | | 17 | l_ear |

(`r_` = right side of the *subject*, which is on the *viewer's left* in a frontal image. Don't get confused.)

Confidence (`c`) is in [0, 1]. Joints with `c < 0.05` are typically considered "not detected" — `render_pose_skeleton` skips them.

Hands have 21 keypoints each (`hand_left_keypoints_2d`, `hand_right_keypoints_2d`); face has 70 (`face_keypoints_2d`). For ControlNet OpenPose, body keypoints alone are usually enough.

## Recipe A — Modify a pose from a reference image

User has a reference photo / existing output and wants the same pose with different content.

```
1. upload_input(reference_path) [if not already in input/]
   └─ or copy_to_input(filename, source_type="output") if it's a previous output
2. extract_pose_keypoints(image_filename)
   ├─ returns: {keypoints: {people: [{pose_keypoints_2d: [...]}], canvas_width, canvas_height},
   │           skeleton_image: {filename, ...}}
   └─ view the skeleton_image to verify pose was detected correctly
3. [Python in Bash] modify the keypoints — examples below
4. render_pose_skeleton(modified_keypoints, save_as="custom_pose.png")
   └─ saves to ComfyUI/input/custom_pose.png
5. Build/modify the generation workflow:
     LoadImage(custom_pose.png) → ControlNetApplyAdvanced.image
     ControlNetLoader(openpose_model) → ControlNetApplyAdvanced.control_net
     existing CLIPTextEncode → ControlNetApplyAdvanced.positive/negative
     route apply.positive/negative into KSampler
6. run_workflow → compare to verify the new generation follows the modified skeleton
```

## Recipe B — Build a pose from scratch

User wants a specific pose with no reference image. Construct the keypoints in Python.

```python
# Approximate "leaning forward, hand on chin" pose at 832×1216
pose_keypoints_2d = [
    416, 200, 1.0,    # 0: nose
    416, 280, 1.0,    # 1: neck
    340, 290, 1.0,    # 2: r_shoulder
    320, 380, 1.0,    # 3: r_elbow
    400, 250, 1.0,    # 4: r_wrist  (touching chin)
    492, 290, 1.0,    # 5: l_shoulder
    540, 400, 1.0,    # 6: l_elbow
    560, 500, 1.0,    # 7: l_wrist
    370, 520, 1.0,    # 8: r_hip
    360, 720, 1.0,    # 9: r_knee
    350, 920, 1.0,    # 10: r_ankle
    462, 520, 1.0,    # 11: l_hip
    470, 720, 1.0,    # 12: l_knee
    480, 920, 1.0,    # 13: l_ankle
    400, 192, 1.0,    # 14: r_eye
    432, 192, 1.0,    # 15: l_eye
    386, 200, 0.5,    # 16: r_ear  (low confidence — partially occluded)
    446, 200, 0.5,    # 17: l_ear
]
keypoints = {
    "people": [{"pose_keypoints_2d": pose_keypoints_2d}],
    "canvas_width": 832, "canvas_height": 1216
}
```

Then `render_pose_skeleton(keypoints, save_as="leaning_pose.png")`.

## Common modifications (Python recipes)

All examples assume `kps = extract_result["keypoints"]` and we're editing the first person.

### Lift left arm

```python
body = kps["people"][0]["pose_keypoints_2d"]
# Move l_shoulder→l_elbow→l_wrist upward by 200 px
for joint_idx in (5, 6, 7):
    body[joint_idx*3 + 1] -= 200  # subtract from y to go up
```

### Mirror horizontally (flip left/right)

```python
body = kps["people"][0]["pose_keypoints_2d"]
W = kps.get("canvas_width", 1024)
for i in range(0, len(body), 3):
    body[i] = W - body[i]  # flip x
# Then swap left/right joint labels for symmetry
swap_pairs = [(2, 5), (3, 6), (4, 7), (8, 11), (9, 12), (10, 13), (14, 15), (16, 17)]
for a, b in swap_pairs:
    for off in (0, 1, 2):
        body[a*3 + off], body[b*3 + off] = body[b*3 + off], body[a*3 + off]
```

### Rotate the right arm at the shoulder by 45°

```python
import math
body = kps["people"][0]["pose_keypoints_2d"]
shoulder = (body[2*3], body[2*3 + 1])           # r_shoulder pivot
angle = math.radians(45)                         # +ve = clockwise on screen
cos_a, sin_a = math.cos(angle), math.sin(angle)
for joint_idx in (3, 4):                         # r_elbow, r_wrist
    px = body[joint_idx*3] - shoulder[0]
    py = body[joint_idx*3 + 1] - shoulder[1]
    body[joint_idx*3] = shoulder[0] + px * cos_a - py * sin_a
    body[joint_idx*3 + 1] = shoulder[1] + px * sin_a + py * cos_a
```

### Translate the whole figure (shift x, y)

```python
body = kps["people"][0]["pose_keypoints_2d"]
dx, dy = 100, -50
for i in range(0, len(body), 3):
    body[i] += dx
    body[i + 1] += dy
```

### Scale the figure around its centroid

```python
body = kps["people"][0]["pose_keypoints_2d"]
scale = 0.85
xs = [body[i] for i in range(0, len(body), 3)]
ys = [body[i + 1] for i in range(1, len(body), 3)]
cx = sum(xs) / len(xs)
cy = sum(ys) / len(ys)
for i in range(0, len(body), 3):
    body[i] = cx + (body[i] - cx) * scale
    body[i + 1] = cy + (body[i + 1] - cy) * scale
```

### Add a second person (combine two extracted poses)

```python
person_a = extract_a["keypoints"]["people"][0]
person_b = extract_b["keypoints"]["people"][0]
combined = {
    "people": [person_a, person_b],
    "canvas_width": extract_a["keypoints"]["canvas_width"],
    "canvas_height": extract_a["keypoints"]["canvas_height"],
}
render_pose_skeleton(combined, save_as="duo_pose.png")
```

### Strip face/hands (use body only)

ControlNet OpenPose with body-only conditioning often gives looser, more creative results than full-body+face+hands. To strip:

```python
for person in kps["people"]:
    person.pop("face_keypoints_2d", None)
    person.pop("hand_left_keypoints_2d", None)
    person.pop("hand_right_keypoints_2d", None)
```

## ControlNet OpenPose connection topology

After you've rendered the skeleton, here's the wiring to add to a generation workflow:

```
LoadImage(skeleton.png)  ────────┐
                                 ▼
                    ControlNetApplyAdvanced
                       ├─ image: skeleton
                       ├─ control_net: ControlNetLoader(openpose_model)
                       ├─ positive: existing CLIPTextEncode (positive)
                       └─ negative: existing CLIPTextEncode (negative)
                                 │
                                 ▼  positive/negative outputs
                              KSampler.positive / KSampler.negative
                                  (replace the original CLIPTextEncode→KSampler wires)
```

`ControlNetApplyAdvanced` has `strength` (try 0.6–0.8) and `start_percent`/`end_percent` (default 0.0/1.0 = full range). For a stronger pose lock, raise strength to 0.9; for more creative interpretation, drop to 0.5.

## Pitfalls (from real sessions)

- **DWPose returns `people: []`** on some inputs. Causes seen:
  - Image was masked/clipspaced (alpha channel confuses the body detector). Use a clean, unmasked source.
  - Pose is highly stylized (chibi proportions, extreme camera angles). Try `OpenposePreprocessor` as a fallback.
  - Body is too small in frame (preprocessor downsamples to 512px internally). Crop tighter to the figure first.
- **Coordinate system gotcha.** OpenPose y increases downward. To "raise an arm," subtract from y, don't add. Subject's `r_` = viewer's left.
- **Normalized vs pixel space.** Most DWPose configs return pixel-space coordinates, but some setups normalize to 0-1. `render_pose_skeleton` auto-detects (max value ≤ 1.5 → treated as normalized). If you're modifying coordinates manually, check the format first.
- **Confidence below threshold = not rendered.** If you set a joint's coordinates but leave its confidence at 0, it won't draw. Set `c = 1.0` for joints you've manually placed.
- **ControlNet strength + tag conflicts.** If your prompt has strong pose tags (`from_below`, `arched_back`) AND the skeleton contradicts them, results are muddled. Either match the tags to the skeleton, or drop the explicit pose tags from the prompt.
- **Subgraph workflows.** If your generation workflow uses subgraphs (like the zimage one), insert the ControlNet inside the subgraph definition or before the subgraph instance, depending on where conditioning enters.

## Verification protocol

After rendering:

1. `view_file(skeleton_filename, type="input")` — visually confirm the skeleton looks like the pose you intended. The render is fast; iterate here, NOT after a full generation run.
2. Once skeleton looks right, run the full generation workflow with ControlNet wired in.
3. Compare result to the skeleton with `compare_images([{filename: skeleton, type: "input"}, {filename: gen_output}])` to verify the pose was followed.
4. If the result drifts from the skeleton, raise ControlNet strength (or check that the LoadImage actually points at your saved skeleton, not an old cached one).

## Skills to layer with this one

- **`comfyui-mask-strategy`** — pose keypoints can drive limb-mask creation (polyline along the bones). Cross-pollinates with this skill.
- **`comfyui-image-quality`** — once the pose is right, image-quality recipes apply normally.
- **`prompt-illustrious`** / **`prompt-flux`** — the prompt should match the model's conventions; the pose comes from ControlNet, the style from the prompt.

## Pre-flight before starting

```
search_nodes("DWPreprocessor")
search_nodes("SavePoseKpsAsJsonFile")
list_models("controlnet")        # confirm an openpose-compatible ControlNet model exists
list_custom_nodes | grep -i pose # any pose-related custom nodes
```

If any are missing, fall back to manual workflow wiring (the user can install the missing node via ComfyUI Manager).
