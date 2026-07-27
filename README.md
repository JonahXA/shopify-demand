# shopify-demand

**Find where Shopify merchants are already spending money and still unhappy — before building anything.**

## Why this exists

A previous Shopify app (Reconcile) was built, deployed, and made nothing. It almost certainly did not fail on code quality. It failed on **distribution**: nobody found it.

That is the default outcome for micro-SaaS, and it does not get better just because you can build faster. With AI assistance, building is cheap — days, not months. Distribution is still expensive, and it is now the *only* thing that matters. So the sequence has to invert:

> Don't build and then look for demand. **Measure demand, then build the thing it's asking for.**

On a marketplace, distribution *is* category search — which makes demand measurable instead of a guess. That is what this repo measures.

## What it does

**1. Survey supply** (`shopdemand.survey`)
Samples the ~24,000 English App Store listings via the published sitemap and extracts, per app: rating, review count, category, free-plan availability, and price range. Aggregated by category into:

| signal | meaning |
|---|---|
| `demand` | reviews per app — merchants are demonstrably spending here |
| `weak_share` | share of incumbents rated below 4.5 — the field is beatable |
| `unreviewed_share` | share with no traction — how many entrants die |
| `opportunity` | high demand × weak incumbents |

**2. Mine the complaints** (`shopdemand.reviews`)
Rankings say *where*. They don't say *what*. Pulling the 1–2 star reviews of the leading apps does: merchants describing, in their own words, a problem they are **already paying to solve and still have**. That is a better signal than any survey, because willingness to pay is already proven — they bought the thing they're complaining about.

Complaints are bucketed into the themes a wedge usually exploits: price, support, bugs, speed, complexity, limits, billing, missing features.

## Finding (2026-07-27): the App Store is not a distribution channel

Random sample of 683 of the 24,032 English listings, cross-checked against a full census of 8 categories (773 apps):

| percentile | reviews |
|---|---|
| 50th (median) | **0** |
| 75th | 2 |
| 90th | 18 |
| 95th | 64 |
| 99th | 359 |

**61% of all Shopify apps have zero reviews. Only 5.6% have more than 50. Only 3.5% clear 100.**

The category census kills the "underserved niche" thesis too. Every category examined is crowded (121–495 apps) with well-rated incumbents (mean 4.53–4.73). And two categories are owned outright by a giant: Shopify Flow holds **69%** of workflow-automation reviews, TikTok **42%** of ads — you would be competing with the platform owner's own free app.

**What this means.** The common assumption is that listing on a marketplace *is* distribution. The data says it isn't: the median listing gets nothing at all. Whatever distribution an app gets must come from outside the store — content, an existing audience, partnerships, paid acquisition.

So the binding constraint was never "find the right niche." It is distribution, and the marketplace does not supply it. An earlier app of ours (Reconcile) was built, deployed, and earned nothing — that was the **modal outcome**, not bad luck.

Caveats, stated fairly: reviews are not revenue, and a serious build with a real distribution plan should beat a base rate that includes thousands of abandoned, zero-effort listings. But it beats it *because of the distribution plan* — which is the part the store doesn't give you and the part that is hard to buy.

## Honest limitations

- **Review count is a proxy for installs, not a headcount.** Shopify does not publish install numbers. Only a small and non-uniform fraction of merchants review. Treat it as a *ranking* signal.
- **A sample, not a census.** 700 of ~24k listings characterises category-level supply; it will miss small categories.
- **Weak incumbents ≠ easy market.** Sometimes everything in a category is badly rated because the problem is genuinely hard, or because merchants blame the app for Shopify's own constraints. The review mining is what separates "nobody built it well" from "it can't be built well."
- This measures *opportunity*, not *execution*. It tells you where to aim, not whether you'll hit.
- **Two corrections worth recording.** The first ranking sampled 2.8% of listings and treated sample counts as real supply — it reported "5 apps" for a category with 136, and "8" for one with 360. It also reported mean ratings of 3.83–3.93 for categories whose true means are 4.53–4.64. Both were sampling artifacts; the census exists because of them. Sample rates are not census counts.

## Etiquette

- Discovery via the published `sitemap.xml` — the sanctioned path.
- `robots.txt` disallows `/internal/`, `/services/`, auth params, and **any URL containing `q=`** (search pages). The fetcher **refuses** those URL patterns in code rather than merely avoiding them.
- Every response cached on disk; re-running the analysis costs the source nothing.
- Throttled to ~1 request/0.6s, with an honest User-Agent.

## Usage

```bash
pip install -e .
python -c "from shopdemand.survey import run; run(700)"      # category ranking
python -c "from shopdemand.reviews import mine; mine(['app-handle'])"  # complaint themes
```

Outputs land in `reports/`.
