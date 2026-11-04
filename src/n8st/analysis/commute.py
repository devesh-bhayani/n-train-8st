"""Your commute, replayed on real trains, and a "D or N right now?" model.

For every departure time from home (18 Av & 72 St, Bensonhurst) between 6:30 and
10:30 am on each observed weekday, follow the trains that actually ran (subwaydata.nyc)
through each way of getting to campus:

    D          walk to 71 St, D to W 4 St, walk to campus
    N_backtrack walk to 18 Av, N to 14 St, change platforms, downtown R/W to 8 St, walk
    N_canal    N to Canal, transfer up to the northbound R/W, R/W to 8 St, walk
    N_walk     N to 14 St, walk 15 min from Union Square
    N_V1       hypothetical: the N continues local from Canal to 8 St (timed from the
               weekend N, which does exactly this)

Then train LightGBM to choose between D and the N at the moment of leaving, using only
what a rider could know then (time, weather, countdown clocks for the next trains).

    python -m n8st.analysis.commute
"""

from __future__ import annotations

import argparse
import bisect
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl

from n8st.analysis import observed as ob
from n8st.config import FINDINGS_DIR, PROCESSED_DIR, RAW_DIR

WEATHER = sorted((RAW_DIR / "mta_data" / "recon").glob("*/weather/weather_hourly.csv"))


@dataclass
class Persona:
    walk_to_71st_min: float = 7.0
    walk_to_18av_min: float = 7.0
    walk_w4_to_campus_min: float = 5.0
    walk_8st_to_campus_min: float = 4.0
    walk_union_sq_to_campus_min: float = 15.0
    platform_change_14st_min: float = 2.0
    transfer_canal_min: float = 3.0


@dataclass
class DayTrains:
    """Observed trains on one day, indexed for fast 'next train' lookups."""

    deps: dict = field(default_factory=dict)  # (stop_id, route_group) -> (times, trip_uids)
    arr: dict = field(default_factory=dict)  # (trip_uid, stop_id) -> seconds

    @classmethod
    def build(cls, day_df: pl.DataFrame, groups: dict[str, tuple[str, list[str]]]):
        self = cls()
        # dt.hour() is Int8: cast before multiplying, or 3600 * hour overflows.
        t = day_df.with_columns(
            sec=(pl.col("arr").dt.hour().cast(pl.Int32) * 3600
                 + pl.col("arr").dt.minute().cast(pl.Int32) * 60
                 + pl.col("arr").dt.second().cast(pl.Int32)).cast(pl.Float64))
        for uid, stop, sec in t.select("trip_uid", "stop_id", "sec").iter_rows():
            self.arr[(uid, stop)] = sec
        for name, (stop, routes) in groups.items():
            sub = (t.filter((pl.col("stop_id") == stop) & pl.col("route_id").is_in(routes))
                   .unique("trip_uid").sort("sec"))
            self.deps[name] = (sub["sec"].to_list(), sub["trip_uid"].to_list())
        return self

    def next(self, group: str, t: float, k: int = 0):
        """k-th train (0 = next) leaving the group's stop at or after t: (time, trip)."""
        times, uids = self.deps[group]
        i = bisect.bisect_left(times, t) + k
        return (times[i], uids[i]) if i < len(times) else (None, None)

    def ride(self, group: str, t: float, to_stop: str):
        """Board the first train of `group` at or after t that reaches to_stop."""
        times, uids = self.deps[group]
        i = bisect.bisect_left(times, t)
        while i < len(times):
            a = self.arr.get((uids[i], to_stop))
            if a is not None and a > times[i]:
                return times[i], a
            i += 1
        return None, None


GROUPS = {
    "D@71": ("B17N", ["D"]),
    "N@18": ("N05N", ["N", "W"]),
    "RW@14S": ("R20S", ["R", "W"]),
    "RW@CanalN": ("R23N", ["R", "W"]),
}


def v1_extension_s(df: pl.DataFrame) -> float:
    """Observed weekend seconds from Canal (bridge level) to 8 St on the local N."""
    s = ob.segment_times(df, "N", "Q01", "R21", "N").filter(
        pl.col("daytype").is_in(["saturday", "sunday"]))
    return float(s["seconds"].median())


def replay(df: pl.DataFrame, persona: Persona, start_h: float = 6.5, end_h: float = 10.5,
           step_s: int = 120) -> pl.DataFrame:
    p = persona
    ext = v1_extension_s(df)
    days = sorted(df.filter(pl.col("daytype") == "weekday")["service_day"].unique().to_list())
    rows = []
    for day in days:
        trains = DayTrains.build(df.filter(pl.col("service_day") == day), GROUPS)
        for t in np.arange(start_h * 3600, end_h * 3600, step_s):
            r = {"day": day, "depart_s": float(t)}
            # D
            t71 = t + p.walk_to_71st_min * 60
            d0, d1 = trains.ride("D@71", t71, "D20N")
            r["D"] = (d1 - t) / 60 + p.walk_w4_to_campus_min if d1 else None
            # N legs
            t18 = t + p.walk_to_18av_min * 60
            n_dep, n14 = trains.ride("N@18", t18, "R20N")
            _, ncanal = trains.ride("N@18", t18, "Q01N")
            if n14:
                _, a8 = trains.ride("RW@14S", n14 + p.platform_change_14st_min * 60, "R21S")
                r["N_backtrack"] = (a8 - t) / 60 + p.walk_8st_to_campus_min if a8 else None
                r["N_walk"] = (n14 - t) / 60 + p.walk_union_sq_to_campus_min
            if ncanal:
                _, a8c = trains.ride("RW@CanalN", ncanal + p.transfer_canal_min * 60, "R21N")
                r["N_canal"] = (a8c - t) / 60 + p.walk_8st_to_campus_min if a8c else None
                r["N_V1"] = (ncanal + ext - t) / 60 + p.walk_8st_to_campus_min
            # What a rider can see when leaving: countdown to the next two trains.
            nd, _ = trains.next("D@71", t71)
            nd2, _ = trains.next("D@71", t71, 1)
            nn, _ = trains.next("N@18", t18)
            nn2, _ = trains.next("N@18", t18, 1)
            r["wait_D_min"] = (nd - t71) / 60 if nd else None
            r["gap_D_min"] = (nd2 - nd) / 60 if nd and nd2 else None
            r["wait_N_min"] = (nn - t18) / 60 if nn else None
            r["gap_N_min"] = (nn2 - nn) / 60 if nn and nn2 else None
            rows.append(r)
    out = pl.DataFrame(rows).with_columns(
        hour=(pl.col("depart_s") // 3600).cast(pl.Int32),
        clock=(pl.col("depart_s") // 3600).cast(pl.Int32).cast(pl.String) + ":"
        + ((pl.col("depart_s") % 3600) // 60).cast(pl.Int32).cast(pl.String).str.zfill(2),
        dow=pl.col("day").dt.weekday(),
    )
    return out.drop_nulls(["D", "N_backtrack", "N_canal"])


def add_weather(df: pl.DataFrame) -> pl.DataFrame:
    if not WEATHER:
        return df.with_columns(temp_c=pl.lit(None), precip_mm=pl.lit(None))
    w = pl.read_csv(WEATHER[-1]).with_columns(
        ts=pl.col("time").str.to_datetime("%Y-%m-%dT%H:%M"))
    w = w.select(day=pl.col("ts").dt.date(), hour=pl.col("ts").dt.hour().cast(pl.Int32),
                 temp_c=pl.col("temperature_2m"), precip_mm=pl.col("precipitation"))
    return df.join(w, on=["day", "hour"], how="left")


def summarize(rep: pl.DataFrame) -> pl.DataFrame:
    opts = ["D", "N_backtrack", "N_canal", "N_walk", "N_V1"]
    rows = []
    for o in opts:
        s = rep[o].drop_nulls()
        best = rep.select(pl.min_horizontal(*[pl.col(x) for x in opts[:4]])).to_series()
        rows.append({"option": o, "median_min": s.median(), "mean_min": s.mean(),
                     "p90_min": s.quantile(0.9),
                     "fastest_share_pct": 100 * (rep[o] <= best + 1e-9).mean()
                     if o != "N_V1" else None})
    return pl.DataFrame(rows)


def by_hour(rep: pl.DataFrame) -> pl.DataFrame:
    return (rep.group_by("hour").agg(
        *[pl.col(o).median().alias(f"{o}_median") for o in
          ("D", "N_backtrack", "N_canal", "N_V1")],
        d_faster_pct=100 * (pl.col("D") < pl.col("N_canal")).mean())
        .sort("hour"))


FEATURES = ["hour", "minute", "dow", "wait_D_min", "gap_D_min", "wait_N_min", "gap_N_min",
            "temp_c", "precip_mm"]


def choice_model(rep: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame, dict]:
    """Predict (D time - best N time) at the moment of leaving; take D if predicted < 0.

    Time-based split: the last third of observed weekdays is the test set.
    """
    import lightgbm as lgb
    import shap

    d = rep.with_columns(
        best_N=pl.min_horizontal("N_backtrack", "N_canal"),
        minute=((pl.col("depart_s") % 3600) // 60).cast(pl.Int32),
    ).with_columns(target=pl.col("D") - pl.col("best_N"))
    days = sorted(d["day"].unique().to_list())
    cut = days[int(len(days) * 2 / 3)]
    train, test = d.filter(pl.col("day") < cut), d.filter(pl.col("day") >= cut)
    X_tr, X_te = train.select(FEATURES).to_pandas(), test.select(FEATURES).to_pandas()
    model = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.03, num_leaves=15,
                              min_child_samples=40, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, verbose=-1, random_state=0)
    model.fit(X_tr, train["target"].to_numpy())
    pred = model.predict(X_te)
    te = test.with_columns(pred=pl.Series(pred))
    oracle = pl.min_horizontal("D", "best_N")
    strategies = {
        "always D": pl.col("D"),
        "always N (best of backtrack/Canal)": pl.col("best_N"),
        "first train to arrive at home": pl.when(pl.col("wait_D_min") <= pl.col("wait_N_min"))
        .then(pl.col("D")).otherwise(pl.col("best_N")),
        "LightGBM recommender": pl.when(pl.col("pred") < 0).then(pl.col("D"))
        .otherwise(pl.col("best_N")),
        "oracle (knows the future)": oracle,
    }
    res = pl.DataFrame([
        {"strategy": k, "mean_min": te.select(v.mean()).item(),
         "p90_min": te.select(v.quantile(0.9)).item(),
         "minutes_lost_vs_oracle": te.select((v - oracle).mean()).item()}
        for k, v in strategies.items()
    ])
    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X_te)
    imp = pl.DataFrame({"feature": FEATURES,
                        "mean_abs_shap_min": np.abs(sv).mean(axis=0)}).sort(
        "mean_abs_shap_min", descending=True)
    info = {"train_days": len([x for x in days if x < cut]),
            "test_days": len([x for x in days if x >= cut]),
            "test_rows": te.height,
            "mae_min": float(np.mean(np.abs(pred - te["target"].to_numpy())))}
    return res, imp, info


def md(df: pl.DataFrame, digits: int = 1) -> str:
    df = df.with_columns(pl.col(pl.Float64, pl.Float32).round(digits))
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |"
              for r in df.iter_rows()]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=FINDINGS_DIR / "commute.md")
    args = parser.parse_args()
    df = ob.load()
    persona = Persona()
    rep = add_weather(replay(df, persona))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    rep.write_parquet(PROCESSED_DIR / "commute_replay.parquet")
    res, imp, info = choice_model(rep)
    text = "\n".join([
        "# Your commute on real trains (weekdays, leaving home 6:30–10:30 am)",
        "",
        f"{rep['day'].n_unique()} observed weekdays × a departure every 2 minutes = "
        f"{rep.height:,} trips per option, replayed on the trains that actually ran "
        "(subwaydata.nyc, Sep–Nov 2026). Minutes are door (18 Av & 72 St) to campus.",
        "",
        "Assumptions: " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in
                                    persona.__dict__.items()) + ".",
        "",
        "## Each option",
        "",
        "`fastest_share_pct` = how often the option would have been the quickest of the "
        "four real ones. N_V1 is hypothetical (the N continuing local from Canal to 8 St).",
        "",
        md(summarize(rep)),
        "",
        "## By departure hour (median minutes)",
        "",
        md(by_hour(rep)),
        "",
        "## D or N right now? A LightGBM recommender",
        "",
        f"Trained on the first {info['train_days']} weekdays, tested on the last "
        f"{info['test_days']} ({info['test_rows']:,} departures). It predicts how much "
        "faster the D will be than the best N option, from what you can know when leaving: "
        "clock time, weekday, weather and the countdown to the next two D and N trains. "
        f"Mean absolute error {info['mae_min']:.1f} min.",
        "",
        md(res, 2),
        "",
        "What drives the prediction (mean |SHAP| in minutes):",
        "",
        md(imp, 2),
        "",
    ])
    args.out.write_text(text)
    print(text)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
