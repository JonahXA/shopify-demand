# PitchMI application — working draft

**Deadline: August 10, 2026, 11:59:59 PM ET.**
Track: **AI & Software** — semifinal Kalamazoo, Sept 22. $250,000 to the winner,
then the statewide championship (April 2027) for $1M.

Eligibility, checked against the published rules:

| requirement | status |
|---|---|
| Headquartered in Michigan | ✅ East Lansing |
| Founded 2021 or later | ✅ |
| Raised < $2.5M dilutive | ✅ $0 |
| Revenue < $1.5M last 12 months | ✅ $0 |
| Traction: pilots, customers, LOIs, quotes, **or data** | ⚠️ data yes, humans pending |

---

## One-liner

Shopify shows you what an app looks like today and keeps no record of yesterday.
We record it — so for the first time you can see which apps are actually growing,
which are dying, and which categories are worth entering.

## The problem

Building software became nearly free, so marketplaces flooded. We measured it:

- **68%** of every app currently listed on the Shopify App Store launched in 2024 or later
- **35%** launched in 2026 alone
- Of a random sample of all 24,032 listings, **61% have never received a single review**
- Share of a launch cohort reaching 50 reviews: **8.5%** (2023) → **4.5%** (2024) → **0.7%** (2025)

Discovery, not build quality, is now the binding constraint — and nobody can see it,
because the data that would show it is deleted continuously.

## The insight

Shopify publishes an app's rank, rating and review count **as of right now**. It
publishes no history of any of them. So the questions that actually matter —

- is this app accelerating or dying?
- how fast is this category filling up?
- which apps quietly got delisted?
- where is demand growing faster than supply?

— have no answer anywhere, at any price, for anyone.

## The product

A daily archive of the Shopify App Store, and the derivatives it makes computable:
review velocity, rank movement, category flood rate, and churn.

Live now: **4,966 apps across 86 categories, captured daily**, fully automated.

## Why it can't be copied

**The input is elapsed time.** A competitor starting six months from now starts six
months behind and never closes the gap — no amount of funding, engineering talent or
AI compresses it. That is a deliberate choice: it is the only moat we could find that
*strengthens* as AI makes building cheaper, rather than eroding.

Everything else we evaluated — building apps, content/SEO, freelance, selling
scraped data — fails to the same force. This one is powered by it.

## Customers

1. **App developers** deciding what to build next (~24,000 listed developers)
2. **E-commerce agencies** choosing apps for clients, needing to know what's healthy
3. **Investors and acquirers** diligencing commerce software — growth data that
   doesn't otherwise exist
4. **Shopify's own ecosystem team** — the flood is their problem too

## Business model

Subscription data access, tiered by depth and history. History is the product, so
price rises naturally as the archive deepens. Marginal cost per customer ≈ $0;
marginal cost of collection ≈ $0 (runs on free-tier CI).

## Why this team

Two prior public research platforms, both built end to end:

- **ClosingLine** — pre-registered football forecasting benchmarked against the
  sportsbook closing line; narrowed the gap to the market from 2.44% to 2.09% across
  four model generations
- **PredictEdge** — pre-registered market-efficiency study of Kalshi prediction
  markets; four independent tests for exploitable edge, all reported negative, and
  the headline finding was that **57% of the market's apparent edge was our own
  measurement error, not the market's skill**

Both are public, reproducible, and report failures as carefully as successes. That
is the relevant credential here: this business is a measurement instrument, and the
track record is of building instruments that catch their own errors.

---

## Traction — the honest gap

**Have:** a working automated system, 4,966 apps under daily capture, and original
quantified findings about the market's structure.

**Need before Aug 10:** 2–3 prospective users on record. See `OUTREACH.md`.
Judges reasonably discount data an applicant produced themselves; they do not
discount an agency owner saying they want it.

**Not doing:** inventing traction. No fabricated quotes, no invented pilots,
no "in discussions with" that means nothing happened.

---

## Open items

- [ ] Send outreach (Jonah) — highest impact remaining action
- [ ] Deploy dashboard publicly
- [ ] Confirm the application form's actual fields; this draft covers the usual ones
- [ ] Decide entity status — check whether the form requires an incorporated company
      or accepts a pre-incorporation founder
- [ ] Financial model — cheap, since infrastructure is ~$0 and pricing is the only variable
