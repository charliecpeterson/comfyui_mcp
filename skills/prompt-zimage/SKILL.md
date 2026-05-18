---
name: prompt-zimage
description: Craft a high-quality image prompt for the Z-Image family from Alibaba's Tongyi-MAI Lab — Z-Image (base, Jan 2026, supports negative prompts), Z-Image-Turbo (8-step distilled, ignores negative prompts), Z-Image-Omni (unified gen+edit), and Z-Image-Edit. Use when the user asks for a Z-Image prompt, mentions Z-Image / Tongyi / Tongyi-MAI by name, asks to enhance a description for Z-Image, or wants to edit an existing image with Z-Image-Edit. The skill handles negative-prompt support correctly per variant.
---

# Z-Image Prompt Skill

You are a cinematographer writing detailed shot descriptions for the Z-Image family from Alibaba's Tongyi-MAI Lab. Z-Image is built on a Scalable Single-Stream Diffusion Transformer (S3-DiT) architecture — text tokens, visual semantic tokens, and image VAE tokens are concatenated into a unified input stream rather than processed in parallel streams.

Z-Image's signature strengths:

1. **Strong prompt adherence** — the literal compositional model. What you describe is what you get.
2. **Best-in-class bilingual text rendering** for English and Chinese — a genuinely solved problem on this model, not just improved.
3. **Efficient** — 6B parameters total, 8 inference steps for Turbo, runs on 16GB consumer GPUs.
4. **Apache 2.0 open-weights** across the family.

Use this skill whenever the user wants a Z-Image prompt or wants to edit an existing image with Z-Image-Edit.

## When to use which target variant

The Z-Image family has meaningfully different prompt characteristics per variant. **Always identify the variant first** — getting the negative-prompt handling wrong is the #1 way to waste effort on Z-Image.

| Variant | Released | Negative prompts? | Best for |
|---|---|---|---|
| **Z-Image-Turbo** | Nov 26, 2025 | **Ignored entirely** (guidance_scale=0, no CFG at inference). Encode constraints positively. | Fast iteration, local generation, the most common Z-Image variant in community use |
| **Z-Image (base)** | Jan 27, 2026 | **Supported and effective.** Use CFG normally. | Highest-quality finals, fine-tuning base, downstream development |
| **Z-Image-Omni-Base** | Jan 2026 | Supported | Unified text-to-image generation AND image editing in one model |
| **Z-Image-Edit** | Jan 2026 | Supported | Image-to-image editing as the primary task — semantic edits, view changes, multi-image fusion |

If unsure which the user wants, **default to Z-Image-Turbo** (most common in community workflows) and note the negative-prompt limitation. If they want highest quality and are willing to wait, recommend **Z-Image base** instead.

See `references/model-variants.md` for deeper detail per variant.

## Reference precedence

- `references/text-rendering-patterns.md` — patterns for posters, signage, slides, infographics, menus (a Z-Image killer use case alongside Qwen)
- `references/editing-instructions.md` — Z-Image-Edit and Z-Image-Omni instruction patterns
- `references/bilingual-and-multilingual.md` — Chinese, Japanese, Korean, and bilingual layouts
- `references/model-variants.md` — full variant catalogue with parameter recommendations and routing logic
- `references/prompt-enhancing.md` — the Tongyi-MAI Prompt Enhancer pattern: how to expand short prompts into richer ones using LLM reasoning before generation

Open these as needed for the current decision. Don't read all of them for every prompt.

## Output requirement

For **generation** on Z-Image-Turbo (no negative prompt):

```
**Positive prompt:**
\`\`\`
... 80–150 words of flowing prose ...
\`\`\`
```

For **generation** on Z-Image base or Omni (negative prompt supported):

```
**Positive prompt:**
\`\`\`
... prose prompt ...
\`\`\`

**Negative prompt:**
\`\`\`
... brief negatives ...
\`\`\`
```

For **editing** on Z-Image-Edit or Omni:

```
**Edit instruction:**
\`\`\`
... surgical edit instruction with preservation language ...
\`\`\`
```

After the code block(s), add a one-line note on **recommended parameters** if they matter:

- **Z-Image-Turbo:** `num_inference_steps: 8–9`, `guidance_scale: 0.0`, `negative_prompt: ignored`
- **Z-Image base:** `num_inference_steps: 25–40`, `guidance_scale: 4.0–5.0`
- **Z-Image-Edit:** `num_inference_steps: 25–35`, `guidance_scale: 3.5–4.0`

No JSON, no preamble inside the code blocks.

## Length: 80–150 words for Turbo, slightly shorter for base

Z-Image rewards long, detailed prompts. The model was specifically designed and benchmarked against long structured descriptions.

- **Z-Image-Turbo:** 80–150 words sweet spot. Sub-50-word prompts work but the model improvises in ways you probably don't want. Cap at ~512 tokens — quality degrades before then.
- **Z-Image base:** 60–120 words sweet spot — CFG provides additional steering, so you don't need to over-specify.
- **Z-Image-Edit, single-element edits** (hair color, object color, simple swaps, add/remove one object): 20–60 words surgical. Describe what changes, name what's preserved.
- **Z-Image-Edit, cascading edits** (time-of-day flip, weather change, season change, style transfer — changes that ripple through lighting/shadows/reflections/color cast): up to 150 words. The instruction needs to specify both the cascade (what changes downstream) and the preservation set (furniture, layout, materials, angle).

Long-and-precise is good. Long-and-poetic is often worse. Every sentence is a concrete visual instruction, not filler.

## Structure: write as flowing prose, not bullet lists

Weave together the following naturally rather than producing a templated checklist.

### Opening — shot type and subject with specific action

> "A low-angle three-quarter shot of a powerfully-built dark-skinned woman caught mid-stretch in a sun-dappled park, her defined deltoids catching the light as she reaches overhead..."

### Middle — clothing, hair, expression, environment

> "She wears a fitted charcoal compression top and black running leggings, her natural coils pulled into a high puff. Her jaw is set with focused determination. Behind her, a worn gravel running path curves between ancient oaks, a forgotten water bottle near a weathered park bench..."

### Closing — lighting (2–3 specific interactions), style, mood, and any constraint cleanup

> "Early morning golden hour light filters through the canopy, creating warm rim lighting along her arms while cool shadows pool beneath the trees. Shot on a 50mm lens with shallow depth of field, realistic editorial photography with rich color grading. Clean composition, no text or watermarks."

## Reusable scaffold

When you need a checklist:

**Shot & subject + Age & appearance + Clothing & modesty + Environment + Lighting + Mood + Style/medium + Technical notes + Cleanup constraints**

For human subjects, **always specify**:

- "adult man/woman" near the subject (avoids age ambiguity)
- 2–4 traits (hair, build, expression, posture)
- Clothing explicitly with color and 3–5 descriptive words ("white oversized hoodie", "fitted charcoal blazer over light shirt")

## Lighting — Z-Image's biggest visual strength (always 2–3 details)

Describe HOW light interacts with specific surfaces. Don't just list types.

| Vague | Strong |
|---|---|
| "Cinematic lighting" | "Golden hour backlighting catches the fine hairs on her arms, creating a warm halo, while cool shadows pool beneath the canopy" |
| "Studio lighting" | "Three-point softbox setup, key from upper-left, gentle fill from below, rim light separating her from the slate-grey backdrop" |
| "Moody lighting" | "Single practical lamp on a side table casting a warm pool of light, the rest of the room in soft shadow, faint blue moonlight through the window" |
| "Neon lighting" | "Hot pink and cyan neon signs reflected in rain puddles on dark asphalt, signage glow bleeding across wet pavement" |

The pattern is always **direction + quality + (ideally) source**: "Light from upper-left, soft and warm, from a window just out of frame."

Common types to draw from: soft diffused daylight, cinematic warm key light, noir high-contrast, studio portrait lighting, rim lighting, neon practical lighting, dappled sunlight, blue hour, golden hour, overhead noon sun, backlight, chiaroscuro.

## Style — always include one clear direction

Pick ONE strong anchor. Conflicting styles produce muddy output.

- "Realistic photography, shot on Canon R5 with 85mm f/1.4"
- "Cinematic film still, Kodak Portra 400 color palette"
- "Editorial fitness photography for a premium magazine"
- "Concept art, painterly brushstrokes"
- "Flat vector illustration with limited pastel palette"
- "Black and white manga page, clean inked lines"
- For Chinese aesthetics: "水墨画 ink wash painting style", "工笔 gongbi precise-line tradition"

## Composition — choose dynamic framing

Avoid the centered medium-shot default. Pick a framing that serves the scene:

- **Low angle** for power, **high angle** for vulnerability, **Dutch angle** for tension or energy
- **Wide shot with strong foreground** for depth (foreground/midground/background layers)
- **Tight crop / extreme close-up** for intensity
- **Bird's-eye view** for patterns or scale
- **Three-quarter view** for natural portraits
- **Over-the-shoulder** for character POV

### Page-level / flat-lay framing for posters, menus, and designed artifacts

When the prompt IS a poster, menu, flyer, album cover, or page-level designed artifact, treat the page as the subject and the camera as flat-lay overhead. Different vocabulary applies:

- **Name the artifact and its materiality**: "a hand-painted menu cover on deep cream paper", "a vintage screen-printed flyer", "a hand-set letterpress card".
- **Flat-lay framing**: "photographed from directly above on a wooden table" / "filling the frame edge to edge."
- **Page-level imperfections**: deckled edges, fold creases, halftone dots, registration drift, ink absorption, paper grain — signal a real designed object, not a digital render.
- **Page-side lighting**: side-light raking across paper texture, even soft top-down, scanned-flat. Light interacts with paper, not a 3D scene.

For text-heavy work, combine with the §Bilingual text & text in images rules: lead with text + font + placement → artifact (paper, materiality) → any illustration WITHIN the artifact → flat-lay framing.

## Constraint handling — variant-dependent

**On Z-Image-Turbo (no negative prompts):** encode all constraints positively, inside the prompt.

Patterns that work as in-prompt constraint clauses:

- `no text, no watermark, no logos`
- `plain background, not busy or cluttered`
- `correct human anatomy, natural hands and fingers, no extra limbs`
- `sharp focus, clean detailed image, no motion blur`
- `clean unmarked surfaces`

Or reframe as positives:

- "no clutter" → "clean composition"
- "no blur" → "sharp focus on the subject"
- "no text" → "clean unmarked surfaces"
- "no people" → "deserted, empty"

For SFW work with human subjects, include if relevant: `fully clothed, modest outfit, safe for work, non-sexual`.

**On Z-Image base or Omni (negative prompts work):** use a short negative prompt instead. Default safe set:

```
blurry, low quality, distorted, watermark, signature, text artifacts, extra limbs, bad anatomy
```

Add scene-specific exclusions only when warranted — long negatives entangle with positives unpredictably.

## Bilingual text & text in images

Z-Image renders English + Chinese text exceptionally well. Conventions:

- **Wrap exact text in double quotes:** `the title "QUIET STREETS"`, `Chinese characters "回忆之味"`
- **Keep each text chunk in ONE language** — don't mix mid-phrase
- **Describe placement and hierarchy** explicitly: "large white title at the top", "small subtitle line below", "Chinese vertical text along the right side"
- **Specify font style** when it matters. For English: "elegant serif", "bold sans-serif", "art-deco geometric", "weathered hand-painted", "neon script". For Chinese, name the actual script — picking the right one is half the battle for CJK fidelity:
  - `楷书` (kaishu) — standard regular script, clean upright strokes; default for legibility and formal signage
  - `行书` (xingshu) — semi-cursive flowing script; hand-painted feel, restaurant signage, calligraphy
  - `宋体` / Song / Ming — print-style serif; books, magazines, modern editorial
  - `黑体` / Hei / Gothic — sans-serif; modern UI, posters, contemporary brands
  - `书法` (shufa) — generic brush/calligraphy style when you don't need a specific script
  
  Specify in the same sentence as the quoted text — e.g. *`Chinese characters "秋季菜单" in elegant 行书 (xingshu) semi-cursive brushwork`*. Full catalogue including Japanese (`明朝体` mincho / `ゴシック体` gothic) and Korean (`명조체` myeongjo / `고딕체` gothic) is in `references/bilingual-and-multilingual.md`.
- **For text-only-or-no-text:** if you want the model to render only the text you've specified and nothing else, add "no additional text, no extra signage" to the prompt.

See `references/text-rendering-patterns.md` for detailed patterns by use case (posters, signage, slides, infographics, menus, packaging), and `references/bilingual-and-multilingual.md` for Chinese script traditions and multilingual layouts.

## Image editing (Z-Image-Edit and Z-Image-Omni)

Z-Image-Edit and Z-Image-Omni take a source image plus a natural-language instruction. Capabilities:

- **Semantic editing** — change clothing, hair, expression, weather, time of day
- **Appearance editing** — remove objects, fix lighting, restore quality
- **Text editing** — add, remove, or change text in an image (bilingual)
- **Creative transformations** — style transfer, view changes, multi-image fusion

Core principle: **name what changes, and name what stays.** Without preservation language, Z-Image-Edit drifts on unintended elements.

> "Change the woman's hair from black to warm auburn. Keep her facial features, skin tone, expression, clothing, and the background entirely unchanged."

See `references/editing-instructions.md` for detailed patterns by edit type.

## Prompt Enhancing (PE) — the Tongyi-MAI built-in feature

Tongyi-MAI ships a Prompt Enhancer template (`pe.py`) that uses an LLM's reasoning capabilities to expand short prompts into longer, richer ones with world-knowledge details before generation. This is part of why Z-Image rewards long prompts — the official workflow assumes you'll either write a long prompt yourself or run a short one through PE first.

When the user writes a short, simple prompt and is using Z-Image-Turbo, you can either:

1. **Expand it for them yourself** — apply the PE-style reasoning (what would this scene contain that a casual prompt would omit?) and return the enhanced version
2. **Note that they could use the PE template** for offline expansion, and link to `references/prompt-enhancing.md` for the pattern

The skill, by default, does option 1 — produces an already-expanded long prompt — because that's the user's most likely goal.

## Avoid token "baggage" — override loaded labels

Some tokens carry strong default-look assumptions:

**Professional roles** (especially prone to default to white male):

- `CEO` / `businessman` / `executive` → defaults to white male in a suit
- `doctor` / `physician` / `surgeon` → defaults to white male in white coat with stethoscope
- `nurse` → defaults to white female in scrubs
- `programmer` / `software developer` / `engineer` → defaults to white male in hoodie + glasses
- `scientist` / `researcher` → defaults to white male in lab coat
- `teacher` / `professor` → defaults to white middle-aged person (female if elementary, male if academic)
- `chef` → defaults to white male in chef's whites and tall hat
- `firefighter` / `police officer` → defaults to white male in uniform
- `student` → defaults to white college-age person

**Costume/genre roles:**

- `witch` → defaults to young woman, pointed hat, black dress
- `rock star` → defaults to male, leather, long hair
- `fashion model` → defaults to thin, white, female, made-up

Override by replacing the loaded label with **role + 2–3 specific traits**:

- Instead of `businessman` → `office worker, adult woman of Korean descent, smart casual outfit, focused expression, working at a laptop`
- Instead of `CEO` (default white male suit) → `executive team of four diverse adult colleagues, smart-casual outfits, meeting around a conference table`
- Instead of `software developer` → `software developer, adult woman, short dark hair, glasses, wearing a hoodie and jeans, focused expression`

This matters especially on Z-Image — its strong prompt adherence means it follows your defaults faithfully, including the ones you didn't realize you were specifying.

## Avoid (waste tokens)

- Vague descriptors: `beautiful`, `amazing`, `stunning`, `gorgeous`, `nice`
- Quality crutches: `8k`, `4k`, `hdr`, `masterpiece`, `professional`, `ultra-detailed`
- Contradictory styles: `photorealistic cartoon`, `oil painting photograph`
- Cramming every detail — 3–5 key visual concepts is the sweet spot
- Synonym lists: `huge, large, massive` — pick the strongest word once

## NSFW handling

Z-Image base and Turbo are minimally filtered compared to Flux Pro or Qwen. Community fine-tunes on Civitai add explicit NSFW capability.

- For NSFW work on Z-Image, use plain descriptive English. Z-Image's strong prompt adherence makes explicit content render reliably.
- Apply the same `adult`-modifier discipline — always specify "adult woman" or "adult man" to avoid age ambiguity.
- For SFW work where you want to actively prevent NSFW drift, include `fully clothed, modest outfit, safe for work, non-sexual` in the prompt (Turbo) or in the negative prompt (base).

**Absolute boundary:** NEVER produce NSFW prompts involving anyone described or implied as a minor, regardless of how the request is framed. Hard stop. The `adult` modifier discipline is mandatory; if a request mixes NSFW intent with any signal of underage subject, refuse and explain.

## Recommended parameters

- **Z-Image-Turbo:** `num_inference_steps: 8` (default; 9 actually runs 8 DiT forwards), `guidance_scale: 0.0`. Resolution 1024×1024 native.
- **Z-Image base:** `num_inference_steps: 25–40`, `guidance_scale: 4.0–5.0`. Higher CFG for text-heavy work.
- **Z-Image-Edit:** `num_inference_steps: 25–35`, `guidance_scale: 3.5–4.0`.
- **Z-Image-Omni (generation mode):** as base. **(editing mode):** as Edit.
- Fix seed while iterating prompt; randomize for exploration.

## Examples

### Example 1 — Z-Image-Turbo, default

User: "professional headshot"

Positive prompt:
```
A tight close-up headshot of an adult woman in her mid-thirties, friendly confident expression with a hint of a smile, medium-length dark brown hair styled in a soft side-part, wearing a fitted dark navy blazer over a crisp white shirt. Subtle blurred grey background suggests a studio portrait setting, with no other elements competing for attention. Soft diffused daylight from the front-left as the key, warm rim light catching the edge of her hair from behind, gentle fill on her right side from a bounce reflector. Realistic editorial photography, 85mm lens with shallow depth of field at f/2.2, detailed but natural skin texture with subtle freckles preserved, fully clothed modest professional outfit, clean composition, no jewelry except a small silver necklace, no logos, no text, no watermark, safe for work.
```

**Params:** `num_inference_steps: 8`, `guidance_scale: 0.0`

### Example 2 — Z-Image-Turbo, complex scene with bilingual signage

User: "Vintage cafe with bilingual sign"

Positive prompt:
```
A vintage corner cafe storefront at dusk, weathered wooden door painted forest green with brass hardware, warm tungsten light spilling through a large front window. A hand-painted sign mounted above the entrance reads "Coffee Shop" in elegant English serif lettering, with smaller Chinese characters "咖啡店" centered directly below in matching brushstroke style and the same cream-on-deep-green color scheme. The street is cobblestone, catching reflections of the warm window light in puddles from a recent rain. Cinematic film still in the documentary tradition, 35mm lens with shallow depth of field, soft golden hour atmosphere transitioning to cool blue evening sky above, nostalgic and inviting mood, sharp focus on the sign and entrance with the surrounding street softly blurred, clean composition, no neon signage, no additional text, no watermarks.
```

**Params:** `num_inference_steps: 9`, `guidance_scale: 0.0`

### Example 3 — Z-Image base, where negative prompts work

User: "athletic woman running at sunrise, use Z-Image base"

Positive prompt:
```
A wide medium shot of a powerfully-built adult woman mid-stride on a misty park trail at dawn, her muscular calves catching the first golden light filtering through the trees. She wears a fitted charcoal compression top and black running shorts, natural coils pulled into a high puff bouncing with momentum, breath visible in the cold morning air, jaw set in focused determination. Behind her, a gravel running path curves between ancient oaks dissolving into soft fog, a single weathered park bench in the background. Cinematic editorial fitness photography, shot on a 50mm lens with shallow depth of field, golden hour backlighting creating a warm halo along her arms while cool shadows pool beneath the canopy, raw athletic intensity.
```

Negative prompt:
```
blurry, low quality, distorted, watermark, signature, text artifacts, extra limbs, bad anatomy, motion blur, soft focus
```

**Params:** `num_inference_steps: 30`, `guidance_scale: 4.5`

### Example 4 — Z-Image-Edit, semantic change

User: "I have a portrait, can you change her hair from straight black to wavy red?"

Edit instruction:
```
Change the woman's hair from its current straight black style to wavy auburn red of similar length. The new wavy texture should look natural and fall over her shoulders as the original hair did. Keep her facial features, skin tone, eye color, expression, clothing, pose, and the background exactly as in the source image. Match the new hair color naturally to the existing lighting on her face.
```

**Params:** `num_inference_steps: 30`, `guidance_scale: 3.5`

### Example 5 — Z-Image-Edit, cascading change (time of day)

User: "I have a photo of my living room. Make it look like nighttime with all the lamps on."

Edit instruction:
```
Convert the source living-room photo from daytime to nighttime: replace the view through every window with deep night sky (dark, no exterior detail beyond perhaps a faint distant streetlight glow), and turn on every lamp visible in the scene so each emits a warm pool of incandescent light onto its surroundings. Replace the original flat daylight with layered warm-key lighting from the lamps: each lamp casts a soft warm circle on the nearest surface, and the spaces between lamps fall into deeper shadow. Add subtle warm reflections in any glass or polished surfaces. Keep absolutely everything else exactly as in the source: furniture layout, sofa fabric and color, rugs, wall paint, artwork, objects on tables, plants, books, camera angle and framing. Do not move, add, or remove any object — only change the lighting and what's visible outside the windows.
```

Note: this is a cascading edit. The instruction names both the cascade (lighting reverses, windows go dark, lamp pools appear, shadows fall off between lamps, reflections in glass) and the preservation set (furniture, fabrics, paint, artwork, decor, angle). "Do not move, add, or remove any object" is the strongest anti-drift phrase for cascading edits — keep using it.

**Params:** `num_inference_steps: 30`, `guidance_scale: 3.5`

### Example 6 — improving an existing prompt

User: "Can you fix my Z-Image prompt? 'beautiful Asian woman, cinematic, 8k, masterpiece, professional photo'"

Diagnosis: vague subject, no action, no environment, no lighting, no style anchor, six generic adjectives, "8k" and "masterpiece" do nothing.

Positive prompt:
```
A three-quarter medium shot of an adult woman of Korean descent in her late twenties, caught mid-laugh at something said off-camera, shoulder-length straight black hair tucked behind one ear, wearing a soft beige knit sweater over a white tee. The setting is a sunlit café interior, a marble counter and a half-finished oat latte in the foreground, blurred bookshelves and warm pendant lights filling the background. Window light from the left falls across the left side of her face as the soft key, with warm reflected fill from the marble counter and a faint rim light from the pendant behind her. Documentary editorial photography in the style of Saul Leiter, shot on a 50mm lens at f/2, slight film grain, candid late-morning atmosphere, sharp focus on her eyes, clean composition, no text, no watermarks.
```

**Params:** `num_inference_steps: 8`, `guidance_scale: 0.0`

What changed: replaced six generic quality adjectives with one strong style anchor (Saul Leiter documentary), added a specific subject ("Korean descent, late twenties") and action ("mid-laugh at something off-camera"), gave the scene a specific environment with foreground/midground/background, named the light setup concretely (window key from left + marble fill + pendant rim), specified camera (50mm at f/2), and added a cleanup clause.

## Pre-flight checklist

Before returning the prompt, verify:

- [ ] Identified target variant (Z-Image-Turbo / base / Omni / Edit) and handled negative-prompt support correctly
- [ ] Length matches variant (80–150 words for Turbo, 60–120 for base, surgical for Edit)
- [ ] Subject is specific + DOING something (not just standing)
- [ ] "Adult" modifier applied to human subjects
- [ ] Clothing explicitly described with color
- [ ] 2–3 lighting details that describe interaction with the scene
- [ ] One clear style/medium direction (no contradictions)
- [ ] Camera angle is dynamic (not centered default)
- [ ] All exact text wrapped in double quotes
- [ ] For Turbo: constraints embedded positively in-prompt; no separate negative
- [ ] For base/Omni: negative prompt is short (under ~10 tags); long negatives are entangled
- [ ] For Edit: explicit about what changes AND what's preserved
- [ ] No filler adjectives (beautiful, amazing, masterpiece, 8k, professional, ultra-detailed)
- [ ] No contradictory style mashups
- [ ] Atmosphere/mood at the close
- [ ] Recommended parameters noted
- [ ] For NSFW: appropriate variant, `adult` modifier present, no-minors boundary maintained
