# Wan 2.2 Official Prompt Formula

This reference documents the canonical prompt formulas published by Alibaba's Tongyi Wanxiang team for Wan 2.2. These are the structures the model was trained to expect — using them produces meaningfully better output than ad-hoc prose.

Two formulas are documented: a basic one for new users and an advanced one for richer scenes. Both are still the official guidance for Wan 2.2 T2V and remain the structural foundation for I2V (with the modifications noted in the I2V section).

---

## Basic formula

For new users and simple scenes. Loose, imaginative prompts generate more creative results.

> **prompt = subject + scene + motion**
> (主体 + 场景 + 运动)

### Component definitions

- **Subject (主体)** — the primary visual subject. Can be a person, animal, plant, object, or imaginary entity that doesn't exist physically.
- **Scene (场景)** — the environment the subject is in. Includes background and foreground. Can be a real physical space or an imagined fictional setting.
- **Motion (运动)** — the subject's specific motion plus secondary motion of non-subject elements. Can be: still, small movements, large movements, partial movement, or overall dynamics.

### Basic formula examples

> "A young woman with raven hair in mecha-styled hanfu, in a softly-lit studio space, turning slowly to look at the camera as her hair drifts lightly."

> "An ancient stone dragon coiled around a moonlit mountain peak, slowly opening its eyes."

> "A barefoot child running across a wet beach at sunset, kicking up small splashes with each step."

---

## Advanced formula

For users with some Wan experience. Adds depth and storytelling.

> **prompt = subject(description) + scene(description) + motion(description) + camera language + atmosphere + stylization**
> (主体 + 场景 + 运动 + 镜头语言 + 氛围词 + 风格化)

### Component definitions

- **Subject description (主体描述)** — adjectives or short phrases describing the subject's appearance and traits. Examples: "a black-haired Miao ethnic-minority girl in traditional embroidered dress", "a flying fairy from another world wearing tattered yet beautiful clothes with strange wings made from ruined fragments unfolding behind her".

- **Scene description (场景描述)** — adjectives or short phrases describing environmental features. Layered: foreground, midground, background. Time of day, weather, atmosphere.

- **Motion description (运动描述)** — motion characteristics including amplitude, speed, and effect. Examples: "swaying violently", "moving slowly", "shattering the glass", "drifting gently in the wind".

- **Camera language (镜头语言)** — shot type, angle, lens, and camera movement. See `references/cinematography-vocabulary.md` for the complete vocabulary.

- **Atmosphere (氛围词)** — a single mood word describing the intended feel. Examples: "dreamy" (梦幻), "lonely" (孤独), "majestic" (宏伟), "tranquil", "tense", "ominous", "playful".

- **Stylization (风格化)** — the visual style anchor. Examples: "cyberpunk" (赛博朋克), "line-illustration" (勾线插画), "wasteland aesthetic" (废土风格), "cinematic film still", "anime-style", "claymation", "watercolor".

### Advanced formula example

> A young woman in traditional indigo Miao ethnic-minority robes with intricate silver embroidery, raven hair pulled into a low bun and adorned with a silver headpiece, walks slowly along a narrow earthen path between layered rice terraces at dawn. The terraces are filled with shallow water reflecting the pre-sunrise sky in pale gold and blue, low mist drifting between fields, distant mountains barely visible through the haze. The camera tracks alongside her at waist height with a smooth dolly move, eventually pushing in to a medium close-up as she pauses to look out across the valley. Cool blue-gold ambient light, soft volumetric mist, tranquil contemplative atmosphere, cinematic film still in the documentary tradition.

Break down:
- **Subject description:** young woman in indigo Miao robes with silver embroidery, raven hair in low bun, silver headpiece
- **Scene description:** narrow earthen path between rice terraces at dawn, shallow water reflecting sky, low mist, distant mountains in haze
- **Motion description:** walks slowly, pauses to look across the valley
- **Camera language:** tracks alongside at waist height with smooth dolly, pushes in to medium close-up
- **Atmosphere:** tranquil, contemplative
- **Stylization:** cinematic film still in the documentary tradition

---

## Adapting the formula for I2V (image-to-video)

For Wan 2.2 I2V and Wan 2.5 I2V, the image already provides the subject and scene. Adjust the formula:

> **I2V prompt = motion(description) + camera language + environmental effects + pacing modifiers**

The subject and scene aren't omitted — they're provided by the uploaded image. Your prompt's job is to specify how everything moves.

### I2V example

For a portrait of a woman by a window:

> The woman slowly turns her head toward the camera, a gentle natural smile forming as she fully faces forward. Camera holds static throughout. Soft wind from the window moves a few strands of her hair, and the leaves visible outside sway gently. Slow, controlled motion across the full duration.

Break down:
- **Motion description:** turns head slowly, gentle smile forms
- **Camera language:** static
- **Environmental effects:** wind moves hair, leaves sway outside
- **Pacing modifier:** slow, controlled

### I2V do's

- ✅ Describe motion of elements that ARE already in the image
- ✅ Be explicit about what stays still ("face remains expressionless, only hair moves")
- ✅ Layer motion for depth: foreground (subject) / midground (immediate surroundings) / background (distant elements)
- ✅ Use one main camera move per generation
- ✅ Specify pacing — slow vs fast vs accelerating

### I2V don'ts

- ❌ Don't add new elements not in the image ("she takes out a phone" if no phone is visible)
- ❌ Don't change scenery ("the cafe becomes a beach")
- ❌ Don't combine simultaneous complex camera moves on 2.1/2.2 — chain them sequentially
- ❌ Don't describe the subject's appearance again — that's already locked by the image

---

## Common patterns by use case

### Portrait → animated portrait

> [Subject motion: turns/smiles/blinks/looks], camera static or slow push-in, environmental effects in [hair/clothes/background], slow pacing.

Example:
> The man closes his eyes for a moment then slowly opens them, refocusing on the camera. Camera holds static. His hair lifts slightly in the breeze, the leaves behind him rustle gently. Slow, intimate pacing.

### Landscape → cinematic reveal

> [Environmental motion in the scene], camera [slow pan/tilt/pull-back/push-in], [atmospheric effects], slow majestic pacing.

Example:
> Clouds drift slowly across the mountain peaks, shadows shifting across the slopes below. Camera slowly tilts up from the valley floor to reveal the full mountain range above. Mist rises from the lower altitudes. Slow majestic pacing, contemplative atmosphere.

### Product shot → product video

> [Product subtle motion or none], camera [orbit/push-in/dolly around], [light interaction effects], smooth controlled pacing.

Example:
> The watch face remains the centerpiece, the second hand ticking smoothly forward. Camera orbits 180 degrees around the watch on a slow steady arc. Highlights shift across the polished case as the angle changes. Smooth controlled pacing, premium product reveal.

### Character action → narrative shot

> [Subject's action with specific verbs], camera [tracking/handheld/dolly], [environmental atmosphere], pacing to match action.

Example:
> The chef tosses the pan with practiced ease, ingredients lifting and rotating before settling back. Camera tracks at counter height with a slow handheld feel. Steam rises from the pan, gas flames flicker visibly below. Pacing matches the toss rhythm, kinetic kitchen atmosphere.

---

## What's different between the basic and advanced formulas

Use the basic formula when:
- The user gives you a short, abstract idea
- They want creative latitude — "let the model surprise me"
- Quick iteration or brainstorming
- You're testing a concept before committing to a final render

Use the advanced formula when:
- The user has a specific cinematic intent
- Camera and lighting matter for the final result
- It's for commercial or portfolio work
- The user has provided detailed source material

The advanced formula isn't strictly better — basic formula prompts often produce more imaginative, less constrained output. They're tools for different jobs.

---

## Common mistakes when using the formula

**Subject and scene mashed together:** "a woman in a beautiful forest" doesn't separate clearly. Better: subject = "a woman with auburn hair in a green canvas jacket"; scene = "a misty Douglas fir forest at dawn, fern undergrowth, distant trunks dissolving into haze".

**Motion as static description:** "the woman is happy" is not a motion. Wan needs verbs. Better: "the woman laughs and turns her head to the side, mid-laugh."

**Camera as decoration instead of instruction:** "dramatic cinematic camera" tells Wan nothing. Better: "slow dolly-in from medium shot to close-up, camera at eye level."

**Atmosphere as adjective stack:** "moody, dark, gritty, intense, dramatic, atmospheric" cancels out. Pick one anchor word.

**Style as contradictions:** "photorealistic anime cyberpunk watercolor" produces a mess. Pick one stylization.

---

## When to break the formula

The formula is the recommended structure, but it's not a straitjacket. Skip components when:

- The user explicitly asks for a short prompt
- Style is the whole point and you want it to dominate ("a watercolor of...")
- The motion is the entire prompt ("a slow zoom in on the eye")

In these cases, lead with the dominant element and use the formula's other components only as supporting detail.
