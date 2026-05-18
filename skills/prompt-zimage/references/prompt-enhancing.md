# Prompt Enhancing (PE) for Z-Image

Tongyi-MAI ships an official **Prompt Enhancer template** (`pe.py`) alongside Z-Image. The PE is an LLM-driven preprocessing step that takes a short user prompt and expands it into a longer, richer, more detailed prompt before generation — using the LLM's reasoning capabilities and world knowledge to fill in details a casual prompter would omit.

This is part of *why* Z-Image rewards long prompts: the official workflow assumes you'll either write a long prompt yourself, or run a short one through PE first.

This reference explains the PE pattern and when to apply it inside the skill workflow.

---

## What the PE does

A user types: *"A girl in a hanfu"*

Without PE, Z-Image generates a reasonable but underspecified image based on its defaults.

With PE, that short prompt gets expanded (by an LLM acting on a structured prompt-rewriting template) into something like:

> A young adult Chinese woman in elaborate red hanfu with intricate gold-thread embroidery along the sleeves and collar, impeccable traditional makeup with a red floral forehead pattern (花钿), elaborate high bun adorned with golden phoenix headdress, red silk flowers, and beaded ornaments. She stands in a moonlit courtyard with ancient stone tiles and a single ginkgo tree in the background, soft-lit night atmosphere with paper lanterns providing warm practical lighting. Traditional Chinese aesthetic combined with cinematic depth of field, shot on 50mm lens, 1024×1024.

The PE applies **reasoning chains** to:

- Infer culturally appropriate details the user didn't specify (specific hanfu era, traditional accessories, makeup conventions)
- Suggest a complementary environment that fits the subject
- Pick lighting and atmosphere that match the cultural register
- Add camera/style language that gets the model into a specific output mode
- Avoid generic defaults by picking specific concrete choices

The result is exactly the kind of long, detailed, structured prompt Z-Image was trained to handle best.

---

## When to apply PE-style expansion inside the skill

When the user provides a short prompt (under ~30 words) and is using Z-Image-Turbo, the skill should generally expand it. There are two ways:

### Option A: Expand it yourself (recommended default)

The skill itself acts as the prompt enhancer. Take the user's seed idea, reason about what would make a complete scene, and write the long version directly. This is the default workflow this skill follows — most users want the finished, ready-to-use prompt.

### Option B: Note the PE template for power users

For users running offline pipelines who want repeatable PE behavior, point them to:

- Official PE template: <https://huggingface.co/spaces/Tongyi-MAI/Z-Image-Turbo/blob/main/pe.py>
- They can copy the system prompt from that file into any LLM (Claude, GPT, local Llama) to get repeatable enhancement before generation.

---

## The PE-style reasoning pattern (when expanding yourself)

When the user gives you a short prompt, walk through these questions internally before writing the expanded version:

### 1. Who is the subject, specifically?

Not just "a woman" — what age range, ethnicity (if visually relevant), build, distinguishing features?

User: "a girl in a forest"
Reasoned: "An adult woman in her mid-twenties, with shoulder-length wavy auburn hair and a light dusting of freckles, wearing a fitted moss-green canvas jacket"

### 2. What are they DOING right now?

Not standing — *doing*.

Reasoned: "mid-stride through a misty pine forest at dawn, breath visible in the cool air, eyes scanning the path ahead"

### 3. Where exactly is this happening?

Specific environment. Foreground, midground, background if relevant.

Reasoned: "A narrow dirt path winding between tall Douglas firs, fern undergrowth, a fallen log to one side, dappled morning light filtering through the upper canopy"

### 4. What's the light doing?

Direction + quality + source.

Reasoned: "Early morning side-light from a low sun, creating long horizontal shafts of warm light through the trees, with cool blue shadows pooling in the undergrowth"

### 5. What's the style anchor?

ONE specific direction. Photo? Painting? Concept art? Era?

Reasoned: "Cinematic film still in the documentary tradition, evocative of a Terrence Malick nature sequence"

### 6. What technical details add precision?

Lens, aspect ratio, color grade. Only if they serve the scene.

Reasoned: "Shot on a 35mm lens at f/2.8, slight Kodak Portra 400 color cast"

### 7. What's the mood / closing register?

One short phrase.

Reasoned: "Quiet pre-dawn solitude"

### 8. What cleanup constraints belong at the end?

For Turbo: `no text, no watermark, no logos, clean composition`. For base: in the negative prompt.

---

## Assembling the expanded prompt

Weave the answers together as flowing prose, not bullet points. Goal: 80–150 words for Turbo, 60–120 for base.

**Original:** "a girl in a forest"

**Expanded:**

> A wide medium shot of an adult woman in her mid-twenties walking mid-stride along a narrow dirt path through a misty Douglas fir forest at dawn, her shoulder-length wavy auburn hair lifted slightly by the cold morning air, wearing a fitted moss-green canvas jacket over a cream wool sweater, breath visible, eyes scanning the path ahead. The path winds between tall trunks with fern undergrowth and a single fallen log to one side, low-hanging mist softening the deeper trees into pale silhouettes. Early morning side-light from a low sun cuts through the canopy in long horizontal shafts of warm gold, while cool blue shadows pool in the undergrowth. Cinematic film still in the documentary tradition, shot on a 35mm lens at f/2.8 with slight Kodak Portra 400 color cast, quiet pre-dawn solitude, clean composition, no text or watermarks.

That's a working Z-Image-Turbo prompt produced by walking through the PE pattern.

---

## PE for short-but-text-heavy prompts

If the user's short prompt explicitly involves text — "a coffee shop sign that says 'Open Daily'" — the PE expansion should:

- Quote the user's text exactly as they wrote it (don't paraphrase it)
- Add the surrounding scene, lighting, style, and atmosphere
- Specify font style for the text (the user usually doesn't, but you should)
- Add placement details
- Add a cleanup clause if the user didn't specify "no additional text"

**Original:** "a coffee shop sign that says 'Open Daily'"

**Expanded:**

> A vintage corner coffee shop storefront at golden hour, weathered green-painted wood siding and a brass door handle catching the warm low sun. Centered above the door, a hand-painted wooden sign reads "Open Daily" in elegant cream-colored brush-style serif on a dark teal background, with a small ornamental coffee bean illustration to one side. Cobblestone sidewalk in the foreground, soft window reflections showing the warm interior, blurred passersby in the background. Cinematic film still, 35mm lens with shallow depth of field, nostalgic atmosphere, no additional signage or text visible.

---

## When NOT to expand

Some user prompts arrive already long and specific. Don't pile on more detail just for the sake of it.

Signs that the user has already done the work:

- Prompt is over 80 words
- Already includes specific subject, action, environment, and lighting
- Names a style anchor concretely
- Specifies camera language (lens, aperture, framing)

In these cases, leave the prompt mostly alone. Make small targeted improvements (e.g., adding a cleanup clause if missing, replacing one generic adjective with a specific one), but don't double the length when the user has clearly given you a finished prompt.

The skill's job is to help the user, not to demonstrate effort. A short, specific prompt that the user wrote intentionally short is better left alone than padded.

---

## PE-style expansion is the difference between Z-Image performance levels

Community benchmarks consistently show that Z-Image's output quality is heavily prompt-dependent. The same model with a short prompt produces mediocre output; the same model with a PE-expanded prompt produces flagship-quality output. This is by design — the model was trained on long structured captions, and you get out what you put in.

This is why the skill's default behavior is to apply PE-style expansion automatically when the user provides a short prompt: it's not optional polishing, it's necessary preprocessing to make Z-Image perform at its level.
