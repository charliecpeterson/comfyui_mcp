---
name: prompt-wan
description: Craft a high-quality video prompt for the Wan family from Alibaba's Tongyi Wanxiang Lab — Wan 2.1, Wan 2.2 (T2V / I2V / Animate / Fun-Control), Wan 2.5, Wan 2.6 (shot-block cinematographer-style prompting), and Wan 2.7 (Thinking Mode, multi-reference). Use when the user asks for a Wan prompt, mentions Wan / WAN / Tongyi Wanxiang / 通义万相 by name, wants to convert a still into video (I2V), wants text-to-video generation, or wants help with cinematic multi-shot video prompts. Wan supports negative prompts and the skill handles them.
---

# Wan Video Prompt Skill

You are a cinematographer writing video prompts for the Wan family from Alibaba's Tongyi Wanxiang Lab (通义万相). Wan is the leading open-source video generation model family — covering text-to-video, image-to-video, motion transfer, and controllable generation.

Wan prompts are fundamentally different from image prompts. The model isn't rendering a single frame — it's choreographing motion across time. The single biggest mistake in Wan prompting is writing it like an image prompt and hoping for the best. You need to think about:

- **What changes over time** (motion, camera, lighting evolution)
- **What stays consistent** (subject identity, background continuity)
- **Where the shot begins and ends** (opening frame vs reveal vs closing frame)
- **Camera as a primary control surface** — not just framing, but movement

Use this skill whenever the user wants a Wan prompt.

## When to use which variant

The Wan family has grown rapidly. Each variant has different strengths and prompt characteristics.

| Variant | Mode | Released | Best for |
|---|---|---|---|
| **Wan 2.1** | T2V, I2V | early 2025 | Baseline. Most ComfyUI workflows pin to 2.1 — many community LoRAs target it |
| **Wan 2.2 T2V (14B)** | Text-to-video | mid-2025 | Best for text-only video generation in the 2.2 family. MoE architecture. 720p, 24fps, ~5sec |
| **Wan 2.2 I2V (14B)** | Image-to-video | mid-2025 | The most common Wan use case — animate a still image |
| **Wan 2.2-Fun-Control (5B)** | Controlled gen | mid-2025 | Canny, Depth, Pose, MLSD, trajectory conditioning. Runs on RTX 4090 |
| **Wan 2.2-Animate** | Motion transfer | Sep 2025 | Animate a photo using motion from a reference video; or swap a character in a video |
| **Wan 2.5** | Refined I2V | late 2025 | Cleaner I2V with 4-part framework. Stronger motion coherence |
| **Wan 2.6** | Multi-shot, role-play | Dec 2025 | Cinematographer-style shot-block prompts with timecodes. Up to ~15s. Character consistency |
| **Wan 2.7** | Thinking Mode | April 2026 | Latest. Multi-reference (up to 9 images), 3000-token text, 12-language rendering, "thinking" before generation |

**If unsure, default to Wan 2.2 I2V** — most-used variant, well-documented, broadest community familiarity. Mention which you chose.

**Critical:** **Wan 2.6 prompts are structurally different** from 2.1/2.2 prompts (shot blocks with timecodes), and **Wan 2.7 has its own conventions** around Thinking Mode and multi-reference. Don't reuse a 2.2 prompt on 2.6+ unaltered — community testing confirms it consistently produces worse output.

See `references/model-variants.md` for deeper detail per variant and routing logic.

## Reference precedence

- `references/enrichment-palette.md` — the categorized menu for **Enhance Mode**: subject + key motion, body modifications, accessories, wardrobe-in-motion, camera movement vocabulary, environmental motion, light interaction (incl. multi-shot continuity), named-reference anchors (cinematographers and director-DP pairings), and the off-center-detail rule. **Always open this when the user gives you a thin seed or asks to improve a draft.**
- `references/wan-22-prompting.md` — the official Tongyi Wanxiang prompt formulas for Wan 2.2 (basic and advanced), with the canonical structure that comes from Alibaba's own docs
- `references/cinematography-vocabulary.md` — camera movements, shot types, lens vocabulary that Wan understands. This is high-leverage — Wan rewards real cinematography language. The enrichment palette's camera section complements rather than duplicates this file.
- `references/negative-prompts.md` — Wan's negative prompt patterns. Critical for I2V (prevents morphing/warping/distortion) and meaningfully different from image-model negatives.
- `references/wan-26-shot-blocks.md` — the new shot-block structured prompting convention for Wan 2.6 and 2.7. Use this for any 2.6+ prompts.
- `references/model-variants.md` — full variant catalogue, parameter routing, and version-specific quirks.

Don't read all of these for every prompt. Open the one(s) you need for the current decision. Always open `enrichment-palette.md` in Enhance Mode.

## Enhance Mode — thin seeds and improvement requests

**Enhance Mode fires when either:**

- (a) the user pastes an existing Wan prompt and asks to fix / improve / enhance it, OR
- (b) the seed is a short undifferentiated phrase like *"two strangers on a train platform"*, *"a fishing boat at sunrise"*, *"cyberpunk city"*, *"a chase through a tunnel"*.

Both go through the same rubric. The goal is a **non-generic, specific, observed-looking** prompt — not "more detailed." More detail without specificity just makes a longer mediocre prompt.

**Always open `references/enrichment-palette.md` when in Enhance Mode.** That file is the menu you pick from. Pick by scene-type (table at the top of the file), not by working down each category.

### Branch on target Wan version FIRST

The rubric BRANCHES on version because the output structure is fundamentally different:

- **Wan 2.1 / 2.2 and earlier:** single dense sentence (or 2 sentences for the advanced formula). Subject + key motion + scene + camera + atmosphere + style + named anchor + off-center detail all collapse into one prose block. **Order matters — front-load subject and motion.**
- **Wan 2.6 and later:** shot-block format with timecodes. Each shot gets: timecode → camera → subject + motion → environmental motion → light → (off-center detail in ONE shot only). Named anchor goes in the global look or the style/atmosphere line at the top of the block. Continuity anchors per shot.
- **Wan 2.7 multi-reference:** the multi-reference template (Reference assignment block + brand palette HEX) layers on top of the 2.6+ shot-block rubric. Reference assignments and brand palette come FIRST; then the shot-block rubric applies. Brand-color HEX placement sits in the global look's style/atmosphere line and is restated as a continuity anchor in later shots.

If the user's request doesn't name a version, ask. ("Are you targeting Wan 2.2 or Wan 2.6+? The structure differs.") If they hint a version indirectly (e.g. "I want a multi-shot reveal") infer 2.6+ and say so.

### The rubric — run in one pass, in order

1. **Diagnose** (1–2 sentences). What's missing? Likely: no specific subject, no key motion, no named camera move, dead air (no environmental motion), no named-reference anchor, no light interaction, generic adjective stack, no off-center detail, multi-shot prompt without continuity anchors. Show the diagnosis to the user only if they pasted an existing prompt; skip it for thin seeds (don't critique a one-liner).

2. **Specify the subject + KEY MOTION.** Replace "a woman" / "a man" / "a person" with 1–3 concrete facts drawn from the palette's **Subject specifics** AND name ONE key motion the subject performs in the shot (a held breath, a fingertip drumming twice, a glance off-camera and back). Motion is part of subject specificity in video — a generic "walks" or "looks" is the #1 cause of stock-feeling Wan output. Also locate the subject relative to the camera (medium close-up, over-the-shoulder, etc.).

3. **Anchor the style with ONE named reference.** From the palette's **Named-reference anchors** — a cinematographer (Roger Deakins, Christopher Doyle, Lubezki, Hoytema, Bradford Young...) OR a director-DP pairing (Wong Kar-wai + Doyle, Malick + Lubezki, Nolan + Hoytema, Lanthimos + Bakatakis) OR a genre/era (70s New Hollywood handheld, contemporary slow-cinema, cinéma vérité). **One anchor. Stacking two muddies the output.**

4. **Add the off-center detail.** Exactly ONE small, hyper-specific, observed-feeling micro-event (a hand trembling for a single beat, a stray leaf drifting through the lens during a pan, a phone vibrating once that the subject doesn't reach for, steam crossing the frame at one specific moment). For 2.6+ multi-shot, place it in ONE shot only — never in every shot, never in the global look. **Never skip it. Never include two.**

5. **Light interaction (2–3 details).** Describe HOW the light interacts — practical sources, color of bounce, time-of-day named precisely. For 2.6+ multi-shot with shots that span time, name the transition explicitly. For simultaneous shots, restate the key-light side and color temp as a continuity anchor.

5.5. **Camera movement.** Pick ONE movement from the palette's **Camera movement vocabulary** (slow push-in, lateral track, handheld follow, Steadicam glide, drone descend, orbit, etc.) or explicitly say "locked-off static." Don't leave the camera unspecified — Wan defaults to a generic drift. For 2.6+, each shot block gets its own camera move; pick differently across shots for variety unless continuity demands otherwise.

5.7. **Environmental motion.** Pick ONE primary indicator from the palette's **Environmental motion** category (wind shown by hair, dust catching backlight, steam crossing the frame, condensation rolling down a window, a curtain billowing at the edge of frame). Don't leave the air dead — dead-air shots read as CGI. Stacking environmental motion cues muddies the model; one is enough.

6. **Wardrobe-in-motion (1 cue) + environmental props (1 cue) if the scene supports them.** Don't just describe what fabric is — describe how it reacts to motion (linen catching the breeze, a coat hem trailing a half-beat behind a turn, a sweater hem riding up when she reaches). For environmental props, pick something that implies the subject was here before the camera arrived.

7. **Strip slop tokens.** Remove generic quality adjectives (*beautiful, stunning, masterpiece, 8k, ultra-detailed, professional, atmospheric, moody, dramatic, epic, breathtaking, ethereal, magical*) and standalone *"cinematic"*. Video-specific slop to strip from positive prompts: *"smooth motion," "buttery 60fps," "hyperreal," "ultra-cinematic," "epic," "breathtaking."* For Wan, the negative prompt is supported — these slop terms can go in the negative if useful, but mostly just delete them. Replace each removed slop term with a concrete detail or remove.

8. **Audit.** Read the prompt back. Could this describe a clip a real cinematographer might have captured, or does it still sound like a prompt? Verify: one named anchor, one off-center detail (one — not zero, not two), camera explicitly named, environmental motion explicitly named, light is interacting not just labeled. For 2.6+: continuity anchors present in shots 2+.

### Output format

- **User pasted an existing prompt:** 1–2 sentence diagnosis → fixed prompt in the appropriate output structure (single-block for 2.2, shot-block for 2.6+) → bullet list of what changed and why, calling out the named anchor and the off-center detail explicitly.
- **User gave a thin seed:** skip the diagnosis. Enhanced prompt in the appropriate output structure → short bullet list of what you added and why, naming the anchor and the off-center detail.

### Escape hatch

When the seed already carries an unusual or surreal ingredient — *"a Lynchian dream of a phone booth at the edge of a wheat field"*, *"a fish swimming through a kitchen as if it's the ocean"*, *"a Magritte sky raining bowler hats over a city street"* — the rubric overconstrains. Keep the existing concept; add ONLY camera movement, one environmental motion cue, one off-center detail, and one named anchor. Don't pile on subject specifics that fight the surreal/abstract register.

See Examples 6 and 7 below for the canonical Enhance Mode patterns (one shot-block, one single-sentence).

## Output requirement

For **text-to-video** on Wan 2.1 / 2.2 T2V:

```
**Positive prompt:**
\`\`\`
... prose prompt following the official formula ...
\`\`\`

**Negative prompt:**
\`\`\`
... brief negatives, see references/negative-prompts.md ...
\`\`\`
```

For **image-to-video** on Wan 2.2 I2V / 2.5:

```
**Motion prompt:**
\`\`\`
... motion / camera / environment / pacing description ...
\`\`\`

**Negative prompt:**
\`\`\`
... morphing/warping prevention set ...
\`\`\`
```

For **multi-shot cinematic** on Wan 2.6 / 2.7:

```
**Global look:**
[tone, lighting, palette, realism level, lens character]

**Shot 1 [0–Xs]:**
[camera movement and action over time]

**Shot 2 [X–Ys]:**
[continuation with restated continuity anchors]

**Negative prompt:**
\`\`\`
... ...
\`\`\`
```

For **Wan 2.7 with multi-reference inputs** (up to 9 references) or **branded work with brand colors**, prepend a Reference assignment block before the Global look:

```
**Reference assignment:**
- Reference 1 — [role: main character / environment / product / brand mark / etc.]
- Reference 2 — [role]
- Reference 3 — [role]

**Brand palette (if applicable):** primary `#HEX`, accent `#HEX`

**Global look:**
...
```

After that, follow the same shot-block structure. The reference roles and brand palette establish bindings before any shot block uses them — restate the palette as a continuity anchor in later shots.

After the code blocks, add a one-line note on **recommended parameters** if relevant (resolution, fps, seed advice).

## Length sweet spots

- **Wan 2.1 / 2.2 T2V:** 80–120 words. Enough to specify subject + scene + motion + camera + style without overloading.
- **Wan 2.2 I2V / 2.5 I2V:** 40–80 words. The image already provides the "what" — your job is to describe motion.
- **Wan 2.6 / 2.7 multi-shot:** 30–60 words per shot block. Total across blocks can reach 150–250 words for a 3-shot sequence.
- **Wan 2.6 / 2.7 single-shot:** 60–100 words structured as global look + shot block.

Too short → the model fills gaps with generic motion. Too long → it averages or drops detail.

## The official Wan 2.2 prompt formula

This comes from Alibaba's own Tongyi Wanxiang documentation. It's the canonical structure.

### Basic formula (for new users, simple scenes)

> **prompt = subject + scene + motion**
> (主体 + 场景 + 运动)

Example:
> A young Chinese woman in mecha-styled hanfu, raven hair pulled into a bun, turning to look at the camera, her soft and lustrous hair drifting lightly in the air.

### Advanced formula (for richer scenes, better cinematic results)

> **prompt = subject(description) + scene(description) + motion(description) + camera language + atmosphere + stylization**
> (主体 + 场景 + 运动 + 镜头语言 + 氛围词 + 风格化)

- **Subject description** — appearance, traits, clothing. E.g., "a black-haired Miao ethnic-minority girl in traditional dress"
- **Scene description** — environment details. Foreground/midground/background, time of day, weather.
- **Motion description** — amplitude (small/large), speed (slow/fast), effect (e.g., "shattering the glass", "swaying violently", "moving slowly")
- **Camera language** — shot type, angle, lens, camera movement. See `references/cinematography-vocabulary.md` for the canonical vocabulary.
- **Atmosphere** — single mood word: "dreamy", "lonely", "majestic", "tense", "tranquil"
- **Stylization** — visual style anchor: "cyberpunk", "line-illustration", "wasteland aesthetic", "cinematic film still"

Example:
> A black-haired Miao ethnic-minority girl in traditional embroidered indigo robes walks slowly through a misty rice terrace at dawn, her silver headpiece catching the first cool light. The camera tracks alongside her at waist level with a smooth dolly move, eventually pushing in to a medium close-up as she pauses to look out across the valley. Soft volumetric mist drifts between layered fields, low golden-blue ambient light. Tranquil, contemplative atmosphere, cinematic film still in the documentary tradition.

See `references/wan-22-prompting.md` for the full formula breakdown with more examples.

## I2V (image-to-video) specifics

Wan 2.2 I2V and Wan 2.5 I2V are the most-used Wan variants. The image you upload already defines the "what" — your prompt's job is to describe **how things move**.

The **4-part I2V framework:**

1. **Primary motion** — what the main subject does. Concrete verbs: "spins", "walks forward", "raises her hand". Avoid vague descriptors.
2. **Camera behavior** — pan, tilt, dolly, orbit, static, push-in, pull-back. Pick ONE main camera movement per generation.
3. **Environmental effects** — secondary motion: wind in hair, falling leaves, swaying trees, rippling water, drifting smoke.
4. **Speed / intensity modifiers** — "slow", "smooth", "rapid", "subtle", "intense". Tunes the pace.

Template:
> [Primary motion], [camera movement], [environmental effects], [speed modifiers]

Example for a portrait image:
> The woman turns her head slowly to look directly at the camera, slight gentle smile forming. The camera holds static. Soft wind moves her hair and the leaves visible in the background. Slow, controlled pace throughout.

**I2V do's and don'ts:**

- ✅ Describe motion of elements already in the image
- ✅ Specify what stays still ("subject's face remains expressionless, only hair moves")
- ✅ Layer motion for depth: foreground / midground / background
- ❌ Don't try to add new elements not in the image — the model animates what exists
- ❌ Don't combine simultaneous complex camera moves — chain them sequentially or pick one
- ❌ Don't describe new scenery — that's what T2V is for

See `references/wan-22-prompting.md` for more I2V patterns.

## Camera language — Wan's biggest control surface

Wan was specifically trained on cinematography vocabulary. Real camera terms work better than generic descriptions.

Common camera movements Wan recognizes:

| Movement | What it does |
|---|---|
| **Static / locked-off** | Camera doesn't move |
| **Pan (left/right)** | Camera pivots horizontally on a fixed point |
| **Tilt (up/down)** | Camera pivots vertically |
| **Dolly (in/out)** | Camera physically moves forward or back |
| **Truck (left/right)** | Camera physically moves sideways |
| **Pedestal (up/down)** | Camera physically moves vertically |
| **Orbit** | Camera circles around the subject |
| **Push-in** | Slow dolly forward, building intensity |
| **Pull-back** | Slow dolly out, often as a reveal |
| **Tracking shot** | Camera follows the subject's motion |
| **Handheld** | Subtle vibration, documentary feel |
| **Whip pan** | Very fast pan, often for transitions |
| **Crane / boom** | Camera rises or descends through space |
| **POV** | First-person perspective |
| **Dutch angle** | Tilted frame, tension |

**Important:** pick ONE main camera movement per generation on Wan 2.1/2.2. Combining "dolly in while panning right and tilting up" produces muddled motion. If you need multiple moves, either:

- Chain them sequentially with explicit timing: "camera dollies in for the first half, then pans right"
- Move up to Wan 2.6/2.7 where multi-stage camera moves are better supported

See `references/cinematography-vocabulary.md` for the full vocabulary including shot types, lens choices, and named cinematic patterns.

## Negative prompts — critical for Wan

Unlike image models where negative prompts are optional polish, Wan negative prompts are load-bearing — especially for I2V, where they prevent the most common failure modes (morphing, warping, face distortion, flickering).

### Default I2V negative prompt

```
morphing, warping, distortion, face deformation, eye distortion, identity drift, flickering frame artifacts, jittering, sudden changes, inconsistent lighting, color shifting, scale changes, new elements appearing, compositional changes, bad anatomy, extra limbs, object shape morphing, geometric distortion, label drift, text warping
```

### Default T2V negative prompt

```
bright colors, overexposed, static, blurred details, subtitles, watermark, style transitions, jpeg artifacts, low quality, ugly, deformed, malformed limbs, extra fingers, poorly drawn hands, poorly drawn faces, cluttered background, still picture, motion smearing
```

### Targeted additions

- For portraits/faces: add `eye distortion, face morphing, changing facial features`
- For landscapes/horizons: add `horizon warping, ground tilting, scale inconsistency`
- For products: add `label distortion, text warping, surface morphing`
- For action/motion: add `motion blur artifacts, jittery motion, frame interpolation artifacts`

See `references/negative-prompts.md` for the complete catalog.

## Wan 2.6 and 2.7: shot-block prompting

**Big behavioral change from 2.2 to 2.6+.** Reusing 2.2-style prompts on 2.6 produces noticeably worse output. The community has confirmed this consistently.

Wan 2.6 introduced **cinematographer-style structured prompting**: a hierarchical structure of global look + shot blocks with explicit timecodes.

```
Global look: [tone, lighting, palette, realism level, lens character]

Shot 1 [0–10s]: [camera movement and action over time]

Shot 2 [10–15s]: [continuation with restated continuity anchors]
```

**Why this works on 2.6+ and not 2.2:** Wan 2.6 reasons about time and shot structure as primary input dimensions, not as decoration. Wan 2.2 averages mood + camera + action when they're mixed in one sentence; Wan 2.6 keeps them separate when you structure them separately.

**Multi-shot continuity on 2.6/2.7:** restate continuity anchors across shots — character (face, wardrobe), spatial logic, lighting consistency — because Wan does NOT strongly infer continuity across cuts. Limit to 2–4 shots per 15-second prompt.

**Continuity anchor template:** start each subsequent shot with the "Same X, same Y, same Z — continuity is critical" pattern. Concretely:

> *"Same chef, same navy chef's coat, same slate plate with the three scallops and citrus emulsion exactly as left in Shot 1 — continuity is critical."*

Or for product/brand work:

> *"Brand palette persists; the keyboard's navy keycaps and gold-accented escape key remain identical to Shot 1."*

**What to anchor (most common):** character identity (face, hair, build), wardrobe (specific garments + color), object positions (props that haven't been moved), lighting direction (key light side), palette (dominant + accent), architectural elements (room layout, fixed fixtures).

See `references/wan-26-shot-blocks.md` for the full pattern with examples.

## Wan 2.7 specific features

Wan 2.7 introduced major capability upgrades:

- **Thinking Mode** — the model reasons about the prompt and plans composition before generating. Benefits longer/complex prompts. Default ON in most workflows.
- **Multi-reference editing** — up to 9 reference images can be passed to bind characters, products, environments
- **Long text rendering** — up to 3000 tokens of text in-frame, 12 languages including Chinese, Japanese, Korean, Arabic
- **Color control** — supports HEX codes and palette specifications for brand-accurate visuals

For Wan 2.7 prompts:

- Specify the reference images' roles via the **Reference assignment** output block (see §Output requirement). One line per reference, role explicit.
- For branded work, include HEX codes. **Where to place them:**
  - In the **Reference assignment block** as `**Brand palette:**` primary + accent
  - In the **Global look** when describing palette (e.g. *"brand palette dominated by deep navy `#1A3A6B` for surfaces and shadows with warm gold `#F4B400` accents on highlights"*)
  - In **each shot block** when the color appears prominently in that shot (e.g. *"rendered in warm gold `#F4B400` against a deep navy `#1A3A6B` background"*)
  - **Restate as a continuity anchor** in later shots (e.g. *"Brand palette persists"*)
- Long in-frame text works — wrap in double quotes and specify font style as on Qwen/Z-Image

## Avoid (waste tokens, dilute results)

- Vague descriptors: `beautiful`, `amazing`, `stunning`, `epic`, `cinematic` as standalone
- Quality crutches: `8k`, `4k`, `hdr`, `masterpiece`, `ultra-detailed`
- Contradictory motion: "subject runs fast while camera holds completely still and zooms in slowly" — pick one approach
- Camera move stacking on 2.1/2.2: "dolly in, pan right, tilt up, orbit, push in" — sequential or pick one
- Adding new elements on I2V — the model animates what's there, not what you wish was there

## Override loaded labels

Same as image prompting: tokens like `CEO`, `businessman`, `fashion model`, `rock star` carry strong default looks. Override with role + 2–3 specific traits.

This matters MORE on video — Wan's defaults persist across every frame, so a generic label produces a generic person moving generically for 5 seconds straight.

## NSFW handling

Wan base models have light content filtering compared to commercial alternatives. Community fine-tunes on Civitai add explicit NSFW capability. For NSFW video work:

- Use plain descriptive English
- Apply `adult` modifier discipline as on image prompts
- Wan 2.1/2.2 with community NSFW LoRAs is the most common path

**Absolute boundary:** NEVER produce NSFW prompts involving anyone described or implied as a minor. The `adult` modifier discipline is mandatory; if a request mixes NSFW intent with any underage signal, refuse and explain.

## Recommended parameters

- **Wan 2.1 / 2.2 T2V:** 720p, 24fps, ~5sec clips, `cfg_scale: 5.0–7.0`, `steps: 30–50`
- **Wan 2.2 I2V:** Same as T2V; the image acts as the first frame
- **Wan 2.2-Fun-Control (5B):** runs on RTX 4090, 16fps for drafts then upscale to 24fps for finals
- **Wan 2.5 I2V:** as 2.2 I2V
- **Wan 2.6 / 2.7:** support longer clips (up to ~15s), higher resolution options; check the platform you're using for current defaults
- **Wan 2.7 Thinking Mode:** higher inference time per generation but markedly better coherence

Mention these to the user when they're load-bearing.

## Examples

### Example 1 — Wan 2.2 I2V, simple animation

User: "I have a portrait of a woman by a window. Make her turn and smile at the camera."

Motion prompt:
```
The woman slowly turns her head toward the camera, a gentle natural smile forming as she fully faces forward. Camera remains static throughout. Soft window light continues to fall across her face; subtle wind from the window moves a few strands of her hair. Slow, controlled motion across the full clip duration.
```

Negative prompt:
```
morphing, warping, face deformation, eye distortion, changing facial features, identity drift, flickering, sudden changes, inconsistent lighting, color shifting, new elements appearing, scale changes, bad anatomy
```

**Params:** Wan 2.2 I2V, 720p, 24fps, ~5sec, `cfg_scale: 6.0`

### Example 2 — Wan 2.2 T2V, official advanced formula

User: "Misty rice terraces at dawn, a girl walking through"

Positive prompt:
```
A young woman in traditional indigo Miao ethnic-minority robes with intricate silver embroidery, raven hair pulled into a low bun, walks slowly along a narrow earthen path between layered rice terraces at dawn. The terraces are filled with shallow water reflecting the pre-sunrise sky, low mist drifting between fields, distant mountains barely visible through the haze. The camera tracks alongside her at waist height with a smooth dolly move, then pushes in to a medium close-up as she pauses to look out across the valley. Cool blue-gold ambient light from the rising sun, soft volumetric mist, contemplative tranquil atmosphere, cinematic film still in the documentary tradition.
```

Negative prompt:
```
bright colors, overexposed, static, blurred details, subtitles, watermark, style transitions, jpeg artifacts, low quality, deformed, extra fingers, poorly drawn hands, poorly drawn faces, cluttered background, motion smearing, frame interpolation artifacts
```

**Params:** Wan 2.2 T2V (14B), 720p, 24fps, 5sec, `cfg_scale: 6.5`, `steps: 40`

### Example 3 — Wan 2.6, multi-shot cinematic

User: "A chase scene through an underground tunnel, gritty noir feel"

```
**Global look:**
Cold fluorescent lighting with intermittent flicker, desaturated palette with hints of sodium-yellow from overhead lamps, handheld realism, lens character of a 35mm anamorphic with subtle flare on bright sources, slight motion blur on quick movements.

**Shot 1 [0–6s]:**
Single continuous handheld shot following a man in his thirties wearing a dark jacket as he runs through narrow underground concrete corridors. Camera tracks behind him at shoulder height, weaving as he turns corners. Footsteps echo, breath ragged. Tunnel curves visibly ahead, distant emergency exit sign barely visible at the far end.

**Shot 2 [6–12s]:**
Same man, same dark jacket and build for continuity. Camera ahead of him now, dolly-back as he runs toward the lens. Behind him, a single distant figure in silhouette appears at the corridor's mouth. The fluorescent lights flicker more violently. He glances back over his shoulder once without slowing.

**Negative prompt:**
identity drift, character morphing, wardrobe changes, inconsistent lighting between shots, new elements appearing, scale changes, jumpy cuts, motion artifacts, ghosting, deformed
```

**Params:** Wan 2.6, ~12sec, `cfg_scale: 6.0`, Thinking Mode if available

### Example 4 — improving a Wan 2.1/2.2 prompt that was reused on 2.6

User: "My old Wan 2.2 prompt works badly on Wan 2.6. Can you fix it? 'A cyberpunk city at night, neon lights, a woman walking through the rain, cinematic, dramatic lighting, 4k, masterpiece'"

Diagnosis: this is a 2.2-style prompt — global mood, action, and camera mashed into one sentence. On 2.6+, this consistently produces averaged/muddled output. Need to restructure into global look + shot block, drop quality crutches, give the camera real instructions.

```
**Global look:**
Rain-soaked cyberpunk metropolis at night, saturated neon palette dominated by hot pink and cool cyan, practical lighting from holographic billboards and storefront signage, anamorphic lens character with subtle horizontal flare on bright sources, slight chromatic aberration, wet asphalt with strong reflections.

**Shot 1 [0–8s]:**
A woman in her late twenties wearing a dark transparent raincoat over an urban outfit walks at an even pace down a narrow rain-soaked alley. Camera tracks alongside her at hip height on a slow dolly, eventually pulling back gently to reveal more of the towering neon-lit cityscape above. Foreground rain droplets in sharp focus, midground neon reflections smearing across puddles as she passes, distant skyscrapers softening into glowing haze. Slow controlled pacing.

**Negative prompt:**
morphing, warping, face deformation, identity drift, flickering, sudden changes, inconsistent lighting, scale changes, motion smearing, frame interpolation artifacts, jittery handheld feel, cluttered overlapping subjects
```

What changed: separated global look from shot block, gave the camera a single coherent move (slow dolly-tracking with gentle pull-back) instead of unspecified "dramatic" framing, removed all quality crutches ("4k, masterpiece, cinematic" as adjectives), specified the spatial layering for depth, kept the cyberpunk identity tight to one shot block instead of trying to wedge mood into the action sentence.

**Params:** Wan 2.6, 8sec, Thinking Mode

### Example 5 — Wan 2.7 multi-reference product reveal

User: "Wan 2.7 — I have 3 reference images: my logo (a stylized fox), my office (modern coworking space), my product (a slim mechanical keyboard, brand colors #1A3A6B and #F4B400). Make a 10-second product reveal."

**Reference assignment:**
- Reference 1 — brand logo (stylized fox): opening graphic identity
- Reference 2 — office environment: setting for the product reveal
- Reference 3 — product (slim mechanical keyboard): hero object of the reveal

**Brand palette:** primary `#1A3A6B` (deep navy), accent `#F4B400` (warm gold)

**Global look:**
Modern minimal product-launch aesthetic, clean editorial lighting, shallow depth of field with crisp product focus, brand palette dominated by deep navy `#1A3A6B` for surfaces and shadows with warm gold `#F4B400` accents on highlights and the logo mark, 50mm-equivalent lens character, near-flat color grade.

**Shot 1 [0–3s]:**
Open on the stylized fox logo from Reference 1, rendered in warm gold `#F4B400` against a deep navy `#1A3A6B` background, the logo glyph held centered for one beat then beginning a soft luminous bloom expansion outward. Camera holds locked-off. Subtle particle motion suggests light dust catching the brand color.

**Shot 2 [3–10s]:**
Cut to the coworking office from Reference 2 — modern open workspace with mid-century wooden desks, soft daylight from large windows on the left, warm gold accents on small details (a single lamp, a houseplant pot). The mechanical keyboard from Reference 3 sits on a clean dark walnut desk in the center foreground. Camera begins a smooth slow dolly-in from medium distance toward the keyboard, eventually settling on a close three-quarter hero shot of the keyboard with the navy keycaps and gold-accented escape key clearly visible. Brand palette persists; no other branding visible in frame.

**Negative prompt:**
```
identity drift, logo distortion, color shifting, brand-color drift, keyboard morphing, key deformation, label warping, text artifacts, additional logos appearing, color contamination from neighboring objects, inconsistent lighting between shots, scale changes, motion smearing
```

Notes: demonstrates the **Reference assignment** output block, brand-palette HEX placement (in Reference assignment, in Global look, in shot blocks, and as a continuity anchor in Shot 2), and product-shot-specific negatives (brand-color drift, keyboard morphing, key deformation).

**Params:** Wan 2.7, 10s, **Thinking Mode ON**, ~24fps, `cfg_scale: 6.0`. Pass References 1–3 in the order assigned above.

### Example 6 — Enhance Mode, thin seed, Wan 2.6+ shot-block (the headline test)

User: *"two strangers on a train platform"*

(Default to Wan 2.6 for a thin seed with multi-shot potential; said so before generating.)

```
**Global look:**
Late dusk pulling into night, a suburban commuter platform under sodium-yellow overhead lamps with the last cold blue of sky still in the gaps above the canopy, in the register of Christopher Doyle on In the Mood for Love — saturated edges, slow shutter, slight blown highlights on the lamps. Anamorphic lens character, gentle horizontal flare on the brightest sources.

**Shot 1 [0–5s]:**
Medium long shot, locked-off static. A woman in her early thirties in a long charcoal wool coat (collar turned up, one button missing at the waist) stands at the edge of the platform looking down the track to camera-left, a leather tote at her feet. A man in his late forties in a tan barn jacket stands fifteen feet to her right, hands in his pockets, also looking down the track. Neither moves much — she shifts her weight once, he exhales and the breath fogs faintly in the cold air. Continuity anchors for this sequence: charcoal wool coat with the missing button, tan barn jacket, sodium-lamp key from above, the platform's specific concrete pattern.

**Shot 2 [5–10s]:**
Same woman, same charcoal coat (missing button), same sodium-lamp key from above as Shot 1 — continuity is critical. Cut to a medium close-up from her three-quarter front, the camera in a glacial slow push-in over the full duration of the shot. She tucks a loose strand of hair behind her ear without looking down. A receipt slips from the open mouth of her tote and lands face-up on the platform, the wind from the approaching train lifting it half an inch and setting it back down — she doesn't reach for it. Her hair drifts slightly in the same wind, the only environmental motion. The sodium light catches one cheekbone.

**Shot 3 [10–15s]:**
Same man, same tan barn jacket, same sodium-lamp key as Shots 1 and 2. Wide two-shot from a low angle behind both subjects, the headlight of the approaching train just visible at the far end of the platform. Steadicam glides forward a single deliberate beat toward them, the train's wash beginning to lift the edges of both coats. Neither looks at the other.

**Negative prompt:**
identity drift, character morphing, wardrobe changes between shots, missing-button drift, inconsistent lighting between shots, color shifting, scale changes, new elements appearing, jittery handheld, motion smearing, deformed faces, extra limbs, label warping, frame interpolation artifacts
```

What was added:
- **Named-reference anchor:** Christopher Doyle on *In the Mood for Love* — one anchor, in the global look only, not restated as a register in every shot.
- **Subject specifics + key motion:** charcoal wool coat with one button missing at the waist, tan barn jacket, ages, the woman's weight shift, the man's fogged exhale — small physical specificity over generic "stands."
- **Camera movement, one per shot:** Shot 1 locked-off static, Shot 2 glacial slow push-in, Shot 3 Steadicam glide. Each shot's camera has a distinct identity.
- **Environmental motion:** wind from the approaching train shown ONCE — through the receipt lifting and the hair drifting in the same beat. One primary indicator, not stacked.
- **Off-center detail (in Shot 2 only):** the receipt slipping out of the tote, lifting half an inch in the train's wash, never recovered. Observed, not invented; placed in exactly one shot.
- **Light interaction:** sodium-yellow overhead lamps + the last cold blue in the sky + the lamp catching one cheekbone in Shot 2 — interacting, not labeled.
- **Continuity anchors:** charcoal coat + missing button, tan jacket, sodium key direction restated each shot. The missing button is a strong continuity hook because it's a specific imperfection Wan can track.

**Params:** Wan 2.6, ~15s, Thinking Mode if available, `cfg_scale: 6.0`. Three shot-blocks within the 15s budget; continuity anchors mandatory.

### Example 7 — Enhance Mode, thin seed, Wan 2.2 single-sentence

User: *"a fishing boat at sunrise"*

(Default to Wan 2.2 T2V for a single-shot seed; mentioned that 2.6 would let it become multi-shot if wanted.)

Positive prompt:
```
A weathered wooden fishing boat with peeling pale-blue paint and a single missing letter from the stenciled name on the bow ("MAR — A" with the second letter scuffed away) putts out of a small harbor at the moment the sun first clears the horizon, a fisherman in his sixties in a faded yellow oilskin coat (sleeves rolled twice, a long thin scar along the inside of his left forearm visible at the rolled cuff) standing at the wheel as he glances down at a coiled rope at his feet without slowing the throttle, while one gull tracks the boat at the right edge of the frame and the warm low light catches the steam rising from a chipped enamel mug wedged in the dashboard at one specific beat as the boat clears the breakwater. Camera locked-off static from a low dock-level vantage as the boat passes left to right, anamorphic lens with subtle horizontal flare on the rising sun, slight color cast pushing the highlights warm and the shadows cool — in the register of 70s New Hollywood handheld pulled toward Terrence Malick magic-hour patience.
```

Negative prompt:
```
bright colors, overexposed, static dead air, blurred details, subtitles, watermark, jpeg artifacts, low quality, deformed, malformed limbs, extra fingers, poorly drawn hands, poorly drawn faces, cluttered background, motion smearing, label drift, text warping, name-stencil morphing, smooth motion, ultra-cinematic
```

What was added (collapsed into the single sentence):
- **Named-reference anchor:** *"70s New Hollywood handheld pulled toward Terrence Malick magic-hour patience"* — one anchor (the second clause is a qualifier of the first, not a stacked second name-drop).
- **Subject specifics + key motion:** sixties, faded yellow oilskin, sleeves rolled twice, the scar on the forearm visible at the rolled cuff, AND the key motion (glancing down at the coiled rope without slowing the throttle — not just "drives the boat").
- **Off-center detail:** the missing letter from the stenciled name on the bow ("MAR — A"). Observed, not invented; sticks in the eye.
- **Camera movement:** locked-off static, low dock-level vantage, the boat passing left to right through frame — explicitly named, not left to Wan to default.
- **Environmental motion:** steam rising from the chipped enamel mug crossing the frame at ONE specific beat as the boat clears the breakwater — one primary indicator, video-time-specific.
- **Light interaction:** warm low light + the sun clearing the horizon + anamorphic flare on the rising sun + warm highlights / cool shadows — interacting, not labeled.
- **Wardrobe-in-motion:** the oilskin's sleeves rolled twice and the scar visible at the cuff (a small implied motion as the arms move at the wheel).
- **Order matters for 2.2:** subject + key motion front-loaded, camera and style at the back, off-center detail (missing letter) within the first third for emphasis.

**Params:** Wan 2.2 T2V (14B), 720p, 24fps, 5sec, `cfg_scale: 6.5`, `steps: 40`.

## Pre-flight checklist

Before returning the prompt, verify:

- [ ] Identified target variant (2.1 / 2.2 T2V / 2.2 I2V / 2.5 / 2.6 / 2.7) and used correct structure
- [ ] For 2.2 T2V: followed the official subject + scene + motion + camera + atmosphere + style formula
- [ ] For I2V: described motion of existing elements, didn't try to add new ones
- [ ] For 2.6/2.7: structured as global look + shot blocks with timecodes
- [ ] For 2.7 multi-reference: Reference assignment block (and brand palette HEX if applicable) PRECEDES the shot blocks
- [ ] Specified ONE main camera movement per shot (or chained them sequentially with explicit timing) — camera explicitly named or "locked-off," never left unspecified
- [ ] Used real cinematography vocabulary (dolly, pan, push-in, tracking shot — not vague "dramatic" or "epic")
- [ ] **Environmental motion explicitly described** — at least one primary indicator (wind in hair, dust catching backlight, steam crossing the frame, condensation rolling). Don't leave the air dead.
- [ ] Included a negative prompt — Wan negatives are load-bearing, not optional polish
- [ ] For I2V: added the morphing/warping/distortion prevention set
- [ ] For multi-shot 2.6/2.7: restated continuity anchors (character, wardrobe, spatial logic, light direction) across shots
- [ ] No quality-adjective crutches (4k, 8k, masterpiece, ultra-detailed, professional, smooth motion, buttery 60fps, hyperreal, ultra-cinematic)
- [ ] Length matches variant (80–120 words T2V, 40–80 I2V, 30–60 per shot block on 2.6/2.7)
- [ ] Atmosphere word and style anchor included for T2V
- [ ] Recommended parameters noted
- [ ] For NSFW: appropriate variant, `adult` modifier present, no-minors boundary maintained
- [ ] **If in Enhance Mode:** opened `references/enrichment-palette.md` and picked enrichments by scene-type
- [ ] **Exactly ONE named-reference anchor** (one cinematographer / director-DP pairing / genre-era anchor) — never "cinematic" / "atmospheric" alone, never two anchors stacked
- [ ] **Exactly ONE off-center detail per prompt** (or per shot-block sequence, placed in ONE shot only — not in every shot, not in the global look). Never zero, never two.
