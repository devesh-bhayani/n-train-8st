# Should the N stop at 8 St–NYU?

[![ci](https://github.com/devesh-bhayani/n-train-8st/actions/workflows/ci.yml/badge.svg)](https://github.com/devesh-bhayani/n-train-8st/actions/workflows/ci.yml)

On weekdays the N runs express past 8 St–NYU, the station closest to NYU's Washington
Square campus. On weekends it already stops there. This project uses MTA open data,
simulation and machine learning to test whether a weekday stop, or a cheaper
alternative, would save riders time overall.

The method builds on Josh Wolk's
[Stop the Stop](https://github.com/WoshuaJolk/stopthestop-data) (MIT), which weighed
the time a stop costs through-riders against the time it saves the people who use it.
This project asks the opposite question: what would *adding* a stop gain?

**Interactive summary:** `make app` (Streamlit; deployable from this repo as-is).
**Draft post:** [docs/posts/01-why-the-n-skips-nyu.md](docs/posts/01-why-the-n-skips-nyu.md).
**Methods, in plain language:** [docs/how-it-works.md](docs/how-it-works.md).

## Findings so far

- **When the N left in 2016, people stopped getting off there.** After November 7, 2016,
  exits at 28 St, 23 St, 8 St–NYU and Prince St fell **9.7%** (95% CI 6.8–12.5%)
  relative to nearby stations on other lines, with the same weeks of 2015 differenced
  out. Entries barely moved. ([natural experiment](docs/findings/natural_experiment_2016.md))
- **A local N costs its riders about 3 minutes downtown and 2 uptown**, and the R/W
  7–10 seconds, in a SimPy simulation of the Broadway line that reproduces observed
  running times within about 2%. The Q gets 26–38 seconds faster.
  ([simulation](docs/findings/simulation.md), [calibration](docs/findings/sim_calibration.md))
- **The real 14 St backtrack is worse than the timetable**: about 3 minutes' average
  wait for a downtown R/W in the daytime (2.2–2.8 scheduled), with 1 gap in 10 longer
  than 7–9 minutes. ([observed service](docs/findings/observed_service.md))
- **For a commute from 18 Av & 72 St**, replayed on 43 real weekdays: D 51.8 min median,
  N + Canal transfer 54.8, N + 14 St backtrack 57.2, a one-seat N to 8 St 50.1.
  Changing at Canal beats the backtrack by 2.5 minutes. ([commute](docs/findings/commute.md))
- **The scheduled timetable**, from `make week1` ([full output](docs/findings/week1_gtfs_checks.md)):
  weekday daytime N and Q trains never stop at 8 St–NYU; two weekday W trips run from 18
  Av to 8 St via the Montague tunnel (07:12 and 16:41, 45.5 min); running the N local
  from 34 St to Canal adds 150–180 s in today's schedule (about 210 s observed).
- **The scenario ledger** (net rider-hours per weekday, with and without letting riders
  switch to 8 St) is running on September 2026 origin–destination data.
- **Stop the Stop reproduces exactly.** An independent re-implementation matches all 356
  published stops ([details](docs/findings/phase0_wolk_replication.md)). Closing 8 St–NYU
  to the R/W costs riders time in all 80 cells of the stop-cost × walk-weight grid when
  riders walk to the next R/W or same-type station.
- **One NYU shuttle leg links Union Square to campus.** Routes E and W pick up at 14th St
  & Irving Pl, ~220 m from the subway, and stop next at 715 Broadway by 8 St–NYU, as the
  final leg of a loop through NYU Langone. On the first evening logged (Tuesday, Nov 3)
  Route E came every 15–30 minutes, an 8–16 minute expected wait, against about 3 minutes
  for a downtown R/W at 14 St ([details](docs/findings/shuttle_first_look.md)).

## Scenarios

| ID | Change |
|---|---|
| V1 | N local 34 St → Prince St on weekdays (today's weekend pattern) |
| V2 | N express to 14 St, then local (only if a crossover exists) |
| V4 | Q local instead of the N |
| V5 | V1 only in selected hours |
| V6 | More R/W service or more Sea Beach W trips; no pattern change |
| S1 | An NYU shuttle from Union Square at 5 / 10 / 15 min headways |

Assumptions and decision rules are fixed in advance in
[docs/preregistration.md](docs/preregistration.md).

## Roadmap

| Phase | Work | Skills | Status |
|---|---|---|---|
| 0 | Reproduce Wolk's numbers; check facts; start the shuttle logger | GTFS, routing | done |
| 1 | Data pipeline through GitHub Actions; observed waits and commute replay | DuckDB, Actions, Monte Carlo | done |
| 2 | Scenario ledger: own RAPTOR router, edited timetables, phase averaging, station switching calibrated to the weekend N | Counterfactual routing, placebo tests | done |
| 3 | SimPy model of the Broadway line, calibrated to observed trains; Sobol sensitivity on a GP surrogate | Discrete-event simulation, UQ | done |
| 4 | ML: week-ahead ridership forecasting, commute recommender | LightGBM, SHAP, conformal | done |
| 5 | 2016 natural experiment; weekend-vs-weekday switching | Triple difference, event study, DiD | done |
| 6 | System-wide screen of every express stretch | Batch counterfactuals | done (screen, not verdict) |
| 7 | Dashboard and public post | Streamlit, writing | draft ready |
| next | Shuttle headways once weekday daytime data accumulates (S1, H3); track-map feasibility for the screen's top stretches; does the 14–8 St crossover exist (V2)?; nested-logit switching; deploy the dashboard | | open |

The research behind this plan is in
[docs/research/2026-11-03-research-report.md](docs/research/2026-11-03-research-report.md).
Open fact checks are in [docs/verification.md](docs/verification.md).

## Quickstart

Full Mac setup: [docs/local-setup.md](docs/local-setup.md). Requires [uv](https://docs.astral.sh/uv/).

```bash
make setup     # Python 3.13 and packages
make test
make week1     # download GTFS and regenerate the schedule fact checks
make data      # MTA stations, hourly ridership and origin-destination pulls
```

`make data` calls data.ny.gov. Set `SOCRATA_APP_TOKEN` (free, from your data.ny.gov
account's developer settings) to avoid throttling. Each recipe checks a dataset's
columns before downloading and stops with the real column list if a name has changed.

## NYU shuttle logger

NYU publishes no shuttle timetable or GTFS feed, so the project records its own. The
logger polls the public Passio GO map feed (agency 1007) every 30 s and stores every
bus position as Parquet. The polls themselves are logged too, so gaps in the data are
visible. `n8st.shuttle.headways` turns positions into stop visits, headways and
expected waits at the stops near Union Square.

**On GitHub (recommended):** push this repo to GitHub as a **public** repository. The
`shuttle-logger` workflow then runs each hour from 6 am to 1 am New York time and
commits data to a separate `shuttle-data` branch, so `main` stays clean. Public repos
get unlimited Actions minutes; a private repo would run through its free quota in
under two days.

1. In the repo's Settings → Actions → General, allow workflows **Read and write
   permissions**.
2. Actions → shuttle-logger → **Run workflow**, with `minutes` set to 2, to test it.
3. After a few days: `make shuttle-pull && make shuttle-summary`.

**On your own machine:** `make shuttle-once` to test, then `make shuttle-log`, which
runs until you stop it.

Passio's feed is undocumented and may change. The logger keeps any unknown fields in
an `extra` column so nothing is lost. Poll gently: 30 s is the default, and please
don't go lower. Fall-term service ends December 22.

## Layout

```
src/n8st/config.py           station IDs, dataset IDs, paths
src/n8st/data/               GTFS, data.ny.gov recipes (keyset paging), recon, subwaydata.nyc
src/n8st/routing/            RAPTOR on platforms (numba), generalized cost
src/n8st/scenarios/          timetable edits: V1/V2/V4/V5, any express stretch made local
src/n8st/ledger/             net rider-hours, destination flexibility, phase averaging,
                             the weekend calibration, the system-wide screen
src/n8st/sim/                SimPy Broadway model, calibration, Sobol sensitivity
src/n8st/analysis/           observed service, commute replay, 2016 and weekend experiments,
                             Stop the Stop replication, shuttle first look
src/n8st/ml/                 week-ahead ridership forecasting
src/n8st/shuttle/            Passio client, logger, headways, summary
app/                         Streamlit dashboard (reads app/data/, refreshed by make dashboard-data)
docs/                        method guide, findings, pre-registration, fact checks, post draft
tests/                       pytest suite (fixtures are synthetic)
.github/workflows/           CI, data fetches, the shuttle logger, the daily subwaydata sync
```

## Data and credits

MTA data from [data.ny.gov](https://data.ny.gov) and the MTA's
[developer resources](https://www.mta.info/developers). Method inspired by Josh Wolk's
Stop the Stop. Passio endpoints are as documented by the unofficial
[PassioGo](https://github.com/athuler/PassioGo) package. This is an independent student
project, not affiliated with the MTA or NYU.
