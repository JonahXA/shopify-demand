# 68% of the Shopify App Store was built in the last two years. The median app has zero customers.

I went looking for a good niche to build a Shopify app in. I found something more
interesting instead: the store has been flooded so completely, and so recently, that
picking a niche is close to irrelevant.

Here's what the data says.

## The median listed app has never received a single review

I took a uniform random sample of 683 listings from the 24,032 English apps in
Shopify's sitemap and pulled each one's rating and review count.

| percentile | reviews |
|---|---|
| 50th (median) | **0** |
| 75th | 2 |
| 90th | 18 |
| 95th | 64 |
| 99th | 359 |

**61% have never been reviewed. Only 5.6% have more than 50 reviews. Only 3.5% clear 100.**

Reviews aren't installs — Shopify publishes no install counts, and only some fraction
of merchants ever review. But a listing with zero reviews after a year is not a
listing with a thriving customer base.

## It got dramatically worse, dramatically recently

The obvious objection: maybe that's just what app stores look like, and always has been.
It isn't. Splitting the same sample by launch year:

| launch cohort | got any review | cleared 50 reviews |
|---|---|---|
| 2023 | 59.2% | **8.5%** |
| 2024 | 44.3% | **4.5%** |
| 2025 | 38.0% | **0.7%** |

Age-adjusted traction — reviews gained *per month* since launch — has a median of
**0.00 for every cohort since 2024**, against 0.47 for the 2015 cohort. That's not
young apps needing time; it's per-month.

The mechanism is visible in the store's own composition:

| launched | share of everything currently listed |
|---|---|
| 2024 | 12.9% |
| 2025 | 20.0% |
| **2026 (partial year)** | **35.4%** |

**More than a third of every app on the store today was listed this year.** Two-thirds
arrived in the last two.

## The niches aren't empty either

I ran a full census of eight categories — walking every listing page rather than
sampling — expecting to find underserved corners.

Every one is crowded (121–495 apps) with well-rated incumbents (mean 4.53–4.73). In
two of them a giant owns the category outright: **Shopify Flow holds 69%** of all
workflow-automation reviews, **TikTok 42%** of ads.

An embarrassing detail worth reporting, since it nearly fooled me: my first pass
sampled 2.8% of listings and treated the *sample* counts as real supply. It reported
"5 apps" for a category that actually has 136, and "8" for one with 360. It also
reported mean ratings of 3.83–3.93 for categories whose true means are 4.53–4.64.
Both were sampling artifacts. Had I trusted that table, I'd have built into a
360-competitor category believing I had eight rivals.

## Two numbers that look contradictory, and aren't

Tracking the ranked pages of every category gives a median of **22** reviews per app.
The random catalogue sample gives **0**.

Both are correct, of different populations. Category pages are sorted by popularity,
so they show the market a merchant actually *sees*. The sitemap sample includes
everything, including the enormous tail nobody ever encounters.

That gap is the whole story: **the visible market is healthy; the catalogue is a
graveyard.** Discovery, not build quality, is what separates them.

## What I think is actually going on

Building got cheap. Not "somewhat cheaper" — a working app is now days of work
instead of months, for anyone.

But it got cheap **for everyone simultaneously**. So the supply of apps exploded while
merchant attention stayed exactly the same size. The result is 24,000 listings
competing for the same finite discovery surface, and a median outcome of zero.

This isn't unique to Shopify. Open-source bounty markets now draw
[8–158 competing pull requests within hours](https://dev.to/timmothybuilder/how-to-find-and-win-open-source-bounties-in-2026-2b4b)
of a bounty being posted. Google's AI Overviews cut publisher click-through on
affected queries from
[1.76% to 0.61%](https://www.relevantaudience.com/seo/ai-overview-impact-on-organic-search-2026/).
The same force is hitting every channel where "make something good and be found"
used to work.

**The scarce resource was never the ability to build. It's distribution — and the
thing that got cheap was precisely the other one.**

## What actually correlates with surviving

Weakly encouraging, from the same data:

- **Solo developers outperform app studios.** Developers shipping multiple apps clear
  50 reviews 2.3% of the time; single-app developers, 5.8%. Portfolio spraying loses
  to focus.
- **Finishing matters.** 31.6% of listings never even set a price. Among those that
  did, the odds of clearing 50 reviews rise from 5.6% to 7.5%.
- **The Built for Shopify badge** moves the share of apps earning >1 review/month from
  5.0% to 9.0% — real, worth having, and confounded, since better developers earn badges.

None of that rescues a 0.7% cohort base rate. They're margins on a hard problem.

## The part that bothered me enough to keep going

Every number above describes a *single moment*. Shopify publishes an app's rank,
rating and review count as of right now, and keeps no history of any of them.

So the questions that actually matter — is this app accelerating or dying, how fast is
this category filling, which apps quietly got delisted — cannot be answered by anyone,
at any price, because the data is deleted continuously as it's produced.

So I started recording it. Daily snapshots across 84 categories and 4,966 apps,
automated (88 categories as of the latest run). It's a small, boring thing that gets more valuable every day and can't be
backfilled by anyone who starts later — including by someone with far more resources
than me.

That turned out to be the only moat I could find that gets *stronger* as AI makes
building cheaper, instead of being destroyed by it.

---

*Method: public listing pages only, throttled and cached, honouring robots.txt —
search URLs are refused in code rather than merely avoided. Review counts proxy
popularity and are not install counts. Sample n=683 of 24,032; census n=773 across 8
categories; daily tracking n=4,966 apps across 84 categories.*
