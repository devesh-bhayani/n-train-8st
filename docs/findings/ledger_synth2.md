# Scenario ledger: does an N stop at 8 St–NYU save riders time?

OD: `od_synth2.parquet` (1,088 weekday trips between 8:00 and 18:00). Departures sampled every 120 s. `net_hours` keeps every rider's stations (fixed OD); `net_hours_flexible` lets riders to and from the 13 stations around campus switch to whichever station is cheapest for where they're going (`n8st.ledger.flex`).

Costs are generalized: in-train minutes + 2 × waiting + 2 × walking + 5 min per transfer (base weights). Negative net = riders save time overall.

## Headline (base weights, passenger-hours per weekday)

| variant | trips_changed | added_s_per_trip | hours_saved | hours_lost | net_hours | net_hours_flexible |
|---|---|---|---|---|---|---|
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 241 | 185.0 | 19.0 | 13.0 | -6.0 | -17.0 |
| V2 N local 14 St–Canal only, observed timing | 241 | 110.0 | 19.0 | 13.0 | -6.0 | -17.0 |

## Verdict against the pre-registered decision rule

Rules committed in docs/preregistration.md on 2026-11-03, before any results: (1) net saving at base weights; (2) net saving in at least 75% of the weight grid; (3) simulated R/W knock-on of at most 60 s per trip.

| variant | demand | 1_saves_at_base | 2_saves_in_75pct_of_grid | 3_knock_on_under_60s | passes |
|---|---|---|---|---|---|
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | fixed stations | 1 | 1 | 1 | 1 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | riders can switch | 1 | 1 | 1 | 1 |
| V2 N local 14 St–Canal only, observed timing | fixed stations | 1 | 1 | 1 | 1 |
| V2 N local 14 St–Canal only, observed timing | riders can switch | 1 | 1 | 1 | 1 |

## Robustness across the 13-cell weight grid

Wait/walk weight 1.5, 2, 2.5 × transfer penalty 0, 5, 10, 15 min, plus 2 × 30 min.

| variant | cells | cells_net_saving | cells_saving_flexible | best_net | worst_net |
|---|---|---|---|---|---|
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 13 | 13 | 13 | -39.0 | -1.0 |
| V2 N local 14 St–Canal only, observed timing | 13 | 12 | 13 | -37.0 | 0.0 |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (fixed stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | -1.0 | -5.0 | -11.0 | -18.0 |  |
| 2.0 | -2.0 | -6.0 | -12.0 | -19.0 | -39.0 |
| 2.5 | -3.0 | -8.0 | -14.0 | -20.0 |  |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (riders can switch stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | -5.0 | -15.0 | -27.0 | -39.0 |  |
| 2.0 | -7.0 | -17.0 | -29.0 | -41.0 | -76.0 |
| 2.5 | -9.0 | -19.0 | -31.0 | -43.0 |  |

## Who gains under V1_sim (base weights)

Destinations with the most hours saved:

| destination | riders | hours_saved | avg_min_saved |
|---|---|---|---|
| 18 Av (N) | 60.0 | 7.4 | 7.4 |
| Prince St (R W) | 22.0 | 5.5 | 14.9 |
| 8 St-NYU (R W) | 22.0 | 5.1 | 13.9 |
| 23 St (R W) | 2.0 | 0.2 | 5.6 |
| 28 St (R W) | 2.0 | 0.2 | 5.4 |
| Astor Pl (6) | 21.0 | 0.1 | 0.2 |
| Avenue M (Q) | 2.0 | 0.0 | 0.9 |
| Avenue J (Q) | 2.0 | 0.0 | 0.9 |
| Avenue H (Q) | 2.0 | 0.0 | 0.9 |
| Newkirk Plaza (B Q) | 2.0 | 0.0 | 0.8 |

Origins with the most hours saved:

| origin | riders | hours_saved |
|---|---|---|
| 18 Av (N) | 105.0 | 11.1 |
| Prince St (R W) | 20.0 | 3.7 |
| 8 St-NYU (R W) | 20.0 | 3.7 |
| Astoria-Ditmars Blvd (N W) | 25.0 | 0.3 |
| W 4 St-Wash Sq (A B C D E F M) | 20.0 | 0.1 |

Biggest winning flows (origin → destination):

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 18 Av (N) | Prince St (R W) | 21.0 | -5.4 | -15.5 |
| 18 Av (N) | 8 St-NYU (R W) | 21.0 | -5.0 | -14.4 |
| Prince St (R W) | 18 Av (N) | 20.0 | -3.7 | -11.1 |
| 8 St-NYU (R W) | 18 Av (N) | 20.0 | -3.7 | -11.0 |
| 18 Av (N) | 23 St (R W) | 1.0 | -0.1 | -8.0 |
| 18 Av (N) | 28 St (R W) | 1.0 | -0.1 | -7.6 |
| 18 Av (N) | Astor Pl (6) | 21.0 | -0.1 | -0.2 |
| W 4 St-Wash Sq (A B C D E F M) | 18 Av (N) | 20.0 | -0.1 | -0.2 |
| Astoria-Ditmars Blvd (N W) | Prince St (R W) | 1.0 | -0.1 | -3.5 |
| Astoria-Ditmars Blvd (N W) | 8 St-NYU (R W) | 1.0 | -0.1 | -3.3 |
| Astoria-Ditmars Blvd (N W) | 28 St (R W) | 1.0 | -0.1 | -3.1 |
| Astoria-Ditmars Blvd (N W) | 23 St (R W) | 1.0 | -0.1 | -3.1 |

## Who loses under V1_sim

Origins with the most hours lost:

| origin | riders | hours_lost |
|---|---|---|
| 18 Av (N) | 258.0 | 9.0 |
| Astoria-Ditmars Blvd (N W) | 127.0 | 2.6 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 20.0 | 0.6 |
| Astor Pl (6) | 20.0 | 0.3 |

Biggest losing flows:

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 14 St-Union Sq (4 5 6 L N Q R W) | 18 Av (N) | 20.0 | 0.6 | 1.8 |
| 18 Av (N) | 14 St-Union Sq (4 5 6 L N Q R W) | 21.0 | 0.4 | 1.0 |
| Astor Pl (6) | 18 Av (N) | 20.0 | 0.3 | 0.9 |
| 18 Av (N) | 21 St-Queensbridge (M) | 1.0 | 0.1 | 7.3 |
| 18 Av (N) | Roosevelt Island (M) | 1.0 | 0.1 | 7.3 |
| 18 Av (N) | Neptune Av (F) | 1.0 | 0.1 | 7.2 |
| 18 Av (N) | Avenue U (F) | 1.0 | 0.1 | 7.2 |
| 18 Av (N) | Avenue X (F) | 1.0 | 0.1 | 7.2 |
| 18 Av (N) | Kings Hwy (F) | 1.0 | 0.1 | 7.1 |
| 18 Av (N) | Avenue P (F) | 1.0 | 0.1 | 6.8 |
| 18 Av (N) | Avenue N (F) | 1.0 | 0.1 | 6.2 |
| 18 Av (N) | Bay Pkwy (F) | 1.0 | 0.1 | 5.6 |

## Net hours by hour of the day (base weights)

| hour | V1_sim | V2_obs |
|---|---|---|
| 8 | 0.2 | 0.3 |
| 9 | 0.0 | 0.0 |
| 10 | 0.0 | 0.0 |
| 11 | 0.0 | 0.0 |
| 12 | 0.0 | 0.0 |
| 13 | 0.0 | 0.0 |
| 14 | 0.0 | 0.0 |
| 15 | 0.0 | 0.0 |
| 16 | 0.0 | 0.0 |
| 17 | -6.5 | -5.9 |
