# Official LTX Prompt Structure

This reference documents Lightricks' canonical prompt structure for LTX-2 and LTX-2.3, taken directly from their official GitHub README. Following this structure produces meaningfully better output than ad-hoc prose.

## The 7-component structure

Quoted directly from Lightricks' README:

> When writing prompts, focus on detailed, chronological descriptions of actions and scenes. Include specific movements, appearances, camera angles, and environmental details — all in a single flowing paragraph. Start directly with the action, and keep descriptions literal and precise. Think like a cinematographer describing a shot list. Keep within 200 words. For best results, build your prompts using this structure:
>
> 1. Start with main action in a single sentence
> 2. Add specific details about movements and gestures
> 3. Describe character/object appearances precisely
> 4. Include background and environment details
> 5. Specify camera angles and movements
> 6. Describe lighting and colors
> 7. Note any changes or sudden events

The components flow as **one paragraph**, in order. Don't break them into bullets or numbered sections. The model was trained to handle continuous narrative prose, not structured lists.

## Why this structure works

Each component does specific work in the generation:

- **Main action sentence** sets the dominant motion the rest of the clip will revolve around. Front-loading this locks the primary subject of the generation.
- **Movement and gesture details** add motion specificity that prevents the model from inventing generic motion.
- **Character/object descriptions** lock identity for the duration of the clip — without them, identity drifts across frames.
- **Background and environment** establish spatial context, which keeps camera movements coherent.
- **Camera angles and movements** are LTX's primary control surface. Without explicit camera direction, the model picks defaults.
- **Lighting and colors** establish the visual register and prevent color drift across frames.
- **Changes and sudden events** give the model temporal milestones — beats to hit during the clip rather than uniform motion throughout.

## Component-by-component breakdown

### 1. Main action sentence

The opening must contain the dominant action that defines the clip. Pick the strongest verb that summarizes what happens.

**Good first sentences:**

- "A young man in a blue cotton t-shirt sits at a wooden desk and begins typing on a laptop keyboard."
- "A woman walks slowly along a misty forest path at dawn, her breath visible in the cold air."
- "A barista pulls a shot of espresso into a small white ceramic cup at a polished commercial machine."

**Weak first sentences (avoid):**

- "A scene set in a forest." — no action, just establishing
- "Beautiful cinematic shot of a forest with a woman." — adjective-laden, no action
- "A woman exists in a forest environment." — passive, no specificity

### 2. Movement and gesture details

After the opening action, layer in specific physical details about how the action unfolds.

> "...his fingers moving in natural rhythmic strokes before he leans back in his chair to read what he's written, his right hand reaching up briefly to push his glasses back into place."

Specifics that work well: hand movements, weight shifts, head turns, breathing visibility, micro-expressions, gait. Avoid: "moves dramatically", "gestures intensely" (vague verbs without information).

### 3. Character / object appearance

Specific wardrobe, hair, build, distinguishing features. Locked into the early frames and held throughout.

> "He has short dark brown hair, a faint stubble, and glasses pushed slightly down his nose."

Cover at minimum: hair (color + style), main wardrobe item (color + cut), one identifying feature (glasses, scar, jewelry, etc.). For multiple characters, give each their own descriptive beat.

### 4. Background and environment

What's in the space around the subject. Layer foreground / midground / background.

> "The desk is cluttered with a half-empty coffee mug, a small notebook open to a page of handwritten notes, and a tangled phone charger; behind him, a window shows soft autumn afternoon light filtering through partially-drawn curtains."

Be selective — name 2–4 specific environmental elements rather than trying to describe everything. The model will fill in plausible surroundings if you anchor the key items.

### 5. Camera angles and movements

LTX's primary control surface. Always specify both **where the camera is** (angle, framing) and **what it does** (static, dolly, pan, tilt, etc.). Use real cinematography vocabulary.

> "The camera holds at a medium shot from chest height, framing him slightly off-center to the left."

If the camera moves during the clip:

> "The camera begins at a wide establishing angle, then slowly dollies in over the duration to settle on a medium close-up by the end of the clip."

See the cinematography vocabulary appendix below for the full vocabulary.

### 6. Lighting and colors

Direction + quality + source — same rule as image prompting but with more emphasis on the source because video lighting needs to stay consistent across frames.

> "Warm natural window light falls across his face from the right side while cool ambient light from the laptop screen catches his glasses."

Good lighting descriptions name 2–3 light sources and their interactions. Bad ones use a single vague adjective like "dramatic lighting."

### 7. Changes or sudden events

LTX-2 reasons about temporal sequence. If something specific happens at a beat in the clip (not uniform motion throughout), call it out.

> "Halfway through the clip, he glances toward the window briefly before returning his focus to the screen."

This is what separates a 5-second clip with one beat from a 5-second clip with two beats. Without an explicit change, the model defaults to uniform motion across the duration.

## Full example following the structure

Reading the components in order in this prompt:

> A young man in a blue cotton t-shirt sits at a wooden desk and begins typing on a laptop keyboard, his fingers moving in natural rhythmic strokes before he leans back in his chair to read what he's written. He has short dark brown hair, a faint stubble, and glasses pushed slightly down his nose; his right hand reaches up briefly to push them back into place. The desk is cluttered with a half-empty coffee mug, a small notebook open to a page of handwritten notes, and a tangled phone charger; behind him, a window shows soft autumn afternoon light filtering through partially-drawn curtains. The camera holds at a medium shot from chest height, framing him slightly off-center to the left. Warm natural window light falls across his face from the right side while cool ambient light from the laptop screen catches his glasses. Halfway through the clip, he glances toward the window briefly before returning his focus to the screen.

Mapping back to the structure:

- **Component 1 (main action):** "A young man in a blue cotton t-shirt sits at a wooden desk and begins typing on a laptop keyboard"
- **Component 2 (gestures):** "his fingers moving in natural rhythmic strokes before he leans back...", "his right hand reaches up briefly to push them back"
- **Component 3 (appearance):** "short dark brown hair, a faint stubble, and glasses pushed slightly down his nose"
- **Component 4 (environment):** "The desk is cluttered with a half-empty coffee mug, a small notebook... behind him, a window..."
- **Component 5 (camera):** "The camera holds at a medium shot from chest height, framing him slightly off-center to the left"
- **Component 6 (lighting):** "Warm natural window light falls across his face from the right side while cool ambient light from the laptop screen catches his glasses"
- **Component 7 (change):** "Halfway through the clip, he glances toward the window briefly before returning his focus to the screen"

## More examples for different scene types

### Example: portrait i2v animation (LTX-2)

> A woman in her thirties slowly turns her head from the window toward the camera, a gentle smile forming as her gaze settles on the lens, her right hand briefly tucking a loose strand of hair behind her ear. She has shoulder-length auburn hair and freckled cheeks; she wears a pale sage-green linen shirt with the top button open. The room behind her holds soft-focus bookshelves and a single hanging Edison bulb, the light cool morning daylight filtering through gauzy curtains. Camera remains static at her chest height in a medium close-up. Window light from her right falls across her face as the warm key while cool ambient light from the room fills the shadow side. The motion unfolds slowly across the full clip duration, controlled and unhurried.

### Example: action / kinetic

> A heavyset middle-aged man in a leather apron and short-sleeved white shirt swings a sledgehammer down onto a glowing iron bar resting on a blacksmith's anvil, sparks flying outward and clattering against the stone floor. He grips the hammer with both hands and shifts his weight forward through each strike, sweat glistening on his thick forearms and shaved head. Behind him, a brick forge glows orange-red with the iron's heat radiating in waves; the workshop is otherwise dark, hung with hand tools and racks of finished blades. Camera holds at a low-angle medium shot from his left side, emphasizing the height of each hammer arc. The forge provides intense warm key light from his right, while the rest of the workshop falls into deep ambient shadow. The third strike sends a larger spray of sparks across the floor as the iron flattens visibly under the impact.

### Example: landscape / scenic

> The camera rises slowly upward over the rim of a high alpine valley at dawn, revealing layered mountain ridges receding into pale blue-gold mist, with a single river winding through the valley floor below. The grass in the foreground sways gently in a cold morning breeze; tiny details in the distance — a herd of sheep, a single distant cabin with a thin line of woodsmoke — come into view as the angle widens. The landscape stretches across multiple ridge layers, each fading slightly into atmospheric haze, snow-capped peaks barely visible at the horizon. The camera move is a smooth slow jib up, lifting from ground level to a wide aerial perspective over the duration of the clip. Cool dawn ambient light with warm sun-edges catching the highest peaks, soft volumetric mist between the ridges, the lower valley still in blue pre-dawn shadow.

Note: no characters here — components 2 and 3 collapse since there's no subject to gesture or be described. The structure adapts to scene type.

### Example: dialogue / character moment (audio important)

> A man in his sixties sits at a small kitchen table in a modest home, a half-finished cup of tea in his hand, looking down at an open photo album on the table in front of him. He turns a page slowly with his free hand, pausing at one photograph and exhaling quietly; the sound of the paper, his soft breath, and the distant tick of a wall clock are the only audio in the scene. He has thinning grey hair, deep crow's-feet, and wears a faded blue cardigan over a white shirt. The kitchen around him is quiet and modest — a kettle on the stove, a single ceramic mug rack on the wall, an overcast afternoon visible through a small window. Camera holds at a medium close-up from across the table, his eyes the primary point of focus. Soft overcast daylight from the window casts even gentle light across the scene, with no harsh shadows. Halfway through the clip, his expression softens almost imperceptibly as he looks at one specific photograph longer than the others.

## Common structural mistakes

### Bullet-style prompts

❌ "Subject: a barista. Action: making espresso. Camera: medium shot. Lighting: warm."

LTX was not trained on bullet-style structured prompts. It expects continuous prose.

✅ "A barista pulls a shot of espresso into a small white cup at a polished commercial machine, her hands moving with practiced economy. The camera holds at a medium shot from her left side; warm tungsten light from above falls across her face and the steam rising from the cup."

### Out-of-order components

❌ "Beautiful warm lighting fills a scene where a woman walks through a forest in a green jacket, camera tracking."

This puts lighting before action, action before appearance, and camera at the end. LTX handles components in the documented order more reliably.

✅ "A woman walks slowly along a misty forest path. She wears a moss-green canvas jacket. The forest surrounds her with tall trunks and fern undergrowth. The camera tracks alongside her at hip height. Warm dawn light slants in from above through gaps in the canopy."

### Missing the temporal beat

❌ A 10-second prompt with uniform action throughout — same camera move, same subject motion, no specific events.

Result: the model produces 10 seconds of uniform motion that feels static even though things are moving.

✅ Include at least one "halfway through" or "at the X-second mark" or "at the end of the clip" beat.

### Compounding too much in the first sentence

❌ "A young Korean woman in her thirties with long black hair in a sage-green linen shirt walks through a misty Douglas fir forest at dawn while turning to look over her shoulder at the camera, holding a brass lantern that casts warm pools of light onto the path."

This is the entire structure compressed into one run-on sentence. LTX handles a clean main-action opener better than this kind of front-loading.

✅ Open with the action ("A woman walks slowly along a misty forest path at dawn, occasionally turning to look over her shoulder."). Then layer in the appearance, environment, and lighting details in subsequent sentences.

### Quality crutches that LTX ignores

❌ Words that do nothing on LTX: `4k`, `8k`, `hdr`, `masterpiece`, `professional`, `ultra-detailed`, `award-winning`, `cinematic` as a standalone adjective.

Especially for LTX-2.3 which generates natively at 1920×1088 with HDR variants — adding "4K" tells the model nothing it doesn't already do.

## Cinematography vocabulary appendix

Camera vocabulary that LTX recognizes well:

**Shot types:** extreme close-up (ECU), close-up (CU), medium close-up (MCU), medium shot (MS), medium long shot (MLS), full shot, long shot, wide shot, extreme wide shot (EWS), two-shot, over-the-shoulder (OTS), POV, insert shot.

**Camera angles:** eye level, low angle, high angle, bird's-eye view, worm's-eye view, Dutch angle, three-quarter view, profile, direct front, direct back.

**Camera movements (physical translation):** dolly in, dolly out / pull-back, truck left, truck right, pedestal up, pedestal down, crane / boom up, crane / boom down, tracking shot, push-in, steadicam follow.

**Camera movements (rotation in place):** pan left, pan right, tilt up, tilt down, whip pan, roll.

**Compound / specialty:** orbit / arc, vertigo (dolly zoom), handheld, crash zoom, drone shot, reveal, lock-off / static.

**Aperture / DOF:** shallow depth of field, deep focus, f/1.4 (extremely shallow), f/2 (portrait depth), f/8 (sharp), f/11 (deep).

**Focal length:** 24mm wide, 35mm documentary, 50mm naturalistic, 85mm portrait, 135mm telephoto, 200mm long lens.

**Pacing:** slow, controlled, smooth, fluid, kinetic, static, subtle, dynamic, accelerating, decelerating.

For the camera-control LoRAs, see `references/camera-control-loras.md` — these can replace some of the verbal camera direction with more reliable LoRA-driven motion.
