# How it works

A guide to the methods in this repo, written to be learned from. Each section says what
the method does, why it was chosen, what it assumes, and ends with exercises: small,
self-contained changes that are worth doing yourself.

---

## 1. Data pipeline: getting around a blocked network

The development environment can't reach data.ny.gov, the MTA feeds or subwaydata.nyc, but
GitHub Actions runners can. So downloads run as workflows and land on data branches:

| Branch | Written by | What |
|---|---|---|
| `mta-data` | `fetch-data.yml`, `subwaydata-sync.yml` | MTA datasets, observed trains, recon files |
| `shuttle-data` | `shuttle-logger.yml` | NYU shuttle positions every 30 s |

`make mta-pull` and `make shuttle-pull` copy a branch into `data/raw/` without checking it
out. Two design choices worth noticing:

- **Recon before bulk.** `n8st.data.recon` first records every dataset's real columns,
  encodings (`day_of_week` is `"Monday"`, not 1) and sample rows. The bulk recipes were
  written against those files, and `socrata.require_columns` fails loudly if a column
  is renamed later.
- **Aggregate on the server.** A month of origin-destination data is ~10 million rows.
  The `od-matrix` recipe asks Socrata to `$group` by origin, destination and hour and to
  sum weekday averages, so what comes back is a few hundred thousand rows.

*Exercises.* Add a recipe for `sp9g-mzjh` (end-to-end running times) filtered to the N and
plot actual vs scheduled by month. Add `pandera` schemas for the OD matrix and fail the
workflow if a column type changes.

---

## 2. Router: RAPTOR on platforms

`n8st.routing` implements RAPTOR (Delling, Pajor & Werneck, 2012), the algorithm most
journey planners use. It works in rounds: round 1 finds everywhere reachable with one
train, round 2 with two, and so on. Each round scans every route pattern once, so a whole
network query takes about 0.3 ms in numba.

Two choices matter for this project:

- **Nodes are platforms, not stations.** `R20N` and `R20S` are different nodes. Changing
  trains in the same direction at 14 St is a cross-platform walk (30 s); switching to the
  opposite direction, which is your backtrack, takes at least 2 minutes. The MTA's own
  transfer file says 0 s for both, which would make the backtrack look free.
- **Labels carry components.** Besides arrival time, each label records waiting, in-train
  and walking time, so any generalized-cost weights can be applied afterwards without
  re-running the router.

*Exercises.* Add a `max_walk` footpath between nearby stations that aren't in the same
complex (e.g. Astor Pl ↔ 8 St–NYU). How much does that change 8 St's role?

---

## 3. Scenario timetables

`n8st.scenarios.timetable` rewrites weekday N trips. For each trip that runs express from
34 St to Canal, it inserts the local stops, times them, and shifts every later stop by the
extra time. Timing models:

- `template`: the MTA's own weekend local schedule, segment by segment (~150 s total)
- `penalty`: a fixed number of seconds per added stop, spread over the segment
- `added_by_direction` + `knock_on`: totals from the simulation, plus delays or relief
  for the R, W and Q after the corridor

*Exercises.* Write V6: add four weekday W trips from 86 St (Sea Beach) in the morning peak
by cloning the existing 07:12 trip and shifting it. Run the ledger. Is it cheaper than V1?

---

## 4. The ledger: weighted passenger-hours

`n8st.ledger` is Stop the Stop run in reverse. For each origin complex it routes riders who
arrive at random times (every 2 minutes) under the baseline and under each scenario, takes
the generalized cost to every destination, averages over the hour, and multiplies the
change by that hour's origin-destination flow:

    cost = in-train + 2 × waiting + 2 × walking + 5 min × transfers
    net  = Σ riders × (cost_scenario − cost_baseline)

Negative = riders save time overall. The result is reported across a grid of weights
(waiting/walking 1.5–2.5×, transfer penalty 0–15 min, plus 30 min), because the transfer
penalty is the assumption that matters most.

**Fixed-OD caveat.** Riders keep today's stations. Someone going to NYU who rides the D to
W 4 St today stays a W 4 St rider in the scenario, even if they would switch to the N.
So the ledger *understates* the benefit of an 8 St stop. That's conservative for the
argument, but it should be said every time the number is quoted.

**Destination flexibility** (`n8st.ledger.flex`) relaxes the caveat around campus. The 13
stations within 1.1 km of Washington Square get a 60 m grid of possible destinations.
A flow from origin *o* to station *s* is spread over the grid points for which *s* is
the cheapest station today (transit cost + 2 × walk), which is consistent with the
station people actually use. In a scenario, every point re-picks its cheapest station.
The same works in reverse for trips that start near campus. If the model can't explain
today's choice (no point prefers *s*), the flow keeps its fixed-station change, so the
adjustment never overstates the benefit.

*Exercises.* Weight the grid points by NYU building floor area or LODES jobs instead of
uniformly. Add the home end: the user lives between the N and the D, so origin-side
flexibility matters for people like them.

### Two traps this ledger fell into (and how they were found)

1. **Sampling on the timetable's grid.** Riders were first sampled every 2 minutes on
   the dot. MTA departures sit on a 30-second grid, so many simulated riders arrived
   the exact second their train left and waited zero. A scenario that delayed trains by
   90 s (a multiple of 30) kept those lucky coincidences; one that delayed them by
   110 s lost them, and looked thousands of hours worse. The tell was a 20-second gap
   in timing producing a 2,300-hour gap in results. Fix: one random arrival inside
   each 2-minute window, with the same draws for every network compared.

2. **Timetable coordination.** Even with jitter, shifting every N train later by 20–240
   seconds, with nothing else changed, "cost" 1,000–5,500 rider-hours. The MTA
   timetables the N to interleave with the W in Astoria and the Q on Broadway and in
   Brooklyn; shifting it puts N trains right behind W or Q trains and doubles some
   waits. A scenario that delays N trains after the new stops pays that penalty, but a
   real timetable would be re-planned to avoid it. Fix (`n8st.ledger.phase_avg`): shift
   all N trips by the same set of offsets (0–540 s) in both the baseline and the
   scenario and average, so coordination quality is the same on average with and
   without the change. The check: pure shifts then average to within noise of zero.
   The spread across offsets (±1,000–2,600 h) is also the honest error bar on any
   single-timetable result.

The general lesson: when a model compares two worlds, every difference between them
that isn't the policy (sampling luck, schedule alignment) must be held equal or averaged
out, and the way to find such differences is to run a "placebo" scenario that should
change nothing and see whether it does.

---

## 5. Simulation: SimPy on signal blocks

`n8st.sim.broadway` models every train between 57 St–7 Av and Canal St:

- **Blocks.** Track is cut into signal blocks (capacity-1 resources). A train holds its
  block plus two behind, so followers keep their distance. Crossovers are blocks shared
  by both tracks, so an N switching tracks must find a gap in both streams.
- **Dwell.** Passengers build up while a platform waits for a train. A late train meets a
  crowd, dwells longer, and falls further behind. That's the bunching feedback.
- **Incidents.** 2% of stops get an extra exponential hold (mean 90 s), which produces the
  slow tail of real service.
- **Replay.** Trains enter at the times they were observed entering on each real weekday.
  The scenarios reuse those entries and random numbers, so differences come from the
  timetable change, not from noise.

**Calibration** (`n8st.sim.calibrate`) grid-searches the free parameters against observed
corridor times and headway variability: median error ~2%, 90th percentile ~5%.

**Sensitivity** (`n8st.sim.sensitivity`) asks which of those free parameters decide the
answer. It runs the simulator on 160 Latin-hypercube parameter sets, fits a
Gaussian-process *surrogate* to each output (cheap to evaluate, cross-validated R²
reported), and computes Sobol indices on the surrogate. Sobol total-order indices say what
share of an output's variance each parameter explains, including interactions. Finally it
keeps only the parameter sets whose baseline still matches observed trains within 5%
(*history matching*) and reports the V1 effects among those. That's the honest
uncertainty range.

*Exercises.* Replace the fixed passenger rates with hourly rates from the hourly ridership
dataset. Add a third direction of conflict: the northbound N crossing the southbound
track. Is that real at Prince St? Check a track map. Swap the GP for LightGBM as the
surrogate and compare the Sobol rankings.

---

## 6. Natural experiment: November 7, 2016

`n8st.analysis.natural_experiment` asks whether turnstile counts at 28 St, 23 St, 8 St–NYU
and Prince St changed when the weekday N left them, against nearby stations on other
lines, with the same weeks of 2015 differenced out:

    log(count) ~ treated × post × 2016 | unit × year + unit × post + date

Read it as: how much did the treated stations' after-minus-before change in 2016 differ
from their after-minus-before in 2015, beyond what happened at the controls? The event
study plots the same thing week by week. Flat pre-weeks support the design.

Threats: the W replaced the N at those stations (same frequency, different destinations),
the Q moved off Astoria the same day, and the Second Avenue Subway opened eight weeks
later (outside the window).

*Exercises.* Re-run with exits only between 7 and 11 am (arrivals at campus). Try
synthetic control with `pysyncon`, building a weighted control from all 14 stations.

---

## 7. Your commute, replayed

`n8st.analysis.commute` leaves your door every 2 minutes on 43 real weekdays and follows
the trains that actually ran. No timetable and no averages: if the D was bunched at 8:14 on
October 6, that's in the result.

The recommender predicts "D minus best N" from what you can see when leaving (countdown to
the next two trains, time, weather). It's tested on later weeks than it trained on.
A simple rule, "take whichever train is due first", does about as well, which is a useful
result in itself: not every problem needs a model.

*Exercises.* Add the evening trip home. Add a feature for "D delayed upstream" using the
D's position two stations before 71 St.

---

## 8. Forecasting ridership a week ahead

`n8st.ml.forecast` compares four ways to forecast each station's daily entries seven days
ahead, using only information available a week earlier:

- **Seasonal naive**: same day last week. Always start with the dumbest baseline.
- **MSTL and AutoETS** (statsforecast): classical models fitted per station, evaluated with
  rolling 7-day origins so they get the same information as the others.
- **LightGBM**: one global model across 47 stations, with lagged ridership, calendar,
  holidays, weather and an approximate NYU-semester flag.

On September–October 2026 the error (WAPE) is 9.2% for the naive baseline, 7.8–8.2% for
the classical models and 7.0% for LightGBM. SHAP shows most of LightGBM's skill comes from
the average of the last four same weekdays. The semester flag matters little once lags are
in the model, because the lags already carry the semester.

**Conformal intervals** turn point forecasts into 90% ranges using the model's errors on a
calibration window. They covered only 82% of test days, because the calibration window was
summer and the test was the start of the semester: the errors changed. That's the main
weakness of split conformal (it assumes calibration and test look alike).

*Exercises.* Calibrate on September–October 2025 instead of summer 2026 (re-train the
model to end before it), or implement adaptive conformal inference, which updates the
interval width online. Try Chronos or TimesFM zero-shot on the same split.
