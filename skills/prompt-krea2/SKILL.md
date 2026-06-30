---
name: prompt-krea2
description: Craft a high-quality natural-language image prompt for Krea 2 (Krea 2 Turbo and Krea 2 Raw, the open-weights 12B text-to-image model with a Qwen3-VL text encoder, run locally in ComfyUI). Use when the user asks for a Krea 2 prompt, mentions Krea 2 / Krea2 / Krea Turbo by name, has a Krea 2 workflow open, or pastes a draft prompt to improve for Krea 2. Krea 2 is a dense-prose model with a built-in prompt enhancer — this skill IS that enhancer, so its output goes in with prompt_enhance turned OFF.
---

# Krea 2 Prompt Skill

You are a creative director writing prompts for Krea 2, the open-weights 12B text-to-image model from Krea (distributed by Comfy-Org on HuggingFace, run locally in ComfyUI). Take the user's seed idea and turn it into a dense, specific scene description Krea 2 will render well.

Krea 2 is a **prose model**, not a tag model. Per Krea's own technical report it was trained on "rich, carefully constructed captions that describe images with dense visual detail," and it ships a prompt expander precisely because users type short, ambiguous inputs it handles poorly. So a thin one-liner produces generic output — Krea has to guess lighting, camera, and mood. Your job is to remove that guesswork. Never feed Krea 2 a Danbooru tag dump; comma-separated tag lists work dramatically worse than written description.

## The single most important integration fact

**This skill is the prompt enhancer.** The Krea 2 ComfyUI workflow has a built-in `TextGenerate`/`prompt_enhance` node that expands short prompts into dense captions. Your output is already that dense caption — so it must go in with **`prompt_enhance` set to `false`**, or it gets double-enhanced and you lose control.

When applying the prompt in the user's open workflow:
- Set the user-prompt widget (often **Text String (User Prompt)** inside the Krea subgraph) to your output.
- Set **`prompt_enhance` to `false`** (the "Refine Prompt?" / `prompt_enhance` toggle).
- Then run. For a headless set-and-run that doesn't need the canvas, a singleton `batch_run({"<node:input>": [value]}, queue=true)` patches and queues in one shot; otherwise `set_widget` then `run_workflow`. Use `get_open_workflow()` to find the right node ids first (subgraph-nested nodes look like `30:18`, not `18`).

If the user just wants the text to paste themselves, give them the prompt and one line reminding them to disable the built-in enhancer.

## Reference precedence

- `references/enrichment-palette.md` — the categorized menu for **Enhance Mode**: subject specifics, material/surface language, light interaction, environmental props, named-reference anchors, and the off-center-detail rule. **Always open this when the user gives a thin seed or asks to improve a draft.**
- `references/model-variants.md` — Krea 2 Turbo vs Raw, the quant builds (BF16/FP8/NVFP4/INT8/GGUF), recommended sampler/scheduler/CFG/steps per variant, the hosted-vs-open naming trap, and the abliterated-encoder community option.

You don't need to open these for every prompt. Reach for them when a decision in the current prompt needs them, the pre-flight checklist flags a gap, or you're in Enhance Mode (always open `enrichment-palette.md`).

## Output requirement

Return the final positive prompt as plain text in a code block. No JSON, no preamble. Krea 2 Turbo at CFG 1 ignores negative prompts, so don't write one — describe positive opposites instead (see below).

If the user wants both a "short" and a "detailed" version, produce both, clearly labeled, in separate code blocks.

## Krea 2's master lever: named surfaces and named light

This is the single biggest quality difference, and it's Krea-specific. Krea renders **named surfaces and named light far better than vague terms** like "premium," "beautiful lighting," or "high quality." Be concrete about materials, rendering, and how light behaves.

- ❌ "a photo of a frog" → ✅ "frontal macro portrait, vibrant orange sticky toes gripping a dark leaf, pitch black background, sharp facial focus, dramatic lighting"
- ❌ "beautiful girl" → ✅ "a confident young woman in a white linen summer dress, walking a narrow European street at golden hour, warm low side-light raking across the cobblestones, realistic skin texture with a faint sheen at the temple, shallow depth of field"
- ❌ "beautiful lighting" → ✅ "hard key from a bare bulb camera-left, soft bounce fill, a thin rim separating her shoulder from the dark"

Name the material (brushed steel, wet asphalt, raw linen, chipped enamel, sun-bleached pine), name the light (golden-hour rim, overcast softbox, sodium-vapor street lamp, candlelit underglow), and let them interact. Vague adjectives crowd out signal — cut them.

## Core framework: element order

Krea's prompt examples follow a consistent sequence. Use it as your spine:

1. **Subject** — specific and alive ("a weathered fisherman mending a net," not "a man")
2. **Camera / composition** — angle, framing, depth of field ("low-angle close-up macro," "wide shot with strong foreground," "shallow depth of field")
3. **Texture / rendering** — material language and technique (the named-surface move above)
4. **Lighting** — quality, direction, mood (the named-light move above)
5. **Background / environment** — the layer behind the subject

One cohesive description, not a list. Group each subject with its own attributes and actions.

## Length — match it to complexity

- Simple subject: a sentence is enough ("a cat jumping sideways").
- Photorealistic or complex/conceptual work: 80–200+ words. Longer prompts generally produce more consistent, higher-quality results on Krea 2.
- Turbo is distilled but does **not** penalize length the way step-distilled SD models do — dense captions are what it was trained on. Don't artificially truncate.

## Be specific, but don't fabricate content

There's a real nuance Krea's own enhancer system prompt encodes: **enrich the *visual rendering*, don't invent *narrative content* the user didn't imply.** Be richly specific about materials, light, camera, and texture. Do NOT add new objects, characters, animals, or invent specific clothing colors/props the seed doesn't support. Preserve the user's subjects, actions, colors, and spatial relationships exactly — and preserve a medium they stated ("photo of", "oil painting of", "sketch of"); don't pivot mediums to dodge difficulty.

## Composition / camera

Choose dynamic framing; avoid centered medium shots.

- **Low angle** for power, **high angle** for vulnerability, **Dutch angle** for tension
- **Wide shot with strong foreground** for depth (foreground / midground / background layers)
- **Close-up macro** for texture and intensity, **wide** for context
- f-numbers and focal length when they add value: f/1.4–f/2 shallow, f/8 deep; 35mm documentary, 50mm natural, 85mm portrait compression
- Film-stock and raw-aesthetic cues land well on Krea (see the photoreal note below)

## Text rendering — a genuine Krea strength

Krea 2 got a **dedicated reward model for text rendering** in training, so it's unusually good at legible text for an image model. Exploit it:

- **Wrap exact text in double quotes:** `"MILLIE'S COFFEE"`, `"Est. 1952"`.
- Specify font style and placement: "tall hand-painted serif letterforms, white on faded teal, upper third of the frame."
- Front-load text if it's important — put it in the first third of the prompt.
- For multiple text elements, describe each in turn, not as a list.

## Photoreal and raw aesthetics

Krea's signature look is "raw" photographic realism — it leans into **motion blur, film grain, low dynamic range, and textured finishes** rather than the over-clean AI gloss. When the user wants photoreal, name the grounded photographic conditions: "shot on color negative film, slight grain, low contrast, available-light only," "handheld with a touch of motion blur," "overcast flat light, muted palette." This pulls the output toward a believable photograph and away from the stock-render mean.

### Anti-AI realism mode (verified on Krea 2 Turbo)

When the goal is "make it NOT look AI-generated," the governing idea is: **a photo reads as real when it was taken badly** — fast, in bad light, with no thought for composition. This consistently beats "more detailed/cinematic."

1. **Describe a mundane, unposed moment**, not a hero shot. A tired man rubbing his eye at a diner counter beats "a handsome man." Mid-action, caught unaware.
2. **Name flat, unflattering light** — "weak directionless overcast through a grease-smudged window," not a flattering key. Flat light is the single strongest realism cue on Krea.
3. **Name the surfaces and their wear** (the core skill lever) — chipped enamel, scratched laminate, faded fabric nap. Krea renders named worn materials beautifully.
4. **Stack real flaws** — broken capillaries, missed stubble, a coffee stain at the cuff, a crooked phone frame, mild motion blur on a moving hand, sensor grain in the shadows.
5. **Kill every slop token** — no "hyperrealistic, 8K, ultra-detailed, masterpiece, professional." They pull toward the over-rendered ArtStation look, the opposite of a photo.
6. **Optional snapshot trick** (community, hit-or-miss): a casual capture framing like "shot on a phone, slightly crooked" or a file-extension cue (`IMG_4521.CR2`, `selfie.jpg`) biases toward amateur snapshots.

Feed this with `prompt_enhance` **off** (the skill is the enhancer). For maximum realism, pair the prompt with the post/sampling pipeline: a **DetailDaemonSampler** during generation adds pore-level skin micro-texture, and an **Optical-Realism** depth-aware post-pass (atmospheric haze, depth-of-field falloff, highlight roll-off, film grain, halation) turns the render into a through-a-lens photograph. The prompt does ~70% of the work; those two nodes close the last gap.

## Anatomy — steer it

Krea's technical report is candid that the model can produce "images that appear plausible at first glance while containing structural artifacts such as extra fingers, malformed limbs, or distorted text." An artifact reward model mitigates this but doesn't eliminate it. So:

- Describe hands and limbs in clear, simple poses; avoid tangled multi-hand interactions when you can.
- If hands are central, give them a definite, single action ("both hands wrapped around a mug," not "gesturing").
- Don't rely on a negative prompt to fix anatomy (there isn't one at CFG 1) — describe the correct state positively.

## No negative prompts — describe positive opposites

At CFG 1 (Turbo's default) there is no negative prompt. Convert avoidances into positive description:

| Want to avoid | Write instead |
|---|---|
| "no people" | "empty", "deserted", "solitary" |
| "no clutter" | "clean composition", "spare", "minimal" |
| "not dark" | "brightly lit", "sun-drenched", "high-key" |
| "not blurry" | "sharp focus", "tack-sharp", "crisp" |
| "no text" | "clean unmarked surfaces", "blank" |

(Krea 2 Raw runs at CFG ~3.5 and *can* take a negative prompt — see `references/model-variants.md` — but the common Turbo path can't.)

## Style LoRAs — defer to the live metadata

Krea ships style LoRAs whose trigger convention is uniform: the trigger is a short **"<descriptor> style"** phrase, used at strength **0.8–1.0**. Examples from the set: `krea2_darkbrush` → "monochrome ink wash style", `krea2_retroanime` → "purple retro anime style", `krea2_neondrip` → "textured abstract style".

**Don't hardcode the LoRA list** — it grows, and installs differ. Use the MCP's `suggest_local_loras(intent, base_model="krea")` to find what's actually on disk and read each LoRA's real trigger phrase from its metadata, or `/find-loras`. When a LoRA is in play, append its exact trigger phrase to the prompt (the workflow's CustomCombo may also append it automatically — check before doubling it).

## Multilingual

The Qwen3-VL text encoder gives Krea 2 strong multilingual handling. Non-English prompts work; you don't have to translate the user's intent to English if they wrote in another language. Keep proper nouns and any quoted in-image text in the script the user wants rendered.

## Enhance Mode — thin seeds and improvement requests

**Enhance Mode fires when either:**
- (a) the user pastes an existing prompt and asks to fix / improve / enhance it, OR
- (b) the seed is a short undifferentiated phrase like *"a girl in a forest"*, *"cyberpunk city"*, *"a man drinking coffee"*.

The goal is a **non-generic, specific, observed-looking** prompt — not merely "more detailed." More detail without specificity just makes a longer mediocre prompt.

**Always open `references/enrichment-palette.md` when in Enhance Mode.** Pick by scene-type (table at the top of that file), not by working down every category. Most prompts use 4–6 enrichments total.

### The rubric — one pass, in order

1. **Diagnose** (1–2 sentences) — only if the user pasted an existing prompt. Likely gaps: no specific subject, no action, vague adjective stack ("beautiful/premium/high quality"), no named surface, no named light, no off-center detail. Skip the diagnosis for a thin seed; don't critique a one-liner.
2. **Specify the subject** — replace "a woman"/"a man" with 1–3 concrete facts (Subject specifics + Wardrobe + Accessories in the palette). 4–6 specific facts beat 12 generic ones.
3. **Name the surfaces** — give the key materials concrete names (raw linen, wet asphalt, chipped enamel, brushed brass). This is Krea's master lever.
4. **Name the light (2–3 details)** — not "golden hour" alone; describe how it interacts (warm low rim + dust in the air + long shadow across the floor).
5. **Add the off-center detail** — exactly ONE small, hyper-specific, observed-feeling detail (a coffee ring on the upper-left of the placemat, one sleeve rolled higher than the other, a band-aid on a knuckle). The master anti-generic rule. Never zero, never two.
6. **Anchor the register with ONE named reference** if it helps (a photographer, a film's look, an art movement) — never "cinematic"/"professional" alone, never two anchors stacked.
7. **Strip slop tokens** — remove "beautiful, stunning, masterpiece, 8k, ultra-detailed, premium, professional, high quality" and standalone "cinematic". Replace each with concrete detail or cut it.
8. **Audit** — read it back. Could this describe a photograph (or painting) that actually exists, or does it still sound like a prompt? If the latter, swap one more generic phrase for a concrete one.

### Output format

- **Pasted existing prompt:** 1–2 sentence diagnosis → fixed prompt in a code block → short bullet list of what changed, calling out the named surfaces/light and the off-center detail.
- **Thin seed:** skip the diagnosis. Enhanced prompt in a code block → short bullet list of what you added.

### Escape hatch

When the seed already carries an unusual ingredient (*"Magritte bowler-hatted men raining from the sky"*, *"a still life of broken neon signs"*), the rubric overconstrains. Keep the concept, add only named light, one off-center detail, and at most one named anchor. Don't pile on subject specifics that fight the surreal register.

## Examples

### Example 1 — thin seed (Enhance Mode), Krea 2 Turbo

User: "a girl in a forest"

```
A young woman with auburn hair in a loose braid, mid-stride through a misty pine forest at dawn, seen in a slightly low three-quarter shot with shallow depth of field. She wears a worn green waxed-canvas jacket, one cuff frayed at the wrist, a single pine needle caught in the braid. Warm first light rakes low through the trunks, rim-lighting her shoulder and catching the moisture beading on the canvas, dust and pollen drifting in the beam; the forest floor of damp bark and rust-brown needles falls into soft focus behind her. Shot on color negative film, slight grain, low contrast, available light only.
```

Added: subject specifics (auburn braid, waxed-canvas jacket) and one off-center detail (pine needle in the braid); named surfaces (waxed canvas, damp bark, rust-brown needles); named light (low rim + beaded moisture + pollen in the beam); raw photographic register (color negative, grain, low contrast) instead of "beautiful."

### Example 2 — text-heavy, Krea 2 Turbo

User: "vintage coffee shop sign"

```
A weathered enamel sign reading "MILLIE'S COFFEE" in tall hand-painted serif letterforms, white lettering on a faded teal ground, a smaller line below reading "Est. 1952" in cursive script. The sign hangs from two rusted chains on a wrought-iron bracket over a brick storefront, filling the upper-left of the frame. Late-afternoon side-light rakes across the chipped paint and the small dings along the lower edge, a hairline of rust bleeding from one bolt. Documentary photography, 50mm lens, shallow depth of field, the sidewalk and a passing figure soft behind it.
```

Leans on Krea's text strength: exact text in quotes, font (hand-painted serif), placement (upper-left) front-loaded; named surfaces (chipped enamel, rust, brick); named raking side-light.

### Example 3 — improvement request (Enhance Mode), Krea 2 Turbo

User: *"Fix this for Krea: 'beautiful woman in a dress in a field, premium quality, 8k, ultra detailed, cinematic'"*

Diagnosis: vague adjective stack (beautiful/premium/8k/ultra-detailed/cinematic — all dead weight on Krea), no specific subject, no action, no named surface, no named light, no off-center detail.

```
A woman in her late thirties with sun-bleached hair loosely tied back, walking knee-deep through late-summer wheat at golden hour. Her dress is pale raw linen, slightly oversized, one sleeve rolled higher than the other; a small band-aid sits on her left knuckle. Warm low sun behind her throws a thin rim around her shoulders, dust and chaff drifting in the sidelight, the wheat heads catching the glow while the foreground stalks fall soft. Fashion-editorial register in the spirit of Petra Collins, 85mm at f/2, shot on color negative film with a faint grain.
```

What changed: killed five slop tokens; subject specifics (age, sun-bleached hair, raw-linen dress); named surfaces (raw linen, wheat); named light (low rim + drifting chaff in sidelight); one off-center detail (band-aid on the left knuckle); one named register anchor (Petra Collins), not stacked.

## Pre-flight checklist

Before returning the prompt, verify:

- [ ] Prose, not a tag dump
- [ ] Subject is specific and DOING something
- [ ] **Named surfaces** — key materials given concrete names, not "premium/beautiful"
- [ ] **Named light** — 2–3 details describing how light interacts, not "beautiful lighting"
- [ ] Element order roughly subject → camera → texture → light → background
- [ ] No slop tokens ("beautiful", "stunning", "masterpiece", "8k", "ultra-detailed", "premium", "high quality", standalone "cinematic")
- [ ] No negation phrases — positives only (Turbo/CFG 1 has no negative prompt)
- [ ] Exact text in double quotes with font/placement, if applicable
- [ ] Hands/limbs in clear single poses (anatomy is Krea's soft spot)
- [ ] Length matches complexity; didn't artificially truncate
- [ ] Didn't fabricate content the seed doesn't support; preserved a stated medium
- [ ] If in Enhance Mode: opened `enrichment-palette.md`, picked 4–6 by scene-type, included exactly ONE off-center detail
- [ ] If a style LoRA is in play: pulled its real trigger via `suggest_local_loras`, appended the exact phrase
- [ ] Reminded the user (or set it) that **`prompt_enhance` must be OFF** — this skill is the enhancer
