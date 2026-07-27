"""Census a category properly, instead of inferring it from a sample.

The first pass sampled ~2.8% of all listings, which is fine for
category-level *rates* but useless for counting competitors: a category
showing "5 apps" in the sample actually had 136. Absolute supply has to
come from the category pages themselves.

Category listing pages carry name, rating and review count for 25 apps
per request, so a full census of a category costs a handful of requests
rather than one per app.
"""

from __future__ import annotations

import html
import re

import pandas as pd

from .fetch import ROOT, get

REPORTS = ROOT / "reports"

# Parse by slicing the page into per-card chunks first, then reading small
# fields out of each chunk. An earlier version used one big regex with
# lazy `.*?` spans across the whole 250KB document; it worked on the page
# it was written against and then backtracked catastrophically on others,
# hanging for 30+ minutes on what is ~30 seconds of fetching. Bounded
# regexes over small slices cannot do that.
_LINK = re.compile(r'href="https://apps\.shopify\.com/([a-z0-9\-]+)\?[^"]*surface_type=category')
_NAME = re.compile(r'class="">\s*(.*?)\s*</a>', re.S)
_RATING = re.compile(r"(\d\.\d)\s*<span class=\"tw-sr-only\"> out of 5 stars")
_REVIEWS = re.compile(r'<span class="tw-sr-only">([\d,]+) total reviews')
_TOTAL = re.compile(r"([\d,]+)\s+apps?")


def _cards(page: str) -> list[dict]:
    """Slice the listing page into one chunk per app card."""
    starts = [(m.start(), m.group(1)) for m in _LINK.finditer(page)]
    out = []
    for i, (pos, handle) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else min(pos + 4000, len(page))
        chunk = page[pos:end]
        name = _NAME.search(chunk)
        rating = _RATING.search(chunk)
        reviews = _REVIEWS.search(chunk)
        if not (name and rating and reviews):
            continue
        out.append({
            "handle": handle,
            "name": html.unescape(re.sub(r"\s+", " ", name.group(1))).strip(),
            "rating": float(rating.group(1)),
            "reviews": int(reviews.group(1).replace(",", "")),
        })
    return out


def category_apps(slug: str, max_pages: int = 8) -> pd.DataFrame:
    """Every listed app in a category (paginated), with rating + reviews."""
    rows, seen = [], set()
    total = None
    for page in range(1, max_pages + 1):
        url = f"https://apps.shopify.com/categories/{slug}/all"
        if page > 1:
            url += f"?page={page}"
        page_html = get(url)
        if not page_html:
            break
        if total is None:
            m = _TOTAL.search(page_html)
            total = int(m.group(1).replace(",", "")) if m else None
        found = 0
        for card in _cards(page_html):
            if card["handle"] in seen:
                continue
            seen.add(card["handle"])
            found += 1
            rows.append({"category": slug, **card})
        if found == 0:
            break
    df = pd.DataFrame(rows)
    df.attrs["total_listed"] = total
    return df


def profile(slug: str, max_pages: int = 8) -> dict:
    """Competitive shape of one category."""
    df = category_apps(slug, max_pages)
    if df.empty:
        return {"category": slug, "error": "no apps parsed"}
    r, v = df["rating"], df["reviews"]
    top = df.nlargest(1, "reviews").iloc[0]
    return {
        "category": slug,
        "listed_total": df.attrs.get("total_listed"),
        "scraped": len(df),
        "mean_rating": round(r.mean(), 3),
        "median_rating": round(r.median(), 2),
        "share_below_4_5": round((r < 4.5).mean(), 3),
        "share_below_4": round((r < 4.0).mean(), 3),
        "total_reviews": int(v.sum()),
        "median_reviews": int(v.median()),
        # Concentration: does one app own the category?
        "top_app": top["name"],
        "top_reviews": int(top["reviews"]),
        "top_rating": float(top["rating"]),
        "top_share_of_reviews": round(top["reviews"] / max(v.sum(), 1), 3),
        "df": df,
    }


def compare(slugs: list[str], max_pages: int = 8) -> pd.DataFrame:
    out, frames = [], []
    for s in slugs:
        p = profile(s, max_pages)
        if "error" in p:
            print(f"  {s}: {p['error']}")
            continue
        frames.append(p.pop("df"))
        out.append(p)
        print(f"  {s}: {p['scraped']}/{p['listed_total']} apps, "
              f"mean {p['mean_rating']}, top={p['top_app'][:32]}", flush=True)
    df = pd.DataFrame(out).sort_values("mean_rating")
    REPORTS.mkdir(exist_ok=True)
    df.to_csv(REPORTS / "category_census.csv", index=False)
    if frames:
        pd.concat(frames).to_csv(REPORTS / "category_apps.csv", index=False)
    return df
