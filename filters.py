"""Decide whether a post matches your criteria. Edit freely: digest.py only calls matches()."""

from __future__ import annotations

import re


def _keyword_pattern(words: list[str]) -> re.Pattern:
    """Whole-word, case-insensitive match on any of the words. A space also matches '-'."""
    parts = [re.escape(w).replace(r"\ ", r"[\s\-]*") for w in words]
    return re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(parts) + r")(?![A-Za-z0-9])", re.I)


POSTAL_CODE = re.compile(r"(?<![A-Za-z0-9])(\d{6})(?![A-Za-z0-9])")
ONLINE = re.compile(r"(?<![A-Za-z])(online|zoom|virtual)(?![A-Za-z])", re.I)


def _location_ok(text: str, loc: dict) -> bool:
    """Postal code wins: if the job has one, only the prefixes count.
    Town names are a fallback for jobs that give a street but no postal code."""
    prefixes = tuple(str(p) for p in loc.get("postal_prefixes", []))
    towns = loc.get("towns", [])
    if not prefixes and not towns:
        return True
    codes = POSTAL_CODE.findall(text)
    if codes and prefixes:
        return any(code.startswith(prefixes) for code in codes)
    return bool(towns) and bool(_keyword_pattern(towns).search(text))


def matches(post, criteria: dict) -> bool:
    text = post.text
    if not text:
        return False

    lowered = text.lower()
    for word in criteria.get("exclude_keywords", []):
        if word.lower() in lowered:
            return False

    if criteria.get("exclude_online") and ONLINE.search(text):
        return False

    levels = criteria.get("levels", [])
    if levels and not _keyword_pattern(levels).search(text):
        return False

    subjects = criteria.get("subjects", [])
    if subjects and not _keyword_pattern(subjects).search(text):
        return False

    return _location_ok(text, criteria.get("locations", {}))
