# Enrichment Palette — LTX

Open this file whenever you're in **Enhance Mode** (user gave a thin seed prompt, asked you to improve a draft, or supplied audio for A2V and needs a visual). It's the menu you pick from.

LTX produces output in **Lightricks' official 7-component prompt structure** (see `official-prompt-structure.md`). This palette is organized into **8 categories** that **map onto** those 7 components — the rubric uses this palette to fill out each component. The 8th category (Audio) is LTX-specific and a first-class concern from LTX-2 onward.

Most prompts use 5–7 enrichments total, drawn from 4–5 categories. Pick by scene-type (table below), not by working down each category.

## The off-center detail rule (master rule)

Every Enhance Mode output MUST contain exactly ONE small, slightly unexpected, hyper-specific detail. This is the single biggest anti-generic move for video — without it, even a richly enriched prompt regresses toward stock b-roll mean.

Because LTX is video with audio, an off-center detail can be **visual-side**, **audio-side**, or a deliberate **audio/visual mismatch**. Pick one form.

**Visual-side examples:**

- A hand trembling for a single beat, then steadying
- A loose strand of hair sticking to her mouth, ignored
- One blink held a moment longer than the other
- A stray leaf carried through the lens during a pan
- A jacket sleeve catching on a doorframe and tugging free
- A receipt slipping from the table edge, never recovered
- A coffee ring on the upper-left of the placemat from a previous cup
- A band-aid on his left knuckle, half-peeling
- Steam from a mug crossing the frame at one specific moment
- A bobby pin tucked behind one ear, holding nothing in place
- One shoelace tied tighter than the other
- A small chip in the rim of the cup, turned away from the camera but visible on a slow rotation

**Audio-side examples (LTX-2+):**

- A single off-screen door click during a quiet moment
- A refrigerator compressor kicking on mid-shot
- A phone buzzing once on the table, never picked up
- A clock chiming a single time, off-screen
- A chair leg scraping that no one in the scene acknowledges
- A distant siren rising and falling across one breath
- The soft thud of a book closing in another room
- A kettle starting to whistle just as the clip ends
- A wind gust momentarily rattling a loose window pane

**Audio/visual mismatch (advanced; counts as one):**

- A foot tapping out a rhythm the audio doesn't echo
- She speaks but the room tone holds a half-beat too long before her voice arrives
- The piano hits a chord — she doesn't react

The detail should feel **observed**, not invented. If a documentary DP would notice it across the set, it belongs. If it reads as a prompt-engineering trick, drop it.

**One per prompt. Never zero. Never more than one.** Visual-side or audio-side both count as one — don't stack a band-aid AND a refrigerator click.

## Scene type → which categories to lean on

| Scene type | Lean heavily on |
|---|---|
| Single-subject T2V | Subject + key motion, wardrobe/accessories, light, atmosphere/anchor, audio (foley + ambient) |
| Character in environment | Subject + key motion, scene environment, camera control, light, ambient audio |
| Environmental establishing | Scene environment, camera control (often jib/dolly), light, ambient audio, ONE human trace |
| Dialogue scene | Subject + key motion, action/emotion, audio (dialogue + ambient + foley), light, atmosphere/anchor |
| A2V (audio-driven) | Audio is FIXED — visual locks to it. Subject + key motion, camera (constrained by audio energy), light, atmosphere/anchor, beat-matched off-center detail |
| Silent-film mode (LTX-2.3) | Subject + key motion, scene, camera, light, atmosphere/anchor. Audio category replaced by an explicit "no diegetic audio" note. |
| Abstract / dreamlike | **Skip the rubric.** Let the seed lead. Add light + one off-center detail + one named anchor + minimal audio bed only. |

---

## 1. Subject specifics + KEY MOTION

Maps to component 1 (main action) and the subject parts of components 2–3. Use 2–4 on any human subject. AI video defaults to symmetrical, unblemished, generically posed; specificity here is the difference between "a person doing a thing" and "this specific person, in this exact moment."

**Face / skin / hair / hands** (same vocabulary as still-image work — but pick details the camera will actually see across the clip):

- Faint asymmetry (one eye slightly smaller, slight cant to the jaw); a chipped front tooth visible when smiling; a small scar through one brow; a beauty mark below the lip; smile lines around the eyes.
- Freckles across the bridge of the nose; visible pores on the cheekbones in close-up; a faint sheen of sweat at the hairline / collarbone / upper lip; a sun-tan line at the sleeve / collar.
- A flyaway strand drifting across the eye that she absent-mindedly tucks back mid-clip; hair slept-on and faintly disheveled; recently cut, slightly uneven at the edges; wet, still drying.
- Calloused palms (specify cause); paint- / ink- / clay-stained fingers; a band-aid on one knuckle; a faint tan line from a removed watch; dirt under specific nails; a scab from a recent cut.

**KEY MOTION** — what the subject is physically doing in this specific shot. Be literal. Video locks better when the action is a single concrete verb + specific manner, not a vague mood:

- Pours coffee from a chipped enamel pot into a ceramic mug
- Tightens a guitar peg by quarter-turns, listening between each
- Holds her breath for two seconds, then exhales slowly
- Taps a fingertip against the rim of the glass twice, then stops
- Watches a moth on the lampshade, eyes tracking
- Folds a paper crane, the last fold pressed flat with a thumbnail
- Pulls the espresso shot, eyes on the timer
- Lights a match against the strike-strip with the back of one thumb
- Turns the page of a paperback, finger crossing the gutter
- Wipes a smudge from the lens of his glasses with a corner of his shirt

The KEY MOTION line is often the FIRST sentence of the 7-component prompt — front-load it.

## 2. Body modifications + accessories + wardrobe

Maps to the subject parts of components 2–3 (specific appearances). Collapsed into one category because video weighs these less than image — pick the highest-leverage items, don't pile up.

**Tattoos** (place + content; small unless asked otherwise):

- A small hand-poked bee on the inner left wrist
- A line of small cursive along the right forearm
- Three small stars along the inside of the right index finger
- A linework snake curling around the right bicep
- A single small heart inside the lower lip (only visible when she smiles)
- A faded ankle band of dots
- A stick-and-poke smiley on the thumb-pad

**Piercings:**

- Two stacked helix studs on the right ear
- A small septum hoop, silver
- A nostril stud, gold
- Small-gauge earlobes (4–6mm)
- A tongue piercing visible only when she speaks

**Scars / marks:**

- A thin pale scar through the left eyebrow
- A small crescent scar on the chin
- A faded burn on the back of one hand

**Accessories** (one or two, not a list):

- A vintage Timex with a sweat-darkened leather strap
- A thin gold chain with a single small charm
- Tortoiseshell wireframes pushed up on the forehead
- A faded G-Shock scuffed at the face
- A friendship bracelet in faded thread
- An elastic hair tie around the wrist
- A bandana knotted at the throat
- Mismatched earrings (one stud, one empty hole)

**Wardrobe** — fabric + fit + condition, plus a video-specific cue: **how it moves**.

- Raw selvedge denim; washed linen catching the breeze; brushed wool; ribbed knit; technical nylon; waxed canvas; brushed cotton flannel.
- Fit: slightly oversized, tailored, cropped, draped, boxy.
- Condition: faded, wrinkled, paint-stained, sun-bleached, missing a top button, hem fraying.
- **Motion cues (LTX-specific):** linen catching the breeze; the sweater sleeve falling past the wrist as she reaches; a coat hem brushing the top of his boots with each step; a scarf end lifting in a passing draft; one curl springing back into place after a head-turn.

Era anchors when useful: 1970s, mid-2000s, 1990s vintage, fin-de-siècle, late-70s punk, mid-century menswear.

## 3. Subject action and emotion

Maps to component 2 (specific movements and gestures) and the emotional register that sits over component 6. **What the subject is doing**, separate from category 1's physical specifics — and the emotional register the action carries.

**Concrete actions** (LTX takes literal verbs better than mood adjectives):

- Peeling an orange in one continuous spiral
- Tying a shoelace, knot drawn tight with a small tug
- Reading a folded letter, lips moving slightly with the words
- Sharpening a pencil with a small pocket knife, shavings falling onto the desk
- Pouring tea from a kettle held in both hands
- Adjusting a record on a turntable, lowering the needle
- Counting bills on the counter, thumb moving across the edge
- Buttoning a cuff against the wrist, then the other
- Tracing a finger along the edge of a photograph
- Cracking knuckles one at a time

**Emotional register** (pair with action; don't state mood as a standalone adjective):

- Unhurried, slightly melancholy
- Focused, the rest of the world muted out
- Quietly amused, on the verge of smiling but not quite
- Tired in a way that's settled in for the long term
- Bracing for something the camera doesn't show
- Resigned to a small repetitive task
- Half-listening for a sound from another room
- Defensive, holding herself slightly inward

**Pair example:** "Peeling an orange in one continuous spiral, focused in a way that suggests she's avoiding looking at the door."

## 4. Scene environment

Maps to component 4 (background and environment details). 1–2 environmental details that imply life-before-the-camera — not staged for the shot.

**Interior:** wooden shelves of beans; a half-finished crossword on the table with ballpoint laid across it; a kettle just off the burner, still ticking; laundry on a line across one corner; a child's chalk drawing low on the wall; a coat hung over a chair-back with one sleeve dragging; a single picture frame slightly askew; an open notebook with handwriting visible; a houseplant slightly wilted on one side; a record sleeve propped against the wall; a stack of unopened mail on the counter.

**Exterior / street:** steam rising from a manhole; a single sock on the pavement; a torn flyer half peeled from a lamppost; a puddle reflecting one neon sign; a pigeon mid-strut in the foreground; construction tape billowing in the wind; gas lamps flickering along a curb (intentional — see qualified negatives in category 6); a fading chalk hopscotch grid on the sidewalk.

**Era / period anchors:** post-war utility, fin-de-siècle, mid-century kitchen, 1970s diner, late-90s bedroom, contemporary minimalist — pick when the scene's period is load-bearing.

**Weather / atmosphere as environmental:** faint mist rising from warm pavement after rain; snow sticking to one side of a tree; heat haze rising off asphalt; falling cherry blossoms; fog rolling in low at ankle height; wind whipping one direction (debris, hair, leaves all consistent — LTX rewards directional consistency).

**Implied life-before-camera traces** (high leverage for video):

- A teapot still warm to the touch, steam thinning
- A half-finished sketch on the desk with the pencil laid across it
- A pair of boots by the door with dried mud on the heels
- A radio playing softly from another room (visible doorway, audible signal — feeds both this category and the audio one)

## 5. Camera control

Maps to component 5 (camera angles and movements). Either name a discrete LTX camera-control LoRA (see `camera-control-loras.md`) OR describe the camera move in free-form cinematography vocabulary. Don't do both with conflicting moves.

**Discrete camera-control LoRA names (cite by name when used):**

- `LTX-2-19b-LoRA-Camera-Control-Dolly-In` — slow forward push (intimate reveal, building intensity)
- `LTX-2-19b-LoRA-Camera-Control-Dolly-Out` — slow backward pull (reveal wider context, ending)
- `LTX-2-19b-LoRA-Camera-Control-Dolly-Left` — sideways truck left (parallax reveal)
- `LTX-2-19b-LoRA-Camera-Control-Dolly-Right` — sideways truck right (parallax reveal, opposite)
- `LTX-2-19b-LoRA-Camera-Control-Jib-Up` — crane up (reveal from low to high, scale)
- `LTX-2-19b-LoRA-Camera-Control-Jib-Down` — crane down (settle into scene)
- `LTX-2-19b-LoRA-Camera-Control-Static` — locked-off (observational, dialogue)

When using a LoRA, still mention the camera move in the prompt — the LoRA reinforces it; the prompt confirms it.

**Free-form camera moves** (when no LoRA fits, or multiple beats are needed):

- A slow tracking dolly alongside the subject at hip height
- A locked-off medium shot at chest height, framing slightly off-center to the left
- A handheld OTS that drifts a fraction of an inch with the subject's breath
- A slow circular orbit around a stationary central subject
- A whip-pan to follow an off-screen sound (audio-anchored move)
- A pull-focus from foreground prop to subject's face on the third beat
- A 90-degree dutch tilt that resolves to level mid-clip

**Angle + height vocabulary:** low angle for power; high angle for vulnerability; eye-level for neutrality; chest-height medium for documentary; hip-height tracking for kinetic following; ground-level for environmental scale.

**Compound moves to AVOID:** "dolly in while panning right while tilting up" — pick one principal move and sequence it. LTX handles single principal moves cleanly; compound moves muddy.

## 6. Light interaction

Maps to component 6 (lighting and colors). Same vocabulary as still-image work, with one LTX-specific addition: **qualified-negative awareness**.

Specify direction + quality + source. 2–3 light details that interact with the scene, not stacked adjectives:

- A single practical source (table lamp, screen glow, candle, gas lamp, reflected neon)
- Two-source: window light + a single warm interior lamp
- Rim light ONLY from behind — silhouette with edge glow, face in shadow
- Light filtered through a curtain / window screen / dirty window
- Light through fabric (a sheer scarf, a thin blouse)
- Caustics — light reflected through liquid
- Colored bounce: red from a brake light onto a cheek, blue from a phone screen on the face, green from a fluorescent tube above
- TV as the only light source in the room
- Time-of-day named precisely: 11pm fluorescent diner, 4am parking-lot sodium-vapor, 6am pre-dawn blue, late golden hour ~7pm summer
- Slanting light through a high window catching airborne dust / sawdust / steam
- Warm tungsten from a single hanging bulb, cool ambient daylight from a window opposite — face half in each

### Qualified-negative awareness (LTX-specific)

When a light source **naturally flickers** in the scene — candle, gas lamp, broken fluorescent, faulty neon, fireplace, lightning, firefly — DO NOT use the bare word `flickering` in the negative prompt. It will suppress the intentional flicker.

Use the qualified form instead:

- `flickering frame artifacts` (targets the digital artifact)
- `frame interpolation artifacts`
- `motion smearing`
- `temporal artifacts`

State the flicker as intentional in the positive: "gas lamps flickering along the curb, warm amber pools rippling on the wet stone" — this anchors the model to keep it.

## 7. Atmosphere and aesthetic

Maps to component 6 (colors/mood end) and the atmosphere/style overlay implicit in the official structure. Color palette + emotional register + ONE named-reference anchor.

**Color palette:** cool dawn blue with one warm interior accent; warm tungsten across face, cool daylight across background; saturated longing (Wong Kar-wai); cool desaturated noir; warm autumn palette of ochre and rust; high-contrast B&W; muted earth tones; saturated neon; bleached sun.

**Pacing register** (LTX listens to pacing cues): contemplative and slow-paced; kinetic and quick; observational and patient; tense and held; warm and unhurried.

### ONE named-reference anchor (the single biggest non-generic move)

Pick ONE per prompt. Name an actual cinematographer / director-DP pairing / slow-cinema director. This anchors LTX to a real visual register instead of "the average of all internet b-roll."

**Cinematographers** (safe list — use these):

| Reference | Register |
|---|---|
| Roger Deakins | controlled cinematic precision, long take, naturalistic |
| Christopher Doyle | saturated handheld longing, neon and rain |
| Emmanuel Lubezki | natural-light wide, magic-hour |
| Hoyte van Hoytema | IMAX wide, controlled epic |
| Bradford Young | low-key warm shadow, hushed |
| Newton Thomas Sigel | hard light, documentary edge |
| Greig Fraser | epic-scale wide, cool tonal control |
| Robbie Ryan | handheld humanist, naturalistic |
| Linus Sandgren | warm chemical color, motivated practical light |

**Director-DP pairings** (one register — count as ONE anchor, not two):

| Pairing | Register |
|---|---|
| Wong Kar-wai + Christopher Doyle | saturated longing, slow shutter, neon |
| Terrence Malick + Lubezki | natural-light magic hour, wide, drifting |
| Christopher Nolan + Hoytema | IMAX wide, controlled |
| Yorgos Lanthimos | wide cold awkward, symmetrical |
| Nicolas Winding Refn | saturated neon, locked-off |
| David Lynch | dream temporality, designed sound |
| Andrei Tarkovsky | long-take patience, weighted silence |

**Slow-cinema specific** (LTX excels here — its slower default pacing fits these registers):

| Reference | Register |
|---|---|
| Kelly Reichardt | quiet American, observational |
| Hou Hsiao-hsien | long-take static, layered planes |
| Chantal Akerman | locked-off, ritual repetition |
| Béla Tarr | extreme long-take, monochrome |
| Apichatpong Weerasethakul | jungle/ambient, languid |

**For audio-rich registers** (especially A2V):

| Reference | Register |
|---|---|
| David Lynch | designed sound, dread-ambient |
| Apichatpong Weerasethakul | jungle/ambient, natural soundscape |
| Andrei Tarkovsky | weighted silence, sparse foley |

**One anchor per prompt. Don't stack.** "Roger Deakins meets Wong Kar-wai" produces muddy hybrid output.

## 8. Audio layer (LTX-2 and later — first-class)

Maps to **the audio half of LTX-2+'s native A+V generation**. There is no equivalent component in image models — for LTX-2+ this category is mandatory. (For pre-LTX-2 variants or LTX-2.3 silent-film mode, skip this category and add a "no diegetic audio" note instead.)

Three required sub-layers + two optional:

### Ambient layer (always — pick ONE primary bed)

Room tone / environmental wash. Don't stack three ambient beds; pick the dominant one.

- Refrigerator hum + distant traffic
- Wind through eaves, occasional gust rattling a windowpane
- Ocean swell with intermittent gull calls
- Forest breath: layered birdsong, distant wood creak
- Rain on glass / rain on stone (pick which surface)
- The deep room tone of a large empty hall
- The buzz of a single fluorescent tube
- Cafe murmur — soft layered conversation, ceramic clinks
- The low rumble of an idling diesel engine, distant
- Cricket chorus + a far-off frog

### Foley layer (always — match to the action in category 3)

The specific sounds the subject's KEY MOTION makes. Foley follows action. If the action is "peeling an orange," the foley is "the wet tear of pith from skin, citrus oil hissing as the rind bends." Be specific:

- Shoelace tightening with a small leather creak
- Coffee pouring into a ceramic mug, the changing pitch as the cup fills
- Paper unfolding, a single crisp crackle at each fold
- A knife on a wooden cutting board, slow and even
- A hammer striking a nail — strong solid thud, metallic ring as it seats
- The wet tear of pith from orange skin
- Match strike against a strip — the small flare
- Ice cubes settling in a glass
- A page turning, the soft brush of paper edges
- The click of a record's run-out groove

### Music (optional — diegetic or non-diegetic; specify which)

- **Diegetic** (source visible or implied in the scene): "a small antique gramophone plays soft country blues at low volume, the music slightly crackling"; "a distant radio in another room plays a half-heard pop song from the late 70s"; "a piano in the next room, someone practicing scales, occasional fumble"
- **Non-diegetic** (score over the scene): "a slow piano melody enters at the third beat and holds under the dialogue"; "low strings, sustained, no melodic motion"

Mood + genre + presence: a slow piano melody / a humming distant trumpet practicing scales / a single sustained organ tone / soft country blues on a gramophone / no music.

### Dialogue (optional — register + register + one specific line max)

- Language (English / Spanish / Japanese / etc.)
- Register: whispered / spoken / called out / sung / muttered to himself
- ONE specific line max — long quoted dialogue derails generation. "She murmurs 'I told you' under her breath" beats a paragraph of script.

### A2V mode rules (when audio drives the video — see also "Scene type" table)

When the user supplies an audio file, the audio is FIXED. The visual MUST lock to it:

- **Duration**: visual = audio length exactly (use the closest valid discrete duration: 2/3/4/5/6/7/8/9/10s)
- **Beats and impulses**: any prominent audio event (a piano note hit, a beat drop, a chord change, a sudden silence) MUST be matched by a corresponding visual event. The off-center detail in A2V is OFTEN a visual beat-match: "she opens her eyes on the third bell strike," "the candle gutters as the bass drops," "the cup lowers exactly as the held note resolves."
- **Camera pacing constrained by audio energy**: slow audio → slow camera or locked-off; sudden audio → sudden cut, zoom, or whip-pan; sustained drone → near-imperceptible drift; rising build → tracking move that resolves at the swell.
- **Palette and mood mirror audio character**: see the audio-character table in `SKILL.md`.
- **OMIT the audio cue block in the output**: the supplied audio is the conditioning. Output Visual prompt + Negative only.

### Qualified negatives for audio

If the scene contains intentional ambient sound (candle flicker = also a soft fizz; gas lamp = a faint hiss; fluorescent = the audible buzz; rain = the constant patter), DO NOT use bare words like `flickering`, `hissing`, `buzzing`, `noisy` in the negative prompt. They'll suppress the intentional sound.

Use qualified forms:

- `silent video, missing audio, audio-visual desync`
- `flickering frame artifacts` (not `flickering`)
- `audio dropouts, audio glitches` (not `noisy`)
- `mismatched mood, audio-visual register mismatch`

---

## Quick reference: 8 categories → 7 Lightricks components

| Palette category | Lightricks component(s) |
|---|---|
| 1. Subject specifics + KEY MOTION | 1 (main action) + 3 (character appearance) |
| 2. Body mods + accessories + wardrobe | 3 (character/object appearance) |
| 3. Subject action and emotion | 2 (movements and gestures) |
| 4. Scene environment | 4 (background and environment) |
| 5. Camera control | 5 (camera angles and movements) |
| 6. Light interaction | 6 (lighting and colors, light half) |
| 7. Atmosphere and aesthetic + ONE named anchor | 6 (colors/mood end) + implicit style overlay |
| 8. Audio layer (LTX-2+) | woven through the paragraph + 7 (changes/sudden events when audio cues a visual beat) |

The 7-component structure remains a **single flowing paragraph**. The palette tells you what to put IN each component; the structure dictates the order.
