# Flux Model Variants Reference

The Flux family has expanded substantially since 2024. This file catalogues every variant the skill should know about, how each one prompts, and when to recommend each.

---

## Flux 1 family (2024 — Black Forest Labs)

### Flux 1 Dev

The open-weights workhorse. Most LoRA ecosystem, most local-installation tutorials, most ComfyUI workflows. Apache-restricted-research license — not for commercial use without paid arrangement.

- **Text encoder:** T5-XXL + CLIP-L (dual encoder)
- **Prompt length:** Up to 512 tokens. Sweet spot 30–80 words.
- **Strengths:** Strong prompt adherence, beautiful default aesthetic, great with named photo styles, very LoRA-compatible
- **Weaknesses:** Hand issues, no native multi-image reference, can produce "Flux face" (the slightly-too-smooth default look)
- **Best for:** Local/self-hosted workflows, LoRA-based character or style customization, anything where you can't use a hosted API

### Flux 1 Pro

The hosted, API-only commercial variant. Slightly higher quality than Dev, faster inference, no local weights.

- **Text encoder:** Same as Dev
- **Prompt length:** Same as Dev
- **Strengths:** Faster than self-hosted Dev, no infrastructure needed
- **Weaknesses:** No LoRAs (can't customize), hosted-only, content filter
- **Best for:** Quick commercial work, anything where you'd rather pay per image than run infrastructure

### Flux 1 Schnell

The 1–4-step distilled fast variant of Flux 1. Open-weights under Apache 2.0 (more permissive than Dev).

- **Text encoder:** Same as Dev
- **Prompt length:** Same as Dev technically, but keep prompts shorter — distillation drops subtlety
- **Strengths:** Very fast, Apache 2.0 license, useful for iteration and at-scale generation
- **Weaknesses:** Lower quality than Dev/Pro, drops nuance in long prompts
- **Best for:** Rapid iteration, brainstorming compositions before final-rendering in Pro/Max, large-batch generation
- **Prompting tip:** 15–40 words is the sweet spot. Strip every word that isn't load-bearing.

---

## Flux 2 family (late 2025 / 2026 — Black Forest Labs)

Flux 2 is a genuinely new architecture, not a fine-tune. The text encoder changed from T5+CLIP to a single Mistral-3 VLM, which is why it interprets prompts more literally and handles longer compositional descriptions better.

### Flux 2 Pro

The standard balanced Flux 2 variant. Default recommendation for most work.

- **Text encoder:** Mistral-3 VLM (single field)
- **Prompt length:** Up to 512 tokens. Sweet spot **50–150 words** — substantially longer than Flux 1.
- **Strengths:** Strongest prompt adherence in the family, multi-reference generation, much better text rendering, much better hands, more literal interpretation
- **Weaknesses:** Hosted-only at API tier, content filter, more expensive per generation
- **Best for:** Most production work. The default.
- **Prompting tip:** Flux 2 weighs early tokens *more* than Flux 1 did. Put the non-negotiable element first and Flux 2 will protect it.

### Flux 2 Max

Premium tier for finals. Same architecture as Pro, more inference compute.

- **Text encoder:** Same as Pro
- **Prompt length:** Same as Pro
- **Strengths:** Highest output quality in the family
- **Weaknesses:** Slowest, most expensive
- **Best for:** Portfolio pieces, client deliverables, anything where the per-image cost is justified by the final-quality requirement
- **Prompting tip:** Prompts that work on Pro work better on Max. No special tuning needed.

### Flux 2 Flex

Specialized for text-heavy work — posters, packaging, UI mockups, infographics, signage.

- **Text encoder:** Same as Pro, but tuned for text fidelity
- **Prompt length:** Same as Pro
- **Strengths:** Best-in-class text rendering, follows typography instructions precisely
- **Weaknesses:** Less optimized for pure photographic / pure illustration work — use Pro for those
- **Best for:** Anything where text is a major visual element
- **Prompting tip:** Front-load the text content. Specify font style, color, placement, and any secondary text elements. Wrap all literal text in double quotes.

### Flux 2 Dev

Open-weights version of Flux 2. Less filtered than Pro variants.

- **Text encoder:** Same as Pro
- **Prompt length:** Same as Pro
- **Strengths:** Self-hostable, LoRA-compatible (community LoRAs exist), less aggressive content filtering than Pro
- **Weaknesses:** Same as Flux 1 Dev — needs hardware, license restrictions on commercial use
- **Best for:** Local/self-hosted Flux 2 workflows, NSFW work (most permissive Flux 2 path), researchers
- **NSFW note:** Flux 2 Dev is the current best non-LoRA NSFW path. Less reliable than dedicated NSFW LoRAs but more flexible and supports the full prompt-adherence of Flux 2.

### Flux 2 Klein

Fast distilled variant of Flux 2. The Flux 2 equivalent of Schnell.

- **Text encoder:** Same as Pro
- **Prompt length:** Sweet spot **20–50 words**. Long prompts get muddy.
- **Strengths:** Fast, Apache-licensed, great for iteration
- **Weaknesses:** Drops subtlety, less reliable on hands, less reliable on text
- **Best for:** Brainstorming compositions, rapid iteration before moving to Pro/Max

---

## NSFW paths

### Flux 2 Dev (no LoRA needed)

The simplest NSFW path. Flux 2 Dev's content filter is much weaker than Pro variants', and the model's strong prompt adherence handles explicit prose well.

- Write descriptive prose as normal, using direct anatomical language
- Don't use Danbooru-style tags (`nsfw`, `nude` as bare tokens) — Flux 2's VLM encoder wants prose
- Lighting and composition rules apply *more*, not less. Well-lit explicit content reads as professional; flat-lit reads as low-quality.

### Flux 1 Dev + Flux-Uncensored v2 (LoRA)

The community-standard Flux 1 NSFW path. EnhanceAI's LoRA, freely available on Hugging Face.

- **Trigger words:** `nsfw`, `naked`, `nude`, `erotic`, `sensual`, `explicit`, `adult content`
- **LoRA weight:** 0.8–1.0 typical
- Use trigger words near the front of the prompt, then write descriptive prose as normal
- Combines well with other Flux 1 LoRAs (style, character) at moderate weights

### Flux 1 Dev + Lewd Flux Beta (LoRA)

Civitai community LoRA, specializes in surreal/artistic NSFW. Earlier proof-of-concept; full fine-tune in progress.

- **Trigger words:** `l3wddall3`
- **LoRA weight:** 1.0 recommended
- Strengths: removes the "Flux face" on female subjects, good with body shots, multi aspect ratios
- Weaknesses: dataset is mostly women; men less well-represented

### Other community NSFW LoRAs

The Civitai Flux ecosystem has many specialized NSFW LoRAs (anime-NSFW, photorealistic-NSFW, specific kink LoRAs, etc.). For these:

- Always check the LoRA's model card for its specific trigger words
- Use the recommended LoRA weight from the model card as a starting point
- Combine LoRAs at lower weights (0.5–0.7 each) when stacking

### NSFW conventions across all paths

- **Direct anatomical language** beats Danbooru tags or euphemisms. Flux models were not trained on booru vocabulary.
- **Standard cinematography still applies.** Three-point lighting, real lens specs, named photo styles all work on NSFW prompts.
- **Pose specificity matters more, not less.** Generic "nude on bed" produces stock-looking output. "Sitting on the edge of the bed pulling on a t-shirt, half-light from a single window" produces something with composition.
- **Absolute boundary:** never generate or assist with NSFW prompts involving anyone described or implied as a minor. No reframing, no fictional-character workaround. Hard stop, explain briefly, redirect.

---

## Variant routing logic

When the user asks for "a Flux prompt" without specifying:

1. **Default to Flux 2 Pro** — current strongest balanced model, broadest applicability
2. If they mention text-heavy use (posters, packaging, signage), suggest **Flux 2 Flex**
3. If they mention local/self-hosted, suggest **Flux 2 Dev** (or Flux 1 Dev if they reference an existing LoRA workflow)
4. If they mention iteration speed or volume, suggest **Flux 2 Klein** or **Flux 1 Schnell**
5. If they mention NSFW intent, suggest **Flux 2 Dev** or **Flux 1 Dev + uncensored LoRA**, noting the choice
6. If they reference a specific LoRA, default to **Flux 1 Dev** (most LoRAs are still Flux 1 ecosystem as of 2026)

When the user already specified a variant, use that variant and don't second-guess unless their prompt content is genuinely mismatched (e.g., they asked for Schnell but wrote a 200-word prompt — note that briefly and offer a trimmed version).

---

## Quick comparison table

| Variant | Length sweet spot | Hands | Text | Speed | License | NSFW-friendly |
|---|---|---|---|---|---|---|
| Flux 1 Dev | 30–80 words | weak | OK | medium | research/non-commercial | with LoRA |
| Flux 1 Pro | 30–80 words | weak | OK | fast (hosted) | commercial API | no (filtered) |
| Flux 1 Schnell | 15–40 words | weak | OK | very fast | Apache 2.0 | with LoRA |
| Flux 2 Pro | 50–150 words | good | great | medium (hosted) | commercial API | no (filtered) |
| Flux 2 Max | 50–150 words | great | great | slow (hosted) | commercial API | no (filtered) |
| Flux 2 Flex | 50–150 words | good | best-in-class | medium (hosted) | commercial API | no (filtered) |
| Flux 2 Dev | 50–150 words | good | great | medium (local) | research | yes |
| Flux 2 Klein | 20–50 words | OK | OK | very fast | Apache | yes |
