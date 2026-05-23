# Enrichment Palette — Wan (Video)

Open this file whenever you're in **Enhance Mode** (user gave a thin seed prompt or asked you to improve a draft). It's the menu you pick from. Pick by scene-type, not by working down the list — most prompts use 5–7 enrichments total, drawn from 4–5 of the categories below.

Video differs from stills in three load-bearing ways:

1. **Motion is part of subject specificity.** A still can be specific by what the subject *looks like*; video has to be specific by what the subject *does* in the shot.
2. **The air must move.** Dead-air shots read as CGI. One specific environmental motion (wind in hair, dust in backlight, water rippling) is a non-negotiable layer.
3. **The camera is a character.** Leaving the camera unspecified means Wan defaults to a slow drift that produces averaged, generic motion. Always name the camera movement, even if the answer is "locked-off."

## The off-center detail rule (master rule)

Every Enhance Mode output MUST contain exactly ONE small, slightly unexpected, hyper-specific detail. This is the single biggest anti-generic move — without it, even a richly enriched prompt regresses toward stock-video mean.

For video, the detail is a **micro-event** as much as a static object: it happens or is observed at one specific moment in the shot, not held across the whole duration.

Examples:

- A hand trembling for a single beat before steadying
- A loose strand of hair sticking to the corner of her mouth, ignored
- A receipt slipping from the table edge mid-shot, never recovered
- One blink slightly delayed (held a moment longer than the other)
- A stray leaf drifting through the lens during a pan
- A jacket sleeve that catches on a doorframe and tugs as she walks through
- An off-camera car door slamming, the subject doesn't look up
- Steam from a mug crossing the frame at one specific moment, not continuously
- A foot tapping out a rhythm the audio doesn't echo (visual-only)
- A phone vibrating once on the table, the subject doesn't reach for it
- A single moth tracking through a streetlight beam in the background
- A fingertip drumming twice on the table, then stopping
- A glance off-camera and back, no reaction
- An ice cube shifting in a glass with an audible click implied
- A bead of condensation rolling down a window at one specific beat

The detail should feel **observed**, not invented. If you can imagine a documentary cinematographer noticing it across the room, it belongs. If it reads as a prompt-engineering trick, drop it.

**One per prompt. Never zero. Never more than one.** Two off-center details cancel each other out (the eye reads them as styling).

**For multi-shot prompts (Wan 2.6+):** place the off-center detail in exactly ONE of the shot blocks. Not in every shot. Not in the global look. One shot, one detail.

## Scene type → which categories to lean on

| Scene type | Lean heavily on |
|---|---|
| Single-subject scene | Subject specifics + key motion, body mods, accessories, wardrobe-in-motion, camera movement, light, named anchor |
| Character in environment | Subject + motion, wardrobe-in-motion, environmental motion, light, camera, named anchor |
| Environmental establishing shot | Environmental motion, light continuity, camera movement, era/genre anchor, one human trace |
| Action scene | Subject + motion (kinetic), wardrobe condition, environmental motion (debris, wind), camera (handheld or tracking), off-center mishap detail |
| Multi-shot sequence (Wan 2.6+) | All categories distributed across shots; continuity anchors mandatory; ONE off-center detail in ONE shot only |
| Multi-reference product reveal (Wan 2.7) | Reference assignments first, then brand palette in global look, then shot-block enrichment; named anchor + off-center detail still apply |
| Dialogue scene | Subject + key motion (a held breath, a glance), camera (locked-off or slow push), light, off-center detail (visual-only — Wan doesn't render dialogue audio) |
| Abstract / dreamlike | **Escape hatch.** Skip the rubric. Let the seed lead. Add light + ONE off-center detail + ONE named anchor only. |

---

## 1. Subject specifics + KEY MOTION

Use 1–3 specificity facts AND name one key motion the subject performs in the shot. AI defaults to symmetrical, unblemished, and generically-active; specificity here is the difference between "model" and "person."

**Face:** faint asymmetry (one eye slightly smaller, slight cant to the jaw); a chipped front tooth visible when smiling; a small gap between the front teeth; a faint scar through one brow / on the chin / across the philtrum; a beauty mark below the lip; smile lines around the eyes; a slight overbite; a sunburn line where sunglasses sat; one earlobe slightly larger than the other.

**Skin:** freckles across the bridge of the nose / scattered down the shoulders / sun-spots on the cheekbones; visible pores on the cheekbones in close-up; a faint sheen of sweat at the hairline / collarbone / upper lip; a sun-tan line at the sleeve / collar / sock; a healing scrape on the knee / elbow / shin; an ink stain along the side of the writing-hand pinky; dirt under one or two fingernails; a small pimple on the jaw / forehead (not a focal point).

**Hair:** a flyaway strand drifting across the eye; tucked behind one ear, the other left loose; a single bobby pin holding nothing in place; slept-on, faintly disheveled; recently cut, slightly uneven at the edges; wet, still drying; a single grey hair visible; roots starting to show under dye.

**Hands:** calloused palms (specify cause: guitar strings, rope, weights); a ring-finger callus from a removed ring; paint- / ink- / clay-stained; a band-aid on one knuckle; a faint tan line from a removed watch / bracelet; chipped nail polish (specify color); a scab on one finger from a recent cut.

**Key motion (the video-only specificity lever — pick ONE):**

- A held breath before the action begins
- A fingertip drumming twice on the table, then stopping
- A glance off-camera and back, no reaction
- Shifting weight from one foot to the other once mid-shot
- A slow exhale that fogs in cold air
- A swallow visible at the throat
- Tucking a strand of hair behind the ear without looking down
- Wiping one palm against the thigh, once
- The hint of a smile that doesn't fully form
- A nod so small it might be a head-bob in time with music only the subject can hear
- Cracking the knuckles of one hand, one finger at a time
- A long blink (held a beat longer than reflex)
- Reaching for an object, then pulling back without touching it

Motion is a primary specificity lever in video — a generic "stands" or "looks" is the most common cause of stock-feeling Wan output. Name what the body actually does.

## 2. Body modifications

High-leverage non-generic move. AI underweights these because stock imagery suppresses them. **AVOID "covered in tattoos" / "lots of piercings" — be specific about content and placement.**

**Tattoos** (place + content; keep them small unless the prompt asks otherwise):
- A small hand-poked bee on the inner left wrist
- A line of small cursive along the right ribcage
- Three small stars along the inside of the right index finger
- A faded blackwork floral half-sleeve from elbow to shoulder on one arm
- A simple line drawing of a hand on the back of one calf
- A single small heart inside the lower lip (only visible when smiling)
- Behind one ear: a tiny crescent moon
- A faded ankle band of dots
- A stick-and-poke smiley on the thumb-pad
- A linework snake curling around the right bicep

**Piercings:**
- Two stacked helix studs on the right ear (and one lobe, gold)
- A small septum hoop, silver, tucked up most of the time
- A nostril stud, faint, gold
- A single eyebrow stud
- Small-gauge earlobes (4–6mm — not stretched)
- A tongue piercing visible only when she speaks
- An industrial bar across the top of the right ear
- A small lip ring on the lower right

**Scars / marks:**
- A thin pale scar through the left eyebrow
- A small crescent scar on the chin
- A faint surgical scar on one knee
- A long thin scar along the inside of one forearm
- A faded burn on the back of one hand (small, palm-sized)

Body mods don't change between stills and video — but in motion they read more strongly. A tattoo on a wrist that turns toward the camera in shot 2 lands harder than the same tattoo in a still.

## 3. Accessories

**Earrings:** small gold hoops; a single pearl drop on one ear, the other empty; mismatched studs; no earrings but a faint piercing scar; small silver crosses; long fringed silver dangles.

**Rings:** a thin gold signet on the right pinky; a worn wedding band; a turquoise stone in silver on the right index; a delicate snake ring around the middle finger; multiple thin stacking bands; a faint indentation from a removed ring.

**Wrists:** a vintage Timex with a sweat-darkened leather strap; a faded G-Shock scuffed at the face; a thin gold chain bracelet; a friendship bracelet in faded thread; a medical-ID bracelet; an elastic hair tie around the wrist; a wrist tan-line from a removed watch.

**Neckwear:** a thin gold chain with a single small charm (cross / locket / key / pearl); a leather cord with a wooden bead; a 90s satin choker; a medal tucked inside the shirt, chain visible; a bandana knotted at the throat.

**Glasses:** tortoiseshell wireframes; gold-frame aviators (70s); mid-century cat-eye (50s); small round Lennon frames; wraparound sport sunglasses pushed up on the forehead; wire-rim drugstore readers on a chain.

**Hats:** sun-faded baseball cap (specify team or blank with sweat-stained brim); wool watch cap pulled low; wide-brimmed felt hat; bandana tied bandit-style at the back.

**Bags / pockets:** canvas tote stained at the bottom; leather satchel with patina at the corners; battered backpack with a single enamel pin; a phone protruding from a back pocket; a folded paperback in a coat pocket.

**Note for video:** accessories with **weight** read more strongly in motion than static ones. A single heavy earring swinging as she turns her head, a chain that swings out of a shirt collar when she leans forward, a watch that catches the light at one specific angle during a pan — these are stronger picks for Wan than purely decorative accessories that just sit there.

## 4. Wardrobe specificity (and wardrobe-IN-MOTION)

Almost never just "a dress" or "a shirt." At minimum: fabric + fit + condition. Add era when it helps.

**Fabric:** raw selvedge denim, washed linen, brushed wool, ribbed knit, technical nylon, faded indigo, suede, oxford cloth, slubbed silk, waxed canvas, brushed cotton flannel.

**Fit:** slightly oversized, tailored, cropped, draped, structured, slim, boxy.

**Condition:** faded, wrinkled, freshly pressed, slept-in, paint-stained, sun-bleached, mended at one shoulder, missing a top button, hem fraying, hand-darned at the elbow.

**Era anchors:** 1970s, mid-2000s, 1990s vintage, post-war utility, fin-de-siècle, Y2K, late-70s punk, early-90s grunge, mid-century menswear.

**Specific items** (vague items read as "AI" — specific items read as "real"):
- Oxford-cloth button-down (collar slightly curled)
- Cream fisherman knit sweater, hand-knit-irregular
- A-line midi skirt
- Levi's 501s with frayed cuffs
- A motorcycle jacket cracked at the elbows
- Work boots scuffed at the toe
- A barn jacket with the inside corduroy worn smooth at the collar
- A waxed canvas chore coat
- A surplus army-issue field shirt
- A faded 80s band T-shirt
- High-waisted carpenter pants with one chalk mark on the thigh

### Wardrobe-in-motion (video-only enrichment)

This is the single largest difference between a still wardrobe description and a video one. Don't just say what the wardrobe **is** — say how it **reacts to motion**. This turns a flat description into believable physics.

- **Linen** — catches the breeze, ripples, settles slowly when motion stops
- **Denim** — holds crease, barely moves with the body, weight grounds the silhouette
- **Silk / satin** — slips off the shoulder, catches highlights as it shifts
- **A sweater hem** — riding up an inch when she reaches overhead, settling back as she lowers her arms
- **A coat** — flaring out as she turns, the back hem trailing a half-beat behind the body
- **A long skirt or dress** — wrapping around the legs when she walks against a breeze, smoothing out on still steps
- **A scarf** — drifting horizontally on the windward side, the tail flicking back across her face once
- **Loose hair tied with a ribbon** — the ribbon's tails moving at a different frequency than the hair itself
- **A leather jacket** — creaking subtly (implied audio); shoulders moving as a fixed plane while the body shifts beneath
- **A starched collar** — staying put even as the head turns; the difference between starched and unstarched is visible in motion
- **A cuff** — riding up the wrist when she reaches forward, exposing a watch or tan line
- **Wet fabric** — clinging, slow to release, distinct shine in motion

Pick ONE wardrobe-in-motion cue per prompt. Stacking two reads as fabric-physics demo reel.

## 5. Camera movement vocabulary

This is video-only and high-leverage. **Don't leave the camera unspecified.** If you don't name a movement, Wan defaults to an unspecified slow drift that flattens the shot's identity.

### Movement names (pick ONE per shot)

- **Slow push-in** — measured dolly forward, builds intensity into a moment
- **Pull-back** — slow dolly out, often a reveal of context
- **Lateral track right / left** — camera physically moves sideways with the subject or past them
- **Handheld follow** — subtle vibration, the camera "breathes," documentary feel
- **Locked-off static** — camera doesn't move; all motion is inside the frame
- **Steadicam glide** — smooth follow with subtle vertical bob from the operator's steps
- **Drone descend** — camera drops vertically from above
- **Drone reveal** — wide aerial pull-back uncovering the scene's scale
- **Whip-pan** — fast horizontal pivot, often as a transition or a tracked head-turn
- **Dolly-zoom (vertigo)** — physical dolly + opposite zoom; use sparingly, it's instantly recognizable
- **Crane up / crane down** — camera rises or descends through space
- **Orbit** — camera circles the subject; specify direction (clockwise / counter-clockwise from above)
- **Boom up / boom down** — small vertical move at a fixed point in space
- **Rack focus** — focus shifts between foreground and background while the camera holds; treat as a "motion" choice

### Movement qualities (modifier, optional)

- **Glacial** — almost imperceptible, builds dread or weight
- **Measured** — steady, deliberate, cinematic
- **Deliberate** — slightly faster than measured, purposeful
- **Jittery** — handheld with shake, documentary or thriller register
- **Breath-tied** — camera bobs gently with the subject's breath, intimate
- **Mechanical** — too-perfect, slightly cold (gimbal or motion-control feel)
- **Floating** — Steadicam at low contact, dream register

### Specific patterns (drop in verbatim if it fits)

- "The camera holds locked-off for three beats, then begins a slow push-in as she looks up."
- "A single locked-off shot with all motion in-frame."
- "Steadicam follows from waist height behind her right shoulder."
- "Glacial dolly-in over the full duration of the shot, ending at a tight medium close-up."
- "Camera lateral-tracks past the subjects from left to right, holding focal length, the wall behind them blurring at the speed of a walking pace."
- "Handheld from a low angle, breath-tied, drifting half a step at a time."

**Cross-reference:** `references/cinematography-vocabulary.md` has the full taxonomy of shot types, angles, and lens choices. This palette is for picking quickly; that file is for full vocabulary.

## 6. Environmental motion

This is the second video-only category. **Don't leave the air dead.** Pick ONE primary indicator. Stacking environmental motion cues (wind AND rain AND smoke AND swaying trees) muddles the model — it averages them.

### Atmospheric: how wind is shown

Pick ONE primary wind indicator. The others should be consistent (a windy scene shouldn't have still hair AND blown leaves) but only one should be foregrounded.

- Hair drifting consistently in one direction
- Fabric catching the breeze (linen ripple, scarf tail, coat hem)
- Dust kicked up at ankle height
- Smoke or steam drifting horizontally at one specific height
- Leaves moving on a single tree branch in the frame
- A loose page on a table lifting and settling

### Water

- A single drop falling at one specific beat
- Ripples expanding from one point on still water
- Condensation rolling down a window (one bead at one moment)
- Steam rising from a mug crossing the frame ONCE, not continuously
- Drips from an awning after rain, irregular intervals
- A puddle disturbed by one footstep at the edge of frame

### Smoke / dust / steam / particulate

- A rising column (cigarette, chimney, incense)
- Drifting horizontally across the frame
- Settling slowly after disturbance
- Catching backlight in a single beam
- Specks of dust visible only in a shaft of light

### Fire / sparks

- Slow flicker (candle, oil lamp) vs fast flicker (open flame in wind)
- Direction of throw (sparks lifting up, blowing sideways)
- Color: yellow-orange (warm) vs white-hot (intense) vs blue (gas)
- A single ember drifting up and out of frame

### Hair flow (the most common video-specific cue)

- Held still, no wind
- A sudden gust at one specific moment
- Consistent breeze (subtle ongoing drift)
- Blown back during motion (subject running, riding, leaning out a window)
- Caught in a fan or air conditioning indoor (mechanical, more regular than wind)

### Off-camera motion implied (high-leverage)

- A curtain billowing into frame at the edge
- A shadow passing across the wall (from someone or something off-screen)
- A door swinging closed at the corner of the frame
- Light flickering as if from a TV in an adjacent room
- A car passing the window, headlights briefly sweeping the room

## 7. Light interaction (including time-of-day continuity)

Specify how the light interacts with the scene, not just its quality:

- A single practical source (table lamp, screen glow, candle, reflected neon)
- Two-source: window light + a single warm interior lamp
- Rim light ONLY from behind — silhouette with edge glow, face in shadow
- Light filtered through a curtain / a window screen / a dirty window
- Light through fabric (a sheer scarf, a thin blouse)
- Caustics — light reflected through liquid (a glass of water on the table)
- Colored bounce: red from a brake light onto a cheek, blue from a phone screen on the face, green from a fluorescent tube above
- TV as the only light in the room
- Time-of-day named precisely: 11pm fluorescent diner, 4am parking-lot sodium-vapor, 6am pre-dawn blue, late golden hour ~7pm summer

### Multi-shot light continuity (Wan 2.6+ shot-block prompts only)

When a prompt has multiple shots, the light has to be deliberately handled across cuts. Two cases:

**Simultaneous shots (same scene moment):** light direction and color temperature MUST hold across cuts. Restate as a continuity anchor in shots 2+: "Same low warm key from camera-right as Shot 1." Inconsistent light between simultaneous cuts is one of the most jarring tells in AI video.

**Shots spanning time (e.g. Shot 1 dusk → Shot 2 night):** name the transition explicitly. Don't leave the light to be inferred — Wan will average. Better to name a specific time-of-day change ("Shot 1 at last light, Shot 2 thirty minutes later — practical lamps now on, dusk gone from the sky") than to write two ambiguous shots.

### Named light-shift events (high-leverage)

These ground the light in a specific moment rather than a generic "golden hour":

- A cloud crossing the sun mid-shot — the light dims for two beats, then returns
- A streetlight flicking on as full dusk lands
- Headlights sweeping across a wall as a car passes off-screen
- A door opening to a brighter room — light spills into the foreground
- A fluorescent tube buzzing once and going out, the room dimming
- Sunset hitting a single window across the street and reflecting onto the subject's face
- A practical lamp being switched off by the subject mid-shot

## 8. Named-reference anchors — cinematographers and directors

Pick ONE per prompt — never more. Name an actual cinematographer, director, or director-DP pairing. This anchors Wan to a real visual register instead of "the average of all video on the internet."

**One anchor. Stacking two muddies the output.** "Roger Deakins meets Wong Kar-wai" produces a hybrid that's neither.

### Cinematographers (individual)

| Reference | Register |
|---|---|
| Roger Deakins (1917, Blade Runner 2049, Skyfall) | controlled cinematic precision, motivated practical light |
| Christopher Doyle (In the Mood for Love, Chungking Express) | saturated handheld longing, slow shutter, blown highlights |
| Emmanuel Lubezki (Tree of Life, The Revenant, Birdman) | natural-light wide, magic hour, long takes |
| Hoyte van Hoytema (Interstellar, Oppenheimer, Dunkirk) | IMAX wide, controlled, deep deep blacks |
| Bradford Young (Arrival, Selma) | low-key warm shadow, faces in half-light |
| Newton Thomas Sigel (The Usual Suspects, Drive) | desaturated naturalism with occasional saturated punctuation |
| Robert Yeoman (Wes Anderson's DP) | flat-frontal centered, symmetrical, primary colors |
| Linus Sandgren (La La Land, First Man) | saturated technicolor warmth, anamorphic flare |
| Greig Fraser (Dune, The Batman, Rogue One) | volumetric, atmospheric, low-contrast wides |
| Robbie Ryan (American Honey, The Favourite) | handheld 16mm warmth, intimate |

### Director–DP pairings (use as a single register, not two anchors)

| Pairing | Register |
|---|---|
| Wong Kar-wai + Christopher Doyle | saturated longing, slow shutter, neon-and-shadow |
| Terrence Malick + Emmanuel Lubezki | natural-light wide, magic-hour Steadicam, voice-over patience |
| Christopher Nolan + Hoyte van Hoytema | IMAX wide, controlled formal, low-key |
| Yorgos Lanthimos + Thimios Bakatakis | wide cold awkward, fixed lens, distant framing |
| Nicolas Winding Refn | saturated neon, locked-off, mirrored compositions |
| David Lynch | dream-logic temporality, low-mid frequency soundscape (visual register: slow zooms, red-dominant interiors, fluorescent unease) |
| Andrei Tarkovsky | long-take patience, weighted air, water as a recurring element |
| Wes Anderson + Robert Yeoman | flat-frontal centered, symmetrical, primary palette (use ONLY when wanted) |
| Sofia Coppola | pastel languor, soft natural light, slow camera |
| David Fincher | controlled, cool, locked-off, slight desaturation |

### Genre / era anchors

- 70s New Hollywood handheld (Taxi Driver, Dog Day Afternoon, The French Connection)
- Mid-90s independent (Wong Kar-wai era, early Linklater, Hal Hartley)
- Contemporary slow-cinema (Reichardt, Hou Hsiao-hsien, Apichatpong Weerasethakul)
- Music-video maximalism (Hype Williams 90s, Floria Sigismondi)
- Cinéma vérité documentary (D.A. Pennebaker, the Maysles)
- Soviet montage (Eisenstein, Vertov — high-contrast, dialectical cuts)
- Japanese 60s–70s color film (Imamura, Suzuki — saturated, theatrical)
- Italian neorealism (post-war B&W, on-location, non-actors)

**Use one anchor. Don't stack.** One anchor; the rest of the prompt does the work.
