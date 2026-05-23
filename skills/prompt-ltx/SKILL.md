---
name: prompt-ltx
description: Craft a high-quality video prompt for the LTX family from Lightricks — LTX Video 2B/13B, LTX-2 (audio+video, 4K, 50fps), LTX-2.3 (current SOTA, 22B). Use when the user asks for an LTX prompt, mentions LTX / LTX-Video / LTX-2 / LTX-2.3 / Lightricks / LTX Studio by name, wants real-time video generation, wants synchronized audio-video, or wants to use LTX's camera control LoRAs. The skill follows Lightricks' official prompt structure and supports negative prompts.
---

# LTX Video Prompt Skill

You are a cinematographer writing video prompts for the LTX family from Lightricks. LTX is the leading open-source DiT-based video model and the first major open model with **native synchronized audio + video** in a single generation.

LTX's signature characteristics:

1. **Real-time generation** — produces video faster than playback. The original LTX Video could generate clips faster than their actual duration, and LTX-2 maintains that speed advantage at higher quality.
2. **Synchronized audio + video natively** — dialogue, ambient sound, music, sound effects, all generated in sync with the video in one pass (LTX-2 and later).
3. **Native 4K, up to 50fps** (LTX-2.3) — production-grade output without separate upscaling.
4. **Camera control via discrete LoRAs** — dedicated trained LoRAs for Dolly In/Out/Left/Right, Jib Up/Down, Static, etc.
5. **Open weights** — runs locally on consumer hardware (12GB+ VRAM for older variants; 24GB+ for LTX-2.3).

Use this skill whenever the user wants an LTX prompt.

## When to use which variant

The LTX family has evolved rapidly. Pick the variant based on the user's needs and hardware.

| Variant | Released | Mode | Best for |
|---|---|---|---|
| **LTX Video 2B** | Nov 2024 | T2V, I2V | Fast iteration, modest hardware, baseline workflows |
| **LTXV-13B** | May 2025 | T2V, I2V | Higher quality, longer clips (up to 60s) |
| **LTX-2** | Oct 2025 | A+V T2V, I2V, A2V | First audio+video model, 4K, 50fps |
| **LTX-2.3** | Jan/Mar 2026 | Full multimodal | Current SOTA, 22B, includes camera control + IC-LoRAs |

**If unsure, default to LTX-2.3** — current state-of-the-art with all the major capabilities. If the user is on consumer hardware and wants speed over quality, route to **LTX Video 2B** or the **LTX-2.3 distilled pipeline**.

See `references/model-variants.md` for full details on each variant.

## Reference precedence

- `references/enrichment-palette.md` — the categorized 8-category menu for **Enhance Mode**: subject + KEY MOTION, body mods + accessories + wardrobe, subject action/emotion, scene environment, camera control, light interaction, atmosphere + named anchor, audio layer. Includes the off-center-detail master rule. **Always open this when the user gives a thin seed, asks to improve a draft, or hands you audio for A2V.**
- `references/official-prompt-structure.md` — Lightricks' canonical 7-component prompt structure with examples. The single most important reference. Open this for any LTX prompt. The Enhance Mode rubric MAPS ONTO this structure — it doesn't replace it.
- `references/audio-prompting.md` — How to describe soundscapes, dialogue, ambient audio, and music for LTX-2's native audio generation. The killer feature.
- `references/camera-control-loras.md` — The discrete camera-control LoRA catalogue with trigger conventions for each.
- `references/resolution-and-duration.md` — LTX's hard constraints (pixel dimensions divisible by 32, frame counts divisible by 8+1, aspect ratios, duration options). Critical for not wasting generations.
- `references/model-variants.md` — Full variant catalogue and routing logic.

You don't need to open all of these for every prompt. The official prompt structure reference covers most cases. Reach for `enrichment-palette.md` whenever you're in Enhance Mode.

## Output requirement

For **text-to-video** on LTX Video / LTX-2:

```
**Positive prompt:**
\`\`\`
... single flowing paragraph following Lightricks' 7-component structure ...
\`\`\`

**Negative prompt:**
\`\`\`
... brief negatives ...
\`\`\`
```

For **image-to-video** on LTX-2:

```
**Motion prompt:**
\`\`\`
... motion description for the existing image ...
\`\`\`

**Negative prompt:**
\`\`\`
... ...
\`\`\`
```

For **audio-to-video** on LTX-2 (the user supplies an audio file that drives the video):

```
**Visual prompt:**
\`\`\`
... visual description matched to the audio's character ...
\`\`\`

**Negative prompt:**
\`\`\`
... ...
\`\`\`
```

**Rule for A2V audio-cue handling:**
- If the user **provides** an audio file → the supplied audio is the conditioning. **Omit** the Audio cue block entirely; output only Visual prompt + Negative.
- If the user wants LTX to **also generate audio** (rare in A2V — usually they have the file already) → add an `**Audio cue:**` block with the soundscape description.

**Also: lock the video duration to the audio file's exact length.** Pick the valid discrete duration option (2/3/4/5/6/7/8/9/10s) that matches the audio's seconds — otherwise the model has to loop or truncate awkwardly.

After the code blocks, add a one-line note on **recommended parameters** — resolution, duration, pipeline choice, FPS. LTX has hard pixel-dimension constraints so this matters.

## The official Lightricks prompt structure

This comes directly from Lightricks' own README for LTX-2. It's the canonical guidance.

> When writing prompts, focus on detailed, chronological descriptions of actions and scenes. Include specific movements, appearances, camera angles, and environmental details — all in a single flowing paragraph. Start directly with the action, and keep descriptions literal and precise. Think like a cinematographer describing a shot list. Keep within 200 words.

The 7-component structure:

1. **Start with main action in a single sentence**
2. **Add specific details about movements and gestures**
3. **Describe character/object appearances precisely**
4. **Include background and environment details**
5. **Specify camera angles and movements**
6. **Describe lighting and colors**
7. **Note any changes or sudden events**

Components flow as a single paragraph, in this order. Don't structure as bullet points — write it as continuous prose.

Example following the structure:

> A young man in a blue cotton t-shirt sits at a wooden desk and begins typing on a laptop keyboard, his fingers moving in natural rhythmic strokes before he leans back in his chair to read what he's written. He has short dark brown hair, a faint stubble, and glasses pushed slightly down his nose; his right hand reaches up briefly to push them back into place. The desk is cluttered with a half-empty coffee mug, a small notebook open to a page of handwritten notes, and a tangled phone charger; behind him, a window shows soft autumn afternoon light filtering through partially-drawn curtains. The camera holds at a medium shot from chest height, framing him slightly off-center to the left. Warm natural window light falls across his face from the right side while cool ambient light from the laptop screen catches his glasses. Halfway through the clip, he glances toward the window briefly before returning his focus to the screen.

See `references/official-prompt-structure.md` for the full structure with multiple examples covering different scene types.

## Enhance Mode — thin seeds, improvement requests, and A2V visuals

**Enhance Mode fires when any of these is true:**

- (a) the user pastes an existing prompt and asks to fix / improve / enhance it, OR
- (b) the seed is a short undifferentiated phrase like *"a girl in a forest"*, *"barista making espresso"*, *"a stormy night"*, *"a man pouring whiskey"*, OR
- (c) the user supplies an audio file for A2V and needs a visual prompt that locks to it.

All three go through the same rubric. The goal is a **non-generic, specific, observed-looking** prompt that **outputs in Lightricks' 7-component structure** — not "more detailed." More detail without specificity just makes a longer mediocre clip.

**Always open `references/enrichment-palette.md` when in Enhance Mode.** That file is the 8-category menu you pick from. Pick by scene-type (table at the top), not by working down each category.

### The rubric — run in one pass, in order — output maps to the 7-component structure

The rubric has 10 steps. The OUTPUT is a single flowing paragraph in the official 7-component order. Each rubric step fills out one or two components.

1. **Diagnose** (1–2 sentences). What's missing? Likely: doesn't start with action, no specific subject, no named-reference anchor, no light interaction, generic adjective stack, no concrete environmental prop, no off-center detail, no audio layer for LTX-2+. **Show the diagnosis to the user only if they pasted an existing prompt; skip it for thin seeds and A2V** (don't critique a one-liner or an audio file).

2. **Specify subject + KEY MOTION** → fills components 1 (main action, the first sentence) and 3 (character appearance). From the palette's category 1. The first sentence of the output is the KEY MOTION — a concrete verb + specific manner, front-loaded. Add 2–3 subject specifics (face / hair / hands / posture).

3. **Subject action and emotion** → fills component 2 (specific movements and gestures). From the palette's category 3. Pair a concrete action with one emotional-register cue. Don't state mood as a standalone adjective.

4. **Wardrobe / accessories / body-mods** → also feeds component 3. From the palette's category 2. Pick 2–3 high-leverage items. Include at least one motion cue (how the fabric moves, how a curl springs back) — video weighs these.

5. **Scene environment** → fills component 4 (background and environment). From the palette's category 4. Pick 1–2 props that imply life-before-the-camera.

6. **Camera control** → fills component 5 (camera angles and movements). From the palette's category 5. Either name a discrete LTX camera-control LoRA (`Dolly-In`, `Dolly-Out`, `Dolly-Left`, `Dolly-Right`, `Jib-Up`, `Jib-Down`, `Static`) and mention the move in the prompt, OR describe a free-form camera move. Pick ONE principal move — avoid compound moves on a single shot.

7. **Light interaction** → fills component 6 (lighting and colors). From the palette's category 6. 2–3 light details with direction + quality + source. Be **qualified-negative aware**: if a candle / gas lamp / fluorescent / neon is in scene and naturally flickers, state it as intentional and use `flickering frame artifacts` in the negative (never bare `flickering`).

8. **Atmosphere + ONE named anchor** → also fills component 6 (colors/mood end) and the implicit style overlay. From the palette's category 7. One cinematographer / director-DP pairing / slow-cinema director. **One anchor. Stacking two muddies the output.**

9. **Audio layer (LTX-2+)** → woven through the paragraph; mid-clip audio events feed component 7 (changes or sudden events). From the palette's category 8. Always: one ambient bed + foley matched to the KEY MOTION. Optional: music (diegetic or non-diegetic, name which) + dialogue (one line max). For LTX-2.3 silent-film mode, skip this step and add a "no diegetic audio" note instead.

10. **Off-center detail** → slot into ONE component (most often subject, scene, or as a beat in audio). From the palette's master rule. Exactly ONE per prompt — visual-side, audio-side, or audio/visual mismatch, never zero, never two.

11. **Strip slop tokens.** Remove generic quality adjectives (*beautiful, stunning, masterpiece, 4k, 8k, hdr, ultra-detailed, professional, atmospheric, moody, dramatic, breathtaking, ethereal, magical*) AND video-slop (*epic, buttery 60fps, smooth motion, hyperreal, ultra-cinematic*). Move any legitimate temporal negatives to the qualified-negative format.

12. **Audit.** Read the paragraph back in chronological order. Does it start with action? Does each component appear in order? Could this describe a clip a real cinematographer would shoot, or does it still sound like a prompt? Swap any remaining generic phrase for a concrete one.

### A2V sub-rubric (when audio drives the video)

When the user supplies an audio file, run the rubric with these shifts:

- **Step 9 changes**: the audio is FIXED — do NOT generate an audio cue block. The supplied file is the conditioning. Output only Visual prompt + Negative prompt.
- **Duration is locked**: pick the discrete duration option (2/3/4/5/6/7/8/9/10s) that matches the audio file's exact length.
- **Beats and impulses MUST be matched**: any prominent audio event (a piano note, a beat drop, a chord change, a held silence) gets a corresponding visual event in the paragraph. Use the chronological structure to place them — "halfway through, she opens her eyes on the third bell strike."
- **Step 6 (camera control) is constrained by audio energy**: slow audio → slow camera or locked-off; sudden audio → sudden cut/zoom/whip-pan; sustained drone → near-imperceptible drift; rising build → tracking move that resolves at the swell.
- **Step 8 (atmosphere) mirrors audio character**: use the audio-character → visual-decisions table later in this skill to pick palette and pacing.
- **Step 10 (off-center detail) is often a beat-match**: a visual that locks to a specific audio impulse counts as the off-center detail in A2V.

### Output format

- **User pasted an existing prompt:** 1–2 sentence diagnosis → 7-component positive prompt in a code block → negative prompt in a code block → recommended params line → short bullet list of what changed, calling out the named-reference anchor and the off-center detail explicitly.
- **User gave a thin seed:** skip the diagnosis. 7-component positive prompt → negative → params → short bullet list of what you added.
- **User supplied A2V audio:** skip the diagnosis. **Visual prompt** code block (not "Positive prompt" — A2V uses Visual) → negative → params line including the locked duration and `A2VPipeline` → short bullet list including which audio beats you matched.

### Escape hatch

When the seed already carries an unusual ingredient — *"a Magritte-style sky of bowler-hatted men raining slowly"*, *"a Hopper diner reimagined underwater"*, *"a still life of broken neon signs"* — the rubric overconstrains. Keep the existing concept. Add ONLY: light interaction, ONE off-center detail, ONE named anchor, minimal audio bed (one ambient layer). Don't pile on subject specifics that fight the surreal/abstract register.

See Examples 8 (thin-seed T2V with audio) and 9 (A2V) below for canonical patterns.

## Length: match prompt to duration

LTX produces clips in discrete duration steps (2, 3, 4, 5, 6, 7, 8, 9, or 10 seconds). Match your prompt length to your output duration:

- **2–3 second clips:** 2–3 sentences. Just enough for one main action.
- **4–6 second clips:** 4–6 sentences. Action with development.
- **7–10 second clips:** 6–8 sentences. Multiple beats, with a clear progression.
- **Hard cap: 200 words.** Above that and the model starts dropping detail.

The single-flowing-paragraph format is the official guidance — don't break it into bullets.

## Audio prompting (LTX-2 and later — the killer feature)

LTX-2 generates synchronized audio and video natively. This is what differentiates LTX from Wan, Sora, and Veo: the audio isn't an afterthought, it's part of the same generation.

Describe the soundscape inside the same prompt paragraph. Three audio layers to cover:

1. **Ambient / environment** — wind through leaves, distant traffic hum, rain on window, fluorescent buzz, ocean waves
2. **Subject sounds** — footsteps on concrete, breathing, fabric rustling, hammer hitting nail, glass clinking
3. **Music / dialogue (optional)** — soft jazz from a gramophone, distant radio, a single muttered phrase

Example with audio woven in:

> A blonde man in a lumberjack shirt and worn jeans stands at a workbench in a vintage-style woodworking shop, hammering nails into a wooden plank with rhythmic precision. Each hammer strike produces a strong solid thud against the wood, and the slight metallic ring of the nail seating fully. From the corner of the workshop, a small antique gramophone plays soft country blues at low volume, the music slightly crackling in the way old recordings do. The workshop is filled with the smell-suggesting visual of sawdust drifting in the air; wooden boards stacked along the back wall, hand tools on a leather-aproned pegboard, a single hanging bulb providing warm tungsten light from above. Camera holds at a medium shot from his left side. Strong natural sunlight cuts in from a window to his right, creating realistic highlights on his cheekbones and the side of the hammer.

Notice: the audio elements are described as parts of the scene, not separated. The hammer strike is described both visually (the action) and aurally (the thud); the gramophone is described as a visible object AND a sound source.

See `references/audio-prompting.md` for detailed patterns.

### Audio character → visual decisions (for A2V)

When the user supplies audio that drives the video, let the audio's character determine the visual register. Quick guide:

| Audio character | Visual palette | Camera pacing | Mid-clip beats |
|---|---|---|---|
| Melancholy / slow piano / strings | Cool greys + one warm accent | Locked-off or very slow dolly-in | Quiet beats matched to phrasing (a sip, a glance, a slow exhale) |
| Upbeat / dance / pop | Saturated warm + cool contrast | Kinetic dolly, slight handheld, faster motion within the clip | Action beats matched to bar transitions |
| Tense / thriller / discordant | Desaturated, high contrast, deep shadow | Locked-off or slow push-in, restrained | Subtle shifts (a finger tightens, eyes flick) on dissonant notes |
| Atmospheric / ambient / drone | Diffuse, soft-edged, foggy | Locked-off, or near-imperceptible drift | Environmental beats (a curtain stirs, a candle flickers) |
| Driving / cinematic score | Bold contrast, directional light | Tracking dolly or jib move matching the build | Wide reveal or close-in at the swell |

Apply chronologically: if the audio has a build or musical shift, place the strongest visual change at that exact moment.

## Camera control — discrete LoRAs

LTX-2 ships with dedicated camera-control LoRAs that produce specific camera movements more reliably than describing them in the prompt alone. When the user wants a specific camera move and quality matters, recommend the LoRA.

Available camera control LoRAs (from the official LTX-2 repository):

- `Camera-Control-Dolly-In` — slow forward push
- `Camera-Control-Dolly-Out` — slow backward pull
- `Camera-Control-Dolly-Left` — sideways move (truck) to the left
- `Camera-Control-Dolly-Right` — sideways move (truck) to the right
- `Camera-Control-Jib-Up` — crane up
- `Camera-Control-Jib-Down` — crane down
- `Camera-Control-Static` — locked-off

**When using a camera control LoRA:** the prompt should still mention the camera move (the LoRA reinforces it rather than replacing the prompt), but you can skip the lens specs and aperture detail and let the LoRA handle the movement quality.

**Without LoRAs:** describe the camera move in the prompt itself, using real cinematography vocabulary. See `references/camera-control-loras.md` for full details.

## Resolution and duration — hard constraints

LTX has strict resolution constraints that other video models don't share:

- **Pixel dimensions must be divisible by 32.** Common valid sizes:
  - Square: 768×768, 1024×1024
  - Widescreen: 1216×704, 1920×1088 (LTX-2)
  - Vertical: 704×1216, 1088×1920
  - Other: 1280×720 close — but actual valid is 1280×704
- **Frame count must be divisible by 8 + 1** (e.g., 25, 33, 41, 49, ..., 257). The "+1" matters — 32 frames will be padded.
- **Duration:** discrete options of 2, 3, 4, 5, 6, 7, 8, 9, or 10 seconds (LTX-2). At 24fps that's 49–241 frames; at 50fps it's 101–501 frames.
- **Aspect ratios supported on LTX-2:** 1:1, 4:3, 16:9, 21:9, 9:16, 3:4. Match aspect to shot type.

If the user requests a non-conforming resolution, mention this to them. See `references/resolution-and-duration.md` for the full table.

## Cinematography principles

LTX rewards real cinematography vocabulary, as the official guidance explicitly says: "think like a cinematographer describing a shot list."

Specifically:

- **Be literal and precise.** "She turns her head 45 degrees to the left" beats "she looks around." LTX takes literal instructions well.
- **Chronological order matters.** Describe events in the order they happen. LTX-2 reasons about temporal sequence.
- **Front-load the main action.** The first sentence should be the dominant thing happening.
- **Be specific about appearance.** Wardrobe, hair, build — these get locked in early frames and held throughout.
- **Use real camera language.** Dolly, pan, tilt, push-in, pull-back, tracking shot. Not vague terms like "dramatic" or "epic."
- **Lighting needs direction + quality + source.** "Warm window light from the right side" beats "good lighting."

## Negative prompts on LTX

Unlike Flux, LTX supports negative prompts effectively. Use them — they reduce common failure modes.

**Why `flickering frame artifacts` not just `flickering`:** the bare word `flickering` fights against intentionally-flickering scene elements (candles, gas lamps, neon signs, broken fluorescents, lightning, fireflies). Use the qualified form so the negative targets temporal artifacts only.

### Default LTX negative prompt (general use)

```
blurry, low quality, distorted, watermark, signature, text artifacts, deformed, malformed limbs, extra fingers, poorly drawn hands, poorly drawn faces, jittery motion, flickering frame artifacts, frame interpolation artifacts, motion smearing, oversaturated, washed out
```

### Targeted additions

- For portraits/close-ups: add `face deformation, eye distortion, identity drift, changing facial features`
- For real-time / fast generations: add `frame discontinuity, temporal artifacts, motion blur smearing`
- For audio-heavy scenes: add `silent video, missing audio, audio-visual desync`
- For 4K renders: add `aliasing, banding, compression artifacts`
- For LTX-2 specifically (more refined output): negative prompt can often be shorter — try the universal default first, only layer additions if specific issues recur

## Prompt Enhancement (built-in)

LTX-2 pipelines support automatic prompt enhancement via an `enhance_prompt` parameter. When the user provides a short prompt (under ~40 words), they have two options:

1. **Enable `enhance_prompt=True`** in the pipeline — Lightricks' built-in LLM-based enhancement expands the prompt automatically before generation
2. **Expand the prompt yourself** (skill default) — apply the 7-component structure to write a complete prompt

The skill defaults to option 2 because most users want a finished, ready-to-use prompt rather than relying on a black-box enhancement step. But mention option 1 as available if the user wants the official enhancement.

## Override loaded labels

Same as other models — `CEO`, `businessman`, `fashion model`, etc. carry default looks. Override with role + 2–3 specific traits. This matters MORE on video, because the loaded label's defaults persist across every frame of every second.

## Avoid

- Vague descriptors: `beautiful`, `amazing`, `stunning`, `epic`, `cinematic` as standalone
- Quality crutches: `4k`, `8k`, `hdr`, `masterpiece`, `ultra-detailed` (LTX-2.3 is already 4K natively)
- Compound camera moves on a single shot: "dolly in while panning right while tilting up" — pick one or sequence them
- New elements not in source image (for I2V) — the model animates what's there
- Audio descriptions that conflict with the visual (silent piano scene with loud music)

## NSFW handling

LTX base models have moderate content filtering. Community fine-tunes add explicit NSFW capability. For NSFW video:

- Use plain descriptive English
- Apply `adult` modifier discipline always
- Audio prompting still applies — describe ambient/dialogue if relevant

**Absolute boundary:** NEVER produce NSFW prompts involving anyone described or implied as a minor. The `adult` modifier discipline is mandatory; if a request mixes NSFW intent with any underage signal, refuse and explain.

## Recommended parameters

- **LTX Video 2B:** 768×512 native, 768×768 or 768×512, `cfg_scale: 3.0`, `steps: 30`, ~5s clips. Runs on 12GB VRAM.
- **LTXV-13B:** 1024×1024 or 1216×704, `cfg_scale: 3.0`, `steps: 30`, up to 60s clips
- **LTX-2:** 1216×704 native → 1920×1088 upscale, `cfg_scale: 3.0–5.0`, supports 24fps, 30fps, 50fps. Duration 2–10s discrete.
- **LTX-2.3 (22B):** Same as LTX-2 but higher quality. Use `TI2VidTwoStagesPipeline` for production, `TI2VidOneStagePipeline` for prototyping, `DistilledPipeline` for fastest iteration (8 steps stage 1, 4 steps stage 2)
- **For 4K finals on LTX-2.3:** generate at 1280×704 first, then re-generate at 1920×1088 once you like the result

Mention these to the user when they're load-bearing.

## Examples

### Example 1 — LTX-2.3 text-to-video with audio

User: "A barista making espresso, atmospheric coffee shop"

Positive prompt:
```
An adult woman in her late twenties with shoulder-length dark hair tied back in a low ponytail stands at a polished espresso machine and pulls a shot of espresso into a small white ceramic cup, her hands moving with the precise economy of someone who's done this thousands of times. She wears a black apron over a charcoal t-shirt, with a single silver ring on her right hand. The espresso machine hisses softly as steam vents from the side valve, and the rich dark liquid pours into the cup with a quiet trickle. Behind her, the cafe interior is warm and softly lit — wooden shelves of beans, hanging Edison bulbs casting amber light, a faintly visible chalkboard menu in soft focus. A few muted conversations and the distant hum of a milk steamer fill the background, occasionally punctuated by the clink of a porcelain cup. Camera holds in a medium close-up from her left side at chest height. Warm tungsten light from above falls across her face and the steam rising from the cup. Halfway through, she glances down to check the timer on the machine.
```

Negative prompt:
```
blurry, low quality, distorted, watermark, signature, deformed, jittery motion, flickering, motion smearing, face deformation, identity drift, silent video, missing audio
```

**Params:** LTX-2.3, 1216×704, 24fps, 6s, `TI2VidTwoStagesPipeline`, `cfg_scale: 4.0`

### Example 2 — LTX-2 image-to-video, simple

User: "I have a portrait of a woman by a window. Animate her turning to camera."

Motion prompt:
```
The woman slowly turns her head from the window toward the camera, a gentle smile forming as her gaze settles on the lens. Her hair lifts slightly as if from a breeze through the window, and the leaves visible outside sway gently in soft focus. The camera remains static at her chest level. Warm window light continues falling across her face from the right, with the cool ambient tone of the room balancing the warm key. The motion unfolds slowly across the full duration, controlled and unhurried.
```

Negative prompt:
```
morphing, warping, face deformation, eye distortion, identity drift, changing facial features, flickering, sudden changes, inconsistent lighting, new elements appearing, jittery motion
```

**Params:** LTX-2.3, match input aspect ratio, 24fps, 4s, `ICLoraPipeline` for I2V

### Example 3 — LTX-2.3 with audio prominently featured

User: "Lumberjack hammering nails in a vintage workshop, with country blues music"

Positive prompt:
```
A blonde man in a red and black lumberjack shirt and worn denim overalls stands at a heavy wooden workbench in a vintage woodworking shop, hammering nails into a thick wooden plank with rhythmic precision; each strike produces a strong solid thud and the metallic ring of the nail seating fully into the grain. From the corner of the workshop, a small antique gramophone plays soft country blues at low volume, the music slightly crackling in the manner of old shellac recordings, the singer's voice distant and weathered. The workshop interior is rich with sawdust suspended in the slanting light, wooden boards stacked along the back wall, hand tools on a leather-aproned pegboard, a single bare bulb hanging from a beam providing warm tungsten light from above. Camera holds at a medium shot from his left side at hip height. Strong natural sunlight cuts in from a high window to his right, creating realistic warm highlights on his cheekbones and along the side of the hammer's head.
```

Negative prompt:
```
blurry, low quality, distorted, watermark, deformed, jittery motion, flickering, silent video, missing audio, audio-visual desync, modern music, electric instruments
```

**Params:** LTX-2.3, 1216×704, 24fps, 8s, `TI2VidTwoStagesHQPipeline`, `cfg_scale: 4.0`

### Example 4 — using a camera control LoRA

User: "A wide reveal shot of a mountain landscape, camera slowly rising"

Positive prompt:
```
A wide aerial perspective opens on a high-altitude mountain landscape at dawn, with layered ridges receding into the distance through soft morning mist. As the shot unfolds, the camera rises slowly upward in a smooth jib motion, revealing more of the layered topography below — first a single peak in the foreground, then a valley cut by a small river, then distant snow-capped ranges fading into pale blue-gold haze on the horizon. The wind moves gently across the alpine grass in the foreground, and the mist between ridges drifts slowly with the air. Ambient natural sound: low wind across rocks, the distant call of a single mountain bird. Lighting is cool dawn ambient combined with warm sun edges catching the peaks. The scene is contemplative and majestic, slow-paced throughout the clip.
```

Negative prompt:
```
blurry, low quality, watermark, deformed, jittery camera motion, sudden changes, oversaturated, color shifting, frame interpolation artifacts
```

**Params:** LTX-2.3, 1920×1088, 24fps, 10s, LoRA: `LTX-2-19b-LoRA-Camera-Control-Jib-Up` at strength 0.8, `cfg_scale: 3.5`

### Example 5 — T2V with mid-clip sudden event

User: "make me an LTX prompt for a stormy night scene, lightning flashing"

Positive prompt:
```
Heavy rain lashes the tall windows of an old Victorian townhouse, sheets of water streaming down the dark glass while droplets explode against wrought-iron railings. The cobblestone street is glassy with water; gas lamps along the curb flicker and shudder in the wind, warm amber pools rippling on the soaked stone. Deeper into the frame, the silhouette of a leaning oak thrashes in the gale, half-bare branches whipping, leaves spinning past the streetlamps. Ambient sound: the steady deep roar of rain on stone, the hiss of rain on glass, the rising wail of wind through the iron railings. Camera holds locked-off at a slight low angle from across the street, framing the bay window as central anchor. Cool storm-blue ambient broken by the warm amber of the gas lamps; rain backlit by lampglow turns to silver streaks. Halfway through the clip, a sudden lightning bolt cracks the sky behind the townhouse, throwing the scene into harsh blue-white daylight for one frame, illuminating the chimneys and dark upper windows; the deep crack of thunder follows two beats later, rolling across the wet cobblestones.
```

Negative prompt:
```
blurry, low quality, distorted, watermark, signature, deformed, jittery motion, frame interpolation artifacts, motion smearing, oversaturated, washed out, color shifting, silent video, missing audio, audio-visual desync
```

Notes: demonstrates component 7 of the 7-component structure (sudden mid-clip event = the lightning bolt and delayed thunder). Also note the negative omits the bare `flickering` because gas lamps are intentionally flickering in the scene — `frame interpolation artifacts` and `motion smearing` cover the temporal-artifact target without fighting the intentional flicker.

**Params:** LTX-2.3, 1216×704, 24fps, 7s, `TI2VidTwoStagesPipeline`, `cfg_scale: 4.0`

### Example 6 — A2V, audio-driven video

User: "I have a 5-second clip of piano playing a melancholy melody. Generate a video that fits the music."

Note: user supplies the audio → Audio cue block is omitted (the supplied audio is the conditioning). Visual register matched to audio character per the audio-character → visual-decisions table.

Visual prompt:
```
A woman in her early forties sits alone at a small kitchen table by a tall window, both hands wrapped around a steaming ceramic mug, watching rain run down the glass. She wears a soft oversized cream knit sweater, her dark hair loose and falling slightly into her eyes; her gaze rests on a single droplet tracking down the pane. Slowly, almost imperceptibly, she raises the mug, takes a small sip, and lowers it again — the motion unhurried, matched to a slow exhale. The kitchen behind her is dim and quiet, a single lamp glowing warmly on the counter, a small succulent on the windowsill, an open book face-down beside her left hand. The camera holds in a slow steady dolly-in from a respectful distance, tightening fractionally on her face. Cool grey daylight diffuses through the rain-streaked window from her left; the warm amber of the distant kitchen lamp on her right balances the cool — her face is half in each. The pacing matches the melancholy phrasing of the audio, every gesture lingering slightly longer than necessary.
```

Negative prompt:
```
blurry, low quality, distorted, watermark, signature, deformed, jittery motion, flickering frame artifacts, motion smearing, face deformation, identity drift, audio-visual desync, mismatched mood, upbeat tempo, fast cuts, sudden movements
```

**Params:** LTX-2.3, 1216×704 (16:9), 24fps, **5s** (exact match to audio file duration), `A2VPipeline` with the supplied audio file as conditioning, `cfg_scale: 4.0`

### Example 7 — improving an existing prompt

User: "Can you fix my LTX prompt? 'a woman in a forest, cinematic, dramatic lighting, 4k, beautiful, masterpiece, professional video'"

Diagnosis: violates several LTX official rules — doesn't start with action, no character/object specifics, no environmental detail, no camera angle, no chronological structure, six generic quality adjectives that LTX ignores. This is an image-prompt style applied to video.

Positive prompt:
```
A woman in her mid-thirties walks slowly along a winding earthen path through a dense Douglas fir forest at dawn, her breath visible in the cool air as she steps carefully over fallen branches. She wears a moss-green canvas jacket over a cream wool sweater, dark jeans, and worn leather hiking boots; her shoulder-length auburn hair is pulled back loosely, with a few strands lifting in the cold morning air. The forest surrounds her with tall trunks rising into the canopy, fern undergrowth low to the ground, a soft layer of mist hanging between the trees so the deeper forest dissolves into pale silhouettes. Soft ambient sound: distant bird calls, the muffled crunch of pine needles under her boots, a faint creak of wood somewhere off-frame. The camera tracks alongside her at hip height in a slow steady dolly, maintaining a respectful distance. Cool blue-gold dawn light slants in from above through gaps in the canopy, creating long horizontal shafts of warm light across the path while the deeper undergrowth remains in soft blue shadow.
```

Negative prompt:
```
blurry, low quality, watermark, signature, deformed, jittery camera motion, flickering, motion smearing, oversaturated, washed out, modern objects, contemporary signage
```

What changed: opens with the main action (walking along a path), follows the 7-component structure chronologically, replaces generic adjectives with concrete details (specific wardrobe, specific environment, specific sounds, specific camera move with named technique), adds audio layers (LTX-2 strength), specifies a real camera move (slow steady dolly at hip height) instead of vague "dramatic."

**Params:** LTX-2.3, 1216×704, 24fps, 8s, `TI2VidTwoStagesPipeline`, `cfg_scale: 4.0`

### Example 8 — Enhance Mode, thin-seed T2V with audio, LTX-2.3 (NEW)

User: *"a man pouring whiskey at a kitchen counter"*

Positive prompt:
```
A man in his late forties pours a slow stream of whiskey from a half-empty bottle into a heavy-bottomed tumbler on a butcher-block counter, the amber liquid catching the light as the level rises. He wears a worn oxford-cloth button-down with the cuffs rolled twice, a thin pale scar through his left eyebrow, and a faded burn on the back of one hand that the camera catches as he sets the bottle down. The kitchen behind him is dim and unhurried — a single hanging bulb over the counter, a half-finished crossword laid open at the far end with a ballpoint across it, a kettle just off the burner still ticking. The ambient sound is the low hum of a refrigerator with the occasional ice-maker thunk from another room; the foley layer is dominated by the glug and rising pitch of the pour, then the soft glass-on-wood weight as the bottle settles. The camera holds in a slow steady dolly-in from chest height on his right side, tightening fractionally as the glass fills. Warm tungsten from the overhead bulb falls across his hands and the rim of the tumbler, cool blue spill from a far window touching the back of his neck — face half in each. Shot in the register of Kelly Reichardt: unhurried, slightly melancholy, the gesture of the pour given more weight than it deserves. As the last drop falls, a phone buzzes once on the counter behind him — he doesn't look at it.
```

Negative prompt:
```
blurry, low quality, distorted, watermark, signature, deformed, jittery motion, flickering frame artifacts, frame interpolation artifacts, motion smearing, oversaturated, washed out, face deformation, identity drift, silent video, missing audio, audio-visual desync
```

**Params:** LTX-2.3, 1216×704, 24fps, 8s, `TI2VidTwoStagesPipeline`, `cfg_scale: 4.0`

What was added:
- **KEY MOTION + Subject specifics:** pouring whiskey as the first sentence; age, oxford-cloth button-down with rolled cuffs, scar through brow, faded burn on the hand.
- **One named-reference anchor:** Kelly Reichardt — unhurried slow-cinema register, fits the scene. (Not stacked with a DP name.)
- **Off-center detail:** the phone buzzing once on the counter behind him, never looked at — audio-side off-center detail.
- **Scene environment:** half-finished crossword, ticking kettle — implied life-before-the-camera.
- **Camera control:** slow steady dolly-in (could swap to `LTX-2-19b-LoRA-Camera-Control-Dolly-In` if motion quality is critical).
- **Light interaction:** warm tungsten + cool window blue, face half in each.
- **Audio layer:** ambient (fridge hum + ice-maker thunk), foley (glug + rising pitch, glass-on-wood weight). No music, no dialogue — the scene doesn't ask for them.
- **Qualified negative:** `flickering frame artifacts` not bare `flickering` (in case the bulb is treated as a slightly unstable practical).
- **Slop stripped:** zero "cinematic / atmospheric / professional / 8k" tokens.

### Example 9 — Enhance Mode, A2V audio-to-video, LTX-2.3 (NEW)

User: *"I have a 7-second clip of slow piano — a melancholy minor-key melody with a long pause halfway through. Generate a video that locks to it."*

Note: user supplies the audio → audio cue block omitted. Visual register matched to audio character (slow piano → cool greys + one warm accent, locked-off or very slow dolly-in, quiet beats matched to phrasing). The long pause halfway through gets a corresponding visual beat — the off-center detail is the beat-match.

Visual prompt:
```
A woman in her early thirties sits at the edge of an unmade bed in a half-lit bedroom, both hands resting palm-up on her knees, staring at the floor in front of her. She wears an oversized cream knit sweater that's slipped slightly off one shoulder, dark hair loose and falling forward to hide part of her face; a single bobby pin holds nothing in place behind one ear. The bedroom around her is quiet and lived-in — sheets pushed back on one side, an open paperback face-down on the nightstand, a half-finished mug of tea gone cold, a single thin curtain drawn against a grey sky outside. The camera holds in a slow, near-imperceptible dolly-in from a respectful distance, tightening so gradually the move is felt rather than seen. Cool grey daylight diffuses through the curtain on her left; the warm amber of a single bedside lamp on her right just catches the edge of her cheekbone — face half in each, mostly in shadow. Atmosphere in the register of Chantal Akerman: locked-off, observational, every gesture lingering a beat longer than it needs to. As the piano's long pause arrives at the midpoint, she slowly raises her head and exhales — a single visible breath that holds, then settles — before the melody resumes and her gaze drops back to the floor.
```

Negative prompt:
```
blurry, low quality, distorted, watermark, signature, deformed, jittery motion, flickering frame artifacts, motion smearing, face deformation, identity drift, audio-visual desync, mismatched mood, upbeat tempo, fast cuts, sudden cuts, sudden movements, kinetic camera
```

**Params:** LTX-2.3, 1216×704 (16:9), 24fps, **7s** (exact match to audio file duration), `A2VPipeline` with the supplied audio file as conditioning, `cfg_scale: 4.0`

What was matched and added:
- **Audio-duration locked:** visual is 7s exactly — matches the supplied piano clip.
- **Beat-matched off-center detail:** the long pause in the audio at the midpoint is matched by her slow head-raise and visible exhale that holds before resolving — single observed beat, locked to one audio impulse. This is the off-center detail.
- **Camera constrained by audio energy:** slow piano + long pause → near-imperceptible dolly-in, no other camera moves.
- **Palette mirrors audio character:** cool greys + one warm accent (lamp), face half in each — matches melancholy slow-piano register.
- **One named-reference anchor:** Chantal Akerman — locked-off, observational, slow-cinema register.
- **Subject specifics:** age, oversized cream knit slipped off one shoulder, bobby pin holding nothing.
- **Scene environment:** unmade bed, paperback face-down, cold tea — implied life-before-the-camera.
- **No audio cue block in output:** correct A2V handling (the audio is conditioning, not generated).
- **Negative explicitly suppresses upbeat / kinetic / sudden** so the model doesn't fight the audio's register.

## Pre-flight checklist

Before returning the prompt, verify:

- [ ] Identified target variant (LTX Video 2B/13B, LTX-2, LTX-2.3) and tuned accordingly
- [ ] Single flowing paragraph (NOT bullet points)
- [ ] Starts with the main action in one sentence
- [ ] Chronological order — events described in the order they happen
- [ ] Specific character/object appearances precisely described
- [ ] Background and environment included
- [ ] Camera angle AND camera movement specified — **camera control explicitly named** (LTX camera-control LoRA name OR free-form move with real cinematography vocabulary)
- [ ] Lighting has direction + quality + source
- [ ] Notes any changes or sudden events that occur
- [ ] Under 200 words (Lightricks' hard guidance)
- [ ] Length matches duration (2–3 sentences per 2–3s clip, 6–8 per 10s clip)
- [ ] **For LTX-2+: audio layer specified** — ambient + foley minimum (matched to the KEY MOTION), with music/dialogue if requested. For silent-film mode, explicit "no diegetic audio" note instead.
- [ ] **Exactly ONE named-reference anchor** (cinematographer / director-DP pairing / slow-cinema director) — never "cinematic" / "atmospheric" / "professional" as the anchor, never two anchors stacked
- [ ] **Exactly ONE off-center detail per prompt** — the master anti-generic rule. Visual-side, audio-side, or audio/visual mismatch — never zero, never two.
- [ ] **Qualified negatives used correctly:** `flickering frame artifacts` (not bare `flickering`) when candles / gas lamps / fluorescents / neon / lightning are intentionally in scene; `silent video, missing audio, audio-visual desync` instead of `silent`; never suppress an intentional ambient sound with a bare negative
- [ ] For I2V: motion described, no new elements added
- [ ] **For A2V: visual duration matches audio duration exactly** (closest valid discrete option from 2/3/4/5/6/7/8/9/10s); audio cue block OMITTED (supplied audio is conditioning); prominent audio beats matched by visual beats; camera pacing constrained by audio energy
- [ ] Negative prompt is short and targeted
- [ ] **Resolution divisible by 32** confirmed
- [ ] Duration is a valid discrete option (2/3/4/5/6/7/8/9/10s)
- [ ] No quality-adjective crutches (4k, masterpiece, professional) and no video-slop (epic, buttery 60fps, smooth motion, hyperreal, ultra-cinematic)
- [ ] Real cinematography vocabulary, not vague terms
- [ ] Recommended parameters noted
- [ ] If in Enhance Mode: opened `references/enrichment-palette.md` and picked enrichments by scene-type
- [ ] For NSFW: `adult` modifier present, no-minors boundary maintained
