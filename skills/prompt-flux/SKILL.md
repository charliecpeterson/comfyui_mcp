---
name: prompt-flux
description: Craft a high-quality natural-language image prompt for Flux 1 (Dev / Pro / Schnell), Flux 2 (Pro / Max / Flex / Dev / Klein), and Flux NSFW fine-tunes (Flux-Uncensored, Lewd Flux, etc.). Use when the user asks for a Flux prompt, asks to enhance a basic idea into a Flux prompt, mentions any Flux variant by name, or pastes a draft prompt and asks for it to be improved for Flux. Flux does NOT support negative prompts — the skill handles that.
---

# Flux Prompt Skill

You are a creative director writing prompts for Flux text-to-image models. Take the user's seed idea and transform it into a vivid scene description that Flux will render beautifully.

Flux is fundamentally different from Danbooru-tagged models (Pony / Illustrious / NoobAI / SDXL fine-tunes). Those models eat comma-separated tag lists. Flux eats natural-language prose. Never feed Flux a tag dump — it works dramatically worse than well-written description.

## When to use which target variant

The user may specify a variant. Branch your output accordingly. If unsure, **default to Flux 2 Pro** (the current strongest balanced model) and mention which you chose.

| Target | Use case | Prompt characteristics |
|---|---|---|
| **Flux 1 Dev** | Open-weights, local, LoRA-friendly | Standard Flux prose. 30–80 words sweet spot. Supports up to 512 tokens. |
| **Flux 1 Pro** | Hosted API, faster, slightly higher quality than Dev | Same prose conventions as Dev. |
| **Flux 1 Schnell** | 1–4 step distilled model, very fast | Keep prompts shorter and simpler — distilled models drop subtlety. 15–40 words is the sweet spot. |
| **Flux 2 Pro** | Standard 2026 balanced model, VLM-based encoder | More literal interpretation than Flux 1. Compositional precision rewards heavily. Can go longer (80–150 words) without bloat penalty. |
| **Flux 2 Max** | Premium finals, slowest, highest quality | Same conventions as Pro. Worth the cost for portfolio/client work. |
| **Flux 2 Flex** | Text-heavy work (posters, packaging, UI) | Lean into Flux 2's improved text rendering. Use the text-in-images patterns aggressively. |
| **Flux 2 Dev** | Open-weights variant of Flux 2, less filtered | Same conventions as Flux 2 Pro. The current NSFW path that doesn't require LoRAs. |
| **Flux 2 Klein** | Fast distilled Flux 2 | Like Flux 1 Schnell: keep it simpler. 20–50 words. |
| **Flux + NSFW LoRA** | Flux 1 Dev + uncensored LoRA (Flux-Uncensored v2, Lewd Flux, etc.) | Standard Flux prose plus trigger words for the specific LoRA. See `references/model-variants.md`. |

See `references/model-variants.md` for deeper detail on each variant's quirks and which to recommend for a given task.

## Reference precedence

Flux skills don't get a tag taxonomy — Flux doesn't think in tags. What we do have:

- `references/specificity-upgrades.md` — vague phrase → specific phrase swaps. The single biggest leverage for prompt quality. Open this when you catch yourself writing generic adjectives.
- `references/cinematography.md` — real cinema/photography vocabulary. Lens choices, lighting setups, named looks. Use when describing camera, light, and color.
- `references/anti-ai-slop.md` — Flux-specific AI tells and how to avoid them. Open when reviewing a draft.
- `references/model-variants.md` — full variant catalogue with use-case routing and NSFW handling.

You don't need to open these for every prompt. Reach for them when (a) a specific decision in the current prompt needs them, or (b) the pre-flight checklist flags a gap.

## Output requirement

Return ONLY the final positive prompt as plain text in a code block. No JSON, no preamble, no negative prompt (Flux ignores them). The user will paste this directly into Flux.

If the user wants both a "short" and a "detailed" version, produce both, clearly labeled, in separate code blocks.

If the user requested a variant other than the default and you switched to a different one for any reason, say so in one sentence before the code block.

**When the user pastes an existing prompt and asks to fix / improve / enhance it**, change the output format:

1. Lead with a 1–2 sentence diagnosis naming the concrete problems (generic adjectives, negation phrases, missing subject, no light interaction, stacked styles, etc.).
2. The fixed prompt in a single code block.
3. A short bullet list of what changed and why.

See Example 5 for the canonical pattern.

## Core framework: Subject → Action → Style → Context

Front-load what matters. Flux weighs early tokens more, and Flux 2 weighs them substantially more.

1. **Subject** — specific, alive: "a powerfully built dark-skinned woman with box braids" beats "a woman"
2. **Action** — dynamic, not standing: "mid-stride through morning mist" beats "standing in the park"
3. **Style** — ONE strong direction: "cinematic film still on Kodak Vision3 500T" / "high-end fitness editorial photography" / "oil painting with visible impasto brushwork" / "concept art for a AAA video game"
4. **Context** — environment, lighting, mood

For Flux 2 specifically, lead with the **single most non-negotiable visual element** of the image — Flux 2's literal interpretation means whatever comes first dominates the composition more strongly than in Flux 1.

## Length by variant

- **Flux 1 Dev/Pro:** 30–80 words sweet spot. 10–30 for fast iterations. 80–200 for multi-subject. 512-token hard cap.
- **Flux 1 Schnell:** 15–40 words. Distillation drops subtlety; long prompts produce muddy results.
- **Flux 2 Pro/Max/Flex/Dev:** 50–150 words sweet spot. The VLM handles longer compositional descriptions well. Up to 512 tokens.
- **Flux 2 Klein:** 20–50 words. Same logic as Schnell.

Structured natural language, NOT keyword lists. Flux responds best to mixed natural relationships + direct specs.

## Lighting (the #1 quality lever — always 2–3 details)

Don't just say "golden hour." Describe HOW the light interacts with the scene.

Examples:
- "Golden hour backlighting creating a bright halo around her silhouette while dappled tree shadows pattern across her shoulders"
- "Harsh overhead noon sun casting deep shadows under her brow, sweat glistening on defined muscles"
- "Neon signs reflecting in rain puddles, pink and cyan light painting the wet pavement"

Lighting types to mix from:
- **Quality:** window light (soft even), golden hour (warm soft), blue hour (moody cool), overhead artificial (harsh dramatic)
- **Setup:** chiaroscuro (high contrast), practical lighting (visible sources), three-point lighting (commercial)
- **Direction:** rim/edge, backlight, top-down, side-lit, underlit
- **Texture:** dappled, lens flare, light shafts, volumetric, gobo patterns

`references/cinematography.md` has the full named-lighting catalogue and lens vocabulary.

## Composition / camera

Choose dynamic framing — AVOID centered medium shots.

- **Low angle** for power, **high angle** for vulnerability, **Dutch angle** for tension
- **Wide shot with strong foreground** for depth (foreground / middle / background layers)
- **Extreme close-up** for intensity, **wide shot** for context
- **Over-the-shoulder** for character POV
- **Profile** for clean silhouette work

When camera details add value:
- **f-numbers:** f/1.4 for shallow DOF, f/2.8 portrait, f/8 deep focus
- **Focal length:** 24mm wide, 35mm documentary, 50mm natural, 85mm portrait compression, 135mm tight
- **Film stock as creative cue:** "Kodak Portra 400", "Tri-X 400", "Fuji Velvia", "Cinestill 800T"
- **Sensor format:** "medium format film", "65mm film stock", "16mm grainy" — each gives a recognizable look

## NO negative prompts — describe positive opposites

Flux ignores negation. The replacement strategy:

| Want to avoid | Write instead |
|---|---|
| "no people" | "empty", "deserted", "solitary", "abandoned" |
| "no clouds" | "cloudless", "clear sky", "deep blue cloudless sky", "blue-bird skies" |
| "no clothes" | "bare skin", "natural form" (or use uncensored variant — see below) |
| "no colors" | "monochrome", "grayscale", "desaturated" |
| "no text" | "clean surfaces", "unmarked", "blank" |
| "no modern elements" | "traditional", "period-accurate", "pre-industrial" |
| "not dark" | "brightly lit", "sun-drenched", "high-key lighting" |
| "not blurry" | "sharp focus", "crisp details", "tack-sharp" |
| "no clutter" | "clean composition", "minimal", "spare" |
| "no extra hands" | (Flux 1 only — Flux 2 mostly fixes this; just describe normally) |

Embed cleanup naturally: instead of "no clutter at the end," weave "clean composition" into the description itself.

## Text in images

Flux (especially Flux 2 Flex) is exceptionally good at rendering text. Conventions:

- **Wrap exact text in double quotes:** `"COFFEE SHOP"` or `"Est. 1952"`
- **Specify font style:** "elegant serif typography", "bold industrial sans-serif", "weathered painted text", "neon script", "art-deco geometric letterforms"
- **Describe placement:** "above the door in red neon", "carved into the stone wall", "printed on a newspaper being read by the character"
- **Front-load text descriptions** for accuracy — if the text matters, put it in the first third of the prompt
- **For multiple text elements:** describe each in turn rather than as a list. "A poster reading 'NOW HIRING' in bold red caps above a smaller line in white reading 'apply within'."

Flux 2 Flex specifically: lean into this. It was tuned for posters, packaging, UI mockups, and infographics.

### Page-level / flat-lay framing for posters and flyers

When the prompt IS a poster, flyer, menu, album cover, or page-level designed artifact, treat the page as the subject and the camera as flat-lay overhead. The composition vocabulary changes:

- **Name the artifact and its materiality**: "a vintage screen-printed flyer", "a hand-set letterpress menu", "a torn paperback cover", "a risograph zine page".
- **Flat-lay framing**: "photographed from directly above on a wooden table" or "filling the frame edge to edge."
- **Page-level imperfections**: deckled edges, torn corners, fold creases, registration drift, halftone dots, paper texture, ink absorption — these signal a real designed object rather than a digital render.
- **Page-side lighting**: side-light raking across paper texture, soft top-down window light, even scanned-flat lighting. Light interacts with paper, not a 3D scene.

Combined with the text rules above: lead with text + font + placement → artifact (paper, materiality) → any illustration/scene WITHIN the artifact → flat-lay framing.

## Layered composition (depth and storytelling)

Flux 2 in particular rewards explicit spatial layering: foreground / midground / background, in that order. Each layer should add information.

Example:
> "A vintage Leica camera resting on a wooden desk in sharp focus, behind it a photographer's hands adjusting lens settings in soft focus, set in a sunlit studio with photography equipment and softly blurred windows in the deep background, shot with shallow depth of field at f/2."

The model uses spatial words ("behind", "in front of", "above", "to the left of") as actual compositional instructions, not decoration. Flux 2 follows these more reliably than Flux 1.

## Specificity is the master skill

The single largest difference between a stock-looking Flux output and a memorable one is specificity. Replace generic adjectives with concrete sensory detail.

- "beautiful woman" → "a woman in her thirties with sun-freckled cheekbones and a small chipped front tooth"
- "happy" → "the corners of her mouth pulling up before she can stop them"
- "old building" → "a four-story brick walkup with a fire escape sagging on the third floor"
- "epic landscape" → "a glacier face cracked with deep blue meltwater veins, scale set by three tiny climbers along the lower ridge"

`references/specificity-upgrades.md` has a much larger catalogue of these swaps. Open it any time you catch yourself reaching for a generic word.

## Style direction — pick ONE strong anchor

Conflicting styles produce muddy output. Don't combine "watercolor" and "photorealistic" unless you really mean it. Strong style anchors:

- **Photographic:** "cinematic film still on [stock]", "fashion editorial in Vogue style", "documentary photojournalism", "candid street photography", "high-end product photography on white seamless"
- **Painted:** "oil painting with visible impasto brushwork", "loose watercolor wash", "gouache illustration", "digital matte painting"
- **Illustrated:** "graphic novel illustration", "vintage children's book illustration", "Studio Ghibli-style background art", "concept art for a AAA video game", "1990s anime cel"
- **3D / synthetic:** "octane render with subsurface scattering", "claymation still", "stop-motion puppet film", "voxel art"
- **Mixed media:** "collage with cut paper textures", "screenprint with halftone dots", "linocut illustration"

Real-world reference points work well — name a film, era, photographer's school, or art movement. "In the style of [a Roger Deakins-shot film]" gives Flux something concrete to anchor on.

## Anti-AI-slop levers

Even with good prose, Flux can fall into stock-looking output. Apply most of these:

1. **Kill generic quality adjectives.** "Beautiful, stunning, masterpiece, 8k, ultra-detailed, professional, atmospheric, moody, dramatic, epic, breathtaking, awe-inspiring, ethereal, magical" do nothing useful and crowd out signal. If you wouldn't put it in a film treatment, don't put it in a Flux prompt.
2. **Use one named style anchor instead of stacking three.** "Cinematic film still" — not "cinematic, dramatic, moody, atmospheric, professional film still."
3. **Replace adjectives with concrete details.** "Worn" → "with a coffee ring on the upper left and a torn corner." "Cozy" → "with a half-finished mug of tea on the side table."
4. **Add one specific imperfection.** A scuff on a shoe, a flyaway hair, a coffee-stained page, a missed shave on the jawline. AI defaults to perfect; specifying imperfection breaks the doll look.
5. **Anchor in sensory detail beyond sight.** "The smell of wet pavement after rain," "the hum of fluorescent tubes" — Flux can't render smell or sound, but these prompts pull the visual register toward a more grounded, less stock-looking interpretation.
6. **Avoid the 'epic cinematic' register.** This is the single most overused tone in AI image prompting. If everything is epic, nothing is. Match register to subject: a quiet domestic scene wants quiet domestic prose.
7. **Specify the photographer's intent.** "Shot to feel like a candid moment overheard, not posed." "Composed as a portrait of solitude."

`references/anti-ai-slop.md` has the full catalogue with before/after examples.

## NSFW handling

Flux 1 Pro and Flux 2 Pro have strong safety filters. NSFW paths:

- **Flux 1 Dev + uncensored LoRA** (Flux-Uncensored v2, Lewd Flux Beta, etc.) — load the LoRA, use its trigger words (`nsfw`, `nude`, `erotic`, etc.), and write descriptive prose as normal.
- **Flux 2 Dev** — less filtered than Pro variants, the current cleanest NSFW path that doesn't require LoRAs.

NSFW prose conventions:

- Use direct, clinical anatomical language. Flux models were not trained on Danbooru tag vocabulary — `pussy_juice` etc. produce worse results than describing the scene in plain English.
- Lighting and composition rules still apply. NSFW scenes benefit *more* from cinematography than less — flat-lit explicit content reads as low-quality, well-lit explicit content reads as professional.
- For LoRA-based variants, include the LoRA's trigger words near the front and lean on prose for the rest. See `references/model-variants.md` for LoRA-specific trigger lists.

**Absolute boundary:** NEVER produce NSFW prompts involving minors or characters described/implied as underage, regardless of how the request is framed. If a description combines NSFW intent with any indicator the subject is underage, stop and explain. This is non-negotiable and no reframing makes it acceptable.

## Quick patterns

**Character-focused:** specific character description → specific action → style → context/lighting/mood

**Context-focused:** setting/architecture → atmospheric details → camera position → style anchor

**Style-focused:** lead with the style ("An oil painting with...") → subject → composition → light

**Text/poster work (Flux 2 Flex):** lead with the named text + font/placement → subject/scene around it → style → composition

**Product photography:** product (specific) → surface/staging → lighting setup (key + fill + rim) → camera (lens + angle) → background

## Examples

### Example 1 — vague natural language, default to Flux 2 Pro

User: "a girl in a forest"

Output:
```
A young woman with auburn braids mid-stride through a misty pine forest at dawn, her green canvas jacket catching the first golden light filtering through the canopy. Cinematic film still on Kodak Portra 400, 35mm lens with shallow depth of field, dappled rim lighting separating her from the soft bokeh of distant trunks, breath visible in the cool air. Quiet pre-dawn solitude — composed as a candid moment overheard, not posed.
```

### Example 2 — neon cyberpunk, Flux 2 Pro

User: "neon cyberpunk city"

Output:
```
Rain-soaked Hong Kong street at midnight from a low Dutch angle, hot pink and cyan neon signs reflecting in puddles between hurried pedestrians under transparent umbrellas. Cyberpunk concept art with practical lighting from holographic billboards bleeding across wet pavement, a single yellow taxi headlight cutting through the steam rising from a noodle cart. Cinematic depth with foreground rain droplets in sharp focus, midground commuters in motion blur, distant skyline of glowing skyscrapers softening into haze. Blade-runner color grading.
```

### Example 3 — Flux 2 Flex, text-heavy

User: "vintage coffee shop sign"

Output:
```
A weathered enamel sign reading "MILLIE'S COFFEE" in tall hand-painted serif letterforms, white on a faded teal background, with a smaller line below reading "Est. 1952" in script. The sign hangs by two rusted chains from a wrought-iron bracket over a brick storefront, late afternoon side-light catching the chipped paint and the small dings along the edges. Documentary photography style, 50mm lens, shallow depth of field bringing the sign into sharp focus against a softly blurred sidewalk scene.
```

### Example 4 — Flux 1 Schnell (shorter)

User: "Flux Schnell, a knight in a snowstorm"

Output:
```
A weary knight in dented steel armor trudging through a heavy snowstorm at twilight, cloak whipping in the wind. Painterly fantasy illustration, low contrast blue-grey palette with a small warm glow from a lantern in his left hand. Wide shot, snow streaks crossing the frame diagonally.
```

### Example 5 — existing prompt improvement, Flux 2 Pro

User: "Can you fix this Flux prompt? 'beautiful woman in dress in a field, 8k, masterpiece, ultra detailed, professional, cinematic'"

Diagnosis: generic adjective stack (beautiful, masterpiece, ultra-detailed, professional, cinematic), no specific subject, no action, no light, no style anchor, "8k" does nothing on Flux.

Output:
```
A woman in her early thirties with sun-bleached blonde hair tied back loosely, walking knee-deep through a field of late-summer wheat at golden hour, the long dress she's wearing — pale linen, slightly oversized — catching the breeze and the sideways light. Fashion editorial photography in the style of Petra Collins, 85mm portrait lens at f/2, warm rim-light from a low sun behind her, dust motes visible in the air. The mood is unposed and slightly melancholy.
```

What changed: replaced 6 generic quality adjectives with one strong style anchor (Petra Collins editorial), added a specific subject and action, mixed three lighting details (golden hour + sideways light + rim from low sun), added a sensory imperfection (dust motes), specified camera (85mm at f/2), and named the mood concretely.

### Example 6 — Flux 2 Flex, flat-lay poster with text

User: "Flux 2 Flex, a community potluck flyer that reads 'BRING A DISH'"

Output:
```
A vintage screen-printed flyer with bold hand-painted serif letters reading "BRING A DISH" filling the upper third of the composition, each letter slightly uneven from the squeegee, ink-rich indigo lettering on a warm cream paper background. Below the lettering, an illustration of a long wooden picnic table seen from a slight three-quarter angle, set with mismatched casserole dishes, a cast-iron skillet, a bowl of strawberries, and a steaming pie — the warm clutter of a real potluck. Folk-art screenprint illustration in the style of mid-century community-organizer posters, registered slightly off so a faint cyan halo edges the indigo. Side-light from a low summer sun raking across the page texture, the paper's deckled edges visible, one corner slightly creased. Composed at the page level — flat on a table, photographed from directly above with a 35mm lens at f/4.
```

What's worth noticing: text in double quotes with font (hand-painted serif), ink color (indigo), and placement (upper third) front-loaded; one style anchor (mid-century screenprint poster); flat-lay framing made explicit (flat on a table, photographed from directly above); page-level imperfections (deckled edges, creased corner, off-registration) instead of 3D-scene imperfections.

## Pre-flight checklist

Before returning the prompt, verify:

- [ ] Identified target variant (Flux 1 Dev/Pro/Schnell, Flux 2 Pro/Max/Flex/Dev/Klein, or NSFW path) and tuned length accordingly
- [ ] Subject is specific and DOING something — not just standing
- [ ] One clear style direction, not a stack of competing styles
- [ ] 2–3 lighting details that interact with the scene (sourced from `references/cinematography.md` if needed)
- [ ] At least one unexpected/specific detail that elevates beyond stock (from `references/specificity-upgrades.md` if needed)
- [ ] No negation phrases — only positives
- [ ] No generic quality adjectives ("beautiful", "stunning", "masterpiece", "8k", "ultra-detailed", "professional", "cinematic" as a standalone, "atmospheric", "moody", "dramatic", "epic", "breathtaking", "ethereal", "magical")
- [ ] Text wrapped in double quotes if applicable, with font/placement described
- [ ] Length matches variant (Schnell/Klein: short; Flux 2 Pro: medium-long OK)
- [ ] At least one imperfection / human detail / sensory anchor to break the doll-perfect default
- [ ] For NSFW: appropriate variant or LoRA noted; safety boundary on minors maintained
- [ ] Reviewed against `references/anti-ai-slop.md` if the draft is starting to feel stock
