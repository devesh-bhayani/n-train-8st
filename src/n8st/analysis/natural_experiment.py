"""Did ridership at 8 St-NYU change when the weekday N stopped stopping there?

On Monday November 7, 2016 the W returned and the weekday N went back to running express
between 34 St and Canal St. The Broadway local stations (28 St, 23 St, 8 St-NYU,
Prince St) kept the same number of trains, since the W replaced the N, but lost their
one-seat ride from the N's Brooklyn branch (Sea Beach line) and from Astoria-bound N riders.

Design: triple difference on daily turnstile counts (weekdays only)

    log(count) ~ treated x post x 2016 | unit x year + unit x post + date

- treated: turnstile units at 28 St, 23 St (Broadway), 8 St-NYU, Prince St
- controls: nearby stations on other lines (Astor Pl, Bleecker, Spring, Houston,
  Christopher, 14 St 6 Av/8 Av, 1 Av, 2 Av, 3 Av, 6 Av, 8 Av)
- post: on/after Nov 7, 2016, and the same weeks of 2015 (no change that year), so
  station-specific seasonality (e.g. NYU's semester) is differenced out
- standard errors clustered by turnstile unit

A separate regression asks whether W 4 St and 14 St-Union Sq gained riders
(Sea Beach riders switching to the D/F or transferring).

    python -m n8st.analysis.natural_experiment
"""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import pyfixest as pf

from n8st.config import FINDINGS_DIR, PROCESSED_DIR, RAW_DIR

TURNSTILE = RAW_DIR / "mta_data" / "bulk" / "turnstile"
# Remote-unit IDs (station names changed in late 2015; units did not).
TREATED = {"R082": "28 St", "R083": "23 St", "R085": "8 St-NYU", "R086": "Prince St"}
CONTROLS = {"R248", "R105", "R163", "R175", "R300", "R330", "R390", "R160", "R194", "R189",
            "R548", "R290", "R282", "R322"}  # 1 Av, 14 St, 2 Av, 3 Av, 8 Av, Astor Pl,
# Bleecker, Christopher, Houston, Spring
SPILLOVER = {"R170": "14 St-Union Sq", "R138": "W 4 St"}
CHANGE_2016 = date(2016, 11, 7)
CHANGE_2015 = date(2015, 11, 9)  # same weekday, same week of the year
PRE_WEEKS, POST_WEEKS = 8, 6  # Sep 12 - Nov 4 and Nov 7 - Dec 16 (2016)
HOLIDAYS = {date(2015, 11, 26), date(2015, 11, 27), date(2016, 11, 24), date(2016, 11, 25),
            date(2015, 10, 12), date(2016, 10, 10)}
MAX_PER_READING = 6000  # larger jumps are counter resets


def daily_counts(folder: Path = TURNSTILE) -> pl.DataFrame:
    """Daily entries and exits per turnstile unit (sum of per-turnstile counter deltas)."""
    files = [folder / f"turnstile_{y}.parquet" for y in (2015, 2016, 2017)]
    t = pl.concat([pl.read_parquet(f) for f in files if f.exists()], how="diagonal_relaxed")
    t = t.with_columns(
        ts=pl.col("date").dt.date().cast(pl.Datetime) + pl.col("time").cast(pl.Duration))
    t = t.unique(["c_a", "unit", "scp", "ts"]).sort("c_a", "unit", "scp", "ts")
    key = ["c_a", "unit", "scp"]
    t = t.with_columns(
        d_in=pl.col("entries").diff().over(key),
        d_out=pl.col("exits").diff().over(key),
    )
    ok = lambda c: pl.when(pl.col(c).is_between(0, MAX_PER_READING)).then(pl.col(c))  # noqa: E731
    t = t.with_columns(d_in=ok("d_in"), d_out=ok("d_out"))
    # A reading at 00:00-03:59 mostly counts the previous evening.
    t = t.with_columns(day=(pl.col("ts") - pl.duration(hours=4)).dt.date())
    group = (pl.when(pl.col("unit").is_in(list(TREATED))).then(pl.lit("treated"))
             .when(pl.col("unit").is_in(list(CONTROLS))).then(pl.lit("control"))
             .when(pl.col("unit").is_in(list(SPILLOVER))).then(pl.lit("spillover"))
             .otherwise(pl.lit("other")))
    names = {**TREATED, **SPILLOVER}
    return (t.with_columns(group=group,
                           station=pl.col("unit").replace_strict(names, default=pl.col("station")))
            .group_by("unit", "station", "group", "day")
            .agg(entries=pl.col("d_in").sum(), exits=pl.col("d_out").sum(),
                 readings=pl.len()))


def panel(daily: pl.DataFrame) -> pl.DataFrame:
    rows = []
    for year, change in ((2015, CHANGE_2015), (2016, CHANGE_2016)):
        start = change - timedelta(weeks=PRE_WEEKS)
        end = change + timedelta(weeks=POST_WEEKS) - timedelta(days=3)
        p = daily.filter(pl.col("day").is_between(start, end)).with_columns(
            year=pl.lit(year),
            post=(pl.col("day") >= change).cast(pl.Int8),
            week=((pl.col("day") - pl.lit(change)).dt.total_days() // 7).cast(pl.Int32),
        )
        rows.append(p)
    p = pl.concat(rows)
    p = p.filter((pl.col("day").dt.weekday() <= 5) & ~pl.col("day").is_in(list(HOLIDAYS))
                 & pl.col("group").is_in(["treated", "control", "spillover"]))
    # drop unit-days with too few readings (partial days, outages)
    p = p.filter((pl.col("readings") >= 4) & (pl.col("entries") > 50) & (pl.col("exits") > 20))
    return p.with_columns(
        unit_year=pl.col("unit") + "_" + pl.col("year").cast(pl.String),
        unit_post=pl.col("unit") + "_" + pl.col("post").cast(pl.String),
        log_entries=pl.col("entries").log(), log_exits=pl.col("exits").log(),
        log_total=(pl.col("entries") + pl.col("exits")).log(),
        y2016=(pl.col("year") == 2016).cast(pl.Int8),
    )


def ddd(p: pl.DataFrame, group: str, outcome: str) -> dict:
    d = p.filter(pl.col("group").is_in([group, "control"])).with_columns(
        ddd=((pl.col("group") == group) & (pl.col("post") == 1) & (pl.col("year") == 2016))
        .cast(pl.Int8)).to_pandas()
    fit = pf.feols(f"{outcome} ~ ddd | unit_year + unit_post + day", data=d,
                   vcov={"CRV1": "unit"})
    coef = fit.coef()["ddd"]
    se = fit.se()["ddd"]
    return {"group": group, "outcome": outcome, "effect_pct": 100 * (np.exp(coef) - 1),
            "ci_low_pct": 100 * (np.exp(coef - 1.96 * se) - 1),
            "ci_high_pct": 100 * (np.exp(coef + 1.96 * se) - 1),
            "p_value": fit.pvalue()["ddd"], "n_obs": fit._N,
            "units": int(d[d["group"] == group]["unit"].nunique())}


def event_study(p: pl.DataFrame, outcome: str = "log_total") -> pl.DataFrame:
    """Week-by-week treated-vs-control gap in 2016 minus the same gap in 2015 (ref: week -1)."""
    d = p.filter(pl.col("group").is_in(["treated", "control"])).with_columns(
        tr=(pl.col("group") == "treated").cast(pl.Int8))
    out = []
    for w in sorted(d["week"].unique().to_list()):
        if w == -1:
            out.append({"week": w, "effect_pct": 0.0, "ci_low_pct": 0.0, "ci_high_pct": 0.0})
            continue
        sub = d.filter(pl.col("week").is_in([w, -1])).with_columns(
            x=((pl.col("tr") == 1) & (pl.col("week") == w) & (pl.col("year") == 2016))
            .cast(pl.Int8)).to_pandas()
        fit = pf.feols(f"{outcome} ~ x | unit_year + unit^week + day", data=sub,
                       vcov={"CRV1": "unit"})
        c, s = fit.coef()["x"], fit.se()["x"]
        out.append({"week": w, "effect_pct": 100 * (np.exp(c) - 1),
                    "ci_low_pct": 100 * (np.exp(c - 1.96 * s) - 1),
                    "ci_high_pct": 100 * (np.exp(c + 1.96 * s) - 1)})
    return pl.DataFrame(out)


def md(df: pl.DataFrame, digits: int = 1) -> str:
    df = df.with_columns(pl.col(pl.Float64).round(digits))
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.iter_rows()]
    return "\n".join(lines)


def main() -> None:
    daily = daily_counts()
    p = panel(daily)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    p.write_parquet(PROCESSED_DIR / "turnstile_panel.parquet")

    means = (p.group_by("group", "year", "post").agg(
        units=pl.col("unit").n_unique(), mean_entries=pl.col("entries").mean(),
        mean_exits=pl.col("exits").mean()).sort("group", "year", "post"))
    at8 = (p.filter(pl.col("unit") == "R085").group_by("year", "post")
           .agg(daily_entries=pl.col("entries").sum() / pl.col("day").n_unique(),
                daily_exits=pl.col("exits").sum() / pl.col("day").n_unique())
           .sort("year", "post"))
    results = pl.DataFrame([ddd(p, g, o) for g in ("treated", "spillover")
                            for o in ("log_exits", "log_entries", "log_total")])
    es = event_study(p)
    es.write_csv(PROCESSED_DIR / "event_study.csv")
    results.write_csv(PROCESSED_DIR / "ddd_results.csv")
    at8.write_csv(PROCESSED_DIR / "ddd_8st_means.csv")

    text = "\n".join([
        "# Natural experiment: the N leaves the Broadway local (Nov 7, 2016)",
        "",
        "Daily turnstile counts, weekdays, 8 weeks before and 6 weeks after the change, with "
        "the same weeks of 2015 as a no-change comparison year. See the module docstring for "
        "the model.",
        "",
        "## Average weekday counts per turnstile unit",
        "",
        md(means, 0),
        "",
        "8 St–NYU, all units (weekday averages):",
        "",
        md(at8, 0),
        "",
        "## Triple-difference estimates",
        "",
        "Effect of the change on daily counts, in percent (95% confidence interval).",
        "`treated` = 28 St, 23 St, 8 St–NYU, Prince St; `spillover` = W 4 St, 14 St–Union Sq.",
        "",
        md(results, 2),
        "",
        "## Event study (treated vs control, 2016 minus 2015, entries + exits)",
        "",
        "Week 0 = the week of Nov 7, 2016. Week −1 is the reference. Pre-change weeks near "
        "zero support the parallel-trends assumption.",
        "",
        md(es, 1),
        "",
    ])
    path = FINDINGS_DIR / "natural_experiment_2016.md"
    path.write_text(text)
    print(text)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
