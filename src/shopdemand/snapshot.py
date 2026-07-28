"""Daily ranking snapshots — the part that cannot be backfilled.

Shopify publishes an app's *current* rank, rating and review count. It
publishes no history of any of them. So the interesting quantities do
not exist anywhere:

  * **review velocity** — reviews gained per day, the closest public
    proxy for how fast an app is actually growing
  * **rank movement** — who is climbing, who is dying
  * **new-listing flow** — how fast the category is flooding
  * **churn** — apps that disappear entirely

None of it can be reconstructed later, by us or by anyone else, at any
price. A competitor starting in six months starts six months behind and
stays there. That is the whole thesis: the input is elapsed time, and
elapsed time is the one thing AI cannot compress.

Runs unattended on a schedule. Each run appends one dated row per app
per category and never rewrites history.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd

from .category import _cards, _TOTAL
from .fetch import ROOT, get

ARCHIVE = ROOT / "data" / "archive"
SNAPSHOTS = ARCHIVE / "rankings.parquet"
CATEGORIES = ROOT / "data" / "categories.txt"


def known_categories() -> list[str]:
    """Categories to snapshot. Seeded from the survey and extended
    whenever a crawl reveals a new one, so coverage only grows."""
    if CATEGORIES.exists():
        return [c.strip() for c in CATEGORIES.read_text().splitlines() if c.strip()]
    # Seed from whatever the sample survey found.
    sample = ROOT / "reports" / "apps_sample.csv"
    cats = sorted(pd.read_csv(sample)["category"].dropna().unique()) if sample.exists() else []
    CATEGORIES.parent.mkdir(parents=True, exist_ok=True)
    CATEGORIES.write_text("\n".join(cats))
    return cats


def snapshot_category(slug: str, max_pages: int = 4) -> list[dict]:
    """One dated observation per app, with its rank in the listing."""
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    captured_at = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    rows: list[dict] = []
    rank = 0
    listed_total = None
    for page in range(1, max_pages + 1):
        url = f"https://apps.shopify.com/categories/{slug}/all"
        if page > 1:
            url += f"?page={page}"
        # refresh=True: a cached copy would silently re-record an old day.
        html = get(url, refresh=True)
        if not html:
            break
        if listed_total is None:
            m = _TOTAL.search(html)
            listed_total = int(m.group(1).replace(",", "")) if m else None
        cards = _cards(html)
        if not cards:
            break
        for c in cards:
            rank += 1
            rows.append({
                "date": today, "captured_at": captured_at,
                "category": slug, "rank": rank,
                "listed_total": listed_total, **c,
            })
    return rows


def _merge(new_rows: list[dict]) -> pd.DataFrame:
    """Fold rows into the archive. Idempotent per (date, category, app),
    so a re-run on the same day corrects that day and never touches
    earlier history."""
    new = pd.DataFrame(new_rows)
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    if SNAPSHOTS.exists():
        combined = pd.concat([pd.read_parquet(SNAPSHOTS), new], ignore_index=True)
        combined = combined.drop_duplicates(subset=["date", "category", "handle"], keep="last")
    else:
        combined = new
    # Write via a temp file so an interrupted write cannot corrupt the
    # archive — the one file whose loss would be unrecoverable.
    tmp = SNAPSHOTS.with_suffix(".parquet.tmp")
    combined.to_parquet(tmp, index=False)
    tmp.replace(SNAPSHOTS)
    return combined


def run(max_pages: int = 4, limit: int | None = None, checkpoint_every: int = 10) -> pd.DataFrame:
    """Capture today's rankings, checkpointing as it goes.

    Checkpointing matters more than it looks: an all-or-nothing write
    means a crash at 90% loses the entire day, and a missing day is a
    permanent hole in a dataset whose only value is continuity."""
    cats = known_categories()
    if limit:
        cats = cats[:limit]
    print(f"snapshotting {len(cats)} categories ({dt.date.today().isoformat()})", flush=True)
    pending: list[dict] = []
    total = 0
    for i, slug in enumerate(cats, 1):
        try:
            pending.extend(snapshot_category(slug, max_pages))
        except Exception as e:
            print(f"  [{i}/{len(cats)}] {slug}: FAILED {e}", flush=True)
            continue
        if i % checkpoint_every == 0 or i == len(cats):
            if pending:
                _merge(pending)
                total += len(pending)
                pending = []
            print(f"  [{i}/{len(cats)}] {total} rows committed", flush=True)

    if not SNAPSHOTS.exists():
        print("no rows captured — archive untouched")
        return pd.DataFrame()
    combined = pd.read_parquet(SNAPSHOTS)
    days = combined["date"].nunique()
    print(f"\narchive: {len(combined):,} rows, {combined['handle'].nunique():,} apps, "
          f"{days} day(s) of history")
    if days < 2:
        print("(velocity and rank-movement unlock on the second day — that is why starting now matters)")
    return combined
