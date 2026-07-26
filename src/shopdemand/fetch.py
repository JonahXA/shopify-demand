"""Cached, rate-limited fetching of public Shopify App Store pages.

Scope and etiquette, deliberately narrow:

  * Discovery is via the published sitemap, which is the sanctioned path.
  * `robots.txt` disallows `/internal/`, `/services/`, auth params and
    **any URL containing `q=`** (i.e. search result pages). We never
    request search; only sitemap-listed app pages and category pages.
  * Every response is cached on disk, so a page is fetched at most once
    no matter how often the analysis is re-run.
  * Requests are throttled and identify themselves honestly.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache"
BASE = "https://apps.shopify.com"
SITEMAP = f"{BASE}/sitemap_apps_en.xml"

_MIN_INTERVAL = 0.6  # seconds between real requests
_last = 0.0
_session = requests.Session()
_session.headers["User-Agent"] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(compatible; shopify-demand-research; non-commercial market research)"
)


def _disallowed(url: str) -> bool:
    """Mirror the robots.txt rules we must honour."""
    return ("q=" in url) or ("/internal/" in url) or ("/services/" in url) \
        or ("shpxid=" in url) or ("auth=" in url)


def get(url: str, *, binary: bool = False) -> str:
    if _disallowed(url):
        raise ValueError(f"robots.txt disallows this URL pattern: {url}")
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()
    path = CACHE / f"{key}.html"
    if path.exists():
        return path.read_text(errors="replace")

    global _last
    for attempt in range(5):
        wait = _MIN_INTERVAL - (time.monotonic() - _last)
        if wait > 0:
            time.sleep(wait)
        _last = time.monotonic()
        r = _session.get(url, timeout=30)
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2**attempt)
            continue
        if r.status_code == 404:
            path.write_text("")
            return ""
        r.raise_for_status()
        path.write_text(r.text, errors="replace")
        return r.text
    raise RuntimeError(f"gave up fetching {url}")


def app_urls() -> list[str]:
    """Every English app listing URL, from the sitemap."""
    xml = get(SITEMAP)
    return re.findall(r"<loc>([^<]+)</loc>", xml)
