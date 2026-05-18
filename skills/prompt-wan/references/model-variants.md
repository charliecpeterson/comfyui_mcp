# Wan Model Variants Reference

The Wan family from Alibaba's Tongyi Wanxiang Lab (通义万相) is the leading open-source video generation lineage. This file catalogues every variant in current use, with parameter recommendations and routing logic.

All Wan variants are **open-source** with permissive licensing for most uses. The base 2.x models are available on GitHub, Hugging Face, and ModelScope, with API access via Alibaba Cloud.

---

## Wan 2.1

The baseline model. Released early 2025. Many community workflows still pin to 2.1 because of LoRA compatibility.

- **Released:** Early 2025
- **Architecture:** Diffusion transformer, 14B parameters
- **Modes:** T2V (text-to-video), I2V (image-to-video)
- **Resolution:** 480p or 720p, ~5 second clips
- **Strengths:** Mature ecosystem, most LoRAs target it, well-documented community workflows
- **Weaknesses:** Less coherent motion than 2.2+, weaker hand quality, more prone to identity drift
- **Best for:** Workflows pinned to specific 2.1 LoRAs; baseline community ComfyUI setups
- **Prompting tips:** 80–120 words, subject + scene + motion formula, strong negative prompt mandatory

---

## Wan 2.2 (the focus of this skill)

Released mid-2025. Introduced Mixture-of-Experts (MoE) architecture to video diffusion for the first time. Currently the most-used Wan variant in community workflows.

### Wan 2.2 T2V (14B)

- **Mode:** Text-to-video
- **Parameters:** 14B active (27B total in MoE — only ~14B parameters active per generation)
- **Resolution:** 720p
- **Frame rate:** 24fps native (16fps for fast drafts)
- **Duration:** ~5 second clips
- **Strengths:** Cleaner, sharper motion than 2.1; better aesthetic and semantic control; MoE keeps quality high while not paying for full 27B in compute
- **Weaknesses:** Still ~5 seconds (newer Wan versions extend this); hand quality still imperfect
- **Best for:** Most T2V work
- **Parameters:** `cfg_scale: 5.0–7.0`, `steps: 30–50`
- **Prompting tips:** Use the official subject + scene + motion + camera + atmosphere + style formula. 80–120 words.

### Wan 2.2 I2V (14B)

- **Mode:** Image-to-video (animate a still)
- **Parameters:** Same 14B MoE as T2V
- **Input:** First-frame image + motion prompt
- **Output:** Animated continuation
- **Strengths:** Strong subject preservation; the most-used Wan variant in production
- **Weaknesses:** Will drift if motion prompt is too ambitious or contradicts the image
- **Best for:** Animating photos, product shots, portraits; turning a Flux/Qwen still into video
- **Prompting tips:** Focus on motion of existing elements; don't try to add new ones. 40–80 words. Strong negative prompt is critical.

### Wan 2.2 Last Frame

- **Mode:** Last-frame conditioning
- **Capability:** Specify the final frame of a video to guide the generation toward a specific ending
- **Use case:** Chaining multiple clips together with smooth transitions; controlling the end state of motion
- **Best for:** Animated sequences that need to land on a specific final pose or composition

### Wan 2.2-Fun-Control (5B)

- **Mode:** Controlled generation with explicit signals
- **Parameters:** 5B (smaller, runs on RTX 4090)
- **Control conditions:** Canny edges, Depth maps, Pose skeletons, MLSD lines, motion trajectories
- **Strengths:** Precise control over composition and motion; runs on consumer hardware
- **Weaknesses:** Smaller model means slightly lower quality vs 14B; requires preprocessing the control signal
- **Best for:** Workflows where exact pose/composition control matters (character animation with pose control, architectural visualization with depth, etc.)

### Wan 2.2-Animate

- **Mode:** Motion transfer (released September 2025)
- **Capabilities:** 
  - **Motion imitation** — transfer actions and expressions from a reference video to a still photo
  - **Character replacement** — swap a character in a video with the subject from a photo
- **Strengths:** Strong identity consistency from the photo source; integrates skeletal + facial signals
- **Weaknesses:** Requires a clean reference video; works best with frontal-facing subjects
- **Best for:** Character animation from stills, music videos, deepfake-style character replacement

---

## Wan 2.5

Refined I2V model released late 2025. Stronger motion coherence and the introduction of the 4-part I2V framework (motion / camera / environment / pacing).

- **Released:** Late 2025
- **Mode:** Primarily I2V
- **Strengths:** Best-in-class motion coherence among 2.x; clean handling of subtle motion; respects source image strongly
- **Weaknesses:** More limited multi-shot than 2.6
- **Best for:** High-quality single-shot I2V where preserving the source image matters most
- **Prompting tips:** 4-part framework — primary motion + camera + environmental effects + pacing/intensity. 40–80 words.

---

## Wan 2.6

Released December 2025. Major behavioral shift — introduced **cinematographer-style structured prompting** with shot blocks and timecodes. Reusing 2.2 prompts unaltered produces worse output.

- **Released:** December 2025
- **Modes:** T2V, I2V, role-playing, storyboard control, multi-shot
- **Duration:** Up to ~15 seconds practical
- **Strengths:** 
  - Temporal awareness — reasons over time, not just frames
  - Explicit multi-shot composition with continuity
  - Camera-first thinking
  - Synced facial expressions and audio
  - Role-playing — generate video with a specific person's IP and voice
- **Weaknesses:** Different prompt structure required; old prompts don't carry over
- **Best for:** Cinematic multi-shot work, role-playing video, narrative sequences, anything where camera direction is the primary control
- **Prompting tips:** Use shot blocks with timecodes. See `references/wan-26-shot-blocks.md`.

---

## Wan 2.7

Released April 2026. Latest major release. Introduced **Thinking Mode** and major capability extensions.

- **Released:** April 2026
- **Modes:** Image gen, video gen, video editing (covers full Wan capability)
- **Key features:**
  - **Thinking Mode** — model reasons about the prompt and plans composition before generating
  - **Thousand-Face Realism** — better facial bone structure, eye detail, eliminating AI-same-face issues
  - **Precise Color Control** — HEX codes and palette specifications for brand-accurate visuals
  - **Industry-Leading Text Rendering** — 3,000+ tokens of in-frame text; 12 languages including Chinese, Japanese, Korean, Arabic
  - **Multi-Reference Editing** — up to 9 reference images; pixel-level local editing; group image generation
- **Strengths:** Most coherent, most consistent, most-featured Wan version. Comparable to commercial alternatives.
- **Weaknesses:** Higher inference time per generation (Thinking Mode); newer ecosystem
- **Best for:** Premium finals, branded work, narrative video with character consistency, any task that previous Wan versions couldn't quite deliver
- **Prompting tips:** Same shot-block structure as 2.6 with additional features. See `references/wan-26-shot-blocks.md`.

---

## Variant routing logic

When the user asks for "a Wan prompt" without specifying:

1. **Default to Wan 2.2 I2V** — most-used variant in community workflows. Mention which you chose.
2. If they want **text-to-video only** with no source image, use **Wan 2.2 T2V**.
3. If they want **highest quality and have access to it**, recommend **Wan 2.7** with its shot-block structure.
4. If they want **multi-shot cinematic** sequences, use **Wan 2.6 or 2.7** with shot blocks.
5. If they want **character animation from a photo using a reference video**, use **Wan 2.2-Animate**.
6. If they want **explicit pose/composition control**, use **Wan 2.2-Fun-Control**.
7. If they're on a **specific LoRA workflow**, use whichever Wan version that LoRA targets (typically 2.1 or 2.2).

When the user already specified a variant, use that one and don't second-guess unless their prompt content is genuinely mismatched (e.g., they asked for 2.2 but wrote a shot-block multi-shot prompt — note that 2.6+ would handle that better and offer to retarget).

---

## Quick comparison table

| Variant | Mode | Duration | Architecture | Best for |
|---|---|---|---|---|
| Wan 2.1 | T2V, I2V | ~5s | Diffusion 14B | Legacy workflows, LoRA-pinned |
| Wan 2.2 T2V | T2V | ~5s | MoE 14B active (27B total) | Standard T2V |
| Wan 2.2 I2V | I2V | ~5s | MoE 14B | Standard I2V — the most-used Wan variant |
| Wan 2.2-Fun-Control | Controlled | ~5s | 5B | Consumer-GPU, control signals |
| Wan 2.2-Animate | Motion transfer | varies | 14B | Photo+reference video animation |
| Wan 2.5 | I2V | ~5s | Refined 2.2 | Highest I2V coherence |
| Wan 2.6 | T2V, I2V, multi-shot | ~15s | Temporal-aware | Cinematic multi-shot |
| Wan 2.7 | Full multimodal | varies | Thinking Mode | Premium finals, branded, multi-reference |

---

## Hardware requirements

Approximate VRAM needs (varies by workflow):

| Variant | VRAM | Speed (RTX 4090) |
|---|---|---|
| Wan 2.1 14B | 24GB+ | 5–10 min per clip |
| Wan 2.2 14B (MoE) | 24GB+ | 4–8 min per clip (MoE efficiency) |
| Wan 2.2-Fun-Control 5B | 16GB | 2–4 min per clip |
| Wan 2.5 14B | 24GB+ | 4–8 min |
| Wan 2.6 | 24GB+, optimal 48GB | 6–15 min for multi-shot |
| Wan 2.7 (Thinking Mode) | 24GB+, optimal 48GB | 8–20 min |

For Wan 2.6 and 2.7 multi-shot work, hosted API access (via Alibaba Cloud, fal, Replicate, etc.) is usually more practical than self-hosting.

---

## Comparison to other video model families

**vs Sora 2 (OpenAI):** Wan is open-source; Sora is closed and API-only. Wan 2.6+ approaches Sora's multi-shot capabilities. Sora still has the edge for some experimental scenarios; Wan for production where ownership matters.

**vs Veo 3 (Google):** Veo 3 has audio generation and very long clips. Wan 2.6+ closed the audio gap with synced facial/voice generation. Wan's open-source nature is the differentiator.

**vs Runway Gen-4 / Gen-5:** Runway has a polished commercial product; Wan has the raw capability with more flexibility. For non-commercial or self-hosted use, Wan wins.

**vs Hunyuan Video (Tencent):** Direct competitor, both open-source. Hunyuan is slightly stronger on some uncensored use cases; Wan is stronger on multi-shot, identity consistency, and audio sync.

**vs Pika / Luma / Kling:** Mostly commercial competitors. Wan is the open-source baseline most of them are now being compared against.

---

## Workflow recommendations

**For most users starting out:** Wan 2.2 I2V — pair it with Flux 2 Pro or Qwen for the still, then animate.

**For commercial / branded video:** Wan 2.7 with Thinking Mode and multi-reference.

**For narrative video:** Wan 2.6 multi-shot with structured prompting. Plan 2–3 shots per 15-second generation.

**For experimentation / iteration:** Wan 2.2-Fun-Control on consumer GPU for fast drafts; promote to 14B for finals.

**For character animation:** Wan 2.2-Animate with a clean reference video.

**For LoRA-based workflows:** Whatever version the LoRA targets, usually 2.1 or 2.2.
