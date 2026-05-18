# Danbooru tag-group extractor

Pulls Danbooru's official tag-group taxonomy from their wiki API and writes
out a structured set of Markdown files — one per tag group, organized by
top-level category, with the wiki's own subsections preserved and post counts
attached to every tag.

The output is designed to drop into a skill's `references/` folder so the
prompt-construction LLM has a clean, navigable reference for tag choices.

## Why this exists

Danbooru maintains a hand-curated taxonomy at
<https://danbooru.donmai.us/wiki_pages/tag_groups>. It groups general tags
into categories like Lighting, Posture, Hair, Eyewear, etc., and within each
group it further splits into subsections (Lighting → Directional / Types /
Time of day / Light sources / Misc / Absence of light).

This is the right structure for a prompting reference: when the LLM is
picking a lighting tag, it can open the lighting page and scan a focused
list rather than searching a flat dump of 200k tags.

## Install

Requires Python 3.10+ and `requests`.

```bash
pip install requests
```

No Danbooru account or API key needed for read access.

## Use

Basic run, writes everything to `./refs`:

```bash
python extract_danbooru_tag_groups.py --out ./refs
```

Filter out tags with fewer than 100 posts (matches the prompting-floor rule
in the prompt-illustrious skill):

```bash
python extract_danbooru_tag_groups.py --out ./refs --min-posts 100
```

Pull only specific top-level categories:

```bash
python extract_danbooru_tag_groups.py --out ./refs --only body attire image-composition
```

Dry-run to see what would be extracted without writing files:

```bash
python extract_danbooru_tag_groups.py --out ./refs --dry-run
```

Available top-level categories (`--only` accepts any of these):

- `image-composition` — lighting, backgrounds, colors, focus, visual aesthetic, etc.
- `body` — hair, eyes, face, posture, gestures, hands, feet, etc.
- `attire` — accessories, dress, handwear, headwear, legwear, eyewear, etc.
- `sex` — sex acts, positions, BDSM
- `objects` — holding tags, piercings, sex objects, etc.
- `creatures` — birds, cats, dogs, legendary creatures
- `plants` — flowers
- `games` — board games, sports, video games
- `real-world` — companies, jobs, locations, history, etc.
- `themes-and-misc` — dances, food, fire, water, theme, verbs and gerunds, etc.
- `meta` — metatags, drawing software (usually not useful for prompting)

For typical prompt-construction use, the high-value categories are
`image-composition`, `body`, `attire`, and `themes-and-misc`.

## Runtime

The script rate-limits itself to one request per second by default. A full
extraction of all ~80 tag groups takes roughly 5–10 minutes depending on how
many subpages each one references. You can lower the delay with `--delay 0.5`
if you're in a hurry, but stay above Danbooru's posted limit of 10 req/sec.

## Output shape

```
refs/
├── README.md                 # auto-generated index
├── image-composition/
│   ├── lighting.md
│   ├── backgrounds.md
│   ├── colors.md
│   ├── visual-aesthetic.md
│   └── ...
├── body/
│   ├── hair.md
│   ├── hair-color.md
│   ├── hair-styles.md
│   ├── eyes-tags.md
│   ├── posture.md
│   ├── gestures.md
│   └── ...
├── attire/
│   └── ...
└── ...
```

A single tag-group file looks like:

```markdown
# Lighting

## Directional
- `backlighting` (45,231 posts) — Light comes from behind the subject making a luminous contour
- `sidelighting` (12,889 posts) — Light comes from the left or right side
- `overlighting` (8,104 posts) — Light comes from above usually making the face and torso shaded
- `underlighting` (3,221 posts) — Light comes from below, typically to create an ominous effect

## Types
- `bloom` (15,447 posts) — Bright areas that blur with surrounding areas
- `dim lighting` (28,556 posts) — For dimly lit posts
- `dappled sunlight` (12,448 posts) — Sunlight seen through the shadow cast by tree leaves
- ...
```

Tags within each subsection are sorted by post count descending, so the
most-trained-on (and therefore most-reliable) tags surface first.

## Limitations and caveats

- The category structure is hard-coded in `CATEGORY_STRUCTURE` at the top of
  the script, mirroring Danbooru's current `tag_groups` page. If Danbooru
  reorganizes (rare, but it happens) the hard-coded list will drift. Edit it
  there.
- Some entries on Danbooru's master page are plain wiki pages rather than
  `tag_group:*` pages (e.g. `injury`, `swimsuit`, `eyebrows`). The script
  falls back to the unprefixed name when the prefixed version 404s.
- The DText parser is intentionally conservative: it skips wiki links that
  look like external references, help pages, or other tag-groups (which are
  followed separately). Edge cases may miss a tag or two — if you spot one,
  it's usually because the wiki page formats it unusually.
- Post counts are a snapshot at extraction time. They'll drift; re-run the
  script periodically if you care about current counts.
- The `--min-posts` flag filters at output time. Setting it to 100 drops most
  of the long tail; setting it to 1000 gives you a focused "common tags only"
  reference.

## Re-running

The script is idempotent — running it again overwrites previous output. There
is no caching, so a re-run means another full pull. If you want incremental
behavior, that's a fork-and-modify exercise.

## Politeness

Danbooru runs the wiki API for free and asks scrapers to be respectful. The
default 1 req/sec rate is well under their cap. Don't crank `--delay` down
without good reason. If you're going to re-extract repeatedly, consider
caching the wiki bodies locally and re-running only the post-count lookup
when you want fresh numbers.
