# Cinematography Vocabulary for Wan

Wan was trained on real cinematography content with proper film vocabulary. Using the actual terms a cinematographer would use produces meaningfully better results than generic descriptions. This file catalogues the camera, lens, and shot vocabulary that Wan recognizes well.

This is one of the highest-leverage references for Wan prompting — and one of the biggest differentiators between mediocre and great Wan output.

---

## Shot types (how much is visible)

| Shot | What it shows |
|---|---|
| **Extreme close-up (ECU)** | A single detail — an eye, lips, hands on a tool |
| **Close-up (CU)** | Head and shoulders, or one focused element |
| **Medium close-up (MCU)** | Head to mid-chest, classic dialogue framing |
| **Medium shot (MS)** | Waist-up, conversational |
| **Medium long shot (MLS)** | Knees-up, environmental but subject-led |
| **Long shot / Full shot** | Full body with some environment |
| **Wide shot** | Subject small in a larger environment |
| **Extreme wide shot (EWS)** | Landscape with subject as a detail |
| **Two-shot** | Two subjects in frame |
| **Over-the-shoulder (OTS)** | From behind one subject, looking at another |
| **POV** | First-person — what the subject sees |
| **Insert shot** | Brief detail cutaway (a clock, a phone, a note) |

---

## Camera angles

| Angle | Effect |
|---|---|
| **Eye level** | Neutral, naturalistic |
| **Low angle** | Subject appears powerful or imposing |
| **High angle** | Subject appears small, vulnerable, or under threat |
| **Bird's-eye view / overhead** | Pattern, abstraction, divine perspective |
| **Worm's-eye view** | Extreme low angle, monumentalizing |
| **Dutch angle** | Tilted frame, tension or instability |
| **Three-quarter view** | Slight angle, natural for portraits |
| **Profile** | Side-on, often used for silhouette work |
| **Direct front** | Confrontational, formal |
| **Direct back** | Following or observational |

---

## Camera movements

The single most important Wan vocabulary category. Pick ONE main movement per shot on 2.1/2.2 (Wan 2.6+ supports multi-stage moves better but still prefers clarity).

### Movements where the camera physically translates

| Movement | What it does |
|---|---|
| **Dolly in** | Camera physically moves forward, into the scene |
| **Dolly out / Pull-back** | Camera physically moves backward, often as a reveal |
| **Truck left / Truck right** | Camera physically moves sideways (parallel to subject) |
| **Pedestal up / Pedestal down** | Camera physically moves vertically (typically on a tripod head) |
| **Crane / Boom up / Boom down** | Camera rises or descends through space, often dramatically |
| **Tracking shot** | Camera moves with the subject, maintaining distance |
| **Push-in** | Slow dolly forward, building intensity |
| **Slider move** | Smooth horizontal or diagonal translation |
| **Steadicam follow** | Smooth handheld-feel motion following the subject |

### Movements where the camera rotates in place

| Movement | What it does |
|---|---|
| **Pan left / Pan right** | Camera pivots horizontally on a fixed point |
| **Tilt up / Tilt down** | Camera pivots vertically |
| **Whip pan** | Very fast pan, often for transitions |
| **Roll** | Camera rotates along the lens axis (Dutch effect) |

### Compound / specialty movements

| Movement | What it does |
|---|---|
| **Orbit / Arc** | Camera circles around the subject, maintaining distance |
| **Vertigo (dolly zoom)** | Dolly in while zooming out, or vice versa — the iconic Hitchcock effect |
| **Handheld** | Subtle vibration, documentary feel |
| **Crash zoom** | Very fast zoom in, often used dramatically |
| **Drone shot** | Aerial perspective, often a rising or sweeping move |
| **Reveal** | Any move that exposes new information — typically pull-back, crane up, or pan |
| **Lock-off / static** | Camera doesn't move at all |

---

## Lens / focal length

Naming a focal length gives Wan a recognizable look.

| Focal length | Look | When |
|---|---|---|
| **14–24mm (ultra-wide)** | Distorted edges, exaggerated depth, foreground feels close | Architectural interiors, dramatic landscapes, claustrophobic spaces |
| **24–35mm (wide)** | Slight perspective stretch, environmental | Environmental portraits, documentary feel |
| **35mm** | Most documentary — what the eye sees with slight expansion | Reportage, candid storytelling |
| **50mm** | Natural — closest to human eye | Standard portrait, naturalistic scenes |
| **85mm** | Portrait compression, flattering proportions | Beauty/fashion portraits, isolated subject |
| **100–135mm** | Strong subject isolation, compressed planes | Detail shots, stalking-the-subject feel |
| **200mm+** | Heavily compressed, flattens depth | Sports, wildlife, "stolen moment" |

**Aperture:**

- **f/1.2–f/1.8** — extremely shallow DOF, dreamy
- **f/2–f/2.8** — classical portrait depth
- **f/4–f/5.6** — environmental subject with somewhat soft background
- **f/8–f/11** — deep focus, landscape standard

---

## Lens character / stylization

These give Wan specific aesthetic anchors.

| Term | Look |
|---|---|
| **Anamorphic** | Horizontal lens flare, oval bokeh, cinematic widescreen feel |
| **Anamorphic flare** | Specific horizontal-streak highlight artifacts |
| **Fisheye** | Extreme wide with curved distortion |
| **Tilt-shift** | Selective focus that makes scenes look like miniatures |
| **Vintage glass** | Lower contrast, slight haze, character imperfections |
| **Cinematic flare** | Light bleed from bright sources |
| **Bokeh** | Out-of-focus background blur quality |
| **Smooth bokeh** | Soft, creamy out-of-focus background |
| **Hexagonal bokeh** | Geometric out-of-focus highlights from older apertures |

---

## Film stocks (named looks)

Naming a real film stock gives Wan a recognizable color/grain signature.

**Color negative:**
- **Kodak Portra 400** — warm skin tones, soft contrast, fashion/portrait standard
- **Kodak Portra 800** — pushed Portra look, more grain
- **Kodak Ektar 100** — saturated, fine grain, landscape favorite
- **Kodak Gold 200** — warm consumer color, vintage feel
- **Fuji Pro 400H** — cool tones, soft pastels
- **Fuji Velvia 50** — extremely saturated, vivid landscapes
- **Cinestill 800T** — tungsten-balanced, red halos around bright lights, neon-night look

**Black and white:**
- **Kodak Tri-X 400** — classic documentary B&W, visible grain
- **Ilford HP5 Plus** — slightly softer than Tri-X
- **Ilford Delta 3200** — heavily grained, available-light night

**Cinema:**
- **Kodak Vision3 250D** — daylight cinema standard
- **Kodak Vision3 500T** — tungsten cinema, low-light
- **16mm grain** — visible grain, indie film feel
- **65mm IMAX** — large-format clarity, monumental

---

## Color grading vocabulary

| Grade | Look |
|---|---|
| **Teal and orange** | Hollywood blockbuster default — skin pushed orange, shadows pushed teal |
| **Bleach bypass** | Desaturated highlights, retained silver in shadows — Saving Private Ryan look |
| **Cross-processed** | Magenta/green color shifts from slide-in-negative chemistry |
| **Day-for-night** | Underexposed and blue-graded daytime simulating moonlight |
| **Faded film** | Slightly washed contrast, lifted blacks |
| **Push-processed** | Higher grain, increased contrast, journalistic |
| **Muted palette** | Limited color range, one dominant hue family |
| **Two-tone** | Two dominant complementary colors |
| **High-contrast B&W** | Deep shadows, bright highlights |
| **Soft contrast** | Lifted blacks, gentle tonal range, Portra/wedding |
| **Neon-saturated** | Hot pink and cyan emphasized, Blade Runner |
| **Earth-tone** | Browns, ochres, deep greens — Westerns and grounded drama |

---

## Lighting setups (named patterns)

| Setup | Look |
|---|---|
| **Three-point lighting** | Key + fill + rim — commercial standard |
| **Rembrandt** | Single key at 45°, small triangle of light on the shadowed cheek |
| **Chiaroscuro** | High contrast, strong directional key, deep shadows preserved |
| **Butterfly lighting** | Light directly above the camera, beauty/glamour |
| **Split lighting** | Key 90° to one side, half the face in shadow |
| **Practical lighting** | Visible in-scene sources (lamps, neon, candles, windows) |
| **Available light** | No added light — documentary |
| **High-key** | Bright, low-contrast, optimistic |
| **Low-key** | Dark, high-contrast, noir |
| **Volumetric / God rays** | Visible beams of light through atmosphere |
| **Window light** | Diffused single-source from a window |
| **Golden hour** | Warm low-angle sun, first/last hour of daylight |
| **Blue hour** | Twilight, cool ambient with warm artificial accents |

---

## Speed / pacing vocabulary

How motion unfolds in time.

| Term | Effect |
|---|---|
| **Slow motion** | Sub-real-time motion, intensifies detail |
| **Real-time** | Default — natural speed |
| **Time-lapse** | Compressed time, clouds racing |
| **Hyperlapse** | Time-lapse with camera moving |
| **Smooth / fluid** | Even, controlled pacing |
| **Kinetic / energetic** | Fast cuts, aggressive motion |
| **Static / locked-off** | No camera movement, only subject motion |
| **Subtle / minimal** | Small amplitude, gentle |
| **Dynamic** | Pronounced motion, attention-grabbing |
| **Accelerating** | Pace builds across the clip |
| **Decelerating / settling** | Pace slows toward the end |

---

## Specific cinematic patterns Wan recognizes

These shorthand phrases trigger specific looks Wan was trained on:

- **"Single continuous handheld shot following [X]"** — gritty action documentary feel
- **"Locked-off wide shot with [X] entering/leaving frame"** — composed observational
- **"Slow push-in from medium to close-up as [X happens]"** — intimate emotional reveal
- **"Aerial drone shot rising above [X]"** — sweeping landscape reveal
- **"Tracking shot at hip height alongside [X]"** — Steadicam follow
- **"Static frame, [X] enters from the left and walks across"** — classic theatrical staging
- **"Crane up from [low element] to reveal [wider scene]"** — dramatic reveal
- **"Slow orbit around [X] at eye level"** — character study or product reveal
- **"POV through [X's] eyes as they [Y]"** — first-person immersion
- **"Whip pan from [A] to [B]"** — energetic transition

---

## How to combine these

A complete camera-language clause typically combines: **shot type + camera movement + lens/focal-length (optional) + lighting + pacing**.

Examples:

> "Medium close-up on a slow dolly-in, 85mm lens at f/2, soft window light from the left, smooth controlled pacing."

> "Wide aerial drone shot rising above the canyon, 24mm wide lens, golden hour side-lighting, slow majestic pacing."

> "Single continuous handheld tracking shot at hip height following the runner, 35mm documentary feel, available daylight with cool overcast, kinetic energetic pacing."

You don't need every category in every prompt. Most prompts need: **camera movement + one lighting detail + pacing.** Add lens or film stock when the visual texture matters.

---

## Wan 2.6+ specific notes

On Wan 2.6 and 2.7, you can combine multiple camera moves within a single shot block — but the model still prefers explicit sequencing rather than simultaneous compound moves.

Good (sequenced):
> "Camera starts on a medium close-up, holds for 2 seconds, then dollies back smoothly to reveal the wider room."

Bad (simultaneous):
> "Camera dollies back while panning right and tilting up while zooming in."

The second example will produce muddled, averaged motion. Even on Wan 2.7 with Thinking Mode, sequencing produces cleaner output than compounding.
