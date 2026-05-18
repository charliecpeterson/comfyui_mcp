# Anti-AI-Slop Levers for Flux

Even with prose, Flux can produce output that looks generically AI-generated. This file catalogues the specific "AI tells" that show up in Flux output and the prompt-side fixes for each. Apply these defensively during draft review.

The general principle: AI-slop output comes from prompts that are *abstract* (beautiful, stunning, epic) rather than *concrete* (the small chipped tooth, the coffee ring on the desk). Every fix in this file is some version of "trade abstraction for concrete detail."

---

## Tell #1: The Adjective Stack

The single most common AI-prompt mistake: stacking decorative adjectives at the front or end.

**Bad:**
> "a beautiful, stunning, gorgeous, professional, cinematic, ultra-detailed, 8k masterpiece of a woman"

**Why it's bad:** None of these words give Flux *visual* information. They cancel each other out and crowd the prompt's information budget.

**Fix:** Pick ONE strong style anchor. Replace the rest with concrete detail.

**Good:**
> "Fashion editorial photograph of a woman in her thirties with sun-freckled cheekbones, shot on Kodak Portra 400, 85mm at f/2."

The list of adjectives to delete on sight: *beautiful, stunning, gorgeous, breathtaking, epic, masterpiece, ultra-detailed, hyper-detailed, 8k, 4k, hdr, professional, high-quality, award-winning, masterful, intricate.*

---

## Tell #2: The "Epic Cinematic" Register

The most overused tone in AI image prompting. If everything is epic, nothing is. AI-output that screams "EPIC" looks instantly fake.

**Bad:**
> "Epic cinematic shot of a hero standing on a cliff, dramatic lighting, intense atmosphere, breathtaking landscape"

**Fix:** Match the register to the subject. Quiet scenes want quiet prose. Domestic scenes want domestic prose. Reserve the cinematic register for moments that actually warrant it, and even then, ground it in specifics.

**Good (quiet):**
> "A man at the edge of a granite outcrop in the last hour of daylight, hands in his jacket pockets, looking at something far enough away that he's stopped moving."

**Good (genuinely cinematic):**
> "Cinematic film still, wide shot from below the cliff edge, the figure tiny against a sky split half stormcloud and half late sun, 65mm large-format film, the kind of frame Hoyte van Hoytema would compose."

---

## Tell #3: The Doll-Perfect Face

AI defaults to symmetrical, blemish-free, lit-from-everywhere faces that look like a 3D-rendered dummy.

**Fix — sprinkle in one or two of these:**
- Asymmetry: "one eyebrow slightly higher than the other", "an old scar through the left brow", "uneven freckles across the bridge of the nose"
- Imperfections: "a small mole on the temple", "lips chapped at the corner", "the kind of tan that ends sharply at the shirt sleeve"
- Live human details: "a flyaway hair across the forehead", "lipstick worn off in the center", "the slight redness of someone just back from a walk"
- Caught-in-the-moment: "mid-blink", "halfway through saying something", "with her hand still on the cup she just set down"

One per face is enough. Stacking them past two starts to look like a checklist.

---

## Tell #4: Over-Detailed Backgrounds

AI defaults to over-rendered, fully-textured backgrounds where every object competes for attention. Real photography (and real painting) has hierarchy — one thing is sharp, the rest serves the subject.

**Fix:**
- Specify shallow depth of field: "f/2 background bokeh", "softly blurred background"
- Use compositional flatness: "against a simple plaster wall", "against a pale grey backdrop"
- Limit what's in the background: "the only object visible behind her is a single wooden chair" — naming one specific thing keeps Flux from freelancing five
- Embrace negative space: "with the rest of the frame empty"

If the scene *is* meant to have a busy environment, give Flux a hierarchy: name one foreground element, one midground, one background element. Don't let it freelance a full city of detail.

---

## Tell #5: Symmetrical Centered Composition

Flux's default composition is the most boring one: subject dead-center, equal margin on all sides. Real photographers use the rule of thirds, leading lines, off-center placement, and dynamic framing.

**Fix — name a specific framing:**
- "Subject in the right third of the frame, looking left into negative space"
- "Low angle, three-quarter view, shot from below the subject's shoulder line"
- "Dutch angle of roughly fifteen degrees"
- "Tight crop from the chest up, subject filling 80% of the frame"
- "Wide environmental shot, subject small in the lower third, sky filling the upper two-thirds"

The cinematography reference has more named framings. Pick one rather than letting Flux default.

---

## Tell #6: The "Cinematic, Atmospheric, Mood" Word Soup

Words like *cinematic, atmospheric, moody, ethereal, dreamy, magical, enchanting, mystical, otherworldly* are weak because they tell the model nothing concrete.

**Fix:** Replace each with the specific visual element that *produces* that mood.

| Word soup | Concrete replacement |
|---|---|
| "atmospheric" | "with fog low to the ground" / "with steam rising from grates" / "with light cutting through dust in the air" |
| "moody" | "lit by a single practical lamp" / "with the curtains half-drawn" / "in mostly shadow with a single rim of light" |
| "ethereal" | "with light particles drifting through the air" / "with everything slightly out of focus except her eyes" |
| "dreamy" | "with a faint haze softening the image" / "shot through a smeared lens" / "with pastel grading and lifted blacks" |
| "magical" | "with motes of warm light suspended in mid-air" / "with one impossible element rendered matter-of-factly" |
| "mystical" | "with smoke curling from a single source visible in the frame" / "with the only light from a held lantern" |
| "otherworldly" | name the specific thing that's wrong — "the sky is the wrong color of green" / "the shadows fall in the wrong direction" |

---

## Tell #7: AI Hand Disasters (Flux 1 specifically)

Flux 1 still has hand issues. Flux 2 mostly fixes them.

**On Flux 1:**
- Don't draw attention to hands unless they matter (avoid "hands prominent in frame", "holding object close to camera")
- If hands must be visible, give them a specific job: "hands wrapped around a mug", "one hand resting on the doorframe", "holding a thin paperback" — Flux does better with hands that have a clear purpose
- Crop creatively if hands aren't load-bearing: "shot from the chest up", "framed from behind"

**On Flux 2:** mostly not an issue. Describe normally.

---

## Tell #8: The "Professional Photography" Crutch

Adding "professional photography" or "high-end photography" as filler does nothing — Flux doesn't have a "make this look professional" knob. What you actually want is to name *what kind* of professional photography.

| Generic crutch | Specific replacement |
|---|---|
| "professional photography" | "fashion editorial photography in the style of Vogue" |
| "high-end photography" | "high-end product photography on white seamless with three-point softbox lighting" |
| "studio photograph" | "studio portrait against a slate grey backdrop, 85mm at f/2.8, butterfly lighting" |
| "commercial photo" | "commercial food photography, top-down composition, soft window light from the left" |
| "professional portrait" | "headshot for an actor's reel, neutral expression, soft fill from below, sharp on the eyes" |

---

## Tell #9: Lighting Without Direction

"Beautiful lighting" or "great lighting" tells Flux nothing. Light needs a **direction**, a **quality**, and ideally a **source**.

**Bad:** "Beautiful lighting"

**Good:** "Soft window light from the left, falling across her face and leaving the right side in gentle shadow, with one warm practical lamp visible in the background."

Three elements: where it comes from (window, left), what it does (falls across, leaves shadow), and what else is visible (warm lamp in background).

---

## Tell #10: Color Without Anchor

"Vibrant colors" or "rich colors" doesn't help. Either name the **palette** or name **specific colors** in **specific places**.

**Bad:** "Vibrant rich colorful palette"

**Good (palette named):** "Limited palette of forest green, brick red, and bone white" / "Teal-and-orange grading typical of contemporary blockbusters"

**Good (specific placements):** "Cyan neon reflected in puddles on dark asphalt, with one warm yellow window glowing on the upper floor"

---

## Tell #11: Action That's Actually Stillness

AI defaults to subjects standing slightly off-center, slightly turned, slightly smiling — all "slightly." It's the visual equivalent of corporate-speak.

**Fix:** verbs of actual action. The subject should be **mid-something**.

| "Slightly standing" | Actual action |
|---|---|
| "standing in a kitchen" | "stirring something on the stove without looking at it" |
| "looking out a window" | "leaning her forehead against the cool glass" |
| "in a forest" | "ducking under a low branch, eyes still on the path ahead" |
| "by a car" | "reaching into the open driver's window for something on the dash" |
| "in an office" | "halfway through highlighting a paragraph, pen capped between her teeth" |

The verb should be doing real work in the sentence.

---

## Tell #12: The "Default Pretty Woman"

AI's #1 default subject. Generic prompts produce: thin, young, conventionally attractive, white, smooth-skinned, often turned three-quarter to camera. If that's not what you want, specify.

**Fix:**
- Specify age range concretely: "in her forties", "early twenties", "around fifty"
- Specify body type concretely: "with a swimmer's broad shoulders", "with the wiry build of a long-distance runner", "tall and gangly", "compact and strong"
- Specify ethnicity / specific features: "with dark skin and shaved sides on her head", "with East Asian features and a beauty mark just below the eye", "Mediterranean complexion and a strong nose"
- Specify what *isn't* default-attractive: "with a face that's more interesting than beautiful", "with one front tooth slightly crooked"

This is doubly important for diverse subjects — Flux's defaults skew narrow, and specificity is what overcomes that bias.

---

## Quick checklist (run before returning a prompt)

- [ ] No words from the delete-on-sight list (beautiful, stunning, masterpiece, 8k, professional, ultra-detailed, hyper-detailed, breathtaking, epic)
- [ ] One named style anchor — not three
- [ ] Lighting has direction, quality, and (ideally) source
- [ ] Subject is mid-something, with a real verb
- [ ] At least one specific imperfection / live-human detail
- [ ] Background has hierarchy (or named flatness), not freelance detail
- [ ] Composition is named (rule of thirds, low angle, etc.), not default centered
- [ ] If "atmospheric/moody/ethereal" appears, replaced with concrete visual element
- [ ] Subject is specified beyond "default pretty"
