# Collapse Index

A single figure for how far the world sits between a healthy state and a
collapsed one, built from 50 measured indicators across 10 domains.

    weighted index   53.2%
    equal weight     44.8%
    time to 100%     23.1 years at current rates

## How it works

1. **`model/indicators.py`** — the 50 indicators. Each carries a current value,
   a healthy-baseline anchor, a collapse anchor, a source and a confidence flag.
   Score is the position between the two anchors, clamped to 0–100.

2. **`model/weights.py`** — weights are *derived*, not assigned. Each indicator
   is scored 1–5 on four axes:

   | axis | meaning | 5 | 1 |
   |---|---|---|---|
   | S | severity ceiling | ends civilization | local nuisance |
   | V | velocity | minutes | decades |
   | I | irreversibility | permanent | fixable in years |
   | C | coupling | drags everything down | isolated |

   `weight ∝ S^1.0 · V^0.8 · I^0.4 · C^0.6`

   Velocity carries the second-largest exponent on purpose. A hazard that can
   cross its whole range before anyone reacts deserves more weight than one of
   equal size that takes forty years. The result: nuclear carries 26.6% of all
   weight, inflation 0.28%.

3. **`model/dynamics.py`** — domains are coupled (resources → conflict →
   nuclear). Each has an intrinsic drift rate from observed trends, plus a
   non-symmetric coupling matrix. Integrating forward gives the projection and
   the time-to-100% that drives the countdown.

       dx_i/dt = r_i · (x_i/100) · (1 − x_i/100) · 4 + Σ_j K_ij · (x_j/100)

4. **`fetch/sources.py`** — live values for the handful of indicators with free
   keyless sources (NOAA CO₂, NASA GISTEMP, World Bank, UCDP, Stooq). Every
   fetcher returns `(None, None)` on failure and the stored value is kept.

5. **`model/build.py`** — runs all of it and writes `web/data.js`.

## Cadence and build time

Daily. Not because the data moves daily — most of it is annual — but because
that is the fastest cadence at which anything in the set actually changes.
Each indicator carries its own `as_of` date so the page can show what is
eight days old and what is from last January.

**The build runs at 03:47 UTC**, and that time is chosen rather than picked.
`model/schedule.py` models global news output as the weighted sum of eleven
regions, each following its own local working day, with the publishing curve
GDELT describes for its crawlers: an automated CMS dump near 05:00 local, a
lull at 05:30, then the real ramp from 06:00.

    global minimum  02:45 UTC  (44.5% of daily peak)
    quiet band      00:15 – 03:45 UTC
    chosen          03:47 UTC

03:47 is the late edge of that trough — the last quiet moment before Europe
ramps at 06:00 local. US East sits at 23:47, Europe at 04:47–05:47. Asia is
awake, but Asia contributes little to the sources this pipeline actually
reads, which are US and European institutions. Under winter time the window
moves deeper into the trough rather than out of it, so no DST handling is
needed.

Minute 47 is deliberate too: GitHub throttles scheduled workflows hardest at
the top of the hour, where runs are most often delayed or silently dropped.

    python3 model/schedule.py     # prints the curve and the reasoning

## Deploy

**GitHub Actions + any static host.** The workflow rebuilds daily and commits
`web/data.js`. Point Vercel, Netlify or GitHub Pages at `web/`.

    pip install numpy scipy
    python3 model/build.py        # local build
    python3 -m http.server -d web # local preview

Free-tier notes: GitHub Actions is free and unlimited for public repos;
scheduled runs can be delayed under load, which does not matter at this
cadence. Vercel Hobby cron is limited to daily, which is all this needs.
Cloudflare Workers Cron Triggers run more often on the free tier if you ever
want sub-daily.

## What this is not

Not a forecast. The weighting formula is mechanical but the axis scores
feeding it are judgments, several anchors have no scientific threshold behind
them, and the projection assumes current rates and couplings hold — which is
exactly what fails in a real crisis. The breakdown is the content; the
headline is a handle.
