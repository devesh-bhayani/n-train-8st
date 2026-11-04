"""Which simulation assumptions decide the answer? A surrogate model + Sobol indices.

    python -m n8st.sim.sensitivity --samples 160 --days 6

1. Draw parameter sets with a Latin hypercube over plausible ranges.
2. For each, simulate the baseline and V1 on the same observed weekdays, recording the
   V1 effects (extra seconds for the N each way, knock-on for the R/W, relief for the Q)
   and how well the baseline reproduces observed corridor times.
3. Fit a Gaussian-process surrogate to each output (cross-validated R^2 reported).
4. Compute Sobol sensitivity indices on the surrogate (cheap: thousands of evaluations).
5. History matching: keep only parameter sets whose baseline matches observed trains
   within 5% (median error), and report the range of V1 effects among them.

Writes docs/findings/sim_sensitivity.md and data/processed/sim_sensitivity.parquet.
"""

from __future__ import annotations

import argparse
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import polars as pl
from scipy.stats import qmc

from n8st.config import FINDINGS_DIR, PROCESSED_DIR
from n8st.sim import broadway as bw
from n8st.sim import experiment as ex

# Plausible neighbourhood of the calibrated values (wider ranges gridlock the line:
# holding 4 long blocks caps throughput below the scheduled service).
RANGES = {
    "base_dwell_s": (22.0, 38.0),
    "per_pax_s": (0.06, 0.16),
    "block_target_s": (35.0, 55.0),
    "hold": (1.6, 3.4),  # rounded to 2 or 3
    "run_noise_sd": (0.04, 0.10),
    "incident_prob": (0.0, 0.035),
}
OUTPUTS = ["n_down_s", "n_up_s", "rw_knock_on_s", "q_relief_s", "baseline_error_pct"]

_STATE: dict = {}


def _init(days):
    from n8st.analysis import observed as ob

    df = ob.load()
    _STATE["df"] = df
    _STATE["days"] = days
    _STATE["s2s"] = ex.stop_to_stop(df)
    _STATE["pax"] = ex.pax_rates()
    _STATE["hourf"] = {h: v / max(ex.HOUR_PROFILE.values()) for h, v in ex.HOUR_PROFILE.items()}
    _STATE["entries"] = {(d, k): ex.entries(df, d, k) for d in days for k in ("S", "N")}
    obs = pl.concat([ex.observed_corridor(df, d, k).with_columns(direction=pl.lit(k))
                     for d in days for k in ("S", "N")])
    _STATE["obs_median"] = (obs.filter(pl.col("hour").is_between(7, 19))
                            .group_by("direction", "route").agg(m=pl.col("seconds").median()))


def _run_one(x: dict) -> dict:
    kw = {**ex.CALIBRATED, **x, "hold": int(round(x["hold"]))}
    params = bw.Params(**kw)
    params.pax_rate = _STATE["pax"]
    params.hour_factor = _STATE["hourf"]
    rows = []
    for (day, direction), ent in _STATE["entries"].items():
        for scenario in ("base", "V1"):
            recs = bw.simulate(ent, direction, scenario, _STATE["s2s"], params, seed=0)
            for r in recs:
                if r.stops and 7 * 3600 <= r.entry_s < 20 * 3600:
                    rows.append((day, direction, scenario, r.train_id, r.route,
                                 r.exit_s - r.entry_s))
    df = pl.DataFrame(rows, schema=["day", "direction", "scenario", "trip", "route", "s"],
                      orient="row")
    piv = df.pivot(on="scenario", index=["day", "direction", "trip", "route"], values="s")
    piv = piv.with_columns(d=pl.col("V1") - pl.col("base"))

    def mean_delta(route_set, direction=None):
        f = pl.col("route").is_in(route_set)
        if direction:
            f = f & (pl.col("direction") == direction)
        return float(piv.filter(f)["d"].mean())

    base = (df.filter(pl.col("scenario") == "base").group_by("direction", "route")
            .agg(sm=pl.col("s").median()).join(_STATE["obs_median"], on=["direction", "route"]))
    err = float((((base["sm"] / base["m"]) - 1) ** 2).mean() ** 0.5 * 100)
    return {**x, "n_down_s": mean_delta(["N"], "S"), "n_up_s": mean_delta(["N"], "N"),
            "rw_knock_on_s": mean_delta(["R", "W"]), "q_relief_s": -mean_delta(["Q"]),
            "baseline_error_pct": err}


def sample(n: int, seed: int = 0) -> list[dict]:
    keys = list(RANGES)
    lo = np.array([RANGES[k][0] for k in keys])
    hi = np.array([RANGES[k][1] for k in keys])
    u = qmc.LatinHypercube(d=len(keys), seed=seed).random(n)
    xs = qmc.scale(u, lo, hi)
    return [dict(zip(keys, row, strict=True)) for row in xs]


def surrogate_and_sobol(res: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    from SALib.analyze import sobol
    from SALib.sample import sobol as sobol_sample
    from sklearn.gaussian_process import GaussianProcessRegressor
    from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
    from sklearn.model_selection import cross_val_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    keys = list(RANGES)
    X = res.select(keys).to_numpy()
    problem = {"num_vars": len(keys), "names": keys, "bounds": [list(RANGES[k]) for k in keys]}
    grid = sobol_sample.sample(problem, 2048, calc_second_order=False, seed=0)
    fits, sob = [], []
    for out in OUTPUTS:
        y = res[out].to_numpy()
        kernel = ConstantKernel() * Matern(length_scale=np.ones(len(keys)), nu=2.5) \
            + WhiteKernel()
        gp = make_pipeline(StandardScaler(), GaussianProcessRegressor(
            kernel=kernel, normalize_y=True, n_restarts_optimizer=2, random_state=0))
        r2 = cross_val_score(gp, X, y, cv=5, scoring="r2")
        gp.fit(X, y)
        fits.append({"output": out, "cv_r2_mean": float(r2.mean()), "cv_r2_min": float(r2.min()),
                     "mean": float(y.mean()), "sd": float(y.std())})
        si = sobol.analyze(problem, gp.predict(grid), calc_second_order=False, seed=0)
        for k, s1, st in zip(keys, si["S1"], si["ST"], strict=True):
            sob.append({"output": out, "parameter": k, "first_order": float(s1),
                        "total": float(st)})
    return pl.DataFrame(fits), pl.DataFrame(sob)


def md(df: pl.DataFrame, digits: int = 2) -> str:
    df = df.with_columns(pl.col(pl.Float64).round(digits))
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.iter_rows()]
    return "\n".join(lines)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--samples", type=int, default=160)
    p.add_argument("--days", type=int, default=6)
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args()

    from n8st.analysis import observed as ob

    weekdays = sorted(ob.load().filter(pl.col("daytype") == "weekday")["service_day"]
                      .unique().to_list())
    idx = np.linspace(0, len(weekdays) - 1, args.days).round().astype(int)
    days = [weekdays[i] for i in sorted(set(idx))]
    xs = sample(args.samples)
    # "spawn", not fork: forking a process that has Polars' thread pool running can deadlock.
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=args.workers, initializer=_init,
                             initargs=(days,), mp_context=ctx) as pool:
        results = []
        for i, r in enumerate(pool.map(_run_one, xs)):
            results.append(r)
            if i % 20 == 0:
                print(f"  {i + 1}/{len(xs)}", flush=True)
    res = pl.DataFrame(results)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    res.write_parquet(PROCESSED_DIR / "sim_sensitivity.parquet")
    fits, sob = surrogate_and_sobol(res)

    plausible = res.filter(pl.col("baseline_error_pct") <= 5)
    summary = pl.DataFrame([{
        "output": o, "all_p10": res[o].quantile(0.1), "all_p50": res[o].median(),
        "all_p90": res[o].quantile(0.9), "plausible_p10": plausible[o].quantile(0.1),
        "plausible_p50": plausible[o].median(), "plausible_p90": plausible[o].quantile(0.9)}
        for o in OUTPUTS if o != "baseline_error_pct"])
    top = (sob.filter(pl.col("output") != "baseline_error_pct").sort("total", descending=True)
           .group_by("output", maintain_order=True).head(3))
    text = "\n".join([
        "# Simulation sensitivity: surrogate model + Sobol indices",
        "",
        f"{len(xs)} Latin-hypercube parameter sets × {len(days)} observed weekdays × both "
        "directions × (baseline, V1). Outputs are mean seconds per train, 7 am–8 pm.",
        "",
        "Parameter ranges: " + "; ".join(f"{k} {a:g}–{b:g}" for k, (a, b) in RANGES.items()),
        "",
        "## V1 effects across all parameter sets, and the plausible ones",
        "",
        f"Plausible = baseline matches observed corridor times within 5% "
        f"({plausible.height} of {res.height} sets).",
        "",
        md(summary, 1),
        "",
        "## Gaussian-process surrogate fit (5-fold cross-validated R²)",
        "",
        md(fits, 3),
        "",
        "## What drives each output (Sobol total-order indices, top 3)",
        "",
        "Total-order index = share of the output's variance due to that parameter, "
        "including its interactions.",
        "",
        md(top, 3),
        "",
    ])
    (FINDINGS_DIR / "sim_sensitivity.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
