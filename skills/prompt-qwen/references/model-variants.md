# Qwen Image Model Variants Reference

The Qwen Image family covers text-to-image generation and image-to-image editing, all from Alibaba. This file catalogues each variant, its strengths and limitations, and which to recommend for a given task.

All Qwen Image variants are **Apache 2.0 open-weights** — the most permissive licensing in the major image-model field, including commercial use.

---

## Qwen Image 1.0

The original Qwen Image release. 20B parameters.

- **Released:** mid-2025
- **Architecture:** Larger end-to-end diffusion model (no separate VLM encoder)
- **Resolution:** 1024×1024 native
- **Token budget:** Standard CLIP-like context
- **Strengths:** Strong baseline quality, text rendering (English + Chinese)
- **Weaknesses:** Superseded by 2.0 on every benchmark; larger and slower
- **License:** Apache 2.0
- **Best for:** Legacy workflows, pipelines pinned to 1.0, environments without 2.0 support
- **Prompting tip:** 30–60 words sweet spot. Use the old guidance scale of 2.5–4.0.

---

## Qwen Image 2.0 (current SOTA)

The Feb 2026 release. Architectural redesign — smaller, faster, better.

- **Released:** February 10, 2026
- **Architecture:** Encoder-decoder split: 8B Qwen3-VL vision-language encoder + 7B diffusion decoder
- **Resolution:** 2048×2048 native (2K)
- **Token budget:** 1000 tokens — roughly 2x Flux 1, useful for complex compositional prompts
- **Strengths:**
  - #1 on AI Arena's blind evaluation leaderboard at release
  - Outperforms Flux.1 on DPG-Bench (88.32 vs 83.84) despite being 5B smaller total
  - Best-in-class text rendering, including Chinese
  - Native 2K resolution (no separate upscaler needed)
  - Unified gen + edit in the same model
  - Strong spatial reasoning (handles "upper left", "between X and Y", etc., as compositional instructions)
  - Smaller VRAM footprint than 1.0 — runs on 24GB consumer GPUs
- **Weaknesses:**
  - Newer ecosystem — fewer community LoRAs and fine-tunes (growing fast)
  - Some specialized capabilities (extreme stylization, very specific aesthetics) lag behind purpose-built models
- **License:** Apache 2.0
- **Best for:** Most new work. The default recommendation.
- **Prompting tips:**
  - 1–3 sentences for general images (the model uses ~50–80 tokens well)
  - Up to 1000 tokens for text-heavy / multi-element compositions
  - Front-load the subject — bidirectional attention weights early tokens more heavily
  - `guidance_scale: 4.0–5.0` (higher than older guides suggest)
  - Lean conversational. The VLM encoder handles natural instruction-style prompts very well.

---

## Qwen Image Edit (Qwen-Image-Edit-2511 and successors)

Image-to-image editing using the same Qwen Image 2.0 model.

- **Architecture:** Same as Qwen Image 2.0 — the encoder takes both text and source images
- **Input:** One or more source images + a text instruction
- **Output:** Single edited image
- **Capabilities:**
  - **Semantic editing** — change content (hair color, clothing, expression, weather, time of day)
  - **Appearance editing** — remove objects, fix lighting, restore quality, remove watermarks
  - **Text editing** — add, remove, or change text in an image (full bilingual support)
  - **View synthesis** — rotate the subject 90°/180° to show other angles
  - **Multi-image fusion** — combine subjects from multiple sources, composite people into new backgrounds, transfer styles between images
- **Strengths:**
  - Unified with generation (same model)
  - Preserves unedited regions reliably when given good preservation language
  - Handles cross-domain edits (illustrated character into photographic background, etc.)
- **Weaknesses:**
  - Drift on unedited elements if preservation language is omitted
  - Complex multi-step edits work better as sequential single edits
- **License:** Apache 2.0
- **Best for:** Any image-to-image work — photo retouching, product photography variants, text overlay/replacement, composite creation
- **Prompting tips:** see `references/editing-instructions.md` for detailed patterns
- **Parameter notes:** `guidance_scale: 3.0–4.0` (lower than for generation), `num_inference_steps: 25–40`

---

## Distilled / fast variants

Qwen Image 2.0 has community-trained step-reduced LoRAs (4-step, 8-step) similar to Flux Schnell's purpose. These aren't separate model releases — they're LoRA adapters.

- **4-step LoRA** — very fast iteration, drops some quality
- **8-step LoRA** — closer to full quality, ~2x faster than native settings
- **Native settings** — 25–40 steps, full quality

For production work, run native settings. For iteration, use the 4-step or 8-step LoRA to brainstorm before final-rendering.

---

## Community fine-tunes

The Qwen Image 2.0 ecosystem is growing on Civitai and Hugging Face. Common categories:

- **Style LoRAs** — anime, watercolor, specific artist styles
- **Character LoRAs** — specific characters trained from reference sets
- **NSFW fine-tunes** — community uncensored variants (Qwen base is filtered for SFW)
- **Domain-specific LoRAs** — fashion, product photography, architectural visualization

When the user references a specific LoRA, use Qwen Image 2.0 as the base and incorporate the LoRA's trigger words near the front of the prompt. Trigger word documentation lives on the LoRA's model card.

---

## NSFW handling

Qwen's base model is filtered. Compared to Flux:

- **Flux 1 Dev + uncensored LoRA** and **Flux 2 Dev** are stronger NSFW paths
- For NSFW work where the user wants Qwen anyway (typically because they need the text-rendering or Chinese-language strength), point them to community Qwen Image 2.0 NSFW fine-tunes on Civitai
- Use plain descriptive English for explicit content — Qwen's VLM encoder rewards natural prose over tag-style vocabulary

**Absolute boundary:** never produce NSFW prompts involving anyone described or implied as a minor. No reframing, no fictional-character workaround. Hard stop, explain briefly, redirect.

---

## Variant routing logic

When the user asks for "a Qwen prompt" without specifying:

1. **Default to Qwen Image 2.0** — current SOTA, broadest applicability
2. If the user wants to **edit an existing image**, route to **Qwen Image Edit** workflow
3. If the user is on a legacy pipeline that's pinned to 1.0, use **Qwen Image 1.0** conventions (shorter prompts, lower guidance scale)
4. If the user mentions a community LoRA, base on **Qwen Image 2.0** and note the LoRA's trigger words
5. If the user wants NSFW, note that **Flux 1 Dev + uncensored LoRA** or **Flux 2 Dev** are stronger paths — but if they're committed to Qwen, point to community NSFW fine-tunes

---

## Quick comparison table

| Variant | Token budget | Resolution | Speed | Edits? | License | Killer feature |
|---|---|---|---|---|---|---|
| Qwen Image 1.0 | ~75 (CLIP-like) | 1024² | medium | no | Apache 2.0 | open-weights, English+Chinese text |
| Qwen Image 2.0 | 1000 | 2048² | medium | yes (unified) | Apache 2.0 | text rendering, spatial reasoning, 2K native, edit + gen unified |
| Qwen Image Edit | 1000 | 2048² | medium | yes (primary) | Apache 2.0 | semantic + view + multi-image edits |

---

## Comparison to other model families

When to choose Qwen over alternatives:

- **vs Flux 2 Pro:** choose Qwen when text rendering is the primary requirement, especially bilingual. Choose Flux 2 Pro when the photographic/cinematic quality of non-text content is primary.
- **vs Flux 2 Flex:** Qwen and Flex are close competitors for text-heavy work. Qwen edges out for Chinese; Flex edges out for very specific Latin-alphabet typographic styles. For mixed-language work, Qwen is usually better.
- **vs Pony / Illustrious:** different worlds. Pony/Illustrious are tag-based anime fine-tunes. Qwen is a general-purpose prose-driven model. Use Qwen when you want photographic, illustrated, or text-heavy realistic work; use Pony/Illustrious when you want danbooru-style anime.
- **vs GPT-Image / DALL-E 3:** Qwen is open-weights, can run locally, and edits within the same model. GPT-Image lives behind an API. For workflows that need ownership or offline use, Qwen wins.
- **vs Midjourney:** Midjourney is aesthetic-first and "loose" with prompts. Qwen is literal and precise. For production work where you need exactly what you specified, Qwen. For art-direction-style experimentation, Midjourney.
