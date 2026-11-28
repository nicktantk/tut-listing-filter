"""Straight-line distance between Singapore postal codes, using OneMap's free search API.

Coordinates are cached for the length of one run only, and never written to the repo,
so home locations stay private. Any lookup failure just means no distance is shown.
"""

from __future__ import annotations

import math
import re
from typing import Optional

import requests

ONEMAP_URL = "https://www.onemap.gov.sg/api/common/elastic/search"
POSTAL_CODE = re.compile(r"(?<![A-Za-z0-9])(\d{6})(?![A-Za-z0-9])")


class Geocoder:
    def __init__(self, fetch=None):
        self.cache: dict[str, Optional[list[float]]] = {}
        self.fetch = fetch or self._onemap
        self.lookups = 0

    @staticmethod
    def _onemap(postal: str) -> Optional[list[float]]:
        resp = requests.get(
            ONEMAP_URL,
            params={"searchVal": postal, "returnGeom": "Y", "getAddrDetails": "Y", "pageNum": 1},
            timeout=15,
        )
        resp.raise_for_status()
        for r in resp.json().get("results", []):
            if r.get("POSTAL") == postal:
                return [float(r["LATITUDE"]), float(r["LONGITUDE"])]
        return None

    def coords(self, postal: str) -> Optional[list[float]]:
        if postal in self.cache:
            return self.cache[postal]
        try:
            result = self.fetch(postal)
        except Exception as exc:
            print(f"[warn] OneMap lookup failed for {postal}: {exc}")
            return None  # not cached, so it's retried next run
        self.cache[postal] = result
        self.lookups += 1
        return result


def km_between(a: list[float], b: list[float]) -> float:
    """Great-circle (straight-line) distance in km."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def distance_km(text: str, home: Optional[str], geo: Geocoder) -> Optional[float]:
    """Distance from home to the first postal code in the text that OneMap knows."""
    if not home:
        return None
    home_xy = geo.coords(str(home))
    if not home_xy:
        return None
    for code in POSTAL_CODE.findall(text):
        xy = geo.coords(code)
        if xy:
            return km_between(home_xy, xy)
    return None
