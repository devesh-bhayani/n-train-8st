# Phase 0: Stop the Stop replication

An independent re-implementation of Wolk's scoring formula, run on his committed `results/stops.json` and checked against his published `results/ranking.csv` (github.com/WoshuaJolk/stopthestop-data, commit 365c028). This reproduces his ranking step, not the timetable simulation or the OD download (levels 2-3 of his README).

## Published numbers reproduced

All stops, against `results/ranking.csv` (differences under 0.05 h are rounding):

| stops_compared | max_abs_diff_net_hrs | rank_mismatches |
|---|---|---|
| 356 | 0.05 | 0 |

| stop | published_net_hrs | our_net_hrs | published_rank | our_rank | match |
|---|---|---|---|---|---|
| R21 | -2867.2 | -2867.2 | 308 | 308 | yes |
| L05 | 1823.8 | 1823.8 | 1 | 1 | yes |

## 8 St-NYU and the other stops a local N would add (defaults: 50 s, walk x2, 1.3 m/s)

`net_hrs` is rider-hours saved per weekday if the stop were *closed* to the R/W; negative means closing it costs riders time.

| stop | name | routes | users | through | ride_saved_hrs | walk_added_hrs | net_hrs | rank |
|---|---|---|---|---|---|---|---|---|
| R18 | 28 St | R W | 19970 | 84327 | 1108.4 | 2534.7 | -1426.3 | 255 |
| R19 | 23 St | R W | 30763 | 74777 | 956.9 | 3602.2 | -2645.2 | 302 |
| R21 | 8 St-NYU | R W | 25423 | 53822 | 728.9 | 3596.2 | -2867.2 | 308 |
| R22 | Prince St | R W | 20909 | 45342 | 602.8 | 3949.5 | -3346.7 | 321 |

## The re-route is almost exactly linear

Wolk re-routes every trip at each stop cost. For 8 St-NYU the saving per through-rider is within ~1 s of the stop cost itself, so few riders change route. For the N scenarios this means the cost side is well approximated by *N riders on board through the added stops x seconds added*, which is what the scenario ledger will compute first.

| stop_cost_s | simulated_saving_s_per_through_rider |
|---|---|
| 30 | 28.8 |
| 70 | 68.8 |

## Sensitivity: is 8 St-NYU worth keeping under every assumption?

`walk` = where displaced riders walk to: `line` = next stop on the same line, `any` = nearest station on any line, `station` = next station of the same complex type.

| walk | cells | cells_where_closing_saves_time | worst_net_hrs | best_net_hrs | best_rank |
|---|---|---|---|---|---|
| any | 40 | 12 | -1326.8 | 789.2 | 139 |
| line | 40 | 0 | -5107.6 | -471.1 | 301 |
| station | 40 | 0 | -8448.5 | -1584.7 | 307 |

Net rider-hours if 8 St-NYU closed, walking to the next R/W stop, by stop cost (rows) and walk weight (columns):

| stop_cost | w=1.0 | w=1.5 | w=2.0 | w=2.5 | w=3.0 |
|---|---|---|---|---|---|
| 20 | -1511 | -2410 | -3310 | -4209 | -5108 |
| 30 | -1368 | -2267 | -3166 | -4065 | -4964 |
| 40 | -1219 | -2118 | -3017 | -3916 | -4815 |
| 50 | -1069 | -1968 | -2867 | -3766 | -4665 |
| 60 | -920 | -1819 | -2718 | -3617 | -4516 |
| 70 | -770 | -1669 | -2568 | -3467 | -4366 |
| 80 | -621 | -1520 | -2419 | -3318 | -4217 |
| 90 | -471 | -1370 | -2269 | -3168 | -4067 |
