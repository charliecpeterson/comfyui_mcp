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

- `references/official-prompt-structure.md` — Lightricks' canonical 7-component prompt structure with examples. The single most important reference. Open this for any LTX prompt.
- `references/audio-prompting.md` — How to describe soundscapes, dialogue, ambient audio, and music for LTX-2's native audio generation. The killer feature.
- `references/camera-control-loras.md` — The discrete camera-control LoRA catalogue with trigger conventions for each.
- `references/resolution-and-duration.md` — LTX's hard constraints (pixel dimensions divisible by 32, frame counts divisible by 8+1, aspect ratios, duration options). Critical for not wasting generations.
- `references/model-variants.md` — Full variant catalogue and routing logic.

You don't need to open all of these for every prompt. The official prompt structure reference covers most cases.

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

## Pre-flight checklist

Before returning the prompt, verify:

- [ ] Identified target variant (LTX Video 2B/13B, LTX-2, LTX-2.3) and tuned accordingly
- [ ] Single flowing paragraph (NOT bullet points)
- [ ] Starts with the main action in one sentence
- [ ] Chronological order — events described in the order they happen
- [ ] Specific character/object appearances precisely described
- [ ] Background and environment included
- [ ] Camera angle AND camera movement specified
- [ ] Lighting has direction + quality + source
- [ ] Notes any changes or sudden events that occur
- [ ] Under 200 words (Lightricks' hard guidance)
- [ ] Length matches duration (2–3 sentences per 2–3s clip, 6–8 per 10s clip)
- [ ] For LTX-2+: audio layers described (ambient + subject sounds + optional music/dialogue)
- [ ] For I2V: motion described, no new elements added
- [ ] Negative prompt is short and targeted
- [ ] Resolution conforms to LTX constraints (divisible by 32)
- [ ] Duration is a valid discrete option (2/3/4/5/6/7/8/9/10s)
- [ ] No quality-adjective crutches (4k, masterpiece, professional)
- [ ] Real cinematography vocabulary, not vague terms
- [ ] Recommended parameters noted
- [ ] For NSFW: `adult` modifier present, no-minors boundary maintained
