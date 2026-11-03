# Should the N stop at 8 St–NYU?

On weekdays the N runs express past 8 St–NYU, the station closest to NYU's Washington
Square campus. On weekends it already stops there. This project uses MTA open data,
simulation and machine learning to test whether a weekday stop, or a cheaper
alternative, would save riders time overall.

The method builds on Josh Wolk's
[Stop the Stop](https://github.com/WoshuaJolk/stopthestop-data) (MIT), which weighed
the time a stop costs through-riders against the time it saves the people who use it.
This project asks the opposite question: what would *adding* a stop gain?

## First findings (scheduled times, MTA GTFS valid Nov 2026)

From `make week1` ([full output](docs/findings/week1_gtfs_checks.md)):

- **Weekday daytime N and Q trains never stop at 8 St–NYU.** The N stops there only
  after about 9 pm and overnight, and all day on weekends.
- **A one-seat ride from 18 Av to 8 St already exists, twice a day.** Weekday W trips
  leave 18 Av at 07:12 and 16:41 and run via the Montague tunnel. They take 45.5 min,
  against 34.4 min on the N to 14 St plus the backtrack.
- **The 14 St backtrack is short on paper.** Downtown R/W trains leave 14 St every
  3.5–5 min in the daytime (expected wait 2.2–2.8 min) and every 5–6 min after 10 pm.
  Observed waits will be longer; measuring them is Phase 1.
- **Running the N local from 34 St to Canal costs about 150–180 s per trip** in today's
  schedule (weekend local minus weekday express). That's the price every N
  through-rider would pay.

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

## Roadmap (about 10 hours a week)

| Weeks | Work | Skills |
|---|---|---|
| 1–2 | Reproduce Wolk's numbers; check facts; start the shuttle logger | GTFS, routing |
| 3–4 | Data pipeline; Monte Carlo of the 14 St transfer wait | DuckDB, Monte Carlo |
| 5–7 | Scenario ledger: add N stops to the timetable and re-route every trip | Counterfactual routing |
| 8–12 | SimPy model of the Broadway line, with a LightGBM dwell-time model | Discrete-event simulation, LightGBM + SHAP |
| 13–15 | ML surrogate of the simulator; global sensitivity analysis | Surrogate models, Sobol indices |
| 16–17 | 2016 natural experiment, with forecasts as the counterfactual | Forecasting, causal inference |
| 18–20 | Public brief and dashboard | Streamlit, writing |

The research behind this plan is in
[docs/research/2026-11-03-research-report.md](docs/research/2026-11-03-research-report.md).
Open fact checks are in [docs/verification.md](docs/verification.md).

## Quickstart

Requires [uv](https://docs.astral.sh/uv/).

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
src/n8st/data/               GTFS and data.ny.gov download recipes
src/n8st/shuttle/            Passio client, logger, headways, summary
src/n8st/analysis/           analyses (week1_checks.py so far)
docs/                        research report, pre-registration, fact checks, findings
tests/                       pytest suite (fixtures are synthetic; see tests/fixtures)
.github/workflows/           CI and the hourly shuttle logger
```

## Data and credits

MTA data from [data.ny.gov](https://data.ny.gov) and the MTA's
[developer resources](https://www.mta.info/developers). Method inspired by Josh Wolk's
Stop the Stop. Passio endpoints are as documented by the unofficial
[PassioGo](https://github.com/athuler/PassioGo) package. This is an independent student
project, not affiliated with the MTA or NYU.
