"""Scoring + fuzzy-match helpers shared by node-search and model-search tools."""
from __future__ import annotations

import re
from typing import Any


_SEARCH_STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "for", "with", "in", "on",
    "is", "are", "from", "by", "this", "that", "node", "nodes",
}


def _basename_no_ext(s: str) -> str:
    """Strip directory and extension. 'foo/bar.safetensors' → 'bar'."""
    base = s.rsplit("/", 1)[-1]
    return base.rsplit(".", 1)[0] if "." in base else base


def _score_query_match(name: str, category: str, description: str, tokens: list[str]) -> int:
    """All tokens must match somewhere; score by where (name>category>description)."""
    name_l = name.lower()
    cat_l = (category or "").lower()
    desc_l = (description or "").lower()
    total = 0
    for t in tokens:
        ts = 0
        if t == name_l:
            ts = 200
        elif t in name_l:
            ts = 80
        if t in cat_l:
            ts = max(ts, 60)
        if t in desc_l:
            ts = max(ts, 40)
        if ts == 0:
            return 0
        total += ts
    return total


def _fuzzy_match_list(needle: str, haystack: list) -> list[dict[str, Any]]:
    """Find candidates in haystack that resemble needle by basename (sans dir + ext)."""
    if not isinstance(needle, str) or not isinstance(haystack, list):
        return []
    needle_base = _basename_no_ext(needle).lower()
    out: list[dict[str, Any]] = []
    for item in haystack:
        if not isinstance(item, str):
            continue
        item_base = _basename_no_ext(item).lower()
        if item_base == needle_base:
            out.append({"value": item, "score": 100, "reason": "exact basename match"})
        elif item_base.startswith(needle_base) or needle_base.startswith(item_base):
            out.append({"value": item, "score": 80, "reason": "prefix"})
        elif needle_base in item_base or item_base in needle_base:
            out.append({"value": item, "score": 50, "reason": "substring"})
    out.sort(key=lambda m: -m["score"])
    return out


def _split_query_tokens(query: str) -> list[str]:
    """Lowercase + split on whitespace/underscore/dash. Drops empties."""
    return [t for t in re.split(r"[\s_\-]+", query.lower()) if t]


def _score_model_path(path: str, q_full: str, tokens: list[str]) -> dict[str, Any] | None:
    """Score a candidate model path against the query.

    Single-token: legacy substring scoring (100=exact, 80=prefix, 50=substring).
    Multi-token: every token must appear somewhere in the path. Score is the sum of
    per-token bonuses, weighted toward basename matches over directory matches, plus
    a small bonus when ALL tokens land in the basename (the "right one" signal).
    """
    base_no_ext = _basename_no_ext(path).lower()
    path_l = path.lower()

    if len(tokens) <= 1:
        # Legacy single-token mode — preserves existing callers
        if q_full == base_no_ext:
            return {"score": 100, "matched_in_basename": True}
        if base_no_ext.startswith(q_full):
            return {"score": 80, "matched_in_basename": True}
        if q_full in base_no_ext:
            return {"score": 50, "matched_in_basename": True}
        return None

    score = 0
    in_base = 0
    for tok in tokens:
        if tok in base_no_ext:
            score += 30
            in_base += 1
        elif tok in path_l:
            score += 10  # matched in directory only — weaker signal
        else:
            return None  # AND-semantics: every token must appear

    # Bonuses for fully-in-basename hits and for full string match
    if in_base == len(tokens):
        score += 20
    if base_no_ext == q_full:
        score += 50
    elif base_no_ext.startswith(q_full):
        score += 20

    return {"score": score, "matched_in_basename": in_base == len(tokens)}
