"""Turn dated snapshots into the metrics nobody else can compute.

A single snapshot is a leaderboard — mildly interesting, and Shopify
already shows it. Two snapshots are a *derivative*, and that is the
product: who is growing, who is stalling, which categories are flooding,
which apps quietly died.

Everything here needs at least two distinct days in the archive and
degrades gracefully before that, so the module is safe to run from day
one.
"""

from __future__ import annotations

import pandas as pd

from .fetch import ROOT
from .snapshot import SNAPSHOTS

REPORTS = ROOT / "reports"


def load() -> pd.DataFrame:
    if not SNAPSHOTS.exists():
        raise FileNotFoundError("no snapshots yet — run shopdemand.snapshot.run() first")
    df = pd.read_parquet(SNAPSHOTS)
    df["date"] = pd.to_datetime(df["date"])
    return df


def coverage(df: pd.DataFrame) -> dict:
    return {
        "days": int(df["date"].nunique()),
        "first_day": str(df["date"].min().date()),
        "last_day": str(df["date"].max().date()),
        "apps": int(df["handle"].nunique()),
        "categories": int(df["category"].nunique()),
        "rows": len(df),
    }


def app_velocity(df: pd.DataFrame) -> pd.DataFrame:
    """Reviews gained per day, per app — the growth signal Shopify hides.

    Reviews only ever increase, so a positive delta is real activity. The
    per-day rate is comparable across apps regardless of how long they've
    been listed, which raw review counts are not."""
    d = (df.sort_values("date")
           .groupby(["handle", "date"], as_index=False)
           .agg(reviews=("reviews", "max"), rating=("rating", "max"),
                name=("name", "first"), rank=("rank", "min"),
                category=("category", "first")))
    first = d.groupby("handle").first()
    last = d.groupby("handle").last()
    span_days = (last["date"] - first["date"]).dt.days.clip(lower=1)

    out = pd.DataFrame({
        "name": last["name"],
        "category": last["category"],
        "reviews": last["reviews"],
        "rating": last["rating"],
        "reviews_gained": last["reviews"] - first["reviews"],
        "rank_now": last["rank"],
        "rank_change": first["rank"] - last["rank"],  # positive = climbed
        "days_observed": span_days,
    })
    out["reviews_per_day"] = (out["reviews_gained"] / span_days).round(3)
    return out.sort_values("reviews_per_day", ascending=False)


def category_health(df: pd.DataFrame) -> pd.DataFrame:
    """Per category: how crowded, how fast it's flooding, how much of the
    growth one incumbent is taking."""
    vel = app_velocity(df)
    latest = df[df["date"] == df["date"].max()]
    rows = []
    for cat, g in latest.groupby("category"):
        v = vel[vel["category"] == cat]
        gained = v["reviews_gained"].sum()
        rows.append({
            "category": cat,
            "listed_total": g["listed_total"].max(),
            "tracked": len(g),
            "mean_rating": round(g["rating"].mean(), 3),
            "share_below_4_5": round((g["rating"] < 4.5).mean(), 3),
            "median_reviews": int(g["reviews"].median()),
            "reviews_gained": int(gained),
            "top_app_share_of_growth": (
                round(v["reviews_gained"].max() / gained, 3) if gained > 0 else None
            ),
        })
    return pd.DataFrame(rows).sort_values("listed_total", ascending=False)


def churn(df: pd.DataFrame) -> pd.DataFrame:
    """Apps present on the first observed day and gone on the last —
    listings that died. Invisible in any single scrape."""
    first_day, last_day = df["date"].min(), df["date"].max()
    if first_day == last_day:
        return pd.DataFrame()
    was = set(df[df["date"] == first_day]["handle"])
    now = set(df[df["date"] == last_day]["handle"])
    gone = was - now
    d = df[df["handle"].isin(gone) & (df["date"] == first_day)]
    return d[["handle", "name", "category", "rating", "reviews"]].drop_duplicates()


def run() -> None:
    df = load()
    cov = coverage(df)
    print("archive coverage:", cov, "\n")

    REPORTS.mkdir(exist_ok=True)
    vel = app_velocity(df)
    vel.to_csv(REPORTS / "app_velocity.csv")
    health = category_health(df)
    health.to_csv(REPORTS / "category_health.csv", index=False)

    if cov["days"] < 2:
        print("Only one day captured so far. Velocity, rank movement and churn\n"
              "unlock on the second run — that is exactly the asset being built,\n"
              "and it is why starting today rather than next month matters.\n")
        print("today's most-reviewed apps:")
        print(vel.nlargest(10, "reviews")[["name", "category", "reviews", "rating"]].to_string())
        return

    print("fastest-growing apps (reviews/day):")
    print(vel.head(15)[["name", "category", "reviews", "reviews_per_day", "rank_change"]].to_string())
    dead = churn(df)
    print(f"\ndelisted since {cov['first_day']}: {len(dead)}")
