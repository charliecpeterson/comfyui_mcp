# Audio Prompting for LTX-2

LTX-2's signature feature is **native synchronized audio-video generation**. Unlike Wan, Sora, Veo, or other video models that bolt audio on as a post-processing step, LTX-2 generates the audio and video in the same diffusion pass, with the audio synced to the visual content.

This reference covers how to write audio cues that produce clean, properly synced soundscapes.

## The fundamental principle

**Describe sound as part of the scene, not as a separate category.** The audio prompt is woven into the same paragraph as the visual prompt, with sound elements described alongside the visual elements they correspond to.

❌ "Visual: a man hammers wood. Audio: hammer sounds, ambient workshop noise, country blues music."

✅ "A man hammers a nail into a wooden plank with rhythmic precision; each strike produces a strong solid thud and the metallic ring of the nail seating fully. From the corner, a small antique gramophone plays soft country blues at low volume, the music slightly crackling in the manner of old shellac recordings."

The audio sources are anchored to their visual sources (the hammer, the gramophone) and described in the same prose flow.

## The three audio layers

Every audio-aware LTX-2 prompt should cover at least one of these layers, ideally two or three:

### Layer 1: Ambient / environment

The background soundscape. Sets the scene's auditory register.

Examples:
- "Wind moves softly through leaves overhead"
- "Distant traffic hum from the street outside"
- "Rain steady against the window, occasional thunder rolling in the distance"
- "Fluorescent ceiling lights buzz faintly"
- "Ocean waves break in a slow regular rhythm just out of frame"
- "The room is quiet except for the soft tick of a wall clock"

### Layer 2: Subject sounds

Sounds the main subject or objects in the scene make. Anchored to specific visible actions.

Examples:
- "Footsteps echoing on the concrete floor"
- "His breathing is steady but slightly heavy from the exertion"
- "The kettle starts to whistle softly"
- "Each strike of the hammer produces a strong solid thud"
- "Glass clinks gently against glass as she sets the tumbler down"
- "Fabric rustles as she adjusts her coat"

### Layer 3: Music / dialogue (optional)

Music or speech in the scene. Use sparingly — LTX-2 handles ambient/effect audio more reliably than complex music or speech.

Examples:
- "A small antique gramophone plays soft country blues at low volume"
- "Distant jazz drifts from a doorway down the street"
- "Faint ambient hum of an old jazz radio in the corner"
- "She mutters a single quiet phrase under her breath"
- "Soft instrumental piano fills the space, slow and contemplative"

**Avoid:**
- Specific named songs or artists (LTX can't reproduce these)
- Long stretches of dialogue (use short utterances if any)
- Genre-specific music with strong requirements ("a complex jazz fusion solo with walking bass")

## Patterns by scene type

### Quiet interior

> Layer 1 (ambient): soft tick of wall clock, distant city hum through windows
> Layer 2 (subject): occasional shuffle of a chair, quiet breathing, soft turn of a page
> Layer 3: typically none — let the quiet do the work

Example:
> "A man sits at a kitchen table reading a newspaper. The room is quiet except for the soft tick of a wall clock and the occasional rustle as he turns a page; outside, the distant hum of city traffic filters through closed windows."

### Workshop / industrial

> Layer 1 (ambient): mechanical hum, distant clanks, occasional shouts in the distance
> Layer 2 (subject): specific tool sounds (hammer strikes, saw whirring, metal on metal)
> Layer 3: optional radio playing softly somewhere

Example:
> "She operates a heavy metal lathe in a dim industrial workshop. The lathe whirs at a steady mid-range pitch with occasional metallic squeaks as it bites into the workpiece; in the background, distant clanks from other machines punctuate the air, and a small radio mounted on the wall plays an indistinct news broadcast at low volume."

### Outdoor nature

> Layer 1 (ambient): wind in trees, distant water, birdsong, the absence of human sound
> Layer 2 (subject): footsteps on natural ground, breathing in cold air, fabric movement
> Layer 3: typically none — natural scenes benefit from naturalistic audio only

Example:
> "A woman walks slowly along a misty forest path at dawn. The forest is quiet — soft wind moves through the upper canopy, occasional distant bird calls, the muffled crunch of pine needles under her boots; somewhere off-frame, a small stream runs quietly."

### Urban / cinematic

> Layer 1 (ambient): traffic, distant sirens, voices, music from windows
> Layer 2 (subject): footsteps on pavement, fabric, occasional close interactions
> Layer 3: practical music from passing cars, distant performance, etc.

Example:
> "A man walks down a rain-slicked city street at night. Distant traffic hums steadily, with occasional sirens far away; rain falls steadily on the pavement and his umbrella, drops striking with a soft constant patter. From an open doorway he passes, faint jazz music drifts briefly into the soundscape then fades behind him as he continues."

### Action / kinetic

> Layer 1 (ambient): adjust to the scene — exterior chase = wind and city; interior fight = building ambient
> Layer 2 (subject): heavy breathing, footsteps, fabric whip, impact sounds
> Layer 3: typically none — let the action sounds dominate

Example:
> "A man runs through narrow underground concrete corridors, his footsteps echoing sharply off the walls with each impact, breath ragged and increasingly heavy. The fluorescent tubes overhead buzz audibly and occasionally flicker, casting brief moments of darkness; somewhere far behind him, the faint sound of another set of footsteps, slower, more deliberate."

### Intimate / emotional

> Layer 1 (ambient): subtle, designed to recede behind subject sounds
> Layer 2 (subject): breathing, micro-sounds (heartbeat suggested by stillness, fabric, voice)
> Layer 3: optional quiet music

Example:
> "A woman in her sixties sits at a kitchen table, looking at an open photo album. The kitchen is quiet — a kettle ticks slightly as it cools on the stove, the distant tick of a wall clock, her own soft breathing. As she turns a page, the paper makes a thin gentle sound; her exhale on one particular photograph is barely audible but distinct."

## Avoid: common audio prompting mistakes

### Naming songs or specific music

❌ "Plays 'Stand By Me' by Ben E. King"

LTX-2 generates audio from training; it doesn't have a song library. The result will be vaguely similar at best, garbled at worst.

✅ "Plays a soft slow-tempo 1960s soul song with a male vocalist, the kind that might be on a jukebox in a corner diner"

### Audio that conflicts with visuals

❌ "A man sits in silence reading, with loud rock music blasting in the background"

If the visual shows quiet contemplation and the audio describes loud music, LTX-2 produces incoherent output where one or the other wins randomly.

✅ Either: "...with loud rock music blasting and he occasionally taps his fingers on the table to the beat" (visual matches audio)
OR: "...the room is quiet with only the soft tick of a wall clock" (audio matches visual)

### Over-prescribing dialogue

❌ "She says 'I never wanted this, but here we are. After everything we've been through, you'd think I would have learned by now.'"

LTX-2 handles short utterances OK but produces poor full sentences. Long dialogue is unreliable.

✅ "She mutters something quietly under her breath, the words indistinct but the tone weary."

### Overlapping competing sound sources

❌ "A loud jackhammer outside, dogs barking nearby, a TV playing news, two people having a conversation, music from a radio"

Too many simultaneous distinct sources confuses LTX-2's audio mixing. Pick 2–3 layers at most, with clear hierarchy of foreground vs background.

✅ "A jackhammer drills somewhere down the street with rhythmic impacts; closer to the camera, two voices in conversation cut through the construction noise, their specific words indistinct but tone clearly arguing."

### Describing audio without visual anchor

❌ "Soundscape: footsteps, breathing, distant siren, leaf rustling"

Better to anchor each sound to its visual source or to the spatial position it comes from. LTX-2's audio is generated to match the visual scene; the more grounded the sound source, the cleaner the result.

✅ "Her footsteps strike the wet pavement with each stride; in the distance, a siren rises and falls; the leaves of a maple tree just out of frame rustle in a gust of wind."

## Audio in I2V (image-to-video) mode

For LTX-2 I2V, the source image defines the visual content but you still control the audio through the prompt. This is a powerful combination — you can add a soundscape to a still image.

Example: portrait of a woman by a window

> "The woman breathes slowly, her chest rising and falling visibly. Outside the window, soft rain falls steadily against the glass and a distant car passes; inside the room, the faint hum of a refrigerator and the occasional creak of old wooden floorboards somewhere out of frame complete the quiet domestic soundscape."

The visual provides the woman + window; the prompt provides the breathing + rain + house ambient.

## Audio-to-video (A2V) mode

LTX-2 supports audio-to-video — you provide an audio file and the model generates matching video. For A2V prompts:

- Describe the visual scene that should match the audio
- Don't describe the audio itself (the file provides it)
- Match the visual register to what the audio implies (energy, mood, pacing)

Example: A2V with an audio file of acoustic guitar playing

> "An intimate medium shot of a musician's hands and lap; the musician sits cross-legged on a wooden floor, holding an acoustic guitar tilted toward the camera. They wear faded jeans and a soft cream sweater; the room around them is warm and softly lit with a single window providing afternoon golden-hour light from the left, dust motes drifting in the beam. Camera holds in a static medium close-up on the guitar and hands as they finger the strings. The visual register is intimate, unhurried, contemplative — matching the music's character."

## Parameter notes for audio generation

- **LTX-2 audio quality varies with inference steps** — for clean audio, use `TI2VidTwoStagesHQPipeline` or the standard two-stage with full steps. Fast/distilled pipelines produce serviceable but lower-fidelity audio.
- **Higher fps does not improve audio** — audio is generated independently of frame rate. 24fps and 50fps produce the same audio quality.
- **Resolution doesn't affect audio** — generate at the resolution you need for visual, audio is the same regardless.

## Quick template

For audio-aware LTX-2 prompts, expand the 7-component structure with audio elements woven into the relevant components:

1. Main action (with any associated sounds)
2. Movement details (with any associated sounds — footsteps, breathing, etc.)
3. Character/object appearance (with any sounds they make — clothing rustle, jewelry clinks)
4. Background and environment (with **Layer 1 ambient audio woven in**)
5. Camera angle and movement
6. Lighting and colors
7. Changes/events (with any **Layer 3 music/dialogue or auditory events**)

Audio doesn't get its own dedicated component — it threads through the existing seven, attached to the visual sources that produce each sound.
