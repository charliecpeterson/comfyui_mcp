# Z-Image Model Variants Reference

The Z-Image family from Alibaba's Tongyi-MAI Lab is a coordinated set of variants built on the **Scalable Single-Stream Diffusion Transformer (S3-DiT)** architecture. Unlike dual-stream models where text and image are processed in parallel streams, Z-Image concatenates text tokens, visual semantic tokens, and image VAE tokens into a single unified input sequence.

All Z-Image variants are **Apache 2.0 open-weights** — fully permissive licensing including commercial use.

This file catalogues each variant, its strengths and limitations, prompt characteristics, and routing logic.

---

## Z-Image-Turbo

The 8-step distilled fast variant. Released November 26, 2025. The most-used member of the family in community workflows.

- **Released:** Nov 26, 2025
- **Parameters:** 6B
- **Architecture:** Distilled S3-DiT with Decoupled-DMD (Distribution Matching Distillation)
- **Resolution:** 1024×1024 native; supports 1280×720, 720×1280
- **Inference steps:** 8 (the pipeline uses 9 to produce 8 DiT forwards)
- **Guidance scale:** **0.0 mandatory** — CFG is disabled in the distilled model
- **Negative prompts:** **Ignored entirely.** The `negative_prompt` field is cosmetic.
- **VRAM:** Runs on 16GB consumer GPUs (RTX 4090, RTX 3060 with offload)
- **Speed:** Sub-second on H800; 2–5 seconds on RTX 4090
- **Built on:** distilled from Z-Image (base)

**Strengths:**
- Fastest member of the family — designed for rapid iteration
- Strong prompt adherence despite the distillation
- Best-in-class bilingual text rendering (English + Chinese)
- Runs on consumer hardware
- Ranked #1 open-source model on Alibaba AI Arena's Elo leaderboard at release
- Ranked 8th overall (across closed + open models) on Artificial Analysis Text-to-Image Leaderboard

**Weaknesses:**
- **Cannot use negative prompts** — all constraints must be encoded positively in-prompt
- Lower output diversity per prompt than the base model (more deterministic given a prompt)
- Some specialized aesthetics (extreme stylization, very specific artistic looks) lag behind purpose-built models

**Best for:** Most generation work, especially when speed and local deployment matter. The default Z-Image variant.

**Prompting tips:**
- 80–150 words sweet spot (long, detailed prose)
- Constraint cleanup goes in the prompt itself, near the end
- `num_inference_steps: 8`, `guidance_scale: 0.0`
- Fix seed while iterating prompt; randomize for exploration

---

## Z-Image (base)

The full foundation model that Z-Image-Turbo was distilled from. Released January 27, 2026 — significantly later than Turbo.

- **Released:** Jan 27, 2026
- **Parameters:** 6B (same architecture, undistilled)
- **Architecture:** Full S3-DiT with classifier-free guidance enabled
- **Resolution:** 1024×1024 native; flexible aspect ratios up to 1280×720
- **Inference steps:** 25–50 (full diffusion)
- **Guidance scale:** **Supported, recommended 4.0–5.0**
- **Negative prompts:** **Supported and effective**
- **VRAM:** Same 16GB consumer-GPU profile
- **Speed:** Slower than Turbo (~30 steps vs 8 steps)

**Strengths:**
- Highest output quality and diversity in the family
- Supports negative prompts and classifier-free guidance
- Strong artistic style range — better than Turbo for very specific aesthetics
- Best for fine-tuning base, LoRA training, and downstream development
- Effective with negative prompting (per official docs)

**Weaknesses:**
- ~4× slower than Turbo
- Fewer community workflows and examples (newer release)
- Less battle-tested in community pipelines

**Best for:** Highest-quality finals, work where negative prompts matter, fine-tuning workflows, research and downstream development.

**Prompting tips:**
- 60–120 words sweet spot — CFG steers, so don't over-specify
- Use a short negative prompt (under 10 tags)
- `num_inference_steps: 25–40`, `guidance_scale: 4.0–5.0`
- Higher guidance (5.0–5.5) for text-heavy work

---

## Z-Image-Omni-Base

The unified variant — single model handles both text-to-image generation AND image-to-image editing. Released alongside Z-Image base.

- **Released:** Jan 2026
- **Parameters:** 6B
- **Architecture:** S3-DiT with multi-modal input head (accepts text + optional source images)
- **Resolution:** Same as base
- **Inference steps:** 25–40
- **Guidance scale:** 3.5–5.0 depending on mode
- **Negative prompts:** Supported
- **Input modalities:** Text-only (generation), or text + 1+ source images (editing)

**Strengths:**
- One model for both generation and editing — no model-switching in workflows
- Inherits Z-Image base quality
- "Most raw and diverse starting point for open-source community development" per Tongyi-MAI

**Weaknesses:**
- Newer than other variants, smaller community ecosystem
- For pure generation, base may be marginally faster; for pure editing, Edit may be marginally better-tuned

**Best for:** Workflows that need both generation and editing capability in a unified model; community development and fine-tuning where flexibility matters.

**Prompting tips:**
- Use generation conventions for text-only prompts
- Use editing conventions when source images are included
- Parameters: as base for generation, as Edit for editing

---

## Z-Image-Edit

Specialized for image-to-image editing as the primary task. Released January 2026.

- **Released:** Jan 2026
- **Parameters:** 6B
- **Architecture:** S3-DiT fine-tuned specifically for editing instruction-following
- **Input:** Source image(s) + natural-language instruction (English or Chinese)
- **Resolution:** Matches source image; output 1024×1024 typical
- **Inference steps:** 25–35
- **Guidance scale:** 3.5–4.0
- **Negative prompts:** Supported (less load-bearing than for generation)

**Capabilities:**
- **Semantic editing** — change clothing, hair, expression, weather, time of day
- **Appearance editing** — remove objects, fix lighting, restore quality
- **Text editing** — add, remove, or change text in an image (bilingual)
- **View synthesis** — rotate subject 90°/180° to show other angles
- **Style transfer** — apply painting/illustration styles to photos and vice versa
- **Bilingual instructions** — accepts Chinese, English, or mixed-language edit instructions natively

**Strengths:**
- Specifically tuned for editing; preserves unedited regions reliably
- Strong bilingual instruction-following
- Handles cross-domain edits (illustrated character into photographic background, etc.)

**Weaknesses:**
- Drift on unedited elements without preservation language
- Complex multi-step edits work better as sequential single edits

**Best for:** Any image-to-image work — photo retouching, product variants, text overlay/replacement, composite creation. The dedicated editing tool when editing is the primary task.

**Prompting tips:** see `references/editing-instructions.md`

---

## Distilled / accelerated variants

Community-trained LoRAs (4-step, 8-step) exist for Z-Image base, similar in concept to Z-Image-Turbo itself. These let you run the base model with reduced step counts.

- **4-step LoRA** — very fast iteration, drops quality vs full base
- **8-step LoRA** — closer to full quality, ~3× faster than native settings
- **Native settings** — 25–40 steps, full quality

For most users, Z-Image-Turbo is already the "fast variant" of Z-Image base. The step-reduction LoRAs are mainly useful when you specifically need base-model output (e.g., for negative prompt support) at faster speeds.

---

## Community fine-tunes and LoRAs

The Z-Image ecosystem is growing on Civitai and Hugging Face. Common categories:

- **Style LoRAs** — anime, watercolor, specific artist styles, period photography
- **Character LoRAs** — specific characters trained from reference sets
- **NSFW fine-tunes** — community uncensored variants (Z-Image's base filtering is light, but dedicated NSFW fine-tunes are available)
- **Domain-specific LoRAs** — fashion, product photography, architectural visualization, hanfu/period costume

When the user references a specific LoRA, use the appropriate Z-Image base (Turbo or base) and incorporate the LoRA's trigger words near the front of the prompt. Trigger word documentation lives on the LoRA's model card.

---

## NSFW handling

Z-Image's base filtering is relatively light compared to Flux Pro or Qwen API endpoints. Community fine-tunes add explicit NSFW capability.

- For NSFW work on Z-Image, use plain descriptive English. Z-Image's strong prompt adherence handles explicit content reliably.
- Apply `adult` modifier discipline always.
- For SFW work where you want to prevent NSFW drift, include `fully clothed, modest outfit, safe for work, non-sexual` (Turbo) or in the negative prompt (base).

**Absolute boundary:** never produce NSFW prompts involving anyone described or implied as a minor. No reframing makes this acceptable.

---

## Variant routing logic

When the user asks for "a Z-Image prompt" without specifying:

1. **Default to Z-Image-Turbo** — most common variant, fastest, runs locally. Note the no-negative-prompt limitation in the response.
2. If the user explicitly wants **highest quality** and can wait for full diffusion, recommend **Z-Image base** with negative prompt support.
3. If the user wants to **edit an existing image**, route to **Z-Image-Edit** workflow.
4. If the user wants **gen + edit unified** in one model, use **Z-Image-Omni**.
5. If the user mentions a community LoRA, base on the LoRA's recommended Z-Image variant (usually Turbo for Civitai community LoRAs).
6. If the user is doing **bilingual or text-heavy work** with high text-fidelity requirements, suggest base over Turbo (higher CFG = better text rendering).

When the user already specified a variant, use that one and don't second-guess unless their prompt content is genuinely mismatched (e.g., they asked for Turbo but included a `negative_prompt:` field — note that Turbo ignores it and offer to encode the constraints positively).

---

## Quick comparison table

| Variant | Negative prompts | Steps | CFG | Speed | License | Best for |
|---|---|---|---|---|---|---|
| Z-Image-Turbo | **No (ignored)** | 8 | 0.0 | very fast | Apache 2.0 | speed, local, daily use |
| Z-Image base | Yes | 25–40 | 4.0–5.0 | medium | Apache 2.0 | quality finals, fine-tuning |
| Z-Image-Omni | Yes | 25–40 | 3.5–5.0 | medium | Apache 2.0 | unified gen + edit |
| Z-Image-Edit | Yes | 25–35 | 3.5–4.0 | medium | Apache 2.0 | image-to-image |

---

## Comparison to other model families

**vs Qwen Image 2.0:** Both are Alibaba bilingual models with strong text rendering. Z-Image is faster, simpler, and runs on smaller hardware. Qwen 2.0 has a longer token budget (1000 vs ~512) and handles more complex multi-element compositions better. For single sign or 3–5 element posters, Z-Image is competitive and faster. For 8+ element infographics, Qwen wins.

**vs Flux 2 Pro:** Different positioning. Flux 2 Pro is hosted-only and excels at photographic/cinematic quality. Z-Image is open-weights, free, runs locally. Choose Z-Image when ownership, offline use, or speed matter. Choose Flux 2 Pro for the absolute best photographic quality without infrastructure constraints.

**vs Flux 2 Flex:** Z-Image edges out for Chinese text; Flex edges out for very specific Latin typographic styles. Both produce excellent text-heavy output; the choice often comes down to license (Z-Image Apache vs Flex commercial-API) and Chinese-language requirement.

**vs Pony / Illustrious / NoobAI:** Different worlds. Those are tag-based anime fine-tunes; Z-Image is a general-purpose prose-driven model. Use Z-Image for photographic, illustrated, or text-heavy realistic work; use Pony/Illustrious for danbooru-style anime.

**vs SDXL:** Z-Image is the modern replacement for SDXL workflows in many cases — same VRAM profile, dramatically better prompt adherence, much better text, faster (Turbo) or comparable (base) inference. The main reason to stay on SDXL is a specific LoRA ecosystem you can't replicate yet on Z-Image.
