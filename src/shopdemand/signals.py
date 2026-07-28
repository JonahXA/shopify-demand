"""What actually predicts traction — measured, not asserted.

The base-rate work said ~7.5% of finished apps reach modest traction. The
useful follow-up is *what separates that 7.5%*, because those are the
levers worth pulling before launch.

Two things make a naive comparison misleading:

  * **Age.** Reviews accumulate. An app from 2019 has had years to gather
    them; one from last month has not. Comparing raw counts rewards being
    old, not being good. Everything here is therefore reported as
    reviews per month since launch.
  * **Survivorship.** These are the listings that still exist. Apps that
    were pulled are invisible, so every estimate here is optimistic.

Runs entirely off already-cached pages: no new requests.
"""

from __future__ import annotations

import glob
import re
from datetime import datetime

import numpy as np
import pandas as pd

from .fetch import ROOT
from .parse import parse_app

REPORTS = ROOT / "reports"

# The badge only appears when the app actually holds it (verified against
# pages with and without). Shopify boosts badged apps in store search, so
# it is a plausible causal lever rather than a mere correlate.
_BFS = re.compile(r"Built for Shopify", re.I)
_LAUNCH = re.compile(r"Launched[^<]*</[^>]+>\s*<[^>]*>\s*([A-Z][a-z]+ \d{1,2}, \d{4})")
_LANGS = re.compile(r"Languages\s*</[^>]+>\s*<[^>]*>(.*?)</", re.S)


def _extras(page: str) -> dict:
    launch = _LAUNCH.search(page)
    langs = _LANGS.search(page)
    lang_txt = re.sub(r"<[^>]+>", "", langs.group(1)) if langs else ""
    return {
        "built_for_shopify": bool(_BFS.search(page)),
        "launched": launch.group(1) if launch else None,
        "n_languages": len([x for x in lang_txt.split(",") if x.strip()]) or None,
    }


def build(limit: int | None = None) -> pd.DataFrame:
    """Re-read every cached app page and extract traction signals."""
    rows = []
    for f in glob.glob(str(ROOT / "data" / "cache" / "*.html")):
        page = open(f, errors="replace").read()
        if '"SoftwareApplication"' not in page:
            continue
        rec = parse_app("https://apps.shopify.com/x", page)
        if not rec:
            continue
        rec.update(_extras(page))
        rows.append(rec)
        if limit and len(rows) >= limit:
            break

    df = pd.DataFrame(rows)
    df["reviews"] = pd.to_numeric(df["reviews"], errors="coerce").fillna(0)
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["launched_dt"] = pd.to_datetime(df["launched"], errors="coerce")
    now = pd.Timestamp("today")
    df["age_months"] = (now - df["launched_dt"]).dt.days / 30.44
    # Age-adjusted traction. Guard the denominator so a brand-new app
    # cannot look like a runaway hit on one review.
    df["reviews_per_month"] = df["reviews"] / df["age_months"].clip(lower=3)
    REPORTS.mkdir(exist_ok=True)
    df.to_csv(REPORTS / "signals.csv", index=False)
    return df


def report(df: pd.DataFrame) -> None:
    d = df.dropna(subset=["age_months"])
    d = d[d["age_months"] > 0]
    print(f"{len(d)} apps with a parseable launch date "
          f"(of {len(df)} cached listings)\n")

    print("=== Does the Built for Shopify badge track traction? ===")
    for flag, label in [(True, "has badge"), (False, "no badge")]:
        g = d[d["built_for_shopify"] == flag]
        if len(g) < 5:
            continue
        print(f"  {label:<10} n={len(g):>4}  median rev/mo {g.reviews_per_month.median():>6.2f}  "
              f"share >1/mo {(g.reviews_per_month > 1).mean():>6.1%}  "
              f"median age {g.age_months.median():>5.1f}mo")

    print("\n=== Is the store saturating? (traction by launch year) ===")
    d = d.assign(year=d.launched_dt.dt.year)
    by = d[d.year >= 2015].groupby("year").agg(
        apps=("handle", "size"),
        median_rev_per_mo=("reviews_per_month", "median"),
        share_any=("reviews", lambda s: (s > 0).mean()),
        share_50plus=("reviews", lambda s: (s >= 50).mean()),
    ).round(3)
    print(by.to_string())
