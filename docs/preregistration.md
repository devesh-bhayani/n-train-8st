# Pre-registration (DRAFT: review, edit, then commit before Phase 2)

I ride this line every day and would personally benefit from an N stop at 8 St–NYU.
To keep the analysis honest, these assumptions and decision rules are fixed **before**
any scenario results are computed. The commit that removes "DRAFT" from the title is
the timestamp. Any later change goes in the changelog at the bottom, with a reason.

## Question

On weekdays, would the N train serving 8 St–NYU (or an alternative such as more
W trips, a Q-local pattern, or an NYU shuttle from Union Square) reduce the total
weighted travel time of subway riders?

## Scenarios

| ID | Change | Added stops for N riders |
|---|---|---|
| V1 | N local 34 St → Prince St, then crossover to the Manhattan Bridge (today's weekend pattern) | 28 St, 23 St, 8 St, Prince St |
| V2 | N express to 14 St, then local (only if a crossover south of 14 St exists) | 8 St, Prince St |
| V4 | Q local instead of the N | same four, for Q riders |
| V5 | V1 only in selected hours | as V1, in those hours |
| V6 | No pattern change: more R/W trains, or more Sea Beach W trips | none |
| S1 | NYU shuttle, Union Square → Washington Square, at 5 / 10 / 15 min headways | none |

## Primary metric

Net weighted passenger-hours per weekday = (time saved by riders who gain) − (time
lost by riders who are slowed down), summed over all origin–destination pairs.

## Parameters

| Parameter | Base | Sweep | Source |
|---|---|---|---|
| Stop penalty per added stop | 45 s | 20–90 s | MTA schedule differences; Wolk 50 s; Levy ~45 s |
| V1 penalty per N through-rider | 165 s (scheduled weekend local minus weekday express, 34 St → Canal) | 150–210 s | `docs/findings/week1_gtfs_checks.md` |
| Walk weight | 2.0 | 1.5–2.5 | USDOT 2016; Abrantes & Wardman 2011 |
| Wait weight | 2.0 | 1.5–2.5 | Edinburgh tram appraisal 1.8 |
| Transfer penalty | 5 min | 0–15 min (stretch 30) | Edinburgh 10; Tomhave & Khani 28.8 |
| Walking speed | 1.3 m/s | 1.1–1.4 m/s | Wolk; stahpthestahp |

## Decision rule

A scenario "supports the change" only if all three hold:

1. Net weighted passenger-hours > 0 at base values.
2. Net > 0 in at least 75% of the parameter grid.
3. In the simulation, mean extra delay to R/W riders on the Broadway local is at most
   60 s per trip at peak, beyond the scheduled stop penalty. *(threshold: decide and fix)*

All scenarios are reported, including the ones that fail. If V1/V2 fail and V6 passes,
the public argument is about V6.

## Hypotheses (from the research report, to be tested)

- H1: V2, if physically possible, passes; V1 is marginal.
- H2: V6 captures much of V1's benefit at almost no cost to through-riders.
- H3: At peak, for riders who can climb stairs, no shuttle headway the NYU fleet could run beats the R/W backtrack.

## Changelog

- 2026-11-03: draft created.
- 2026-11-04: scenarios scored. This draft was committed (Nov 3, 15:15 UTC) before any
  scenario was scored, but it was never finalized, so read it as a draft. Changes to
  *method*, all made before final results and documented in `docs/how-it-works.md` §4.
  The decision rule was not changed.
  - **Timing.** The V1 penalty comes from the calibrated simulation (185 s downtown,
    110 s uptown, plus knock-on for the R/W and Q) instead of one fixed 165 s.
    Schedule-timed and observed-timed variants are reported too.
  - **Rule 3.** The 60 s threshold stands; the simulation puts the R/W knock-on at
    7–10 s per train.
  - **Rider sampling.** Arrivals are jittered within each window. Grid-aligned
    sampling produced fake costs on MTA's 30-second schedule grid.
  - **Phase averaging.** Every result is averaged over ten alignments of the N
    (−540 … +540 s) in both baseline and scenario. On one timetable, alignment luck
    alone is worth ±1,000–2,600 rider-hours.
  - **Station switching.** Reported alongside the pre-registered fixed-station metric,
    never instead of it: an upper bound (everyone takes their cheapest station) and a
    central estimate calibrated to the weekend N (`docs/findings/flex_validation.md`).
