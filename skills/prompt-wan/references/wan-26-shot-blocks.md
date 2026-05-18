# Shot-Block Prompting for Wan 2.6 and 2.7

Wan 2.6 introduced a fundamental change in how the model expects prompts: a **cinematographer-style hierarchical structure** with global look + time-bounded shot blocks. Wan 2.7 inherited and extended this.

**Critical:** Reusing Wan 2.1/2.2 prompts unaltered on Wan 2.6+ consistently produces worse output. Community testing has confirmed this repeatedly. The shot-block structure isn't optional polish — it's the format these models were trained to expect.

This reference covers the structure, multi-shot continuity rules, and version-specific features for 2.6 and 2.7.

---

## Why shot blocks work on 2.6+ and not on 2.2

The Wan 2.6 architecture introduced **temporal awareness** as a first-class capability — the model reasons about time and shot structure as primary input dimensions, not as decoration.

When you mix global look (mood, palette, lens character) with shot-level action (subject, motion, camera) in the same sentence on 2.6, the model **averages** them. The result is muddled — neither the mood nor the action lands cleanly.

When you separate them structurally, 2.6 keeps them separate in generation: it locks the global aesthetic in place, then renders the shot block within that aesthetic frame.

On Wan 2.2, this separation didn't help — the model didn't have the architecture to use it. On Wan 2.6, it transformed output quality.

---

## The basic structure

```
Global look: [tone, lighting palette, realism level, lens character, color grade]

Shot 1 [start–end seconds]: [camera movement + action over time]

Shot 2 [start–end seconds]: [continuation with restated continuity anchors]

[Negative prompt]
```

The brackets around timecodes (`[0–10s]`) are part of the convention — keep them.

---

## Global look — what goes here

The global look establishes the consistent visual language across all shots. Include:

- **Tone** — gritty, dreamy, polished, raw, intimate, monumental
- **Lighting palette** — warm tungsten / cool fluorescent / golden hour / blue hour / mixed practical
- **Color grade** — teal-and-orange / bleach-bypass / Kodak Portra cast / desaturated / saturated
- **Realism level** — photorealistic / cinematic film / stylized / illustrated / 3D-rendered
- **Lens character** — 35mm anamorphic / 50mm naturalistic / 16mm grain / clean digital / vintage glass
- **Motion blur and grain** — subtle film grain / clean digital / heavy 16mm grain / slight motion blur

**Don't put in the global look:**
- Subject descriptions
- Specific actions
- Camera movements (those go in shot blocks)
- Time-bounded events

### Global look examples

**Gritty noir:**
> Cold fluorescent lighting with intermittent flicker, desaturated palette with hints of sodium-yellow from overhead lamps, handheld realism, lens character of a 35mm anamorphic with subtle flare on bright sources, slight motion blur on quick movements, restrained contrast.

**Dreamy editorial:**
> Soft natural daylight with a slight golden tint, pastel-leaning palette with lifted blacks, polished cinematic realism, 85mm portrait lens at f/2 with smooth bokeh, gentle film grain reminiscent of Kodak Portra 400.

**Documentary realism:**
> Available daylight, naturalistic neutral grading without heavy stylization, observational tone, 35mm documentary lens character, slight handheld feel, clean digital with minimal grain.

**Cyberpunk neon:**
> Saturated neon palette dominated by hot pink and cool cyan, practical lighting from holographic billboards and storefront signage, anamorphic lens character with strong horizontal flare on bright sources, slight chromatic aberration, wet-surface reflections enhancing color spread, restrained motion blur.

---

## Shot blocks — what goes here

Each shot block is a self-contained instruction for one continuous segment of time.

Include:

- **Timecode** — `[0–6s]`, `[6–12s]`, etc. Be explicit about duration.
- **Subject** — the character or object in this shot
- **Subject's action** — what they do during this shot (verbs, specific)
- **Camera placement and movement** — where the camera starts, how it moves, where it ends
- **Spatial context** — what's in frame foreground / midground / background
- **Sound cues** — Wan 2.6/2.7 generate synced audio; describing key sounds helps

**Don't put in shot blocks:**
- Mood adjectives that contradict the global look
- New stylization choices that override the global look
- Multiple simultaneous camera moves (chain them sequentially, or use one)

### Shot block examples

**Single continuous handheld:**
> Shot 1 [0–8s]: Single continuous handheld shot following a man in his thirties wearing a dark jacket as he runs through narrow underground concrete corridors. Camera tracks behind him at shoulder height, weaving as he turns corners. Footsteps echo, breath ragged. Tunnel curves visibly ahead, distant emergency exit sign barely visible at the far end.

**Static observational:**
> Shot 1 [0–5s]: Locked-off wide shot of an empty rural kitchen at dawn, light just beginning to come through the window. A kettle starts to whistle on the stove. The room is otherwise still, dust motes drifting in the early light.

**Tracking with reveal:**
> Shot 1 [0–10s]: Slow tracking shot at hip height alongside a woman in a beige trench coat walking down a rain-soaked Tokyo alleyway. Camera starts on a medium shot of her from the side, then pulls back smoothly over the duration of the shot, eventually revealing the full alley with hot pink and cyan neon signs reflecting in puddles.

**Push-in for emotion:**
> Shot 1 [0–6s]: Slow push-in from a medium shot to a medium close-up on a woman in her sixties sitting at a kitchen table, holding a letter in her hands. Her expression slowly shifts as she finishes reading, the final beat landing on tears welling but not yet falling.

---

## Multi-shot composition

Wan 2.6 supports 2–4 shots per generation, total around 15 seconds. Wan 2.7 extends this.

**The continuity problem:** Wan does NOT strongly infer continuity across shot cuts. Without explicit anchors, the second shot's character may have different hair, wardrobe, or facial features from the first shot's character.

**The fix:** restate continuity anchors in every shot block.

### Continuity anchors to restate

- **Character identity** — "same man, same dark jacket and build for continuity"
- **Wardrobe specifics** — "same beige trench coat, same auburn hair pulled back"
- **Spatial logic** — "same underground tunnel system", "same Tokyo alleyway"
- **Lighting consistency** — "same flickering fluorescent lighting", "matching the previous shot's blue-hour cast"
- **Camera character** — "same anamorphic lens character", "matching handheld feel"

### Example: 2-shot sequence with continuity

```
Global look: Cold fluorescent lighting with intermittent flicker, desaturated palette with hints of sodium-yellow from overhead lamps, handheld realism, lens character of a 35mm anamorphic with subtle flare on bright sources.

Shot 1 [0–6s]: Single continuous handheld shot following a man in his thirties wearing a dark jacket and worn jeans as he runs through narrow underground concrete corridors. Camera tracks behind him at shoulder height, weaving as he turns corners. Footsteps echo, breath ragged.

Shot 2 [6–12s]: Same man, same dark jacket and worn jeans for continuity, in the same underground concrete corridor. Camera now ahead of him, dolly-back at his running pace. Behind him, a single distant figure in silhouette appears at the corridor's mouth, partially obscured by the flickering lights. He glances back once over his shoulder without slowing.
```

### Multi-shot rules of thumb

- **2 shots:** continuity is reasonable, restate anchors once
- **3 shots:** continuity gets harder, restate anchors in every shot
- **4 shots:** at the practical limit; consider whether sequential single-shot generations would be better
- **5+ shots:** don't try in a single generation — chain separate generations and edit together

---

## When to use single-shot vs multi-shot

**Single-shot is better when:**
- The whole sequence is a continuous camera move (chase, drone fly-through, walk-along)
- Identity drift would be visible (close-up on a character's face for the whole duration)
- The motion has its own internal logic (a single graceful gesture, a single mechanical operation)

**Multi-shot is better when:**
- The sequence needs distinct beats (establishing → action → reaction)
- Time compression is needed (years passing, multiple locations)
- The narrative requires cuts (cause-and-effect sequences, dialogue exchanges)

---

## Sound cues (Wan 2.6+)

Wan 2.6 generates synchronized audio with video. Including sound cues in shot blocks helps the model align audio to the visual.

Good sound cues to include:

- **Ambient** — "light wind through leaves", "distant traffic hum", "rain on the window"
- **Footsteps** — "footsteps echoing on concrete", "soft footsteps on grass"
- **Mechanical** — "kettle starting to whistle", "click of a device activating", "engine ticking down"
- **Vocal** — "soft breathing", "occasional muttered phrase", "laugh from off-camera"
- **Music** — "distant jazz from a doorway", "ambient hum of fluorescent tubes"

**Avoid:**
- Specific dialogue (Wan handles ambient/effect audio better than speech)
- Music with specific genres/songs Wan can't reproduce
- Very loud or sudden sound effects (often render poorly)

---

## Wan 2.7 specific additions

### Thinking Mode

Wan 2.7's Thinking Mode reasons about the prompt and plans composition before generating. With Thinking Mode enabled:

- Longer prompts work better — the planner can use the extra detail
- More complex multi-shot sequences become viable
- The model self-corrects some prompt-vs-image contradictions

Thinking Mode is on by default in most workflows. If a user mentions slow generation, that may be why — Thinking Mode adds inference time.

### Multi-reference (up to 9 images)

Wan 2.7 can accept up to 9 reference images to bind characters, products, or environments.

In the prompt, specify each reference's role:

```
Reference 1: Main character (the woman in the auburn jacket)
Reference 2: Environment (the rural kitchen at dawn)
Reference 3: Key prop (the brass kettle on the stove)
```

This is particularly powerful for branded work — maintain character consistency across a video by pinning their look to a reference image.

### Color control with HEX codes

Wan 2.7 supports HEX color specifications for brand-accurate output:

```
Color palette: primary #1A3A6B (navy), accent #F4B400 (gold), background #F5F0E6 (cream)
```

Useful for commercial work where exact brand colors matter.

### Long in-frame text

Wan 2.7 handles up to 3000 tokens of in-frame text, including:

- Multiple sentences of body copy on screens or signage
- Tables and structured layouts
- Math formulas
- 12 languages including Chinese, Japanese, Korean, Arabic

Wrap exact text in double quotes as on Qwen/Z-Image:

> Shot 1 [0–5s]: Static frame of a digital information display reading "DEPARTURES" at the top in bold sans-serif, with a scrollable list below showing destinations and times: "Tokyo 09:45 GATE B12", "Singapore 10:20 GATE A4", "Sydney 11:15 GATE C8". Soft blue backlight from the LED panel.

---

## Common 2.6/2.7 mistakes

**Mixing global and shot-level concerns:**

❌ "Shot 1 [0–6s]: Cinematic moody dark gritty handheld shot following a man through corridors with flickering fluorescent lighting."

✅ Global look: gritty, handheld, fluorescent with flicker.
    Shot 1 [0–6s]: Single continuous handheld shot following a man through corridors.

**No timecodes:**

❌ "Shot 1: Man runs through corridor. Shot 2: He stops and looks back."

✅ "Shot 1 [0–6s]: Man runs through corridor. Shot 2 [6–10s]: He stops and looks back."

**No continuity anchors across shots:**

❌ "Shot 1: A man in a jacket walks. Shot 2: He sits down."

✅ "Shot 1: A man in a dark jacket and worn jeans walks. Shot 2: Same man, same jacket and jeans, sits down on a wooden bench."

**Too many shots:**

❌ "Shot 1 [0–2s]: Wide. Shot 2 [2–4s]: Medium. Shot 3 [4–6s]: Close-up. Shot 4 [6–8s]: Reaction. Shot 5 [8–10s]: Reveal."

Cutting that fast across that many shots in 10 seconds rarely produces coherent results. Aim for 2–3 shots per ~12 seconds.

**Compound simultaneous camera moves:**

❌ "Shot 1 [0–6s]: Camera dollies in while panning right while tilting up while zooming in."

✅ Either: "Shot 1 [0–6s]: Camera dollies in slowly."
   Or sequenced: "Shot 1 [0–6s]: Camera starts on a wide, holds for 2 seconds, then dollies in to medium close-up."

---

## Quick template

For copy-paste convenience:

```
Global look: [tone, lighting palette, realism level, lens character, color grade]

Shot 1 [0–Xs]: [Subject with continuity anchors], [action], [camera movement], [spatial context], [sound cues].

Shot 2 [X–Ys]: [Same continuity anchors restated], [action continuation or new beat], [camera movement], [spatial context], [sound cues].

Negative prompt: [universal default + targeted additions for subject + identity drift between shots]
```

Fill in the bracketed sections, keep the structure intact, and you have a Wan 2.6/2.7-ready prompt.
