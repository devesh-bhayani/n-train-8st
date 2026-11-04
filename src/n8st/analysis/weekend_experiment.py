"""The weekly natural experiment: the N stops at 8 St-NYU on weekends but not weekdays.

If the one-seat ride matters, riders from the N's Brooklyn branch (Sea Beach line) should
pick 8 St-NYU as their campus-area station more often on weekends. Riders from the D's
West End line, whose service is the same all week, show how much of that difference is
just weekends being different.

    share = riders to 8 St-NYU / riders to any campus-area station
    effect = (Sea Beach weekend - Sea Beach weekday) - (West End weekend - West End weekday)

Campus-area stations: 8 St-NYU, Prince St, 14 St-Union Sq, W 4 St, Astor Pl,
Broadway-Lafayette, Canal St. Uses the 2026 origin-destination estimates (Jan-Sep).

    python -m n8st.analysis.weekend_experiment
"""

from __future__ import annotations

import polars as pl

from n8st.config import FINDINGS_DIR, PROCESSED_DIR, RAW_DIR, SEA_BEACH_STOPS

OD_CAMPUS = RAW_DIR / "mta_data" / "bulk" / "od"
STATIONS = RAW_DIR / "mta_data" / "bulk" / "stations" / "stations.parquet"
WEST_END = [f"B{n}" for n in range(12, 24)]
EIGHT_ST = 16


def complexes(gtfs_ids: list[str]) -> list[int]:
    st = pl.read_parquet(STATIONS).select(
        "gtfs_stop_id", pl.col("complex_id").cast(pl.Float64).cast(pl.Int64))
    return sorted(set(st.filter(pl.col("gtfs_stop_id").is_in(gtfs_ids))["complex_id"]))


def shares(year: int = 2026) -> pl.DataFrame:
    od = pl.read_parquet(OD_CAMPUS / f"od_campus_{year}.parquet")
    sea, west = complexes(SEA_BEACH_STOPS), complexes(WEST_END)
    campus = [16, 17, 602, 167, 407, 619, 623]
    d = od.filter(pl.col("destination").is_in(campus) & pl.col("hour").is_between(6, 21))
    d = d.with_columns(
        line=pl.when(pl.col("origin").is_in(sea)).then(pl.lit("Sea Beach (N)"))
        .when(pl.col("origin").is_in(west)).then(pl.lit("West End (D)")).otherwise(None),
        weekend=pl.col("day_of_week").is_in(["Saturday", "Sunday"]),
    ).drop_nulls("line")
    return (d.group_by("line", "weekend", "month").agg(
        to_8st=pl.col("riders").filter(pl.col("destination") == EIGHT_ST).sum(),
        to_campus=pl.col("riders").sum())
        .with_columns(share_8st_pct=100 * pl.col("to_8st") / pl.col("to_campus"))
        .sort("line", "month", "weekend"))


def main() -> None:
    s = shares()
    overall = (s.group_by("line", "weekend").agg(pl.col("to_8st").sum(), pl.col("to_campus").sum())
               .with_columns(share_8st_pct=100 * pl.col("to_8st") / pl.col("to_campus"))
               .sort("line", "weekend"))
    w = overall.pivot(on="weekend", index="line", values="share_8st_pct")
    w.columns = ["line", "weekday_share_pct", "weekend_share_pct"]
    w = w.with_columns(difference_pts=pl.col("weekend_share_pct") - pl.col("weekday_share_pct"))
    sb = w.filter(pl.col("line") == "Sea Beach (N)")["difference_pts"][0]
    we = w.filter(pl.col("line") == "West End (D)")["difference_pts"][0]
    # month-by-month difference-in-differences, for a spread
    m = s.pivot(on="weekend", index=["line", "month"], values="share_8st_pct")
    m.columns = ["line", "month", "weekday", "weekend"]
    m = m.with_columns(diff=pl.col("weekend") - pl.col("weekday"))
    mm = m.pivot(on="line", index="month", values="diff").sort("month")
    mm.columns = ["month", "sea_beach_diff", "west_end_diff"]
    mm = mm.with_columns(did_pts=pl.col("sea_beach_diff") - pl.col("west_end_diff"))
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    mm.write_csv(PROCESSED_DIR / "weekend_did_by_month.csv")

    def md(df, digits=2):
        df = df.with_columns(pl.col(pl.Float32).cast(pl.Float64)).with_columns(
            pl.col(pl.Float64).round(digits))
        lines = ["| " + " | ".join(df.columns) + " |", "|" + "---|" * len(df.columns)]
        lines += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.iter_rows()]
        return "\n".join(lines)

    text = "\n".join([
        "# The weekly natural experiment: weekend N vs weekday N",
        "",
        "Share of riders bound for campus-area stations who pick 8 St–NYU, 6 am–10 pm, "
        "2026 origin–destination estimates (January–September).",
        "",
        md(w),
        "",
        f"**Difference-in-differences: {sb - we:+.2f} percentage points.** Sea Beach riders "
        f"(whose N stops at 8 St on weekends) shift {sb:+.2f} points toward 8 St at "
        f"weekends; West End riders (same D all week) shift {we:+.2f}.",
        "",
        "Month by month (percentage points):",
        "",
        md(mm),
        "",
        "Caveat: weekend trips have different purposes (fewer classes, more leisure), which "
        "the West End comparison only partly absorbs.",
        "",
    ])
    (FINDINGS_DIR / "weekend_experiment.md").write_text(text)
    print(text)


if __name__ == "__main__":
    main()
