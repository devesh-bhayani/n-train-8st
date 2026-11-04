"""Grid-search the simulation's free parameters against observed trains.

    python -m n8st.sim.calibrate --days 8

Score = mean squared percentage error of median and 90th-percentile corridor times
(each route and direction, 7 am-8 pm) + squared error of the headway CV at 14 St and
8 St local platforms (observed ~0.57-0.59). Writes docs/findings/sim_calibration.md.
"""

from __future__ import annotations

import argparse
import itertools

import numpy as np
import polars as pl

from n8st.analysis import observed as ob
from n8st.config import FINDINGS_DIR, PROCESSED_DIR
from n8st.sim import broadway as bw
from n8st.sim import experiment as ex

GRID = {
    "base_dwell_s": [30.0],
    "per_pax_s": [0.08, 0.12, 0.16],
    "block_target_s": [45.0, 60.0],
    "hold": [3, 4],
    "run_noise_sd": [0.08],
    "incident_prob": [0.0, 0.02, 0.04],
}


def observed_cv(df: pl.DataFrame, days) -> float:
    cvs = []
    for stop, track in (("R20S", "A1"), ("R21S", "A1"), ("R20N", "A2"), ("R21N", "A2")):
        sub = df.filter((pl.col("stop_id") == stop) & (pl.col("track") == track)
                        & pl.col("service_day").is_in(days) & pl.col("hour").is_between(7, 19))
        for _, g in sub.group_by("service_day"):
            t = np.sort(np.array([x.timestamp() for x in g["arr"].to_list()]))
            gaps = np.diff(t)
            gaps = gaps[gaps < 1800]
            if len(gaps) > 20:
                cvs.append(gaps.std() / gaps.mean())
    return float(np.mean(cvs))


def score(sims: pl.DataFrame, obs: pl.DataFrame, reg: pl.DataFrame, cv_obs: float) -> dict:
    hours = pl.col("hour").is_between(7, 19)
    s = sims.filter(hours).group_by("direction", "route").agg(
        m=pl.col("seconds").median(), p=pl.col("seconds").quantile(0.9))
    o = obs.filter(hours).group_by("direction", "route").agg(
        om=pl.col("seconds").median(), op=pl.col("seconds").quantile(0.9))
    j = s.join(o, on=["direction", "route"])
    e_med = ((j["m"] / j["om"] - 1) ** 2).mean()
    e_p90 = ((j["p"] / j["op"] - 1) ** 2).mean()
    cv_sim = float(np.nanmean(np.concatenate([reg["cv_14st_local"].to_numpy(),
                                              reg["cv_8st"].to_numpy()])))
    return {"rmse_median_pct": 100 * e_med ** 0.5, "rmse_p90_pct": 100 * e_p90 ** 0.5,
            "cv_sim": cv_sim, "cv_obs": cv_obs,
            "score": e_med + e_p90 + (cv_sim - cv_obs) ** 2}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=8)
    args = p.parse_args()
    df = ob.load()
    weekdays = sorted(df.filter(pl.col("daytype") == "weekday")["service_day"].unique().to_list())
    # spread calibration days across the period
    idx = np.linspace(0, len(weekdays) - 1, args.days).round().astype(int)
    days = [weekdays[i] for i in sorted(set(idx))]
    cv_obs = observed_cv(df, days)
    rows = []
    keys = list(GRID)
    for values in itertools.product(*GRID.values()):
        kw = dict(zip(keys, values, strict=True))
        params = bw.Params(**kw)
        sims, obs, reg = ex.run(df, days, 1, params, ["base"])
        rows.append({**kw, **score(sims, obs, reg, cv_obs)})
        print(rows[-1], flush=True)
    res = pl.DataFrame(rows).sort("score")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    res.write_csv(PROCESSED_DIR / "sim_calibration.csv")
    best = res.row(0, named=True)
    text = "\n".join([
        "# Simulation calibration",
        "",
        f"{len(rows)} parameter sets × {len(days)} weekdays ({days[0]} … {days[-1]}), "
        "baseline only, both directions. Lower score is better.",
        "",
        ex.md(res.head(10), 3),
        "",
        "Best: " + ", ".join(f"{k}={best[k]}" for k in keys),
        "",
    ])
    (FINDINGS_DIR / "sim_calibration.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
