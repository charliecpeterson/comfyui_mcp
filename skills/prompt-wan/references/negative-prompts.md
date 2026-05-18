# Negative Prompts for Wan Video

Negative prompts are load-bearing on Wan, not optional polish. The most common Wan failure modes — morphing faces, warping subjects, identity drift across frames, jittery motion — are partially prevented by good negative prompts. This file catalogues the standard negative patterns by use case.

The general rule: keep negatives relatively short (10–20 tags). Long negatives entangle with positive concepts in unpredictable ways. The defaults below are tuned to prevent the most-common artifacts without crippling intentional motion or style.

---

## The two universal defaults

### Universal I2V negative (use this as the starting point for ALL image-to-video work)

```
morphing, warping, distortion, face deformation, eye distortion, identity drift, changing facial features, flickering, jittering, sudden changes, inconsistent lighting, color shifting, scale changes, new elements appearing, compositional changes, bad anatomy, extra limbs, ghosting, frame interpolation artifacts
```

**Why each is included:**

- **morphing / warping / distortion** — the #1 I2V failure mode, where subjects' shapes shift unnaturally between frames
- **face deformation / eye distortion / changing facial features** — identity drift, where the subject stops looking like themselves
- **identity drift** — direct generalization of the above; useful as a catch-all
- **flickering / jittering / sudden changes** — temporal inconsistency
- **inconsistent lighting / color shifting** — lighting drift across frames
- **scale changes** — subject getting larger or smaller for no compositional reason
- **new elements appearing** — Wan inventing objects that weren't in the source image
- **compositional changes** — framing drift
- **bad anatomy / extra limbs** — generic anatomy failures
- **ghosting / frame interpolation artifacts** — visible blending between frames

### Universal T2V negative (starting point for text-to-video)

```
bright colors, overexposed, static, blurred details, subtitles, watermark, jpeg artifacts, low quality, ugly, deformed, malformed limbs, extra fingers, poorly drawn hands, poorly drawn faces, cluttered background, still picture, motion smearing
```

**Why each is included:**

- **bright colors / overexposed** — Wan's default sometimes produces washed-out output; these push toward proper exposure
- **static / still picture** — pushes Wan toward generating motion when prompt asks for it (counterintuitive but effective)
- **blurred details / jpeg artifacts / low quality** — generic quality cleanup
- **subtitles / watermark** — Wan sometimes generates fake subtitles or burnt-in watermarks from training data
- **deformed / malformed limbs / extra fingers** — anatomy
- **poorly drawn hands / poorly drawn faces** — Wan 2.1/2.2 hand quality is its weakest area
- **cluttered background** — pushes toward cleaner composition
- **motion smearing** — when motion blur becomes excessive

---

## Targeted additions by subject

Layer these onto the universal defaults when the subject specifically warrants them.

### Portraits / faces

Add:
```
eye distortion, face morphing, changing facial features, asymmetric face shifting, mouth deformation, dental issues, identity inconsistency, gaze shifting unnaturally
```

Faces are Wan's biggest identity-drift concern. These additions specifically protect facial features across frames.

### Landscapes / horizons

Add:
```
horizon warping, ground tilting, scale inconsistency, perspective drift, sky banding, ground morphing
```

Landscape shots are vulnerable to subtle geometric drift that's especially visible in straight horizon lines.

### Products / commercial work

Add:
```
label distortion, text warping, surface morphing, product deformation, color shift on product, branding artifacts, logo distortion
```

Critical for branded work — protects the product's identity and any visible text/branding.

### Action / motion scenes

Add:
```
motion blur artifacts, jittery motion, frame interpolation artifacts, choppy motion, unnatural pacing, motion ghosting
```

Action scenes need clean motion; these prevent the most common motion-quality failures.

### Animals / pets

Add:
```
species drift, anatomy morphing, fur warping, eye distortion, leg count errors, tail distortion
```

Animals are particularly prone to anatomy drift on Wan.

### Architecture / interiors

Add:
```
geometric distortion, perspective warping, wall morphing, ceiling tilting, structural drift, window warping
```

Interior shots are vulnerable to subtle geometric drift, especially when the camera moves.

---

## Targeted additions by style

### For photorealistic output (avoid stylization drift)

Add:
```
cartoon, anime, illustration, painting, drawing, stylized, abstract, sketch
```

### For animated/stylized output (avoid photorealistic drift)

Add:
```
photorealistic, photo, photograph, 3d render, realistic textures
```

### For monochrome work (avoid color creep)

Add:
```
color, saturated, color tinting, accidental color, partial coloring
```

### For specific period work (avoid anachronism)

Add (for vintage period work):
```
modern objects, modern technology, smartphone, modern clothing, contemporary signage, digital displays
```

---

## What NOT to put in Wan negatives

Some things sound like good negative-prompt material but actually hurt your output:

### ❌ Don't negate the style you want

If you want `cinematic` in the positive, don't put `boring` in the negative — that's not how diffusion negatives work. The model learns concepts; "boring" isn't a concept that means "not cinematic."

### ❌ Don't pile on positive concepts as negatives

`beautiful, stunning, amazing` in the negative doesn't make things less beautiful — those words don't have negative-prompt meaning. Save the prompt budget.

### ❌ Don't negate everything you can think of

Long negatives entangle. If you put `blur` in the negative, you may inadvertently remove intentional motion blur or depth-of-field. Use targeted negatives, not blanket ones.

### ❌ Don't use 2D-image negatives unchanged

Image-model negatives like `text, watermark, signature` are fine on Wan, but heavy anatomy negatives like `(bad anatomy:1.4), (worst quality:1.4)` with image-style weighting brackets work less well on Wan than on SDXL/Pony. Wan uses plain comma-separated tags without weight syntax.

### ❌ Don't negate intentional artistic choices

If you want handheld feel, don't put `handheld, jittery, unstable` in the negative. Match negatives to what you actually want to prevent.

---

## Variant-specific notes

### Wan 2.1

Slightly more prone to flickering and identity drift than later versions. Use the full universal I2V default; consider adding `temporal inconsistency, frame discontinuity` for tough cases.

### Wan 2.2

Better temporal coherence thanks to the MoE architecture. The universal defaults are typically sufficient. Don't over-negate — let the MoE do its job.

### Wan 2.5

Most refined I2V quality in the family. Sometimes you can shorten the negative to just `morphing, warping, distortion, face deformation, identity drift, flickering, new elements appearing` and still get clean output.

### Wan 2.6 / 2.7

These models follow structured prompts better, so the negative becomes less load-bearing. You can often skip targeted additions and just use the universals. Multi-shot work benefits from adding `identity drift between shots, wardrobe changes between shots, lighting discontinuity between cuts`.

### Wan 2.2-Fun-Control

When using a control conditioning input (Canny, Depth, Pose, MLSD, trajectory), the negative should NOT contradict the control signal. If you're using a pose control, don't put `bad pose, t-pose, generic pose` in the negative — let the control handle pose; just negate quality/identity issues.

### Wan 2.2-Animate

For motion transfer specifically, focus the negative on the *transferred* identity rather than the *source* motion: `identity drift, character morphing, wardrobe changes, face inconsistency` are more valuable than motion-quality negatives, because the motion is coming from the reference video.

---

## Quick reference: what to layer when

| Subject type | Add to universal default |
|---|---|
| Portrait or close-up of a face | `eye distortion, face morphing, changing facial features` |
| Wide landscape | `horizon warping, ground tilting, perspective drift` |
| Product or branded item | `label distortion, text warping, surface morphing` |
| Action / motion-heavy | `motion blur artifacts, jittery motion, choppy motion` |
| Animal | `species drift, anatomy morphing, fur warping` |
| Architecture / interior | `geometric distortion, perspective warping, wall morphing` |
| Photoreal target | `cartoon, anime, illustration, stylized` |
| Stylized target | `photorealistic, 3d render, realistic textures` |
| Period / vintage | `modern objects, modern technology, smartphone, contemporary signage` |
| Multi-shot 2.6/2.7 | `identity drift between shots, wardrobe changes between shots, lighting discontinuity` |

---

## Sanity check before returning

- Did you start from the universal default? (Don't reinvent the wheel)
- Did you add ONE category of targeted additions, not three?
- Did you avoid negating concepts you want in the positive?
- Is the total length under ~25 tags? (Longer entangles)
- Did you skip artistic-choice negatives that conflict with intentional style?

If yes to all five, you have a clean Wan negative.
