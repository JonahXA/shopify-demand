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

# Below this, review counts simply haven't had time to move and any
# per-day rate is noise amplified by a small denominator.
MIN_ELAPSED_DAYS = 0.5


def load() -> pd.DataFrame:
    if not SNAPSHOTS.exists():
        raise FileNotFoundError("no snapshots yet — run shopdemand.snapshot.run() first")
    df = pd.read_parquet(SNAPSHOTS)
    df["date"] = pd.to_datetime(df["date"])
    # captured_at is the truth for elapsed time; date is only a label.
    if "captured_at" in df.columns:
        df["captured_at"] = pd.to_datetime(df["captured_at"], format="mixed", utc=True)
    else:
        df["captured_at"] = pd.NaT
    # Rows written before captured_at existed fall back to their date
    # label. Leaving them NaT is not harmless: NaN comparisons are always
    # False, so a null timestamp silently disables the elapsed-time guard
    # below and lets meaningless rates through.
    fallback = df["date"].dt.tz_localize("UTC")
    df["captured_at"] = df["captured_at"].where(df["captured_at"].notna(), fallback)
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
    d = (df.sort_values("captured_at")
           .groupby(["handle", "date"], as_index=False)
           .agg(reviews=("reviews", "max"), rating=("rating", "max"),
                name=("name", "first"), rank=("rank", "min"),
                category=("category", "first"),
                captured_at=("captured_at", "max")))
    d = d.sort_values("captured_at")
    first = d.groupby("handle").first()
    last = d.groupby("handle").last()
    # Real elapsed hours. Two snapshots can carry different date labels
    # and be minutes apart (a local run just before a UTC-scheduled one),
    # so dividing by label difference silently invents a rate.
    span_days = ((last["captured_at"] - first["captured_at"]).dt.total_seconds()
                 / 86400).clip(lower=1e-9)

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
    out["elapsed_days"] = span_days.round(3)
    # Only rate-ify once enough time has passed for the number to mean
    # anything; below that, report the raw gain and leave the rate blank.
    enough = span_days >= MIN_ELAPSED_DAYS
    out["reviews_per_day"] = (out["reviews_gained"] / span_days).where(enough).round(3)
    return out.sort_values(["reviews_gained", "reviews"], ascending=False)


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
    span = df["captured_at"].max() - df["captured_at"].min()
    elapsed = 0.0 if pd.isna(span) else span.total_seconds() / 86400
    cov["elapsed_days"] = round(elapsed, 3)
    print("archive coverage:", cov, "\n")

    REPORTS.mkdir(exist_ok=True)
    vel = app_velocity(df)
    vel.to_csv(REPORTS / "app_velocity.csv")
    health = category_health(df)
    health.to_csv(REPORTS / "category_health.csv", index=False)

    if elapsed < MIN_ELAPSED_DAYS:
        print(f"Two date labels, but only {elapsed*24:.1f} hours of real elapsed time\n"
              f"(a local run and the UTC-scheduled run landed minutes apart).\n"
              f"Review counts barely move in hours, so no rate is reported yet —\n"
              f"dividing a near-zero gain by a near-zero denominator invents numbers.\n"
              f"The first genuine velocity reading arrives after the next daily run.\n")
        print("apps that gained a review even in that window:")
        moved = vel[vel["reviews_gained"] > 0]
        print(moved.head(10)[["name", "category", "reviews", "reviews_gained"]].to_string()
              if len(moved) else "  none")
        return

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
