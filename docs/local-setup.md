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
- **March 14, 2027 (daylight saving):** move the logger's hours one earlier in
  `.github/workflows/shuttle-logger.yml`, as its header comment explains.
- **Fall term ends December 22.** Shuttles stop until spring; the logger keeps running
  harmlessly and just records empty polls.
