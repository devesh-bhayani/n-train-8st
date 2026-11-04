# Running the project on your Mac

The **shuttle logger does not need your Mac or a Claude session.** It runs on GitHub
Actions every hour and commits to the `shuttle-data` branch whether your laptop is on
or not. Everything else (downloads, analysis, models) runs locally.

## One-time setup

1. **Get a clean copy of the repo.** Put it somewhere permanent rather than in Downloads:

   ```bash
   mkdir -p ~/Projects && cd ~/Projects
   git clone https://github.com/devesh-bhayani/n-train-8st.git
   cd n-train-8st
   ```

   You can then delete the copy you made from the bundle, and the `.bundle` files.

2. **Install uv**, which manages Python and the packages. Close and reopen Terminal after.

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install the environment and check it works.** `make` comes with the Xcode command
   line tools, which you already have, since `git` works.

   ```bash
   make setup
   make test
   ```

4. **Get a free data.ny.gov app token** so MTA downloads aren't throttled. Sign in at
   data.ny.gov, open Developer Settings, create an app token, then add it to your shell:

   ```bash
   echo 'export SOCRATA_APP_TOKEN=paste-your-token-here' >> ~/.zshrc
   source ~/.zshrc
   ```

5. **Editor.** VS Code with the Python extension works well. Open the folder, then pick
   the interpreter in `.venv/` (Cmd-Shift-P, "Python: Select Interpreter"). For notebooks,
   `uv add --dev jupyterlab ipykernel`, then `uv run jupyter lab`.

## Everyday commands

| Command | What it does | Time |
|---|---|---|
| `make week1` | Download the current MTA schedule and regenerate `docs/findings/week1_gtfs_checks.md` | ~10 s |
| `make wolk` then `make phase0` | Clone Stop the Stop and rerun the replication, `docs/findings/phase0_wolk_replication.md` | seconds |
| `make shuttle-pull` then `make shuttle-first-look` | Copy the logger's data from GitHub and regenerate `docs/findings/shuttle_first_look.md` (stops, routes, headways) | seconds |
| `make shuttle-summary` | Coverage check: polls, failures and gaps per day | seconds |
| `make data` | MTA stations, hourly ridership and origin-destination pulls, filtered to this project's stations | minutes to an hour |
| `make test` / `make lint` | Run the test suite and linter before you commit | seconds |

The analyses, roughly in the order they were built. Each writes a report to
`docs/findings/`. `make mta-pull` first: it copies the MTA downloads (OD matrices,
ridership, turnstiles, observed trains) from the `mta-data` branch.

| Command | What it does | Time |
|---|---|---|
| `make observed` | Observed headways, waits and running times from subwaydata.nyc | ~1 min |
| `make commute` | Your commute replayed on 43 real weekdays, plus the recommender | ~2 min |
| `make experiment2016` / `make weekend` | The 2016 natural experiment; weekend-vs-weekday switching to 8 St | ~1 min each |
| `make calibrate`, `make sim`, `make sensitivity` | Fit, run and stress-test the Broadway simulation | 10 min to 1 h |
| `make forecast` | Week-ahead ridership forecasts | ~5 min |
| `make validate-flex OD=...` | Calibrate station switching against the weekend N | ~5 min |
| `make phase-check` | Placebo: pure shifts of the N should average to ~0 | ~10 min |
| `make ledger-phase OD=...` | The headline ledger for one OD month (default September 2026) | ~40 min |
| `make screen OD=...` | Every express stretch in the system made local | ~1 h |
| `make dashboard-data`, `make figures`, `make app` | Refresh the dashboard's tables and the post's charts; open the dashboard | seconds |

`OD=data/raw/mta_data/bulk/od/od_weekday_2026_04.parquet` picks a month. The long
runs use every core; on a laptop, start one and leave it.

## Saving your work

```bash
git add -A
git commit -m "Describe what changed"
git pull --rebase
git push
```

`git pull --rebase` matters: GitHub Actions only writes to the `shuttle-data` branch, so
`main` won't conflict, but pulling first keeps history clean if you edit on GitHub too.

## Every so often

- Check the repo's **Actions** tab. GitHub emails you if a logger run fails.
- **The logger runs around the clock** (overnight polls just record no buses). Each
  run queues the next one; to stop it, cancel the running job or disable the workflow
  in the Actions tab.
- **Fall term ends December 22.** The self-queueing stops after `STOP_AFTER`
  (2026-12-23) in `.github/workflows/shuttle-logger.yml`; the hourly schedule may still
  start the odd run. For the spring term, move `STOP_AFTER` to the term's end.
