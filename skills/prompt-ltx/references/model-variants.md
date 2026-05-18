# LTX Model Variants Reference

The LTX family from Lightricks has evolved rapidly from a 2B baseline in late 2024 to a 22B SOTA model in 2026. This file catalogues each variant, its capabilities, and which to recommend for a given task.

All LTX models are **open-source** with permissive licensing for most uses.

---

## LTX Video (original, 2B)

The baseline that started the family. Released November 2024.

- **Released:** November 2024
- **Parameters:** 2B
- **Architecture:** DiT (Diffusion Transformer)
- **Modes:** T2V, I2V
- **Resolution:** 768×512 native (older docs reference this — LTX-2+ raised the bar significantly)
- **FPS:** 24
- **Duration:** ~5 seconds
- **VRAM:** 12GB+ recommended (runs on consumer hardware)
- **Audio:** No — purely silent video
- **Strengths:** Fast — first model to generate video clips faster than playback duration; Apache 2.0 friendly licensing
- **Weaknesses:** Lower visual quality vs later versions; no audio; modest resolution
- **Best for:** Legacy workflows, fast iteration, very constrained hardware
- **Prompting tips:** Follow the official 7-component structure but keep prompts shorter (under 100 words). Negative prompts work normally.

---

## LTXV-13B

Larger variant released May 2025. Major quality jump from 2B.

- **Released:** May 2025
- **Parameters:** 13B
- **Architecture:** DiT, scaled-up version of LTX Video
- **Modes:** T2V, I2V
- **Resolution:** Up to 1024×1024 / 1216×704
- **Duration:** Broke the 60-second barrier — first LTX to support extended clips
- **VRAM:** 24GB+ recommended
- **Audio:** No — still silent video
- **Strengths:** Significantly better visual quality than 2B; supports long-form clips (60s+); strong i2v
- **Weaknesses:** Heavier VRAM requirements; still no audio
- **Best for:** Long-form video generation, high-quality silent video, narrative sequences
- **Prompting tips:** Full 7-component structure works well. For long clips, build multiple "beats" into the prompt (component 7 — changes/events).

---

## LTX-2 (current main release)

The major release that introduced audio. Released October 2025.

- **Released:** October 2025 (open-source release January 2026)
- **Parameters:** Multi-stage architecture, ~13-19B effective
- **Architecture:** DiT-based audio-video foundation model — first open-source model with native audio+video
- **Modes:** T2V (with audio), I2V (with audio), A2V (audio-to-video), keyframe interpolation
- **Resolution:** Up to 4K natively; recommended 1216×704 → 1920×1088 upscale workflow
- **FPS:** 24, 30, or 50fps (50fps cinematic)
- **Duration:** Discrete 2/3/4/5/6/7/8/9/10 second options
- **Aspect ratios:** 1:1, 4:3, 16:9, 21:9, 9:16, 3:4
- **VRAM:** 24GB+ for self-hosted; 48GB+ optimal
- **Audio:** **YES — native synchronized audio-video generation** (dialogue, ambient, music, sound effects, all in one pass)
- **Strengths:** First open-source audio+video model; 4K native; 50fps cinematic; multiple performance pipelines
- **Weaknesses:** Higher VRAM requirements; complex prompt structure for full audio-aware output
- **Best for:** Most current LTX work — the default for audio+video generation
- **Prompting tips:** Full 7-component structure with audio woven in. See `references/audio-prompting.md`.

---

## LTX-2.3 (current SOTA, 22B)

The latest major release. January / March 2026.

- **Released:** January 2026 (full open-source release March 2026 with desktop editor)
- **Parameters:** 22B (dev variant); also distilled variants
- **Architecture:** Same DiT-based audio-video foundation, scaled up significantly
- **Modes:** T2V, I2V, A2V, keyframe interpolation, retake (regenerate a time range of an existing video)
- **Resolution:** Up to 4K native, HDR variant available
- **FPS:** 24, 30, 50
- **Duration:** Same discrete options as LTX-2
- **Audio:** Yes (same architecture as LTX-2 but improved)
- **VRAM:** 24GB+ minimum; 48GB+ recommended; FP8 quantization available for memory reduction
- **Available pipelines:**
  - `TI2VidTwoStagesPipeline` — production-quality T/I2V with 2× upsampling (recommended for finals)
  - `TI2VidTwoStagesHQPipeline` — same as above with the res_2s second-order sampler (fewer steps, better quality)
  - `TI2VidOneStagePipeline` — single-stage for quick prototyping
  - `DistilledPipeline` — fastest inference with 8 predefined sigmas (8+4 step two-stage)
  - `ICLoraPipeline` — video-to-video and image-to-video with IC-LoRA conditioning
  - `KeyframeInterpolationPipeline` — interpolate between two keyframe images
  - `A2VidPipelineTwoStage` — audio-conditioned video generation
  - `RetakePipeline` — regenerate a specific time region of an existing video
- **Bundled LoRAs:** Camera control (Dolly In/Out/Left/Right, Jib Up/Down, Static); IC-LoRAs (Union Control, Motion Track Control, Detailer, Pose Control); Distilled LoRA
- **Strengths:** Best LTX quality; comprehensive control via LoRAs; HDR variant; retake capability
- **Weaknesses:** Highest VRAM requirements; longer inference time; newer ecosystem
- **Best for:** Premium finals, commercial work, controlled generation with LoRAs
- **Prompting tips:** Full 7-component structure; use camera-control LoRAs when motion quality is critical. See `references/camera-control-loras.md`.

---

## LTX Studio (the platform, not a model)

Lightricks' commercial AI video creation platform that uses the LTX models as backend. Not a model per se — a UI/workflow product.

Features (as of 2026):
- Audio-to-Video: generate lip-synced talking videos from audio files
- Storyboard Generator: turn scripts into shot-by-shot visuals
- Retake: redirect specific moments within shots without regenerating entire scenes
- Elements: reusable character/prop/environment references
- Projects: full multi-shot project management
- Camera Motion Presets: GUI version of the camera-control LoRAs

When a user mentions "LTX Studio," they're talking about this UI product rather than the underlying LTX-2.3 model. The prompting principles still apply but the user is operating through a GUI rather than ComfyUI/raw API.

---

## Variant routing logic

When the user asks for "an LTX prompt" without specifying:

1. **Default to LTX-2.3** — current SOTA, comprehensive feature set
2. If the user mentions **audio specifically**, confirm LTX-2 or 2.3 (only audio-capable variants)
3. If the user mentions **long-form video (>10s)**, consider LTXV-13B (the 60s+ specialist) or chain multiple LTX-2.3 clips
4. If the user mentions **fast iteration / drafts / consumer hardware**, route to:
   - LTX Video 2B (lowest VRAM)
   - LTX-2.3 `DistilledPipeline` (fastest LTX-2.3 path)
5. If the user mentions a **specific camera move**, route to LTX-2.3 with the appropriate Camera Control LoRA
6. If the user wants to **edit an existing video clip**, use LTX-2.3 with `RetakePipeline`
7. If the user wants to **animate from audio**, use LTX-2.3 with `A2VidPipelineTwoStage`
8. If the user is on **LTX Studio (the platform)**, give them prompts compatible with the GUI's camera motion presets and storyboard workflow

When the user already specified a variant, use that one and don't second-guess unless prompt content is mismatched (e.g., they asked for LTX Video 2B but described a complex audio-heavy scene that requires LTX-2+).

---

## Quick comparison table

| Variant | Audio | Max duration | Max resolution | VRAM | Best for |
|---|---|---|---|---|---|
| LTX Video 2B | No | ~5s | 768×512 | 12GB+ | Legacy, fast iter, modest HW |
| LTXV-13B | No | 60s+ | 1216×704 | 24GB+ | Long-form silent video |
| LTX-2 | **Yes** | 10s | 4K | 24GB+ | Most current work |
| LTX-2.3 | **Yes** | 10s | 4K + HDR | 24GB+ (48GB rec.) | Premium finals, LoRA control |

---

## Comparison to other video model families

### vs Wan 2.x (Alibaba)
LTX has native audio; Wan got synced audio in 2.6 but LTX had it first. Wan has better multi-shot capabilities (2.6+); LTX has better real-time speed. LTX has the camera-control LoRA ecosystem; Wan has Fun-Control with similar (pose/depth/canny) but different mechanics. Both are open-source. **Use LTX for audio-first work, Wan for cinematic multi-shot narrative.**

### vs Sora 2 (OpenAI)
Sora is closed and API-only; LTX is open-source. Sora has slightly more polished output in some scenarios; LTX has the speed advantage and runs locally. **Use LTX when ownership or speed matters; Sora for absolute peak quality if you can pay the API cost.**

### vs Veo 3 (Google)
Veo 3 has audio generation; LTX-2 has audio generation. Veo is API-only at premium pricing; LTX is open-source. **Use LTX when you need ownership; Veo for some specific visual qualities Google has tuned for.**

### vs Runway Gen-4/5
Commercial product with polished UI. LTX-2 / LTX Studio is the open-source/Lightricks-platform parallel. **Use LTX for self-hosted or LTX Studio for a similar commercial-tier experience with open-weights backend.**

### vs Hunyuan Video (Tencent)
Both open-source. Hunyuan is slightly more permissive on certain content; LTX has audio. **Use LTX for audio-aware work; Hunyuan for some specific community use cases.**

### vs Pika / Luma / Kling
Mostly commercial. LTX is the open-source alternative most of them are now compared against. **Use LTX for self-hosted; the commercial options for hands-off polish.**

---

## Workflow recommendations

**For most users starting out:** LTX-2.3 with `TI2VidTwoStagesPipeline`. Generate at 1216×704, 24fps, 5–6 seconds. Once you find a keeper, regenerate at 1920×1088 with the same seed for the final.

**For audio-heavy work:** LTX-2 or LTX-2.3 with full audio prompting. Avoid trying to add audio in post — LTX's native sync is the whole point.

**For real-time / drafts:** LTX-2.3 `DistilledPipeline` or LTX Video 2B.

**For long-form (>10s):** Either LTXV-13B (designed for long clips) OR chain multiple LTX-2.3 generations using keyframe interpolation to bridge them.

**For commercial / portfolio:** LTX-2.3 with camera control LoRAs + IC-LoRAs as needed. Use `TI2VidTwoStagesHQPipeline` for finals.

**For platform users:** If on LTX Studio (the GUI), give them prompts that work with the camera motion presets and storyboard generator.

**For LoRA-trained workflows:** LTX-2.3 has the most comprehensive LoRA ecosystem; the `ltx-trainer` package supports LoRA, full fine-tuning, and IC-LoRA training.
