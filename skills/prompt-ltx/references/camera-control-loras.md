# Camera Control LoRAs for LTX-2

LTX-2 ships with dedicated camera-control LoRAs — discrete trained adapters that produce specific camera movements more reliably than describing them in the prompt alone. This is a distinctive LTX feature compared to Wan, Sora, and Veo.

When the user wants a specific camera move and motion quality matters (commercial work, narrative finals, branded video), the camera control LoRAs produce noticeably cleaner output than text-prompt-only camera direction.

## Available camera control LoRAs

From the official LTX-2 repository:

| LoRA | Movement | Use case |
|---|---|---|
| **LTX-2-19b-LoRA-Camera-Control-Dolly-In** | Slow forward push | Building intensity, intimate reveal, focus on subject |
| **LTX-2-19b-LoRA-Camera-Control-Dolly-Out** | Slow backward pull | Reveal of wider context, ending shots, emotional retreat |
| **LTX-2-19b-LoRA-Camera-Control-Dolly-Left** | Sideways move (truck) to the left | Parallax reveal, lateral movement, kinetic feel |
| **LTX-2-19b-LoRA-Camera-Control-Dolly-Right** | Sideways move (truck) to the right | Same as Dolly-Left, opposite direction |
| **LTX-2-19b-LoRA-Camera-Control-Jib-Up** | Crane / boom up (rising camera) | Reveal from low to high, scale emphasis, majestic feel |
| **LTX-2-19b-LoRA-Camera-Control-Jib-Down** | Crane / boom down (descending) | Reveal from high to low, settling into a scene |
| **LTX-2-19b-LoRA-Camera-Control-Static** | Locked-off (no movement) | Composed observational, theatrical staging, dialogue scenes |

There are also two **content-control IC-LoRAs** distinct from the camera ones:

| LoRA | Function |
|---|---|
| **LTX-2.3-22b-IC-LoRA-Union-Control** | General-purpose conditioning control |
| **LTX-2.3-22b-IC-LoRA-Motion-Track-Control** | Track and replicate motion patterns |
| **LTX-2-19b-IC-LoRA-Detailer** | Sharpens output detail |
| **LTX-2-19b-IC-LoRA-Pose-Control** | Conditions output on a pose skeleton |

## When to use a camera LoRA vs prompt-only camera direction

**Use a camera LoRA when:**
- Motion quality is critical (commercial, portfolio, client work)
- The specific camera move is the defining element of the shot
- Prompt-only camera direction produced inconsistent or unconvincing motion
- You need the camera move to be smooth and continuous throughout the entire clip

**Use prompt-only camera direction when:**
- The shot has multiple camera beats (move + hold + move) that no single LoRA handles
- You want experimental or unusual camera character
- The camera move is secondary to other elements
- You're prototyping and the LoRA-loading overhead isn't worth it

## Workflow integration

LoRA strength is typically `0.6–1.0`. Lower strengths apply more subtle versions of the movement; higher strengths produce strong, pronounced camera moves.

**Recommended starting strengths:**

- Dolly In/Out: `0.7–0.9` (subject-focused moves benefit from a clear push without burning the image)
- Dolly Left/Right: `0.7–0.9` (similar)
- Jib Up/Down: `0.8–1.0` (these moves are most effective at higher strength)
- Static: `0.9–1.0` (you want the lock-off to be firm)

## Prompt conventions when using a camera LoRA

Even when using a camera LoRA, your prompt should still mention the intended camera move. The LoRA reinforces it; the prompt confirms it. Without prompt confirmation, the LoRA's bias might conflict with the rest of the prompt and produce muddled results.

### What to include in the prompt with the LoRA

Mention the camera move naturally as part of component 5 (camera angles and movements) in the official structure:

> "...The camera slowly dollies forward over the duration of the clip, pushing in from a wide medium to a tight close-up by the end..."

This is concise — you don't need to over-describe; the LoRA handles the motion mechanics.

### What you can SKIP when using the LoRA

- **Detailed lens specs:** the LoRA handles the move quality; you don't need "85mm at f/2.0 with smooth bokeh as it pushes in"
- **Specific dolly distance:** "moves forward 3 feet" — the LoRA produces a consistent move regardless
- **Easing details:** "starts slow, accelerates in the middle, eases at the end" — the LoRA has its own learned pacing

### What to STILL include even with the LoRA

- **The general camera direction:** confirms the LoRA's intent
- **Subject framing at start and end:** "begins on a wide medium, settles to a tight close-up"
- **Camera height / angle:** the LoRA covers the move axis, not the starting angle
- **Spatial context:** what the camera sees as it moves

## Combining camera LoRAs with content LoRAs

You can stack camera LoRAs with the IC-LoRAs (Pose-Control, Detailer, etc.). Common combinations:

- **Dolly-In + Detailer:** push toward a subject while keeping details sharp
- **Static + Pose-Control:** fixed camera while subject performs a specific pose
- **Jib-Up + Union-Control:** majestic reveal with additional conditioning

Stack LoRAs at moderate strengths (`0.5–0.7` each) when combining, to avoid over-cooking the output.

## Per-LoRA usage notes

### Dolly-In

The most commonly used LoRA. Builds intensity by literally moving the viewer closer to the subject.

**Strong with:**
- Single-subject scenes (portraits, close character moments)
- Emotional beats (push-in as a realization happens)
- Reveal of a specific detail

**Weak with:**
- Action scenes (the slow push fights kinetic energy)
- Subjects that are themselves moving toward the camera (motion conflict)

**Sample prompt:**
> "A woman in her thirties sits at a small wooden desk, holding a letter; her expression slowly shifts from confused to understanding as she reads. She has shoulder-length dark hair and freckled cheeks; she wears a soft grey sweater. The desk holds a single mug of tea and a small lamp; behind her, an unmade bed and morning light through partially-drawn curtains. The camera begins on a medium shot and slowly dollies forward, settling on a medium close-up of her face by the end of the clip. Warm window light from her right, soft cool ambient from the room. As the dolly completes, her eyes well slightly with tears."

### Dolly-Out

The opposite of Dolly-In. Pulls back to reveal context, often used as a closing move.

**Strong with:**
- Reveal of unexpected wider context
- Emotional pull-back (subject becomes smaller, more alone)
- Establishing how isolated or surrounded a subject is

**Weak with:**
- Action approaching the camera (subjects coming forward become small fast)
- Detailed close-up subjects (you lose the detail you wanted to show)

### Dolly-Left / Dolly-Right

Sideways truck moves. Parallax reveals — the foreground moves at one rate, the background at another.

**Strong with:**
- Walking subjects (the camera tracks alongside)
- Architectural reveals (passing a column, then a doorway, then another column)
- Parallax-heavy scenes with strong foreground/background separation

**Weak with:**
- Static composed shots (the move feels arbitrary)
- Scenes with little depth (parallax doesn't show up)

### Jib-Up / Jib-Down

Vertical crane moves. Reveal scale or settle into intimacy.

**Strong with:**
- Landscape and architectural reveals
- "From the ground up" or "from above looking down" emotional registers
- Establishing the scale of something large (a building, a crowd, a landscape)

**Weak with:**
- Tight interiors with limited vertical space
- Subjects that fill the frame already (the move has nowhere to go)

### Static

A locked-off LoRA — explicit no-movement. This is genuinely useful: it overrides LTX's natural tendency to add subtle drift or breathing camera, producing a truly locked frame.

**Strong with:**
- Dialogue scenes where subject motion is the point
- Theatrical staging (subjects entering and exiting a fixed frame)
- Surveillance / observational tone
- Composed photographic-style shots

**Weak with:**
- Action scenes (the lock-off fights kinetic energy)
- Scenes that need camera energy to feel alive

## When LoRAs aren't enough

Some camera moves are NOT covered by the available LoRAs:

- **Orbit / arc** — circling around the subject. Use prompt-only direction.
- **Whip pan** — very fast pivot. Prompt-only.
- **Vertigo (dolly zoom)** — Hitchcock effect. Prompt-only, and may need experimentation.
- **Tracking shot at variable speed** — speeding up or slowing down. Prompt-only.
- **Compound moves** (dolly + tilt simultaneously) — no single LoRA. Use prompt direction or sequence them.

For these, fall back to the prompt-only camera vocabulary in `references/official-prompt-structure.md`.

## ComfyUI workflow notes

In ComfyUI-LTXVideo, camera LoRAs load through the standard LoRA loader nodes. Order in the loader stack:

1. Base LTX-2.3 checkpoint
2. (Optional) Distilled LoRA for fast inference
3. Camera Control LoRA (at recommended strength)
4. (Optional) IC-LoRA for content control
5. (Optional) Style LoRAs

Each LoRA loaded after the first applies on top — the camera LoRA should be loaded after the distilled LoRA but before any style LoRAs.

## Quick reference

| User wants | LoRA to use | Default strength |
|---|---|---|
| Push in / build intensity | Dolly-In | 0.8 |
| Pull back / reveal context | Dolly-Out | 0.8 |
| Sideways parallax move | Dolly-Left or Dolly-Right | 0.8 |
| Rising reveal | Jib-Up | 0.9 |
| Descending reveal | Jib-Down | 0.9 |
| Truly locked-off frame | Static | 0.95 |
| Orbit / arc | (no LoRA — prompt only) | — |
| Whip pan | (no LoRA — prompt only) | — |
| Compound moves | (sequence them or prompt-only) | — |
