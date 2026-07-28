"""Export the dashboard payload.

The dashboard is the sales surface: nobody buys "marketplace
intelligence", but everybody understands a page that shows which apps
are actually growing and which categories are drowning.

It renders only what the archive can currently support — with one day of
history it shows the state of the market, and as soon as a second day
lands it starts showing movement. The page is honest about which of
those it is, because claiming velocity we haven't measured yet is
exactly the kind of thing that destroys credibility with the buyers who
matter.
"""

from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from .fetch import ROOT
from .velocity import app_velocity, category_health, churn, coverage, load

DEST = ROOT / "site" / "data.json"


def build() -> dict:
    df = load()
    cov = coverage(df)
    vel = app_velocity(df)
    health = category_health(df)
    latest = df[df["date"] == df["date"].max()]

    payload: dict = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "coverage": cov,
        "has_velocity": cov["days"] >= 2,
        # Market structure — available from day one.
        "biggest": json.loads(
            vel.nlargest(20, "reviews")[["name", "category", "reviews", "rating"]]
            .reset_index().to_json(orient="records")
        ),
        "categories": json.loads(
            health.head(40).to_json(orient="records")
        ),
        # Traction among the apps merchants can actually SEE.
        #
        # Population caveat, and it matters: the snapshot walks the first
        # few pages of each category, which Shopify orders by popularity.
        # So this describes the *visible* market — the apps a merchant
        # browsing a category will actually encounter — and its median of
        # ~22 reviews is far healthier than the catalogue as a whole.
        # A uniform random sample of all 24k listings gives a median of
        # ZERO with 61% never reviewed. Both numbers are true of different
        # populations, and quoting one as the other would be wrong.
        "traction_visible": {
            "population": "ranked/visible apps (top pages of each category)",
            "apps": int(latest["handle"].nunique()),
            "median_reviews": int(latest["reviews"].median()),
            "share_under_10": round(float((latest["reviews"] < 10).mean()), 4),
            "share_over_100": round(float((latest["reviews"] > 100).mean()), 4),
        },
        "traction_catalogue": {
            "population": "uniform random sample of all listings (n=683)",
            "median_reviews": 0,
            "share_zero": 0.613,
            "share_over_50": 0.056,
            "note": "the long tail the category pages never show",
        },
    }

    if payload["has_velocity"]:
        payload["movers"] = json.loads(
            vel.nlargest(20, "reviews_per_day")[
                ["name", "category", "reviews", "reviews_per_day", "rank_change"]
            ].reset_index().to_json(orient="records")
        )
        payload["climbers"] = json.loads(
            vel.nlargest(15, "rank_change")[["name", "category", "rank_now", "rank_change"]]
            .reset_index().to_json(orient="records")
        )
        dead = churn(df)
        payload["churn"] = {"count": int(len(dead)),
                            "sample": json.loads(dead.head(10).to_json(orient="records"))}
    return payload


def run() -> None:
    payload = build()
    DEST.parent.mkdir(parents=True, exist_ok=True)
    DEST.write_text(json.dumps(payload, indent=1))
    size = DEST.stat().st_size / 1024
    print(f"wrote {DEST} ({size:.0f} KB)")
    print(f"  coverage: {payload['coverage']}")
    print(f"  velocity available: {payload['has_velocity']}")
