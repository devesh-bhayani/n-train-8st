"""Forecasting daily station ridership a week ahead: baselines vs LightGBM.

    make mta-pull && python -m n8st.ml.forecast

Data: hourly entries at ~60 stations along the Broadway line, Sea Beach / West End and
around campus (MTA Subway Hourly Ridership, Feb 2022 onward), summed to days, plus
Open-Meteo weather.

Models, all forecasting 7 days ahead (only information from a week earlier is used):
    seasonal naive   same day last week
    MSTL / AutoETS   statsforecast, per station, rolling 7-day origins over the test window
    LightGBM         one global model for all stations; lags >= 7 days, calendar,
                     holidays, an approximate NYU-semester flag, weather

Train through Aug 2026; test Sep 1 - Oct 31, 2026 (the start of the fall semester).
Also: SHAP feature importance, the NYU-semester effect at 8 St-NYU, and split-conformal
90% intervals (calibrated on Jun-Aug 2026) with their test coverage.
"""

from __future__ import annotations

from datetime import date, timedelta

import duckdb
import holidays
import numpy as np
import polars as pl

from n8st.config import FINDINGS_DIR, PROCESSED_DIR, RAW_DIR

RIDERSHIP = RAW_DIR / "mta_data" / "bulk" / "ridership"
WEATHER = sorted((RAW_DIR / "mta_data" / "recon").glob("*/weather/weather_daily.csv"))
STATIONS = RAW_DIR / "mta_data" / "bulk" / "stations" / "stations.parquet"
TEST_START, TEST_END = date(2026, 9, 1), date(2026, 10, 31)
CAL_START = date(2026, 6, 1)
EIGHT_ST = 16
HORIZON = 7


def labor_day(y: int) -> date:
    d = date(y, 9, 1)
    return d + timedelta(days=(0 - d.weekday()) % 7)


def nyu_in_session(d: date) -> int:
    """Approximate NYU semesters (VERIFY against NYU's academic calendars).

    Fall: the day after Labor Day to Dec 21; spring: the 4th Monday of January to the
    2nd Friday of May; Thanksgiving week off.
    """
    y = d.year
    ld = labor_day(y)
    # When Labor Day is late (Sep 7, 2026), classes start before it (Sep 2 that year).
    fall_start = date(y, 9, 2) if ld.day >= 7 else ld + timedelta(days=1)
    fall = (fall_start, date(y, 12, 21))
    jan = date(y, 1, 1)
    first_mon = jan + timedelta(days=(0 - jan.weekday()) % 7)
    may = date(y, 5, 1)
    first_fri = may + timedelta(days=(4 - may.weekday()) % 7)
    spring = (first_mon + timedelta(weeks=3), first_fri + timedelta(weeks=1))
    thanksgiving = date(y, 11, 22) + timedelta(days=(3 - date(y, 11, 22).weekday()) % 7)
    if thanksgiving - timedelta(days=3) <= d <= thanksgiving + timedelta(days=1):
        return 0
    return int(fall[0] <= d <= fall[1] or spring[0] <= d <= spring[1])


def load_daily() -> pl.DataFrame:
    files = sorted(RIDERSHIP.glob("hourly_focus_*.parquet"))
    if not files:
        raise SystemExit("No hourly ridership yet: run the fetch-data workflow, then make mta-pull")
    q = ", ".join(f"'{f}'" for f in files)
    df = pl.from_arrow(duckdb.sql(f"""
        SELECT CAST(transit_timestamp AS DATE) AS day,
               CAST(CAST(station_complex_id AS DOUBLE) AS INTEGER) AS complex_id,
               sum(CAST(entries AS DOUBLE)) AS entries
        FROM read_parquet([{q}], union_by_name = true)
        GROUP BY ALL
    """).arrow())
    # keep stations with nearly complete coverage
    n_days = df["day"].n_unique()
    good = df.group_by("complex_id").agg(n=pl.len()).filter(pl.col("n") >= 0.95 * n_days)
    return df.join(good.select("complex_id"), on="complex_id").sort("complex_id", "day")


def features(df: pl.DataFrame) -> pl.DataFrame:
    hol = holidays.country_holidays("US", subdiv="NY", years=range(2021, 2028))
    days = df.select("day").unique().sort("day")
    cal = days.with_columns(
        dow=pl.col("day").dt.weekday(),
        month=pl.col("day").dt.month(),
        doy=pl.col("day").dt.ordinal_day(),
        holiday=pl.col("day").map_elements(lambda d: int(d in hol), return_dtype=pl.Int8),
        nyu_session=pl.col("day").map_elements(nyu_in_session, return_dtype=pl.Int8),
    ).with_columns(
        doy_sin=(2 * np.pi * pl.col("doy") / 365.25).sin(),
        doy_cos=(2 * np.pi * pl.col("doy") / 365.25).cos(),
        covid_trend=(pl.col("day") - pl.lit(date(2022, 1, 1))).dt.total_days() / 365.25,
    )
    if WEATHER:
        w = pl.read_csv(WEATHER[-1]).select(
            day=pl.col("time").str.to_date(), tmax=pl.col("temperature_2m_max"),
            tmin=pl.col("temperature_2m_min"), precip=pl.col("precipitation_sum"),
            snow=pl.col("snowfall_sum"))
        cal = cal.join(w, on="day", how="left")
    out = df.join(cal, on="day").sort("complex_id", "day")
    lag = lambda k: pl.col("entries").shift(k).over("complex_id")  # noqa: E731
    return out.with_columns(
        lag7=lag(7), lag14=lag(14), lag21=lag(21), lag364=lag(364),
        roll28=pl.col("entries").shift(HORIZON).rolling_mean(28).over("complex_id"),
        same_dow_mean4=((lag(7) + lag(14) + lag(21) + lag(28)) / 4),
    )


FEATURES = ["complex_id", "dow", "month", "doy_sin", "doy_cos", "holiday", "nyu_session",
            "covid_trend", "tmax", "tmin", "precip", "snow", "lag7", "lag14", "lag21",
            "lag364", "roll28", "same_dow_mean4"]


def wape(y: np.ndarray, p: np.ndarray) -> float:
    return float(np.abs(y - p).sum() / np.abs(y).sum() * 100)


def fit_lightgbm(df: pl.DataFrame):
    import lightgbm as lgb

    d = df.drop_nulls(["lag7", "lag14", "lag21", "roll28"])
    train = d.filter(pl.col("day") < CAL_START)
    cal = d.filter((pl.col("day") >= CAL_START) & (pl.col("day") < TEST_START))
    test = d.filter(pl.col("day").is_between(TEST_START, TEST_END))
    cols = [c for c in FEATURES if c in d.columns]
    model = lgb.LGBMRegressor(objective="l1", n_estimators=1500, learning_rate=0.03,
                              num_leaves=63, min_child_samples=30, subsample=0.8,
                              subsample_freq=1, colsample_bytree=0.8, verbose=-1,
                              random_state=0)
    X = lambda f: f.select(cols).to_pandas().astype({"complex_id": "category"})  # noqa: E731
    model.fit(X(train), np.log1p(train["entries"].to_numpy()))
    # refit including the calibration window for test predictions? Keep it simple: the
    # calibration window measures out-of-sample error for the conformal intervals.
    pred_cal = np.expm1(model.predict(X(cal)))
    pred_test = np.expm1(model.predict(X(test)))
    return model, cols, cal.with_columns(pred=pl.Series(pred_cal)), \
        test.with_columns(pred=pl.Series(pred_test)), X


def conformal(cal: pl.DataFrame, test: pl.DataFrame, alpha: float = 0.1) -> pl.DataFrame:
    """Split-conformal intervals on relative error, per station."""
    rel = cal.with_columns(r=((pl.col("entries") - pl.col("pred")) / pl.col("pred")).abs())
    q = rel.group_by("complex_id").agg(q=pl.col("r").quantile(1 - alpha))
    t = test.join(q, on="complex_id", how="left").with_columns(
        lo=pl.col("pred") * (1 - pl.col("q")), hi=pl.col("pred") * (1 + pl.col("q")))
    return t.with_columns(covered=((pl.col("entries") >= pl.col("lo"))
                                   & (pl.col("entries") <= pl.col("hi"))).cast(pl.Int8))


def statsforecast_cv(df: pl.DataFrame) -> pl.DataFrame:
    """Rolling 7-day-ahead forecasts from MSTL and AutoETS over the test window."""
    from statsforecast import StatsForecast
    from statsforecast.models import MSTL, AutoETS

    sf_df = df.select(unique_id=pl.col("complex_id").cast(pl.String), ds=pl.col("day"),
                      y=pl.col("entries")).filter(pl.col("ds") <= TEST_END).to_pandas()
    sf = StatsForecast(models=[MSTL(season_length=[7, 365]), AutoETS(season_length=7)],
                       freq="D", n_jobs=-1)
    n_windows = ((TEST_END - TEST_START).days + 1) // HORIZON
    cv = sf.cross_validation(df=sf_df, h=HORIZON, step_size=HORIZON, n_windows=n_windows)
    return pl.from_pandas(cv.reset_index() if "unique_id" not in cv.columns else cv)


def md(df: pl.DataFrame, digits: int = 1) -> str:
    df = df.with_columns(pl.col(pl.Float64, pl.Float32).round(digits))
    lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join("" if v is None else str(v) for v in r) + " |"
              for r in df.iter_rows()]
    return "\n".join(lines)


def main() -> None:
    import shap

    daily = load_daily()
    df = features(daily)
    model, cols, cal, test, X = fit_lightgbm(df)
    test = conformal(cal, test)

    naive = test.with_columns(naive=pl.col("lag7"))
    rows = [{"model": "seasonal naive (last week)", "WAPE_%": wape(naive["entries"].to_numpy(),
                                                                naive["naive"].to_numpy())},
            {"model": "LightGBM (global)", "WAPE_%": wape(test["entries"].to_numpy(),
                                                       test["pred"].to_numpy())}]
    try:
        cv = statsforecast_cv(daily)
        cv = cv.with_columns(complex_id=pl.col("unique_id").cast(pl.Int64), day=pl.col("ds")
                             .cast(pl.Date))
        cvj = cv.join(test.select("complex_id", "day"), on=["complex_id", "day"])
        for m in ("MSTL", "AutoETS"):
            rows.append({"model": f"{m} (statsforecast, rolling)",
                         "WAPE_%": wape(cvj["y"].to_numpy(), cvj[m].to_numpy())})
    except Exception as e:  # keep going without the statistical baselines
        rows.append({"model": f"statsforecast failed: {e!r}"[:80], "WAPE_%": None})
    metrics = pl.DataFrame(rows)

    sample = test.sample(n=min(4000, test.height), seed=0)
    sv = shap.TreeExplainer(model).shap_values(X(sample))
    imp = pl.DataFrame({"feature": cols, "mean_abs_shap": np.abs(sv).mean(axis=0)}).sort(
        "mean_abs_shap", descending=True)

    # The semester effect at 8 St-NYU: SHAP of nyu_session (log scale -> percent).
    e8 = df.filter((pl.col("complex_id") == EIGHT_ST) & pl.col("day").is_between(
        date(2025, 1, 1), TEST_END)).drop_nulls(["lag7", "lag14", "lag21", "roll28"])
    session_effect = None
    if e8.height and "nyu_session" in cols:
        sv8 = shap.TreeExplainer(model).shap_values(X(e8))
        j = cols.index("nyu_session")
        e8 = e8.with_columns(shap_session=pl.Series(sv8[:, j]))
        session_effect = (e8.group_by("nyu_session", (pl.col("dow") <= 5).alias("weekday"))
                          .agg(pct=(pl.col("shap_session").mean().exp() - 1) * 100,
                               days=pl.len()).sort("weekday", "nyu_session"))

    per_station = (test.group_by("complex_id").agg(
        wape=(pl.col("entries") - pl.col("pred")).abs().sum() / pl.col("entries").sum() * 100,
        coverage=pl.col("covered").mean() * 100, mean_daily=pl.col("entries").mean())
        .sort("mean_daily", descending=True))
    names = {}
    if STATIONS.exists():
        st = pl.read_parquet(STATIONS).select(
            pl.col("complex_id").cast(pl.Float64).cast(pl.Int64), "stop_name")
        names = dict(st.group_by("complex_id").agg(pl.col("stop_name").first()).iter_rows())
    per_station = per_station.with_columns(
        station=pl.col("complex_id").replace_strict(names, default="?")).select(
        "station", "mean_daily", "wape", "coverage")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    test.filter(pl.col("complex_id") == EIGHT_ST).select(
        "day", "entries", "pred", "lo", "hi").write_csv(PROCESSED_DIR / "forecast_8st.csv")
    text = "\n".join([
        "# Forecasting daily ridership a week ahead",
        "",
        f"{daily['complex_id'].n_unique()} stations, {daily['day'].min()} to "
        f"{daily['day'].max()}. Test: {TEST_START} to {TEST_END}. Every model only uses "
        "information available 7 days before the day it forecasts.",
        "",
        "## Accuracy on the test window (WAPE: total absolute error / total riders)",
        "",
        md(metrics, 2),
        "",
        "## What LightGBM relies on (mean |SHAP|, log-riders)",
        "",
        md(imp, 3),
        "",
        "## The NYU semester at 8 St–NYU",
        "",
        "Average SHAP contribution of the semester flag to the forecast, as a percent "
        "change in riders (2025–2026 days). The flag uses approximate semester dates.",
        "",
        md(session_effect, 1) if session_effect is not None else "_not estimated_",
        "",
        "## Per station (test window), with 90% conformal interval coverage",
        "",
        md(per_station.head(25), 1),
        "",
        f"Overall interval coverage: {test['covered'].mean() * 100:.1f}% (target 90%).",
        "",
    ])
    path = FINDINGS_DIR / "forecasting.md"
    path.write_text(text)
    print(text)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
