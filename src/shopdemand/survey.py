"""Sample the app store and rank categories by how underserved they look.

The question this answers is the one that killed the last attempt:
*where does demand already exist that nobody is serving well?* Building
is cheap now; distribution is the scarce input, and on a marketplace the
distribution is category search. So we want niches where merchants are
clearly spending (lots of reviews) but the incumbents are weak (low
ratings, few apps, or a single dominant app everyone complains about).

Sampling: a uniform random sample of the ~24k English listings, which is
enough to characterise category-level supply without fetching every page.
Seeded, so reruns are reproducible.
"""

from __future__ import annotations

import random

import pandas as pd

from .fetch import ROOT, app_urls, get
from .parse import parse_app

REPORTS = ROOT / "reports"
SEED = 20260726


def collect(n: int = 700, seed: int = SEED) -> pd.DataFrame:
    urls = app_urls()
    rng = random.Random(seed)
    sample = rng.sample(urls, min(n, len(urls)))
    rows = []
    for i, u in enumerate(sample, 1):
        try:
            rec = parse_app(u, get(u))
        except Exception:
            continue
        if rec:
            rows.append(rec)
        if i % 50 == 0:
            print(f"  {i}/{len(sample)} fetched, {len(rows)} parsed", flush=True)
    df = pd.DataFrame(rows)
    REPORTS.mkdir(exist_ok=True)
    df.to_csv(REPORTS / "apps_sample.csv", index=False)
    return df


def rank(df: pd.DataFrame, min_apps: int = 5) -> pd.DataFrame:
    """Category-level supply and quality."""
    d = df.dropna(subset=["category"]).copy()
    d["reviews"] = pd.to_numeric(d["reviews"], errors="coerce").fillna(0)
    d["rating"] = pd.to_numeric(d["rating"], errors="coerce")

    g = d.groupby("category").agg(
        apps=("handle", "size"),
        total_reviews=("reviews", "sum"),
        median_reviews=("reviews", "median"),
        mean_rating=("rating", "mean"),
        weak_share=("rating", lambda s: (s < 4.5).mean()),
        unreviewed_share=("reviews", lambda s: (s < 5).mean()),
        free_share=("has_free_plan", "mean"),
        median_price=("min_price", "median"),
    )
    g = g[g["apps"] >= min_apps]

    # Demand: money is clearly being spent here (reviews as a proxy).
    # Weakness: incumbents are poorly rated, or most apps have no traction.
    g["demand"] = g["total_reviews"] / g["apps"]
    g["opportunity"] = g["demand"].rank(pct=True) * g["weak_share"].rank(pct=True)
    return g.sort_values("opportunity", ascending=False).round(3)


def run(n: int = 700) -> pd.DataFrame:
    print(f"sampling {n} listings (cached; safe to re-run)...")
    df = collect(n)
    print(f"\nparsed {len(df)} apps across {df['category'].nunique()} categories\n")
    g = rank(df)
    g.to_csv(REPORTS / "category_ranking.csv")
    cols = ["apps", "total_reviews", "demand", "mean_rating", "weak_share",
            "unreviewed_share", "median_price", "opportunity"]
    print(g[cols].head(20).to_string())
    return g
