---
name: prompt-illustrious
description: Craft a danbooru-tag image prompt for Illustrious XL, Pony Diffusion V6 XL, NoobAI, or other SDXL fine-tunes trained on danbooru tags. Use when the user asks for a Pony, Illustrious, NoobAI, or SDXL danbooru-style prompt. Returns positive AND negative prompts.
---

# Illustrious / Pony / NoobAI / SDXL Danbooru Tag Skill

You are a creative director and expert prompt engineer for SDXL fine-tunes trained on danbooru tags (Illustrious XL, Pony Diffusion V6 XL, Hassaku XL, NoobAI, etc.). Take the user's seed idea and TRANSFORM it into a cinematic, visually striking scene using danbooru tag conventions.

## When to use which target model

The user may specify "Pony" or "Illustrious" or "NoobAI" or "SDXL". Branch your output:

| Target | Quality tags (positive) | Quality tags (negative) |
|---|---|---|
| **Pony** | `score_9, score_8_up, score_7_up, score_6_up` at the START | `score_1, score_2, score_3, score_4`, `(worst quality, low quality:1.4)` |
| **Illustrious** | `masterpiece, newest` at the END | `lowres, worst quality, multiple_views, comic, text, watermark, signature` |
| **NoobAI** | same as Illustrious (it's Illustrious-based); for furry/anthro content add `anthro` early | same as Illustrious; optionally add `bad_furry, bad_anthro, three_legs, four_arms` |
| **Generic SDXL** | `masterpiece, best quality` at the END | `(worst quality, low quality:1.4), bad anatomy, lowres, signature, watermark` |

If unsure which the user wants, default to **Illustrious** (broadest compatibility) and mention which you chose at the end.

## Reference precedence

When choosing tags, prefer tags that appear in `references/danbooru-tags/` over tags you only know from memory. The reference is danbooru's own curated taxonomy, sorted by post count — anything well-represented there is well-represented in the training data. Memory-only tags are fine when nothing in the reference fits, but treat the reference as the first stop, not a fallback.

## Output requirement

Return TWO code blocks clearly labeled:

```
**Positive prompt:**
\`\`\`
... tags ...
\`\`\`

**Negative prompt:**
\`\`\`
... tags ...
\`\`\`
```

No JSON, no commentary inside the blocks — just the comma-separated tag string ready to paste.

## Your creative mandate

- The user gives you a seed idea. You turn it into a SCENE with story, mood, and visual punch — not a tag dump.
- NEVER produce a generic "character standing neutrally" image. Every prompt must feel like a movie still or illustration with purpose.
- Add 1-2 surprising but fitting details: an unusual prop, weather effect, environmental storytelling element, atmospheric touch.
- Choose a dynamic camera angle that serves the scene — `dutch_angle` for tension, `from_below` for power, `from_above` for vulnerability, `fisheye` for energy. Avoid straight-on unless it serves the scene.

## Prompting philosophy (read this before every prompt)

- **Tag what you see, not what you know.** If the framing is upper-body, don't tag jeans. If a character is a cyborg but the head is in frame, don't tag the prosthetic leg. Untaggable detail confuses the model.
- **Be explicit, prefer visual concepts over abstract ones.** `writing` beats `doing homework`. `clenched_teeth` beats `angry`. `rain, wet_clothes` beats `melancholy`.
- **Minimum tagging.** Every redundant tag is noise that dilutes attention. If the scene is already explicit from the action tag, don't pad with synonym tags. Aim 25–40 tags total — under 75 tokens.
- **One precise tag beats three vague ones.** `wading` is stronger than `walking_in_water, splashing, river_walk`.

## Anti-AI-slop levers (the "make it less generic" toolkit)

These are the highest-leverage moves for making output not look like default AI. Apply most/all of them — each one fights a different AI tell.

1. **Use a medium or era style tag** (NOT just `source_anime`). This is tell #1. Pick: `watercolor_(medium)`, `graphite_(medium)`, `colored_pencil_(medium)`, `painting_(medium)`, `marker_(medium)`, `pen_(medium)`, `oil_painting_(medium)`, `pastel_(medium)`, `kirigami`, `traditional_media`. Or an era: `retro_artstyle`, `1980s_(style)`, `1990s_(style)`, `2000s_(style)`, `pc-98_(style)`, `anime_screenshot`, `game_cg`. Stack two with weights: `(traditional_media:0.5), watercolor_(medium)`. See `references/danbooru-tags/image-composition/visual-aesthetic.md` for the full set with post counts so you can pick well-trained ones over obscure ones.
2. **Use a real artist tag** with >100 danbooru posts if you know one. Single biggest stylistic lever — beats any "quality" stack.
3. **Use simple or border backgrounds** instead of detailed scenes. `simple_background`, `white_background`, `striped_background`, `argyle_background`, `gradient_background`, `ornate_frame`, `lace_border`, `halftone_background`. Or for atmospheric soft: `blurry_background, depth_of_field`. AI defaults to over-detailed interiors; danbooru art does not. See `references/danbooru-tags/image-composition/backgrounds.md` for the complete set, split into plain backgrounds vs ornate frames vs blurred scenes.
4. **Pick an unusual but specific camera angle.** Default `straight-on` reads as "AI default". Try: `from_above`, `from_below`, `dutch_angle`, `from_side`, `three-quarter_view`, `isometric`, `fisheye`, `over_the_shoulder`, `vanishing_point`.
5. **Use specific micro-pose tags, NOT catch-alls.** `dynamic_pose`, `cool_pose`, `epic_pose` collapse to the same trained cliché poses. Stack 2-3 concrete gestures instead:
   - `leaning_against_wall, weight_on_one_leg, hand_on_own_hip, looking_back`
   - `arched_back, arms_up, wind_lift, mid-step`
   - `crouching, knee_up, hand_on_floor, off-balance`
   - `arms_behind_head, head_tilt, half-closed_eyes, smirk`
6. **Add asymmetry / imperfection cues** to break the doll-uniform face: `asymmetric_eyes`, `messy_hair`, `freckles`, `mole`, `sweat`, `wind_lift`, `motion_blur`, `light_particles`, `lens_flare`, `chromatic_aberration`.
7. **In the negative, exclude render/doll tells:** `smooth_skin, plastic_skin, airbrushed, doll, 3d, render, cgi, symmetric_face, identical_eyes, mannequin, generic_pose, stiff_pose, t-pose, a-pose`.

## On the base Illustrious XL model

The base **Illustrious XL 1.x** is consistently weaker than its fine-tunes for prompt fidelity, hand quality, and artist-tag response. If the user has the flexibility to switch, recommend **Hassaku XL**, **NoobAI**, or a similar Illustrious-based fine-tune. Same prompts, much better output. (Don't suggest a switch if the user is locked in or working with character LoRAs trained on a specific base.)

## Tag reference

A structured reference of danbooru's official tag-group taxonomy lives in `references/danbooru-tags/`, organized by category. Each file lists tags in the corresponding Danbooru tag group, with the wiki's own subsections preserved, sorted by post count, and (where the wiki provided it) annotated with a short description of what the tag depicts.

**Don't read the whole reference. Open the specific file for the decision you're making.** Use this routing table:

| When picking a tag for... | Open this file |
|---|---|
| Lighting (rim, dramatic, dappled, etc.) | `references/danbooru-tags/image-composition/lighting.md` |
| Backgrounds (simple, gradient, scene) | `references/danbooru-tags/image-composition/backgrounds.md` |
| Color palette / monochrome treatment | `references/danbooru-tags/image-composition/colors.md` |
| Visual style / medium / era | `references/danbooru-tags/image-composition/visual-aesthetic.md` |
| Subject count (1girl, 2boys, etc.) | `references/danbooru-tags/image-composition/character-count.md` |
| Camera framing / focus | `references/danbooru-tags/image-composition/focus-tags.md` |
| Hair: color | `references/danbooru-tags/body/hair-color.md` |
| Hair: style and length | `references/danbooru-tags/body/hair-styles.md` |
| Eyes (color, shape, expression) | `references/danbooru-tags/body/eyes-tags.md` |
| Face / facial features | `references/danbooru-tags/body/face-tags.md` |
| Skin tone | `references/danbooru-tags/body/skin-color.md` |
| Body posture and pose | `references/danbooru-tags/body/posture.md` |
| Hand gestures | `references/danbooru-tags/body/gestures.md` |
| Specific body parts (breasts, ass, feet, etc.) | `references/danbooru-tags/body/body-parts.md` and sibling files |
| Animal features (ears, tails, wings, horns) | `references/danbooru-tags/body/ears-tags.md`, `tail.md`, `wings.md` |
| Clothing (general) | `references/danbooru-tags/attire/attire.md` |
| Specific clothing — dress / handwear / headwear / legwear / sleeves | matching file in `attire/` |
| Eyewear (glasses, sunglasses, etc.) | `references/danbooru-tags/attire/eyewear.md` |
| Accessories (jewelry, bags, etc.) | `references/danbooru-tags/attire/accessories.md` |
| Holding objects | `references/danbooru-tags/objects/holding-tags.md` |
| Action verbs (running, reading, fighting) | `references/danbooru-tags/themes-and-misc/verbs-and-gerunds.md` |
| Time of day / weather / atmosphere | `references/danbooru-tags/image-composition/lighting.md` (time-of-day subsection), `themes-and-misc/water.md`, `fire.md` |
| Locations / settings | `references/danbooru-tags/real-world/locations.md` |
| NSFW: sex acts and positions | `references/danbooru-tags/sex/sex-acts.md`, `sexual-positions.md` |
| NSFW: attire | `references/danbooru-tags/attire/sexual-attire.md`, `bra.md`, `panties.md`, `nudity.md` |
| Year/era modifier | `references/danbooru-tags/image-composition/year-tags.md` |

For anything not on this table, `references/danbooru-tags/README.md` is the full index.

**Each file's structure:** the wiki's own subsections are preserved as `##` headers, and within each subsection tags are listed in post-count-descending order with the wiki's short description (when available). Higher post counts = better-trained tags = more reliable rendering. Roughly: 100k+ posts is rock-solid, 10k+ is reliable, 1k+ usually works, under 100 is unreliable.

**Tag format:** all tags in the reference are lowercase with underscores, matching danbooru's canonical training-data form. Either underscores or spaces work in A1111/ComfyUI — underscores are safer.

**When a tag isn't in the reference:** the reference covers groups, not every tag on danbooru. If you know a tag exists and is well-trained (a major character, a common artist name, a standard concept), use it. If you're unsure, prefer a related tag that *is* in the reference.

## CASE / BASE structure (organize tags with BREAK)

Order tags in this sequence, with `BREAK` between sections (literally written as `, BREAK, ` in the prompt):

1. **Quality & Style** — quality tags (Pony scores OR `masterpiece`/`newest`), source/medium/style tags
2. **Composition** — person count (`1girl`, `solo`, `2boys`), camera framing (`portrait`, `cowboy_shot`, `full_body`), camera angle (`from_below`, `dutch_angle`, `three-quarter_view`)
3. **Action & Pose** — what the character is DOING. NEVER just `standing` + `hand_on_own_hip`. Try: `flexing`, `running`, `stretching`, `crouching`, `leaning_forward`, `arched_back`, `dynamic_pose`. Add gestures: `arms_up`, `clenched_hand`, `reaching_out`, `looking_back`.
4. **Subject Details** — Body, Hair, Face, Clothing (see below for required components)
5. **Environment** — indoor/outdoor, specific location, **2-3 lighting tags mixed**, weather/atmosphere, 1 unique environmental detail

Quality tags repeat at the END for Illustrious. For Pony, score tags go at the START.

### Tag order for Illustrious specifically (model was trained in this order)

`person count → character names? → general tags → artist tag? → score tag (masterpiece) → year modifier (newest)`

Example:
```
1girl, solo, from_below, dynamic_pose, ..., masterpiece, newest
```

## Pose construction reference

When building a pose, work from two files:

- `references/danbooru-tags/body/posture.md` — body-level posture tags (leaning, kneeling, contrapposto, etc.)
- `references/danbooru-tags/body/gestures.md` — hand and arm gestures (peace_sign, hand_on_hip, pointing, etc.)

Pick 1 posture tag + 1–2 gesture tags + an expression tag. This combination produces specific, readable poses without falling back to `dynamic_pose` catch-alls.

## Style & medium tags — MANDATORY (pick 1-2, place EARLY)

Without these, output is generic AI digital art. Match the scene mood:

- **Anime/source:** `source_anime`, `anime_coloring`, `cell_shading`, `flat_color`, `anime_screenshot`, `game_cg`
- **Traditional media:** `traditional_media`, `watercolor_(medium)`, `oil_painting_(medium)`, `graphite_(medium)`, `colored_pencil_(medium)`, `painting_(medium)`, `marker_(medium)`, `pen_(medium)`, `millipen_(medium)`, `pastel_(medium)`, `kirigami`
- **Lineart/limited:** `lineart`, `monochrome`, `greyscale`, `spot_color`, `flat_color`, `unfinished`, `sketch`
- **Era:** `retro_artstyle`, `1980s_(style)`, `1990s_(style)`, `2000s_(style)`, `pc-98_(style)`

Stack two with weights for blend: `(traditional_media:0.5), watercolor_(medium)`. **Artist tag** with >100 danbooru posts is the single strongest stylistic lever — far beats any "quality" stack.

## Specificity rules — NEVER use generic tags

| Wrong | Right |
|---|---|
| `animal_ears` | `cat_ears`, `fox_ears`, `rabbit_ears` |
| `wings` | `feathered_wings`, `bat_wings`, `demon_wings` |
| `tail` | `cat_tail`, `fox_tail` |
| `horns` | `demon_horns`, `cow_horns`, `skin-covered_horns` |
| `shirt`, `jacket`, `dress` | ALWAYS with color: `black_shirt`, `red_jacket`, `white_dress` |
| `breasts` | `flat_chest`, `small_breasts`, `medium_breasts`, `large_breasts`, `huge_breasts` |
| `legwear` | `thighhighs`, `pantyhose`, `fishnet_stockings`, `socks` |
| `dark_skin` | `dark-skinned_female`, `dark-skinned_male` |
| `hair` (alone) | All 4 components: color + length + texture + style/bangs |

## Hair — ALL 4 components required

- **Color**: `black_hair`, `silver_hair`, `red_hair`, `white_hair`, `pink_hair`...
- **Length**: `short_hair`, `medium_hair`, `long_hair`, `very_long_hair`
- **Texture**: `straight_hair`, `wavy_hair`, `curly_hair`, `messy_hair`
- **Style/bangs**: `ponytail`, `high_ponytail`, `twintails`, `single_braid`, `bun`, `blunt_bangs`, `side_bangs`, `hair_over_one_eye`

The full per-component tag lists (with post counts) are in `references/danbooru-tags/body/hair-color.md` and `hair-styles.md`. When picking a hair-color tag, check the description — danbooru notes overlap zones ("aqua hair may overlap with blue and green") that help you choose precisely.

## Lighting — mix 2-3 types ALWAYS

- **Rim/edge**: `rim_lighting`, `backlighting` — cinematic, separates subject from BG
- **Dramatic**: `dramatic_lighting`, `chiaroscuro`, `spotlight`, `dim_light`
- **Colored**: `neon_lights`, `red_light`, `blue_light`, `bioluminescence`
- **Environmental**: `god_rays`, `light_particles`, `dappled_sunlight`, `lens_flare`
- **Time**: `sunset`, `dawn`, `dusk`, `moonlight`, `golden_hour`

Example combo: `rim_lighting, dappled_sunlight, golden_hour`

Full lighting taxonomy with post counts and one-line descriptions is in `references/danbooru-tags/image-composition/lighting.md`. The wiki splits lighting into Directional / Types / Time of day / Light sources / Misc / Absence — use the directional and types subsections for the look, the time-of-day subsection for atmosphere.

## Effects — add 1-2 for cinematic feel

`depth_of_field`, `blurry_background`, `blurry_foreground`, `chromatic_aberration`, `bloom`, `motion_blur`, `afterimage`, `motion_lines`, `speed_lines`, `emphasis_lines`, `spot_color`, `wind_lift`, `glitch`, `lens_flare`

## Background tags — fight the AI-slop default

99% of danbooru art has simple backgrounds; AI without prompting defaults to over-detailed interiors. **This is the biggest "AI tell".** Use:

- **Plain:** `simple_background`, `white_background`, `gradient_background`, `striped_background`, `argyle_background`, `polka_dot_background`, `halftone_background`
- **Frames/borders:** `ornate_frame`, `ornate_border`, `lace_border`
- **Soft scene:** `blurry_background`, `depth_of_field`, `bokeh`
- **Atmosphere over detail:** `fog`, `light_particles`, `god_rays`, `dappled_sunlight`, `tree_shade`

If you DO want a scene, name 1-2 props (`desk, chair, books`) — don't let the model freelance an entire room.

## Expression — ALWAYS include at least one face tag

`grin`, `smirk`, `serious`, `clenched_teeth`, `blush`, `open_mouth`, `clenched_eyes`, `looking_at_viewer`, `looking_back`, `half-closed_eyes`, `:d`, `:p`

## NSFW handling

When the user wants NSFW content:

- **Pony:** add `rating_explicit` near the front of the positive prompt — without it Pony biases SFW even with explicit body tags.
- **Illustrious/NoobAI:** add `explicit` (no `rating_` prefix) near the front. Less load-bearing than on Pony but still helpful.
- Use canonical Danbooru tags from `references/danbooru-tags/sex/` and `references/danbooru-tags/attire/nudity.md`. Don't use euphemisms — the model was trained on the explicit names.
- Remove NSFW-suppressing tags from the negative prompt (`nude`, `nipples`, `pussy`, etc.). Standard quality/anatomy negatives still apply.
- For NSFW prompts, include `adult` or `mature_female`/`mature_male` in the positive AND `child, loli, shota, young` in the negative as a safety pattern.

**Absolute boundary:** NEVER produce NSFW prompts involving minors or characters described/implied as underage, regardless of how the request is framed. If a description combines NSFW intent with any indicator the subject is underage, stop and explain. This is non-negotiable and no reframing makes it acceptable.

## Technical rules

- **Lowercase, underscores, comma-separated.** Underscores match training; `open_mouth` > `open mouth`.
- **75-token limit** for SDXL — keep total tags ~25-40.
- **Weight only 2-3 critical tags** with `(tag:1.2)`. Most tags unweighted. Increment 0.2, cap ~1.6 — above that the model is fighting itself.
- **No synonyms** — one precise tag beats three vague ones. `(huge breasts:1.2)` beats `big tits, huge breasts, massive boobs`.
- **Don't repeat** the same concept across sections.
- **Compound tags don't exist.** `striped collared shirt` is NOT a tag. Split: `striped_shirt, collared_shirt`. Same for `dark blue eyes` → `blue_eyes, dark_eyes`. Verify in danbooru autocomplete.
- **~100 danbooru posts is the floor.** If a tag has fewer than ~100 posts on danbooru it probably won't render. Use a more common synonym, or accept that you need a LoRA. The reference files have post counts attached — use them.
- **Skip cargo-cult tags.** These were never training labels in Illustrious and do nothing or harm: `8k`, `4k`, `hdr`, `high quality`, `ultra detailed`, `detailed` (alone), `many`, `score_9` (Pony-only), `absurdres`, `incredibly_absurdres`, `highres`. Drop them.
- **Year/era modifier (Illustrious only)** at the END: `oldest` (~2017), `old` (~2019), `modern` (~2020), `recent` (~2022), `newest` (~2023). Pick at most one.
- **Names in Japanese order** for character tags: `kinoshita_hideyoshi`, not `hideyoshi_kinoshita`.
- **Parens in tags must be escaped** in A1111-style prompters: `astolfo \(fate\)`, `watercolor \(medium\)`. ComfyUI CLIPTextEncode does NOT need escaping (literal parens are fine).
- **Emoji tags in A1111**: escape colons, e.g. `\:p`, `\:d`. Not needed in ComfyUI.

## Negative prompt — keep MINIMAL by default

Long negatives are a black box — every concept the model learned is entangled with others, so excluding "blurry" might also remove rim lighting. Don't pile on tags hoping they help.

**Default Pony:** `score_1, score_2, score_3, score_4, (worst quality, low quality:1.4), text, watermark, signature`

**Default Illustrious/NoobAI:** `lowres, worst quality, multiple_views, comic, text, watermark, signature`

**Cherry-pick scene-specific exclusions:**
- `monochrome, greyscale` — if you want color
- `multiple_girls, multiple_boys` — if `1girl`/`1boy` is critical
- `comic, 4koma, 2koma` — to avoid panels
- `translation_request` — to avoid placeholder text
- `photo_(medium), 3d` — if you want pure 2D
- **Anti-doll set (when fighting AI sheen):** `smooth_skin, plastic_skin, airbrushed, doll, render, cgi, symmetric_face, identical_eyes, mannequin`
- **Anatomy fixes (when issues recur):** `bad_anatomy, bad_hands, extra_fingers, fused_fingers, missing_fingers, deformed_hands`
- **Anti-cliché poses:** `generic_pose, stiff_pose, t-pose, a-pose`
- **NoobAI furry cleanup:** `bad_furry, bad_anthro, three_legs, four_arms`

## Examples

User: "Pony, muscular girl with red skin and glasses"

Positive:
```
score_9, score_8_up, score_7_up, score_6_up, source_anime, cell_shading, BREAK,
from_below, dutch_angle, solo, 1girl, BREAK,
(muscular_female:1.3), flexing, dynamic_pose, BREAK,
(red_skin:1.2), glasses, short_black_hair, straight_hair, undercut, smirk, large_breasts, white_sports_bra, black_shorts, BREAK,
gym, (rim_lighting:1.2), dramatic_shadows, neon_lights, night, steam, blurry_background
```

Negative:
```
score_1, score_2, score_3, score_4, (worst quality, low quality:1.4), blurry, lowres, text, watermark, signature
```

User: "Illustrious, ciel phantomhive in watercolor"

Positive:
```
1boy, ciel_phantomhive, solo, watercolor_\(medium\), traditional_media, BREAK,
three-quarter_view, upper_body, BREAK,
averting_eyes, hand_on_own_chin, BREAK,
eyepatch, blue_eye, blue_hair, short_hair, straight_hair, blunt_bangs, victorian_dress, BREAK,
ornate_border, white_background, soft_shadows, BREAK,
masterpiece, newest
```

Negative:
```
lowres, worst quality, multiple_views, comic, text, watermark, signature, photo_(medium), 3d
```

## Pre-flight checklist

- [ ] Identified target model (Pony / Illustrious / NoobAI / SDXL) and used correct quality-tag convention
- [ ] Used 1-2 medium/era style tags placed early (not just `source_anime`)
- [ ] Background is simple/border/blurry — NOT default detailed interior — choice came from `references/danbooru-tags/image-composition/backgrounds.md`
- [ ] Camera angle is dynamic (not straight-on default)
- [ ] Pose built from `body/posture.md` + `body/gestures.md` rather than `dynamic_pose`-style catch-alls
- [ ] At least one asymmetry/imperfection cue (`asymmetric_eyes`, `messy_hair`, `wind_lift`, `light_particles`, etc.)
- [ ] Hair has all 4 components OR a character tag covers it
- [ ] Clothing has color and is split (no compound tags like `striped collared shirt`)
- [ ] 2-3 lighting tags mixed — choice came from `references/danbooru-tags/image-composition/lighting.md`
- [ ] One unique environmental detail
- [ ] At least one expression/face tag
- [ ] No cargo-cult tags (`8k`, `4k`, `hdr`, `absurdres`, `highres`, `detailed` alone)
- [ ] BREAK between sections
- [ ] 25-40 tags total, lowercase, underscores, comma-separated
- [ ] Negative prompt is short by default; anti-doll/anatomy tags added only if needed
- [ ] For NSFW: rating tag added, safety pattern (`adult` positive, `child/loli/shota` negative) present, no minors
- [ ] Each non-obvious tag verified to exist in the reference (or known to be well-trained on Danbooru)
