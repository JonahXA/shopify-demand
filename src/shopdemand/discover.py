"""Find every category worth snapshotting.

Coverage is the one dimension of the archive that *can* be fixed later —
but only for days that haven't happened yet. A category added next month
starts its history next month, so it is worth widening coverage early
even though the cost is a one-off crawl.

Samples app listings from the sitemap and records the leaf category each
one belongs to, reporting the discovery curve as it goes: if new
categories stop appearing, coverage is effectively complete and further
crawling is waste.
"""

from __future__ import annotations

import random
import re

from .fetch import app_urls, get
from .snapshot import CATEGORIES, known_categories

_CAT = re.compile(r"/categories/([a-z0-9\-]+)/all")


def discover(n: int = 400, seed: int = 7) -> list[str]:
    known = set(known_categories())
    start = len(known)
    urls = app_urls()
    rng = random.Random(seed)
    sample = rng.sample(urls, min(n, len(urls)))

    found_at: list[int] = []  # how many known categories after each fetch
    for i, u in enumerate(sample, 1):
        try:
            page = get(u)
        except Exception:
            continue
        for c in _CAT.findall(page):
            known.add(c)
        found_at.append(len(known))
        if i % 50 == 0:
            recent = len(known) - (found_at[-51] if len(found_at) > 50 else start)
            print(f"  {i}/{len(sample)}  categories={len(known)}  (+{recent} in last 50)",
                  flush=True)

    ordered = sorted(known)
    CATEGORIES.write_text("\n".join(ordered))
    print(f"\ncategories: {start} -> {len(ordered)} (+{len(ordered)-start})")
    if found_at and len(known) - (found_at[-51] if len(found_at) > 50 else start) == 0:
        print("no new categories in the last 50 pages — coverage looks complete")
    return ordered
