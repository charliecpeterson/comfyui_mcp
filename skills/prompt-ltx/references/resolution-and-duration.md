# Resolution and Duration Constraints for LTX

LTX has stricter mathematical constraints on resolution and frame count than most video models. Violating these doesn't produce a hard error — the pipeline pads and crops your input silently — but it wastes generation time on a fundamentally compromised result.

This reference catalogues the constraints and the valid configurations to use.

## The hard rules

1. **Pixel dimensions must be divisible by 32.**
2. **Frame count must be divisible by 8, plus 1.** (e.g., 9, 17, 25, 33, ..., 257)
3. **Duration is discrete on LTX-2 / 2.3:** 2, 3, 4, 5, 6, 7, 8, 9, or 10 seconds.

If you give LTX a non-conforming resolution or frame count, the pipeline pads to the nearest valid size with `-1` placeholder values, then crops back to the requested dimensions. This usually produces a degraded result with visible artifacts at the boundary.

## Why these constraints exist

The divisible-by-32 rule comes from the VAE downsampling factor. Each pass through the VAE encoder reduces dimensions by a factor of 8 spatially; multiple passes compound. 32 is the minimum dimension the VAE can handle without information loss.

The frame-count rule is similar: the temporal compression factor is 8, and the +1 accounts for the first/key frame. So valid counts are 8n+1.

## Valid resolutions

### Square (1:1)

| Resolution | Use case |
|---|---|
| 512×512 | Drafts, prototyping (LTX Video 2B era) |
| 768×768 | Standard quality, modest VRAM |
| 1024×1024 | High quality, social media (Instagram-style) |
| 1280×1280 | LTX-2.3 high res square |

### Widescreen (16:9)

| Resolution | Use case |
|---|---|
| 768×448 | LTX Video older variant |
| 1024×576 | Drafts |
| 1216×704 | LTX-2.3 production (LTX team's recommended) |
| 1280×704 | Slightly wider 16:9 |
| 1600×896 | High-quality intermediate |
| **1920×1088** | LTX-2.3 final / upscaled (NOT 1920×1080 — 1080 is not divisible by 32) |

### Cinematic / ultrawide (21:9)

| Resolution | Use case |
|---|---|
| 1344×576 | LTX-2 ultrawide |
| 1920×832 | LTX-2.3 cinematic |
| 2240×960 | Very wide, large output |

### Vertical (9:16 — Reels, TikTok, Stories)

| Resolution | Use case |
|---|---|
| 448×768 | Drafts |
| 576×1024 | Standard vertical |
| 704×1216 | LTX-2.3 production vertical |
| 1088×1920 | LTX-2.3 final vertical |

### Portrait (3:4)

| Resolution | Use case |
|---|---|
| 576×768 | Portraits, headshots |
| 768×1024 | Standard portrait |
| 960×1280 | High-quality portrait |

### Traditional (4:3)

| Resolution | Use case |
|---|---|
| 768×576 | Retro / TV-style |
| 1024×768 | Standard 4:3 |
| 1280×960 | High-quality 4:3 |

## What about 1080p, 720p, 4K standard resolutions?

LTX's constraints mean some common resolutions aren't directly supported:

- **1920×1080 (Full HD):** 1080 is NOT divisible by 32 (1080/32 = 33.75). Use 1920×1088 instead — pad the result to 1080 in post if needed.
- **3840×2160 (4K UHD):** Both dimensions ARE divisible by 32 (3840/32=120, 2160 — wait, 2160/32=67.5, so 2160 is NOT divisible by 32). Use 3840×2176 or 3840×2144 instead.
- **1280×720 (720p):** 720 is NOT divisible by 32 (720/32=22.5). Use 1280×704 or 1280×736 instead.

The LTX team specifically calls out this gotcha in their NVIDIA collaboration docs: *"LTX needs pixel dimensions divisible by 32, hence abnormal resolutions like 704 and 1088."*

## Valid frame counts

Frame counts must be of the form 8n+1: **9, 17, 25, 33, 41, 49, 57, 65, 73, 81, 89, 97, 105, 113, 121, 129, 137, 145, 153, 161, 169, 177, 185, 193, 201, 209, 217, 225, 233, 241, 249, 257.**

LTX recommends staying at or below **257 frames** in a single generation for best results.

## Duration → frame count

LTX-2 supports discrete durations of 2–10 seconds. Frame counts depend on FPS:

### At 24fps (cinematic)

| Duration | Approximate frames | Valid LTX frame count |
|---|---|---|
| 2 sec | 48 | **49** |
| 3 sec | 72 | **73** |
| 4 sec | 96 | **97** |
| 5 sec | 120 | **121** |
| 6 sec | 144 | **145** |
| 7 sec | 168 | **169** |
| 8 sec | 192 | **193** |
| 9 sec | 216 | **217** |
| 10 sec | 240 | **241** |

### At 30fps

| Duration | Approximate frames | Valid LTX frame count |
|---|---|---|
| 2 sec | 60 | **57 or 65** (closest valid) |
| 3 sec | 90 | **89 or 97** |
| 4 sec | 120 | **121** |
| 5 sec | 150 | **145 or 153** |
| 6 sec | 180 | **177 or 185** |

### At 50fps (LTX-2.3 native)

| Duration | Approximate frames | Valid LTX frame count |
|---|---|---|
| 2 sec | 100 | **97 or 105** |
| 3 sec | 150 | **153** |
| 4 sec | 200 | **201** |
| 5 sec | 250 | **249 or 257** |

The pipelines handle the duration→frame conversion internally — you typically specify duration in seconds and the system rounds to the nearest valid frame count.

## Recommended starting configurations by use case

### Quick draft / iteration

- **Resolution:** 768×448 (16:9) or 768×768 (1:1)
- **Duration:** 3–5 sec
- **FPS:** 24
- **Pipeline:** `DistilledPipeline` (8+4 steps)

### Production quality (general)

- **Resolution:** 1216×704 (16:9) or 1024×1024 (1:1)
- **Duration:** 5–8 sec
- **FPS:** 24
- **Pipeline:** `TI2VidTwoStagesPipeline`

### High-end final (LTX-2.3)

- **Resolution:** 1920×1088 (16:9) or 1280×1280 (1:1)
- **Duration:** 5–10 sec
- **FPS:** 24 or 50
- **Pipeline:** `TI2VidTwoStagesHQPipeline`

### Vertical social (TikTok / Reels)

- **Resolution:** 704×1216 (9:16)
- **Duration:** 5–10 sec
- **FPS:** 24 or 30
- **Pipeline:** `TI2VidTwoStagesPipeline`

### Cinematic ultrawide

- **Resolution:** 1920×832 (21:9)
- **Duration:** 8–10 sec
- **FPS:** 24
- **Pipeline:** `TI2VidTwoStagesHQPipeline`

## Common mistakes

### Requesting "1080p" or "Full HD"

LTX can't produce exact 1920×1080. Either use 1920×1088 and pad in post, or 1920×832 for the cinematic 21:9 close to 1080-tall.

### Requesting "60 fps"

Common workflows assume 60fps cinema, but LTX-2.3's native high-fps is 50fps. Use 50fps for "cinematic high frame rate" and either 24fps or 30fps for everything else.

### Requesting exactly 5 seconds at 30fps

5×30=150 frames; not divisible by 8+1 (the closest are 145 and 153). The pipeline will round. If exact timing matters, use 24fps (5×24=120, nearest is 121) for less drift.

### Requesting unusual aspect ratios

LTX-2 officially supports 1:1, 4:3, 16:9, 21:9, 9:16, 3:4. Other aspects (like 2.39:1 anamorphic) aren't officially supported but can be approximated — find the closest supported aspect and crop in post.

### Generating at high res for drafts

A 1920×1088 draft is wasted GPU time. Generate drafts at 768×448 or 1216×704 to iterate quickly, then re-generate the keeper at full resolution.

## Quick lookup

When the user requests a specific resolution that doesn't conform:

| Requested | Use instead |
|---|---|
| 1920×1080 | 1920×1088 |
| 1280×720 | 1280×704 |
| 3840×2160 | 3840×2176 |
| 1080×1920 | 1088×1920 |
| 720×1280 | 704×1280 |
| 1080×1080 | 1088×1088 |

When the user requests an arbitrary resolution, round each dimension to the nearest multiple of 32. If the result is more than 5% off from the original, note this to the user.
