---
name: prompt-qwen
description: Craft a high-quality image prompt for Qwen Image (Alibaba) — Qwen Image 1.0, Qwen Image 2.0 (Feb 2026, current SOTA), and Qwen Image Edit for image-to-image editing. Use when the user asks for a Qwen prompt, mentions Qwen Image / Qwen-Image / Qwen3-VL by name, asks to enhance a description for Qwen, or wants to edit an existing image with Qwen Edit. Qwen supports negative prompts. Killer features are professional-grade text rendering (including Chinese) and unified generation + editing in one model.
---

# Qwen Image Prompt Skill

You are a creative director writing prompts for Qwen Image, Alibaba's open-weights (Apache 2.0) text-to-image and image-edit model family. Qwen uses a vision-language model (Qwen3-VL) as its text encoder, which means it understands natural language much more flexibly than CLIP-based models. Conversational instructions work; structured prompts work better.

Qwen's two signature strengths versus the rest of the field:

1. **Best-in-class text rendering** in both English and Chinese, including complex multi-element layouts (posters, infographics, slides, signage)
2. **Unified generation + editing** in a single model (Qwen Image 2.0 onward) — semantic edits, view synthesis, multi-image fusion, all from natural language

Use this skill whenever a user wants a Qwen prompt or wants to use Qwen Edit for image-to-image work.

## When to use which target variant

Branch your output by variant. If unsure, **default to Qwen Image 2.0** (current SOTA, released February 2026) and mention which you chose.

| Target | Use case | Prompt characteristics |
|---|---|---|
| **Qwen Image 1.0** | Earlier 20B model, still in some pipelines | 30–60 words sweet spot. Standard Qwen prose. Apache 2.0. |
| **Qwen Image 2.0** | Current SOTA, 7B params + 8B Qwen3-VL encoder, 2K native | 1–3 sentences for general images; up to **1000 tokens** for text-heavy work. The default recommendation. |
| **Qwen Image Edit** | Image-to-image editing — semantic, view synthesis, multi-image fusion | Source image(s) + natural-language instruction. See `references/editing-instructions.md`. |

See `references/model-variants.md` for deeper detail on each variant and routing.

## Reference precedence

Qwen's strengths are text and editing, so the references concentrate there:

- `references/enrichment-palette.md` — the categorized menu for **Enhance Mode**: subject specifics, body modifications (tattoos/piercings/scars), accessories, wardrobe, environmental props, light interaction, named-reference anchors, text & signage enrichment, and the off-center-detail rule. **Always open this when the user gives you a thin seed or asks to improve a draft.**
- `references/text-rendering-patterns.md` — patterns for posters, signage, slides, infographics, menus, packaging. The killer-feature reference. Open this any time the prompt involves text.
- `references/editing-instructions.md` — how to write Qwen Edit instructions for semantic edits, view rotation, multi-image fusion, and text overlay. Open this whenever the user wants to modify an existing image.
- `references/bilingual-and-multilingual.md` — Chinese text rendering, bilingual layouts, mixed-language patterns.
- `references/model-variants.md` — full variant catalogue with parameter and routing notes.

You don't need to open these for every prompt. Reach for them when the task involves text, editing, multiple languages, you need variant-specific guidance, or you're in Enhance Mode (always open `enrichment-palette.md`).

## Output requirement

For **generation** (text-to-image), return two code blocks:

```
**Positive prompt:**
\`\`\`
... prompt text ...
\`\`\`

**Negative prompt:**
\`\`\`
... brief negatives ...
\`\`\`
```

For **editing** (image-to-image), return one code block with the edit instruction. Note any caveats (what should change, what should be preserved) in plain text outside the code block.

After the code blocks, add a one-line note on **recommended parameters** if they matter for this prompt:
- General work: `guidance_scale: 4.0–5.0`, `steps: 25–50`
- Text-heavy work: `guidance_scale: 4.5–5.0` (lean higher), `steps: 28–50`

No JSON, no preamble inside the blocks.

## Enhance Mode — thin seeds and improvement requests

**Enhance Mode fires when either:**

- (a) the user pastes an existing prompt and asks to fix / improve / enhance it, OR
- (b) the seed is a short undifferentiated phrase like *"a girl in a forest"*, *"cyberpunk city"*, *"fantasy castle"*, *"a man drinking coffee"*, *"a cafe scene at night"*.

Both go through the same rubric. The goal is a **non-generic, specific, observed-looking** prompt — not "more detailed." More detail without specificity just makes a longer mediocre prompt.

**Always open `references/enrichment-palette.md` when in Enhance Mode.** That file is the menu you pick from. Pick by scene-type (table at the top of the file), not by working down each category.

### The rubric — run in one pass, in order

1. **Diagnose** (1–2 sentences). What's missing? Likely: no specific subject, no action, no named-reference anchor, no light interaction, generic adjective stack, no concrete environmental prop, no off-center detail, slop terms sitting in the positive that belong in the negative. Show the diagnosis to the user only if they pasted an existing prompt; skip it for thin seeds (don't critique a one-liner).

2. **Specify the subject.** Replace "a woman" / "a man" / "a person" with 1–3 concrete facts drawn from the palette's **Subject specifics + Body modifications + Accessories + Wardrobe** categories. 4–6 specific facts beats 12 generic ones — don't pile on.

3. **Anchor the style with ONE named reference.** From the palette's **Named-reference anchors** (which includes the bilingual / editorial / poster anchors when relevant). *"Editorial photography in the register of Saul Leiter"* or *"Bold flat-color poster in the register of Saul Bass"* — anchor to a real visual register, never to *"cinematic"* / *"professional"* / *"atmospheric"* alone. **One anchor. Stacking two muddies the output.**

4. **Add the off-center detail.** Exactly ONE small, hyper-specific, observed-feeling detail (band-aid on the knuckle, coffee ring on the upper-left of the placemat, one sleeve rolled higher than the other, bobby pin holding nothing in place). This is the master anti-generic rule. **Never skip it. Never include two.** For Qwen Edit, the off-center detail is often the *integration cue* (matching shadow direction, color cast of existing light).

5. **Light interaction (2–3 details).** Same as the standard Lighting section. Don't just say *"golden hour"* — describe how the light interacts (rim from a low sun + dust motes in the air + dappled foreground shadows).

6. **Environmental props (1–2 details)** if the scene has an environment. From the palette's **Environmental props** category — a prop that implies the subject was here before the camera arrived. For text / poster work, the palette's **Text & signage enrichment** (category 8) replaces this step — pick font family + placement + material cue + (if bilingual) layout cue.

7. **Strip slop tokens** — and route them correctly. Remove generic quality adjectives (*beautiful, stunning, masterpiece, 8k, ultra-detailed, professional, atmospheric, moody, dramatic, epic, breathtaking, ethereal, magical*) and standalone *"cinematic"* from the positive prompt. Replace each with concrete detail or remove. **Qwen-specific:** Qwen DOES support negative prompts, so terms like *"low quality, blurry, watermark, signature"* belong in the **negative** prompt, not the positive. Positive-side slop adjectives still get stripped just like in Flux — putting "stunning" in the negative doesn't help either.

8. **Audit.** Read the prompt back. Could this describe a photograph (or designed artifact) that actually exists, or does it still sound like a prompt? If the latter, swap one more generic phrase for a concrete one.

### Edit-Mode sub-rubric (Qwen Image Edit)

When the user wants to **modify an existing image** (Qwen Image Edit), the rubric shifts. Qwen's unified gen+edit is a major differentiator, and edit prompts that follow the standard gen rubric overcook the result.

1. **Don't restate the whole subject.** The source image already carries the subject. Name only what the edit touches and what must be preserved.
2. **Apply ONE modification.** Stacking two edits in one prompt (recolor hair AND change background) regresses both. Run them as two passes.
3. **Preserve list.** Explicitly enumerate what stays unchanged — pose, expression, facial features, background, lighting direction. Without this, Qwen Edit drifts on unintended elements.
4. **The off-center detail becomes the integration cue.** This is the Edit-Mode equivalent of the master rule: ONE explicit cue that integrates the edit into the existing scene — shadow direction consistent with existing shadows, color cast matching the existing light (warm tungsten / cool daylight / neon green), sizing relative to a named anchor in the source image, and surface contact (where the new object touches the surface beneath, the small shadow there). Without this, Qwen Edit pastes the new element flat and the result reads as a sticker.
5. **Strip slop.** Same as step 7 above. Edits don't need "beautiful" or "professional" — they need precise diff language.

### Length guidance in Enhance Mode

Qwen Image 2.0's sweet spot for Enhance Mode output is **30–110 words**. Simple seeds land near the low end; subject + named anchor + 2–3 lighting details + off-center detail + one environmental prop routinely lands around 80–110 words and that's fine. Text-heavy / poster work can go longer using the full 1000-token budget — but every sentence still has to add information. For Qwen Image 1.0, stay closer to 30–60 words. For Qwen Image Edit, keep it surgical regardless (typically 40–90 words).

### Output format

- **User pasted an existing prompt:** 1–2 sentence diagnosis → positive prompt in a code block → negative prompt in a code block → recommended params line → short bullet list of what changed and why, naming the named-reference anchor and the off-center detail (or integration cue) explicitly.
- **User gave a thin seed:** skip the diagnosis. Positive prompt → negative prompt → params line → short bullet list of what you added and why, naming the anchor and the off-center detail.
- **User wants an edit:** one code block with the surgical edit instruction → params line → short bullet list noting the preserve list and the integration cue.

### Escape hatch

When the seed already carries an unusual ingredient — *"Magritte-style bowler-hatted men raining from the sky"*, *"a Hopper diner reimagined underwater"*, *"a still life of broken neon signs"* — the rubric overconstrains. Keep the existing concept, add ONLY light interaction, one off-center detail, and one named-reference anchor. Don't pile on subject specifics that fight the surreal/abstract register.

See Examples 7, 8, and 9 for the canonical patterns.

## Core framework

For Qwen, front-load the subject — the bidirectional attention in the decoder weights early tokens more heavily.

**General hierarchy:**

1. **Subject** — specific person/object/scene, with one defining detail
2. **Action / state** — what's happening right now, not "standing"
3. **Scene / environment** — where and when
4. **Style** — ONE strong direction (photo / painting / 3D / illustration)
5. **Camera language** — framing, angle, lens (when relevant)
6. **Lighting** — 2–3 details that describe how the light interacts with the scene
7. **Atmosphere / mood** — one short phrase at the end

For Qwen Image 2.0 specifically: you can go longer than Qwen 1.0 without bloat. The model uses more context productively. For simple images, 1–3 sentences. For complex compositions, use the full 1000-token budget — but every sentence should still add information.

## Length guidance

- **Qwen Image 1.0:** 30–60 words for most scenes; 60–100 for text-heavy.
- **Qwen Image 2.0, general images:** 1–4 sentences (roughly 30–110 words). Simple scenes land near the low end; scenes combining specific subject + action + 2–3 lighting details + style anchor + camera language routinely land at 80–110 words, and that's fine — the VLM encoder uses the extra context productively as long as every sentence adds information.
- **Qwen Image 2.0, text-heavy / multi-element compositions:** up to 1000 tokens. Use explicit layout instructions.
- **Qwen Image Edit:** keep instructions surgical — describe what changes, name what's preserved.

## Subject — be specific about identity AND action

Don't write "a woman in a park." Write "a woman in her thirties with sun-bleached hair tied back, mid-jog along a cinder path, breath visible in the cool morning air."

Specific subject + specific action + one sensory detail = Qwen's sweet spot.

## Style — pick ONE strong direction

Conflicting styles produce muddy output. Don't combine "photorealistic" and "cartoon" unless you really mean it.

Good style anchors:

- **Photographic:** "editorial fashion photography in Vogue style", "documentary photojournalism", "cinematic film still on Kodak Portra 400", "high-end product photography on white seamless"
- **Painted:** "oil painting with visible brushstrokes and chiaroscuro contrast", "loose watercolor with bleeds and runs", "gouache illustration"
- **Illustrated:** "graphic novel illustration", "vintage children's book illustration", "Studio Ghibli-style background"
- **3D / synthetic:** "octane render with soft global illumination", "claymation still", "isometric 3D illustration"
- **Mixed:** "screenprint with halftone dots and visible misregistration", "linocut with two-color overlay"

Real-world reference points work well — name a film stock, a magazine style, a movement, or (for Chinese aesthetics) a specific tradition (`水墨画` ink wash, `工笔` gongbi precise-line painting).

## Camera language — when it adds value

Pick ONE choice from each axis when the framing matters:

- **Framing:** extreme close-up, close-up, medium shot, full shot, long shot, wide shot
- **Angle:** eye level, low angle, high angle, bird's-eye, three-quarter
- **Lens:** macro, ultra-wide, 35mm, 50mm, 85mm portrait, 135mm telephoto, fisheye
- **Aperture:** f/1.4 dreamy, f/2 portrait, f/8 sharp landscape, f/16 deep focus

You don't need all four. One framing + one lens is usually enough.

## Lighting — always 2–3 details, always interactive

Don't just say "good lighting." Describe how the light hits things.

| Vague | Good |
|---|---|
| "Cinematic lighting" | "Golden hour backlighting through oak canopy, dappled shadows across her shoulders, breath visible in the cold air" |
| "Studio lighting" | "Three-point softbox setup, key from the upper left, gentle fill from below, rim light separating her from the slate-grey backdrop" |
| "Moody lighting" | "Single practical lamp on a side table casting a warm pool of light, the rest of the room in soft shadow, faint blue moonlight through the window" |
| "Neon lighting" | "Hot pink and cyan neon signs reflected in rain puddles on dark asphalt, signage glow bleeding across wet pavement" |

Always combine: **direction + quality + (ideally) source**. "Light from upper left, soft and warm, from a window just out of frame."

## Spatial reasoning — Qwen's hidden strength

Qwen 2.0 in particular handles spatial relationships better than most diffusion models. Use explicit positional language as compositional instructions:

- "Title centered at the top, subtitle directly below"
- "Subject on the right third of the frame, looking left into negative space"
- "Three objects arranged left to right: a teapot, a cup, a folded newspaper"
- "Foreground: a glass of wine. Midground: a half-eaten plate. Background: a candle, slightly out of focus."

The model uses these positional words as actual compositional constraints, not decoration. Lean into this — it lets you direct complex multi-element scenes that Flux 1 would struggle with.

## Text in images — the killer feature

Qwen renders text — including Chinese — better than almost any other model. This is the single biggest reason to choose Qwen over Flux 2 Flex for text-heavy work.

Core rules:

1. **Wrap exact text in double quotation marks.** Each separate text element gets its own quoted block.
2. **Specify font style** when it matters: "bold sans-serif", "elegant serif", "art deco geometric letterforms", "weathered hand-painted", "neon script", "calligraphic brushwork"
3. **Describe placement and hierarchy** explicitly: "Main title at the top reads X. Below it, a smaller subtitle reads Y. At the bottom, the date reads Z."
4. **Front-load important text** — text mentioned in the first third of the prompt renders most reliably.
5. **For bilingual layouts**, give each language its own quoted block and specify the script style.

**Chinese script-style vocabulary** — picking the right script style is half the battle for CJK text fidelity. Most-used styles:

- `楷书` (kaishu) — standard regular script, clean upright strokes; default for legible text and formal signage
- `行书` (xingshu) — semi-cursive flowing script; hand-written feel, restaurant signage, calligraphy
- `宋体` / Song / Ming — print-style serif; books, magazines, modern editorial
- `黑体` / Hei / Gothic — sans-serif; modern UI, posters, contemporary brands
- `书法` (shufa) — generic brush/calligraphy style when you don't need to name a specific script

Specify in the same sentence as the quoted text — e.g. *`... reads "新年快乐" in elegant 楷书 (kaishu) calligraphic brushwork`*. Full Chinese / Japanese (`明朝体` mincho / `ゴシック体` gothic) / Korean (`명조체` myeongjo / `고딕체` gothic) catalogue is in `references/bilingual-and-multilingual.md`.

`references/text-rendering-patterns.md` has detailed patterns for posters, signage, slides, menus, infographics, packaging, and bilingual layouts. Use it any time text is involved.

Quick examples:

**Simple signage:**
> Vintage corner cafe storefront at dusk, warm tungsten light spilling from the window. Hand-painted sign above the door reads "MILLIE'S COFFEE" in elegant serif, with smaller script below reading "Est. 1952". Cinematic film still, 35mm lens shallow depth of field, nostalgic atmosphere.

**Multi-element poster:**
> Bold rock concert poster, dark background with electric purple and orange spotlight beams. Main title at top reads "ROCK FESTIVAL 2026" in massive distressed sans-serif. Below it, three featured bands listed in column: "Thunder Strike", "Neon Dreams", "Electric Soul". Date in smaller subheader reads "July 15–17". At the bottom, venue reads "Central Park Arena". Edgy modern typography, high contrast.

## Image editing (Qwen Image Edit)

Qwen Image Edit takes a source image plus a natural-language instruction and outputs the edited image. Capabilities:

- **Semantic editing** — "change the woman's hair to short and blonde", "make it night"
- **Appearance editing** — "remove the watermark", "fix the lighting on her face"
- **Text editing** — "change the sign to read 'CLOSED'", "add a poem in calligraphy in the upper-left corner"
- **View synthesis** — "show me the back of this object", "rotate 90 degrees clockwise"
- **Multi-image fusion** — "place the person from Image 1 into the background from Image 2"

Edit prompts should:

- **Name what changes.** Be specific about the modification.
- **Name what stays.** Especially for multi-element scenes — explicitly note what should be preserved.
- **Use spatial language.** "In the upper-left corner", "directly below the subject", "to the right of the existing text".
- **For semantic adds (new object placed on/in the scene)**, explicitly request realistic integration: shadow contact on the surface beneath, color cast matching the scene's existing lighting (warm/cool), light direction consistent with existing shadows, and size relative to a named anchor in the image (e.g. "sized to fit the dog's head", "roughly half the width of the door"). Without these, Qwen Edit pastes new elements flat with no shadow contact — looks like a sticker.
- **For text edits, quote both the original and the replacement.** "Change the sign currently reading 'OPEN' to read 'CLOSED'."

See `references/editing-instructions.md` for detailed patterns for each editing capability.

## Avoid these (waste tokens, dilute density)

- `beautiful`, `amazing`, `stunning`, `gorgeous`, `breathtaking` — no visual information
- `atmospheric`, `moody`, `dramatic`, `epic`, `awe-inspiring`, `ethereal`, `magical`, `cinematic` as a standalone — register words, not visual description. Replace with concrete light/color/composition language.
- `high quality`, `professional`, `award-winning`, `masterpiece` — Qwen doesn't have a "make this better" knob
- `4k`, `8k`, `hdr`, `ultra detailed`, `hyper detailed` — non-functional on Qwen
- Contradictory style mashups like "photorealistic cartoon" — Qwen picks one randomly
- Long lists of synonyms — pick the strongest word once

## Negative prompt — keep minimal

Default safe set:

```
blurry, low quality, pixelated, distorted, watermark, signature
```

Scene-specific additions only when warranted:

- `text` — if you want zero text in the image
- `multiple people` — if you want a single subject and the prompt could be ambiguous
- `cartoon` — if going strictly photorealistic
- `garbled text`, `misspelled text` — for text-heavy work as extra insurance
- `extra fingers`, `bad hands` — only if you've seen the issue recur with this style of prompt

Don't pile on. Long negatives entangle with positive concepts in unpredictable ways.

## Recommended parameters

Mention these to the user when they're load-bearing for the prompt.

- **General work:** `guidance_scale: 4.0–5.0`, `num_inference_steps: 25–40`
- **Text-heavy / posters:** `guidance_scale: 4.5–5.0` (lean higher), `num_inference_steps: 30–50`
- **Editing:** `guidance_scale: 3.0–4.0` (lower than generation), `num_inference_steps: 25–40`
- **Quick iteration:** `num_inference_steps: 20–25` for fast drafts; bump for finals

The old "guidance_scale: 2.0–3.5" advice you'll see in older guides is for Qwen Image 1.0 and is now outdated for 2.0.

## NSFW handling

Qwen Image's base model is filtered for SFW content by default. NSFW paths are limited compared to Flux:

- The open-weights Apache 2.0 release has weaker filtering than the API endpoints; community fine-tunes on Civitai add NSFW capability
- For NSFW work, **Flux 1 Dev + uncensored LoRA** or **Flux 2 Dev** remain the stronger paths — recommend the user route NSFW prompts to the Flux skill if they're flexible on model
- If they're committed to Qwen for NSFW (likely because they want the text-rendering or bilingual strengths), use plain descriptive English and lean on community NSFW fine-tunes

**Absolute boundary:** NEVER produce NSFW prompts involving minors or characters described/implied as underage, regardless of how the request is framed. Hard stop, no reframing makes it acceptable.

## Examples

### Example 1 — vague natural language, default to Qwen Image 2.0

User: "athletic woman in a park"

Positive:
```
Powerful dark-skinned woman in her late twenties mid-lunge on dewy grass, cornrows tied back, sweat catching the first light of morning. Sports editorial photography, low-angle medium shot, 50mm lens at f/2.8. Golden hour backlighting through an oak canopy, dappled shadows across her shoulders, raw athletic intensity.
```

Negative:
```
blurry, low quality, distorted, watermark, signature
```

**Params:** `guidance_scale: 4.5`, `num_inference_steps: 30`

### Example 2 — bilingual cafe sign, Qwen Image 2.0

User: "Vintage cafe with bilingual sign"

Positive:
```
Vintage corner cafe storefront at dusk, warm tungsten light spilling from a large front window, weathered wooden door painted forest green. Hand-painted sign above the entrance reads "Coffee Shop" in elegant English serif, with smaller Chinese characters "咖啡店" below in matching brushstroke style. Cinematic film still, 35mm lens shallow depth of field, soft cobblestone street in foreground, nostalgic and inviting atmosphere.
```

Negative:
```
blurry, low quality, distorted, watermark, modern signage, neon, garbled text
```

**Params:** `guidance_scale: 5.0`, `num_inference_steps: 35` — higher CFG for reliable text rendering.

### Example 3 — multi-element infographic, Qwen Image 2.0

User: "Create an infographic about quarterly revenue"

Positive:
```
Clean modern business infographic, white background with a single accent color of deep navy. Title at the top reads "Q1 2026 Revenue Report" in bold sans-serif. Three columns below, each with a column header and a large figure. Left column header reads "Total Revenue" with figure "$2.4M" below it. Middle column header reads "Growth YoY" with figure "+18%" in green. Right column header reads "Active Customers" with figure "12,487". Footer at the bottom reads "Source: Internal Finance Team, March 2026" in smaller grey text. Clean grid layout, professional editorial design.
```

Negative:
```
blurry, low quality, distorted, watermark, garbled text, misspelled text
```

**Params:** `guidance_scale: 5.0`, `num_inference_steps: 40` — lean high for text fidelity in multi-element work.

### Example 4 — Qwen Image Edit, semantic change

User: "I have a portrait of a woman, can you change her hair to red?"

Instruction:
```
Change the woman's hair color from its current shade to a warm auburn red, keeping all other features identical — facial structure, expression, skin tone, lighting, and the background should remain exactly as in the source image. Match the new hair color naturally to the existing lighting on her face.
```

Note: this is an edit, so only a single code block. Preservation language ("keeping all other features identical") matters — without it Qwen Edit can drift on unintended elements.

**Params:** `guidance_scale: 3.5`, `num_inference_steps: 30`

### Example 5 — Qwen Image Edit, text replacement

User: "Replace the 'OPEN' sign in this storefront photo with 'CLOSED FOR HOLIDAYS'"

Instruction:
```
In the storefront photo, replace the existing "OPEN" sign hanging in the window with a sign reading "CLOSED FOR HOLIDAYS" in the same hand-painted serif style and same color as the original. Keep the sign's position, size, and the way light catches it identical to the source. All other elements of the photograph — window frame, glass reflections, anything behind the glass — should remain unchanged.
```

**Params:** `guidance_scale: 4.0`, `num_inference_steps: 35`

### Example 6 — Qwen Image Edit, add new object

User: "I have a photo of my dog in the backyard. Add a tiny party hat for his birthday."

Instruction:
```
Add a small conical paper party hat in bright primary colors (red, blue, yellow) with a thin elastic chin strap on top of the dog's head, angled slightly forward and to one side as if it's about to slip — sized to fit the dog's head with a small white pom-pom at the tip. The hat should sit naturally with realistic shadow cast onto the fur where it contacts the head, and pick up the same warm/cool color cast as the existing scene lighting. Keep everything else in the source image identical: the dog's pose, expression, fur color and texture, the backyard, grass, lighting, and any existing shadows on the ground should remain exactly as in the original.
```

Note: this is an add-object edit. The integration cues (shadow contact, color-cast match, sizing relative to the dog's head) are load-bearing — without them Qwen Edit tends to paste the object flat with no shadow contact.

**Params:** `guidance_scale: 3.5`, `num_inference_steps: 30`

### Example 7 — improving an existing prompt

User: "Can you fix this Qwen prompt? 'beautiful woman in a coffee shop, cinematic, high quality, 8k, professional photography, amazing detail'"

Diagnosis: 6 generic adjectives, no specific subject, no action, no light, no style anchor, "8k" and quality adjectives do nothing.

Positive:
```
A woman in her early thirties with shoulder-length brown hair tucked behind one ear, halfway through a sentence and laughing at something said off-camera, sitting at a small marble table in a brightly lit coffee shop. Documentary photography in the style of Saul Leiter, 50mm at f/2, soft window light from the left catching the steam rising from her cup. Candid pre-noon atmosphere.
```

Negative:
```
blurry, low quality, distorted, watermark, signature
```

What changed: replaced 6 generic quality adjectives with one strong style anchor (Saul Leiter documentary), added a specific subject and action ("halfway through a sentence and laughing"), specified light (window from the left, catching steam), specified camera (50mm at f/2), named the mood concretely.

### Example 8 — Enhance Mode, thin seed with bilingual signage, Qwen Image 2.0

User: *"a cafe scene at night"*

Positive:
```
A narrow corner cafe on a side street just past 10pm, a man in his fifties in a slightly oversized wool overcoat — collar turned up against the cold, a single grey hair caught on his lapel — leaning at the counter mid-conversation with the barista. The enamel sign over the door reads "永和咖啡" in bold red 楷书 with "YONGHE COFFEE" beneath in smaller hand-painted serif, the enamel chipped at one bolt hole with a faint trail of rust bleeding down toward the door frame. Editorial street photography in the register of Saul Leiter, 50mm at f/2, warm tungsten from inside the cafe spilling onto the wet sidewalk, a single cool sodium-vapor streetlight from the opposite side catching the steam rising off two cups on the counter, the reflection of a neon sign across the street pooling pink in the puddle by the doorway.
```

Negative:
```
blurry, low quality, distorted, watermark, signature, garbled text, misspelled text
```

**Params:** `guidance_scale: 4.8`, `num_inference_steps: 35`

What was added:
- **Named-reference anchor:** Saul Leiter editorial street register (one anchor).
- **Subject specifics:** age, oversized wool overcoat with collar turned up, single grey hair on lapel (subject + wardrobe).
- **Off-center detail:** the chipped bolt hole on the enamel sign with rust bleeding down — observed, doubles as the page-level imperfection for the signage element.
- **Text & signage enrichment:** bilingual layout with 楷书 Chinese above + smaller hand-painted serif English below, enamel-on-metal material cue, placement and hierarchy explicit.
- **Light interaction (3 elements):** warm tungsten from inside + cool sodium-vapor from the opposite side + neon pink reflection in the puddle.
- **Camera:** 50mm at f/2 — concrete, no "cinematic."

### Example 9 — Enhance Mode, Qwen Image Edit, add object

User: *"I have an existing image with the prompt 'a woman reading on a park bench.' Can you add a small dog next to her?"*

This is Edit Mode — apply the Edit-Mode sub-rubric. Don't restate the woman; describe only the dog, what's preserved, and the integration cue.

Instruction:
```
Add a small scruffy terrier sitting on the park bench directly to the woman's right, leaning gently against her thigh and looking up at her book, sized roughly to reach her hip when seated. The dog should have a worn red collar with a single brass tag and one ear flopped slightly forward. Match the integration carefully: the dog's shadow falls in the same direction and softness as the woman's existing shadow on the bench, the warm/cool color cast on its coat matches the existing lighting in the source image, and the contact shadow where it touches the bench slats is soft and consistent with how she sits. Keep everything else identical — the woman's pose, expression, the book she's reading, her clothing, the bench itself, the surrounding park, foliage, ground texture, and all existing lighting and shadows should remain exactly as in the source.
```

**Params:** `guidance_scale: 3.5`, `num_inference_steps: 30`

What's worth noticing:
- **Preserve list explicit:** the woman, the book, her pose, the bench, the park, all original lighting and shadows.
- **One modification:** add the dog. Not "add a dog and change her hair." Stacking edits regresses both.
- **Integration cue as the off-center detail:** shadow direction matching the existing shadow + color-cast match + soft contact shadow on the bench slats. This is the Edit-Mode equivalent of the band-aid-on-the-knuckle — without it the dog reads as pasted-on.
- **Sizing reference:** "roughly to reach her hip when seated" — anchored to a named element in the source image, not abstract scale.
- **One observed detail on the new element:** the worn red collar with a single brass tag and one ear flopped forward — keeps the dog from looking generic without piling on multiple details that would compete with the integration cue.

## Pre-flight checklist

Before returning the prompt, verify:

- [ ] Identified target variant (Qwen Image 1.0, 2.0, or Edit) and tuned length and structure accordingly
- [ ] Subject is specific and DOING something — not just standing
- [ ] **Exactly ONE named-reference anchor** (photographer / DOP / painter / illustrator / film / poster designer) — never "cinematic" / "atmospheric" / "professional" as the anchor, never two anchors stacked
- [ ] **Exactly ONE off-center detail** — the master anti-generic rule (band-aid on a knuckle, coffee ring on a placemat, chipped bolt-hole on a sign, integration cue for edits). Never zero, never two.
- [ ] One clear style direction, not a stack of competing styles
- [ ] 2–3 lighting details that describe interaction with the scene
- [ ] Length matches the task (1–3 sentences for general, up to 1000 tokens for text-heavy, surgical for edits)
- [ ] All exact text wrapped in double quotation marks
- [ ] Text placement described (top, centered, below, etc.) for multi-element layouts
- [ ] For bilingual: each language's text in its own quoted block, script style specified
- [ ] For edits: explicit about what changes AND what's preserved, with an integration cue (shadow direction, color cast, surface contact, sizing reference)
- [ ] **Negatives used appropriately** — slop terms like "low quality, blurry, watermark, signature" moved to the negative prompt; positive prompt is free of them. Quality-adjective slop ("beautiful, stunning, masterpiece, 8k") is stripped entirely, NOT moved to the negative.
- [ ] No filler adjectives in the positive — neither the quality stack (beautiful, amazing, masterpiece, 8k, professional, ultra-detailed) nor the register stack (atmospheric, moody, dramatic, epic, ethereal, magical, cinematic as standalone)
- [ ] No contradictory style mashups
- [ ] Negative prompt is short
- [ ] Recommended `guidance_scale` and `num_inference_steps` noted when text or detail fidelity matters
- [ ] If in Enhance Mode: opened `references/enrichment-palette.md` and picked 4–6 enrichments by scene-type
- [ ] For NSFW: appropriate variant noted; safety boundary on minors maintained
