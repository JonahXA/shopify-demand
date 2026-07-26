"""Pull the structured facts out of a Shopify app listing page.

Everything here comes from the page's own JSON-LD block plus a few
robust regexes. Review count is the only public proxy for install base
(Shopify does not publish installs); roughly it tracks popularity, with
the usual caveat that only a small and non-uniform fraction of merchants
ever leave a review. It is a *ranking* signal, not a headcount.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter

PRICE_RE = re.compile(r"\$(\d+(?:\.\d{2})?)\s*/\s*month", re.I)


def _jsonld(page: str) -> dict:
    for blob in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', page, re.S
    ):
        try:
            d = json.loads(blob)
        except json.JSONDecodeError:
            continue
        if d.get("@type") == "SoftwareApplication":
            return d
    return {}


def _category(page: str) -> str | None:
    """The most-referenced leaf category on the page — its own."""
    cats = [c for c in re.findall(r"/categories/([a-z0-9\-]+)/all", page)]
    if not cats:
        return None
    return Counter(cats).most_common(1)[0][0]


def parse_app(url: str, page: str) -> dict | None:
    if not page.strip():
        return None
    d = _jsonld(page)
    if not d:
        return None
    rating = d.get("aggregateRating") or {}
    prices = [float(p) for p in PRICE_RE.findall(page)]
    return {
        "handle": url.rstrip("/").rsplit("/", 1)[-1],
        "name": html.unescape(d.get("name", "") or ""),
        "developer": html.unescape(d.get("brand", "") or ""),
        "description": html.unescape(d.get("description", "") or "")[:300],
        "rating": rating.get("ratingValue"),
        "reviews": rating.get("ratingCount"),
        "category": _category(page),
        "has_free_plan": bool(re.search(r"free plan available|free to install", page, re.I)),
        "min_price": min(prices) if prices else None,
        "max_price": max(prices) if prices else None,
        "url": url,
    }
