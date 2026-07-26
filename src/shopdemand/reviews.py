"""Mine 1-2 star reviews — where the product spec actually comes from.

Category rankings tell you *where* merchants are spending and unhappy.
They do not tell you *what* to build. Negative reviews of the incumbents
do: they are merchants describing, in their own words, a problem they are
already paying money to have solved and still don't.

That is the highest-quality product signal available for free — better
than a survey, because these people have already proven willingness to
pay by buying the thing they're complaining about.
"""

from __future__ import annotations

import html
import re
from collections import Counter

import pandas as pd

from .fetch import ROOT, get

REPORTS = ROOT / "reports"

_BLOCK = re.compile(
    r"data-truncate-content-copy[^>]*>(.*?)</div>", re.S
)
_AUTHOR = re.compile(r'title="([^"]{1,60})"')

# Recurring complaint themes in app-store reviews. Crude but effective:
# these are the categories a wedge usually exploits.
THEMES = {
    "price": ["expensive", "pricing", "price", "cost", "overpriced", "too much", "charge", "fee"],
    "support": ["support", "response", "reply", "customer service", "ignored", "no help", "ticket"],
    "bugs": ["bug", "broken", "crash", "error", "glitch", "doesn't work", "does not work", "stopped working"],
    "slow": ["slow", "lag", "speed", "load time", "freezes", "timeout"],
    "complexity": ["confusing", "complicated", "hard to use", "difficult", "not intuitive", "clunky"],
    "limits": ["limit", "cap", "quota", "only allows", "restricted", "paywall"],
    "billing": ["refund", "charged", "cancel", "billing", "subscription", "uninstall"],
    "missing": ["missing", "no option", "can't", "cannot", "wish it", "would be nice", "lacks", "doesn't support"],
}


def _clean(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def app_reviews(handle: str, stars: tuple[int, ...] = (1, 2), pages: int = 2) -> list[dict]:
    """Negative reviews for one app. Cached, so cheap to re-read."""
    out = []
    for star in stars:
        for page in range(1, pages + 1):
            url = (f"https://apps.shopify.com/{handle}/reviews"
                   f"?ratings%5B%5D={star}" + (f"&page={page}" if page > 1 else ""))
            try:
                html_text = get(url)
            except Exception:
                continue
            blocks = _BLOCK.findall(html_text)
            if not blocks:
                break
            for b in blocks:
                text = _clean(b)
                if len(text) > 25:
                    out.append({"handle": handle, "stars": star, "text": text})
    return out


def themes_of(texts: list[str]) -> Counter:
    c = Counter()
    for t in texts:
        low = t.lower()
        for theme, words in THEMES.items():
            if any(w in low for w in words):
                c[theme] += 1
    return c


def mine(handles: list[str], pages: int = 2) -> pd.DataFrame:
    rows = []
    for i, h in enumerate(handles, 1):
        revs = app_reviews(h, pages=pages)
        rows.extend(revs)
        print(f"  [{i}/{len(handles)}] {h}: {len(revs)} negative reviews", flush=True)
    df = pd.DataFrame(rows)
    if df.empty:
        print("no reviews found")
        return df
    REPORTS.mkdir(exist_ok=True)
    df.to_csv(REPORTS / "negative_reviews.csv", index=False)

    print(f"\n{len(df)} negative reviews across {df['handle'].nunique()} apps\n")
    overall = themes_of(df["text"].tolist())
    total = len(df)
    print("complaint themes (share of negative reviews mentioning):")
    for theme, n in overall.most_common():
        print(f"  {theme:<12} {n:>4}  {n/total:>6.1%}")
    return df
