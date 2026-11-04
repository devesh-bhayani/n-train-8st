"""Static charts for the post (PNG), drawn from the same tables as the dashboard.

    python -m n8st.figures          # after make dashboard-data

Writes docs/posts/img/verdict.png and docs/posts/img/screen.png. Colors are the
dashboard's light-mode palette (validated with the dataviz skill's checker): three
estimates in fixed categorical order, blue/red for save/cost.
"""

from __future__ import annotations

import json

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402

from n8st.config import PROJECT_ROOT  # noqa: E402

APP_DATA = PROJECT_ROOT / "app" / "data"
OUT = PROJECT_ROOT / "docs" / "posts" / "img"

S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, AXIS, SURFACE = "#e1e0d9", "#c3c2b7", "#fcfcfb"
DIV_NEG, DIV_POS = "#2a78d6", "#e34948"
BASE_W = "w2_k2_x5"

SCENARIOS = {
    "V1_sim": "V1 local, simulation timing",
    "V1_sched": "V1 local, weekend-schedule timing",
    "V1_obs": "V1 local, observed local timing",
    "V2_sched": "V2 express to 14 St, then local",
    "V2_obs": "V2, observed timing",
    "V6_W": "V6 no stop change, 8 more W trips",
}
ESTIMATES = [  # (column, label, color) in fixed order
    ("net_hours", "Riders keep today's stations", S1),
    ("net_hours_flex_calibrated", "Switching, calibrated to the weekend N", S2),
    ("net_hours_flex_upper", "Everyone switches (upper bound)", S3),
]


def _style(ax) -> None:
    from matplotlib.ticker import FuncFormatter

    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}".replace("-", "−")))
    ax.set_facecolor(SURFACE)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=10, length=0)
    ax.grid(axis="x", color=GRID, linewidth=1)
    ax.set_axisbelow(True)


def verdict(totals: pl.DataFrame, month: str) -> None:
    from matplotlib.lines import Line2D

    t = totals.filter((pl.col("month") == month) & (pl.col("weights") == BASE_W))
    rows = [s for s in SCENARIOS if s in t["scenario"].to_list()]
    height = 0.62 * len(rows) + 1.7
    fig, ax = plt.subplots(figsize=(9, height), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    present = [e for e in ESTIMATES if e[0] in t.columns]
    dodge = {c: (1 - i) * 0.22 for i, (c, _, _) in enumerate(present)}  # legend order, top down
    for col, _label, color in present:
        xs, ys, es = [], [], []
        for k, s in enumerate(rows):
            r = t.filter(pl.col("scenario") == s).row(0, named=True)
            xs.append(r[col])
            ys.append(len(rows) - 1 - k + dodge[col])
            es.append(2 * (r.get(f"se_{col}") or 0.0))
        ax.errorbar(xs, ys, xerr=es, fmt="o", color=color, ecolor=color, elinewidth=1.5,
                    capsize=0, markersize=7, markeredgecolor=SURFACE, markeredgewidth=1.5,
                    zorder=3)
    ax.axvline(0, color=INK2, linewidth=1, zorder=2)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([SCENARIOS[s] for s in reversed(rows)], color=INK2, fontsize=10)
    ax.set_xlabel("Net weighted rider-hours per weekday  (negative = riders save time)",
                  color=INK2, fontsize=10)
    ax.set_ylim(-0.5, len(rows) - 0.5)
    handles = [Line2D([], [], marker="o", linestyle="", color=c, markersize=7, label=lab)
               for _, lab, c in present]
    top = 1 - 0.62 / height
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.005, top), ncol=3,
               frameon=False, fontsize=9, labelcolor=INK2, handletextpad=0.2,
               columnspacing=1.4)
    fig.suptitle(f"Would a weekday N stop at 8 St–NYU save riders time? ({month} data)",
                 x=0.01, y=1 - 0.12 / height, ha="left", va="top", color=INK, fontsize=12,
                 fontweight="bold")
    fig.text(0.01, 1 - 0.4 / height, "Base weights; averaged over ten timetable alignments "
             "of the N; whiskers = ± 2 standard errors", ha="left", va="top", color=INK2,
             fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.72 / height))
    fig.savefig(OUT / "verdict.png", facecolor=SURFACE)
    plt.close(fig)


def screen(rank: pl.DataFrame, n_best: int = 12) -> None:
    col = f"net_hours_{BASE_W}"
    rank = rank.with_columns(label=pl.col("route") + " " + pl.col("direction").replace(
        {"S": "south", "N": "north"}) + ":  " + pl.col("from") + " → " + pl.col("to")
        + "  (" + pl.col("stops_added").cast(pl.Utf8) + ")")
    best = rank.sort(col).head(n_best)
    n_rows = rank.filter((pl.col("route") == "N")
                         & ~pl.col("scenario").is_in(best["scenario"].to_list()))
    show = pl.concat([best, n_rows]).sort(col, descending=True)
    fig, ax = plt.subplots(figsize=(9, 0.34 * show.height + 1.5), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    for k, r in enumerate(show.iter_rows(named=True)):
        c = DIV_NEG if r[col] < 0 else DIV_POS
        ax.errorbar([r[col]], [k], xerr=[2 * r["se"]], fmt="o", color=c, ecolor=c,
                    elinewidth=1.5, capsize=0, markersize=6, markeredgecolor=SURFACE,
                    markeredgewidth=1.5, zorder=3)
    ax.axvline(0, color=INK2, linewidth=1, zorder=2)
    ax.set_yticks(range(show.height))
    ax.set_yticklabels(show["label"].to_list(), color=INK2, fontsize=9)
    ax.set_xlabel("Net weighted rider-hours per weekday  (negative = riders save time)",
                  color=INK2, fontsize=10)
    fig.suptitle("Every weekday express stretch, made local: the most promising, and the N's",
                 x=0.01, ha="left", color=INK, fontsize=12, fontweight="bold")
    fig.text(0.01, 1 - 0.55 / (0.34 * show.height + 1.5),
             "Today's stations, base weights, each route averaged over four timetable "
             "alignments; whiskers = ± 2 se; (n) = stops added", ha="left", color=INK2,
             fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.75 / (0.34 * show.height + 1.5)))
    fig.savefig(OUT / "screen.png", facecolor=SURFACE)
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta_p = APP_DATA / "ledger_meta.json"
    if (APP_DATA / "ledger_totals.csv").exists() and meta_p.exists():
        meta = json.loads(meta_p.read_text())
        verdict(pl.read_csv(APP_DATA / "ledger_totals.csv"), meta["headline_month"])
        print(f"wrote {OUT / 'verdict.png'}")
    if (APP_DATA / "screen_express_runs.csv").exists():
        screen(pl.read_csv(APP_DATA / "screen_express_runs.csv"))
        print(f"wrote {OUT / 'screen.png'}")


if __name__ == "__main__":
    main()
