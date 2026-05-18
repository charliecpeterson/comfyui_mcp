#!/usr/bin/env python3
"""
extract_danbooru_tag_groups.py

Pulls Danbooru's tag-group taxonomy from their wiki API and emits a structured
set of Markdown files organized by category, with subsections preserved and
post counts attached.

Requires Python 3.7+ (uses `from __future__ import annotations` for the
PEP 604 `X | None` syntax to work on pre-3.10 interpreters).

Output layout:
    output_dir/
        README.md                        index of categories
        image-composition/
            lighting.md
            backgrounds.md
            ...
        body/
            hair.md
            hair-color.md
            posture.md
            ...
        ...

Each file contains tag groups split into the same subsections Danbooru's wiki
uses, with each tag annotated with its post count and (where available) the
short description from the wiki.

Usage:
    python extract_danbooru_tag_groups.py --out ./references/danbooru-tags
    python extract_danbooru_tag_groups.py --out ./references/danbooru-tags --min-posts 100
    python extract_danbooru_tag_groups.py --out ./references/danbooru-tags --dry-run

Requires: requests (pip install requests). No auth needed for read access.
"""

import argparse
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

import requests

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE = "https://danbooru.donmai.us"
USER_AGENT = "tag-group-extractor/1.0 (personal use; not for redistribution)"
REQUEST_DELAY_SEC = 1.0    # be polite; Danbooru asks for <10 req/sec
TAG_BATCH_SIZE = 100       # how many tags to look up per /tags.json call
ROOT_WIKI = "tag_groups"   # the master index page

# Categories from the master tag_groups page. We hard-code the section
# structure here because parsing the master page's headers is brittle, and
# this matches what Danbooru documents at /wiki_pages/tag_groups. If they
# reorganize, edit this dict.
CATEGORY_STRUCTURE = {
    "image-composition": [
        "artistic_license",
        "image_composition",
        "backgrounds",
        "censorship",
        "colors",
        "fine_art_parody",
        "character_count",
        "focus_tags",
        "lighting",
        "prints",
        "visual_aesthetic",
        "patterns",
        "symbols",
        "text",
        "japanese_dialects",
        "year_tags",
    ],
    "body": [
        "body_parts",
        "ass",
        "breasts_tags",
        "face_tags",
        "ears_tags",
        "eyes_tags",
        "hair",
        "hair_color",
        "hair_styles",
        "hands",
        "gestures",
        "feet",
        "neck_and_neckwear",
        "posture",
        "pussy",
        "penis",
        "shoulders",
        "skin_color",
        "skin_folds",
        "tail",
        "wings",
    ],
    "attire": [
        "accessories",
        "attire",
        "dress",
        "handwear",
        "headwear",
        "legwear",
        "sexual_attire",
        "bra",
        "panties",
        "sleeves",
        "embellishment",
        "eyewear",
        "fashion_style",
        "makeup",
        "covering",
        "nudity",
    ],
    "sex": [
        "sex_acts",
        "simulated_sex_acts",
        "sexual_positions",
        "bdsm_and_torture",
    ],
    "objects": [
        "audio_tags",
        "holding_tags",
        "cards",
        "doors_and_gates",
        "piercings",
        "sex_objects",
    ],
    "creatures": [
        "birds",
        "cats",
        "dogs",
        "legendary_creatures",
    ],
    "plants": [
        "flowers",
    ],
    "games": [
        "board_games",
        "sports",
        "video_game",
    ],
    "real-world": [
        "companies_and_brand_names",
        "holidays_and_celebrations",
        "jobs",
        "locations",
        "people",
        "real_world_locations",
        "history",
    ],
    "themes-and-misc": [
        "dances",
        "family_relationships",
        "food_tags",
        "fire",
        "groups",
        "phrases",
        "subjective",
        "technology",
        "theme",
        "verbs_and_gerunds",
        "water",
        "transgender",
        "gender_nonconformity",
        "meme",
    ],
    "meta": [
        "metatags",
        "drawing_software",
    ],
}

# Categories most useful for prompting (everything except the niche ones).
# The script outputs everything but the README and skill instructions can
# point at this subset.
PROMPTING_RELEVANT = {
    "image-composition", "body", "attire", "sex", "objects",
    "creatures", "plants", "themes-and-misc",
}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

class DanbooruClient:
    def __init__(self, delay: float = REQUEST_DELAY_SEC, verbose: bool = True):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.delay = delay
        self.verbose = verbose
        self._last_request_at = 0.0

    def _wait(self):
        elapsed = time.time() - self._last_request_at
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request_at = time.time()

    def get_json(self, path: str, params: dict | None = None) -> dict | list | None:
        self._wait()
        url = f"{BASE}{path}"
        if self.verbose:
            print(f"  GET {url} {params or ''}", file=sys.stderr)
        try:
            r = self.session.get(url, params=params, timeout=30)
        except requests.RequestException as e:
            print(f"  ! request failed: {e}", file=sys.stderr)
            return None
        if r.status_code == 404:
            return None
        if r.status_code != 200:
            print(f"  ! HTTP {r.status_code} for {url}", file=sys.stderr)
            return None
        try:
            return r.json()
        except json.JSONDecodeError:
            print(f"  ! non-JSON response from {url}", file=sys.stderr)
            return None

    def get_wiki_page(self, name: str) -> dict | None:
        """Fetch a wiki page by its title. Returns the page dict or None."""
        # The wiki page API endpoint accepts the page title in the URL.
        # We URL-encode because titles can contain colons (tag_group:lighting).
        encoded = quote(name, safe="")
        return self.get_json(f"/wiki_pages/{encoded}.json")

    def get_tag_post_counts(self, tag_names: list[str]) -> dict[str, int]:
        """Look up post counts for a batch of tags. Returns name → count."""
        if not tag_names:
            return {}
        out: dict[str, int] = {}
        # /tags.json supports search[name_comma] for batch lookup.
        for i in range(0, len(tag_names), TAG_BATCH_SIZE):
            batch = tag_names[i : i + TAG_BATCH_SIZE]
            params = {
                "search[name_comma]": ",".join(batch),
                "limit": TAG_BATCH_SIZE,
            }
            data = self.get_json("/tags.json", params=params)
            if isinstance(data, list):
                for tag in data:
                    name = tag.get("name")
                    count = tag.get("post_count", 0)
                    if name:
                        out[name] = count
        return out


# ---------------------------------------------------------------------------
# DText parsing
# ---------------------------------------------------------------------------

# A wiki body in DText. We need to extract:
#   - h4./h5./h6. section headers (subgroups within a page)
#   - [[tag_name]] and [[tag_name|display]] links (the tags themselves)
#   - Inline descriptions (the text that follows a tag link on the same line)

HEADER_RE = re.compile(r"^h([1-6])\.\s*(.+?)\s*$", re.MULTILINE)
WIKI_LINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:\|([^\]]+))?\]\]")


def parse_wiki_body(body: str) -> list[dict]:
    """
    Parse a wiki body into a list of sections, each with subgroup name and
    a list of tag entries.

    Returns:
        [
            {"subgroup": "Directional", "tags": [
                {"name": "backlighting", "desc": "Light comes from behind..."},
                ...
            ]},
            ...
        ]
    """
    if not body:
        return []

    # Split body into lines, tracking the current heading.
    sections: list[dict] = [{"subgroup": None, "tags": []}]
    current = sections[0]

    for line in body.splitlines():
        # Header? Start a new section.
        m = HEADER_RE.match(line)
        if m:
            depth = int(m.group(1))
            title = m.group(2).strip()
            # Skip h1 (the page title itself) and h2 (rare).
            # Use h4-h6 as actual subgroup markers since Danbooru wikis
            # typically use h4 for top-level sections.
            if depth >= 3:
                current = {"subgroup": title, "tags": []}
                sections.append(current)
            continue

        # Find tag links on this line.
        links = WIKI_LINK_RE.findall(line)
        if not links:
            continue

        # Strip the markup to get the residual description text.
        stripped = WIKI_LINK_RE.sub("", line).strip()
        # Normalize: drop leading bullets and colons.
        stripped = re.sub(r"^[\*\-\s:]+", "", stripped).strip(" :-—–")

        for target, _alias in links:
            # Skip non-tag wiki pages (help pages, etc.) by simple heuristic:
            # tag pages don't carry namespace prefixes. tag_group:* links are
            # nested-group references handled elsewhere, not tags themselves.
            t = target.strip()
            if not t:
                continue
            if ":" in t and not t.startswith("tag_group:"):
                # e.g. "help:wiki" — skip
                continue
            if t.startswith("tag_group:"):
                # nested group reference; handled elsewhere
                continue
            # Normalize to Danbooru's canonical tag form:
            #   - lowercase (wiki links sometimes capitalize for display)
            #   - underscores not spaces (wiki links often use spaces;
            #     Danbooru auto-normalizes, but the tags API is case- and
            #     whitespace-sensitive so we must do it ourselves)
            t = t.lower().replace(" ", "_")
            current["tags"].append({"name": t, "desc": stripped})

    # Dedup tags within each section (a tag can show up linked twice with
    # different casing, which after normalization collapses to one entry).
    # Keep the first occurrence's description.
    for section in sections:
        seen: set[str] = set()
        deduped = []
        for tag in section["tags"]:
            if tag["name"] in seen:
                continue
            seen.add(tag["name"])
            deduped.append(tag)
        section["tags"] = deduped

    # Drop empty leading section if no tags landed there.
    sections = [s for s in sections if s["tags"]]
    return sections


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Convert 'hair_color' or 'tag_group:hair_color' to 'hair-color'."""
    name = name.removeprefix("tag_group:")
    return name.replace("_", "-").lower()


def extract_group(client: DanbooruClient, group_name: str) -> dict | None:
    """Fetch and parse one tag-group wiki page."""
    page_title = f"tag_group:{group_name}"
    page = client.get_wiki_page(page_title)
    if not page:
        # Some entries on the master page aren't prefixed with tag_group:
        # (they're plain wiki pages like "injury" or "swimsuit"). Try again
        # without the prefix.
        page = client.get_wiki_page(group_name)
        if not page:
            return None
    body = page.get("body", "")
    sections = parse_wiki_body(body)
    return {
        "title": page.get("title", group_name),
        "raw_title": group_name,
        "sections": sections,
    }


def enrich_with_post_counts(
    client: DanbooruClient,
    group_data: dict,
    min_posts: int = 0,
) -> dict:
    """Add post_count to each tag entry and optionally filter by min_posts."""
    # Collect all unique tag names across sections.
    all_tags: set[str] = set()
    for section in group_data["sections"]:
        for tag in section["tags"]:
            all_tags.add(tag["name"])

    counts = client.get_tag_post_counts(sorted(all_tags))

    # Annotate and optionally filter.
    for section in group_data["sections"]:
        kept = []
        for tag in section["tags"]:
            tag["post_count"] = counts.get(tag["name"], 0)
            if tag["post_count"] >= min_posts:
                kept.append(tag)
        section["tags"] = kept

    # Drop sections that became empty after filtering.
    group_data["sections"] = [s for s in group_data["sections"] if s["tags"]]
    return group_data


def render_group_markdown(group_data: dict) -> str:
    """Render a single tag-group into Markdown."""
    out: list[str] = []
    title = group_data["title"].removeprefix("tag_group:").replace("_", " ").title()
    out.append(f"# {title}\n")

    for section in group_data["sections"]:
        subgroup = section["subgroup"]
        if subgroup:
            out.append(f"\n## {subgroup}\n")
        # Sort tags by post count descending within each section so the
        # most-trained-on tags surface first.
        tags_sorted = sorted(
            section["tags"], key=lambda t: t["post_count"], reverse=True
        )
        for tag in tags_sorted:
            line = f"- `{tag['name']}`"
            count = tag.get("post_count", 0)
            if count:
                line += f" ({count:,} posts)"
            if tag.get("desc"):
                # Trim a stray trailing colon or " - " etc.
                desc = tag["desc"].strip(" -:—–\u00a0")
                if desc:
                    line += f" — {desc}"
            out.append(line)
    out.append("")
    return "\n".join(out)


def render_index(category_results: dict[str, list[dict]]) -> str:
    """Render the top-level README/index linking to all categories."""
    out = [
        "# Danbooru tag groups",
        "",
        "Auto-extracted from Danbooru's tag-group wiki taxonomy.",
        "Sections preserve the wiki's own subgrouping; tags are sorted by post count within each section.",
        "",
        "Tag names are in Danbooru's canonical form (lowercase, underscored).",
        "Most A1111/ComfyUI prompters accept either underscores or spaces — underscores match training data.",
        "",
    ]
    for category, groups in category_results.items():
        out.append(f"## {category.replace('-', ' ').title()}")
        out.append("")
        for group in groups:
            name = group["raw_title"].replace("_", " ").title()
            slug = slugify(group["raw_title"])
            count = sum(len(s["tags"]) for s in group["sections"])
            out.append(f"- [{name}](./{category}/{slug}.md) — {count} tags")
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True, help="output directory")
    ap.add_argument(
        "--min-posts",
        type=int,
        default=0,
        help="filter out tags with fewer than this many posts (default: 0, no filter)",
    )
    ap.add_argument(
        "--delay",
        type=float,
        default=REQUEST_DELAY_SEC,
        help=f"seconds between requests (default: {REQUEST_DELAY_SEC})",
    )
    ap.add_argument(
        "--only",
        nargs="+",
        help="restrict to specific top-level categories (e.g. --only body attire)",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="fetch and report but don't write files",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="suppress per-request logging",
    )
    args = ap.parse_args()

    client = DanbooruClient(delay=args.delay, verbose=not args.quiet)

    categories = (
        {k: v for k, v in CATEGORY_STRUCTURE.items() if k in args.only}
        if args.only
        else CATEGORY_STRUCTURE
    )

    category_results: dict[str, list[dict]] = defaultdict(list)
    failures: list[str] = []

    total_groups = sum(len(v) for v in categories.values())
    seen = 0

    for category, group_names in categories.items():
        for group_name in group_names:
            seen += 1
            print(
                f"[{seen}/{total_groups}] {category}/{group_name}",
                file=sys.stderr,
            )
            data = extract_group(client, group_name)
            if not data or not data["sections"]:
                failures.append(f"{category}/{group_name}")
                continue
            data = enrich_with_post_counts(client, data, args.min_posts)
            if not data["sections"]:
                # All tags filtered out by min-posts.
                failures.append(f"{category}/{group_name} (all below min-posts)")
                continue
            category_results[category].append(data)

    # Write output.
    if args.dry_run:
        print("\n--- DRY RUN summary ---", file=sys.stderr)
        for category, groups in category_results.items():
            for g in groups:
                total = sum(len(s["tags"]) for s in g["sections"])
                print(f"  {category}/{g['raw_title']}: {total} tags across {len(g['sections'])} sections")
        if failures:
            print(f"\n{len(failures)} failures:", file=sys.stderr)
            for f in failures:
                print(f"  - {f}", file=sys.stderr)
        return

    args.out.mkdir(parents=True, exist_ok=True)
    for category, groups in category_results.items():
        cat_dir = args.out / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        for g in groups:
            path = cat_dir / f"{slugify(g['raw_title'])}.md"
            path.write_text(render_group_markdown(g), encoding="utf-8")

    index_path = args.out / "README.md"
    index_path.write_text(render_index(category_results), encoding="utf-8")

    print(f"\nWrote output to {args.out}", file=sys.stderr)
    if failures:
        print(f"\n{len(failures)} pages could not be extracted:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)


if __name__ == "__main__":
    main()
