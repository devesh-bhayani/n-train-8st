# Scenario ledger: does an N stop at 8 St–NYU save riders time?

> **Superseded.** This first run used one timetable alignment and grid-aligned rider sampling, both of which bias the result (see `docs/how-it-works.md`, "Three traps"). The current numbers are in [`ledger_phase_weekday_2025_10.md`](ledger_phase_weekday_2025_10.md). Kept for the record.

OD: `od_weekday_2025_10.parquet` (4,221,752 weekday trips between 5:00 and 24:00). Departures sampled every 120 s. `net_hours` keeps every rider's stations (fixed OD); `net_hours_flexible` lets riders to and from the 13 stations around campus switch to whichever station is cheapest for where they're going (`n8st.ledger.flex`).

Costs are generalized: in-train minutes + 2 × waiting + 2 × walking + 5 min per transfer (base weights). Negative net = riders save time overall.

## Headline (base weights, passenger-hours per weekday)

| variant | trips_changed | added_s_per_trip | hours_saved | hours_lost | net_hours | net_hours_flexible |
|---|---|---|---|---|---|---|
| V2 N local 14 St–Canal only, schedule timing | 241 | 90.0 | 2,162.0 | 2,533.0 | 370.0 | -362.0 |
| V1 N local 34 St–Canal, MTA weekend timing | 241 | 150.0 | 3,503.0 | 4,086.0 | 583.0 | -75.0 |
| V5 N local only 10–4 and 7–midnight | 132 | 210.0 | 1,630.0 | 2,708.0 | 1,079.0 | 790.0 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 241 | 185.0 | 3,842.0 | 6,145.0 | 2,302.0 | 1,658.0 |
| V4 Q local instead of the N | 273 | 210.0 | 3,243.0 | 5,878.0 | 2,634.0 | 1,656.0 |
| V2 N local 14 St–Canal only, observed timing | 241 | 110.0 | 1,600.0 | 4,236.0 | 2,635.0 | 1,959.0 |
| V1 N local 34 St–Canal, observed weekday timing | 241 | 210.0 | 2,870.0 | 5,781.0 | 2,912.0 | 2,339.0 |
| V1 N local 34 St–Canal, observed weekend timing | 241 | 262.0 | 2,302.0 | 7,105.0 | 4,803.0 | 4,257.0 |

## Verdict against the pre-registered decision rule

Rules committed in docs/preregistration.md on 2026-11-03, before any results: (1) net saving at base weights; (2) net saving in at least 75% of the weight grid; (3) simulated R/W knock-on of at most 60 s per trip.

| variant | demand | 1_saves_at_base | 2_saves_in_75pct_of_grid | 3_knock_on_under_60s | passes |
|---|---|---|---|---|---|
| V1 N local 34 St–Canal, observed weekday timing | fixed stations | no | no | true | no |
| V1 N local 34 St–Canal, observed weekday timing | riders can switch | no | no | true | no |
| V1 N local 34 St–Canal, MTA weekend timing | fixed stations | no | no | true | no |
| V1 N local 34 St–Canal, MTA weekend timing | riders can switch | yes | no | true | no |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | fixed stations | no | no | true | no |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | riders can switch | no | no | true | no |
| V1 N local 34 St–Canal, observed weekend timing | fixed stations | no | no | true | no |
| V1 N local 34 St–Canal, observed weekend timing | riders can switch | no | no | true | no |
| V2 N local 14 St–Canal only, observed timing | fixed stations | no | no | true | no |
| V2 N local 14 St–Canal only, observed timing | riders can switch | no | no | true | no |
| V2 N local 14 St–Canal only, schedule timing | fixed stations | no | no | true | no |
| V2 N local 14 St–Canal only, schedule timing | riders can switch | yes | yes | true | yes |
| V4 Q local instead of the N | fixed stations | no | no | n/a | no |
| V4 Q local instead of the N | riders can switch | no | no | n/a | no |
| V5 N local only 10–4 and 7–midnight | fixed stations | no | no | n/a | no |
| V5 N local only 10–4 and 7–midnight | riders can switch | no | no | n/a | no |

## Robustness across the 13-cell weight grid

Wait/walk weight 1.5, 2, 2.5 × transfer penalty 0, 5, 10, 15 min, plus 2 × 30 min.

| variant | cells | cells_net_saving | cells_saving_flexible | best_net | worst_net |
|---|---|---|---|---|---|
| V1 N local 34 St–Canal, MTA weekend timing | 13 | 2 | 9 | -87.0 | 979.0 |
| V2 N local 14 St–Canal only, schedule timing | 13 | 2 | 11 | -54.0 | 650.0 |
| V5 N local only 10–4 and 7–midnight | 13 | 0 | 0 | 765.0 | 1,171.0 |
| V4 Q local instead of the N | 13 | 0 | 2 | 1,176.0 | 2,873.0 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 13 | 0 | 0 | 1,328.0 | 3,094.0 |
| V2 N local 14 St–Canal only, observed timing | 13 | 0 | 0 | 1,957.0 | 3,241.0 |
| V1 N local 34 St–Canal, observed weekday timing | 13 | 0 | 0 | 2,164.0 | 3,206.0 |
| V1 N local 34 St–Canal, observed weekend timing | 13 | 0 | 0 | 3,869.0 | 5,525.0 |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (fixed stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | 2,306.0 | 1,992.0 | 1,695.0 | 1,459.0 |  |
| 2.0 | 2,713.0 | 2,302.0 | 1,959.0 | 1,729.0 | 1,328.0 |
| 2.5 | 3,094.0 | 2,619.0 | 2,245.0 | 2,003.0 |  |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (riders can switch stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | 1,936.0 | 1,431.0 | 1,072.0 | 791.0 |  |
| 2.0 | 2,276.0 | 1,658.0 | 1,224.0 | 949.0 | 388.0 |
| 2.5 | 2,595.0 | 1,914.0 | 1,436.0 | 1,101.0 |  |

## Who gains under V1_sim (base weights)

Destinations with the most hours saved:

| destination | riders | hours_saved | avg_min_saved |
|---|---|---|---|
| 23 St (R W) | 14,613.6 | 448.3 | 1.8 |
| 8 St-NYU (R W) | 12,908.8 | 433.8 | 2.0 |
| Prince St (R W) | 9,007.5 | 323.0 | 2.2 |
| 28 St (R W) | 9,357.5 | 286.6 | 1.8 |
| 72 St (Q) | 18,256.5 | 181.2 | 0.6 |
| 86 St (Q) | 13,495.6 | 136.1 | 0.6 |
| 96 St (Q) | 9,646.4 | 96.3 | 0.6 |
| Lexington Av/63 St (M Q) | 8,332.2 | 60.5 | 0.4 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 4,388.2 | 56.4 | 0.8 |
| 8 Av (N) | 1,912.3 | 54.6 | 1.7 |

Origins with the most hours saved:

| origin | riders | hours_saved |
|---|---|---|
| 23 St (R W) | 13,536.8 | 332.0 |
| 8 St-NYU (R W) | 11,328.2 | 288.1 |
| 28 St (R W) | 8,696.2 | 213.1 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 15,306.1 | 185.3 |
| Prince St (R W) | 7,645.9 | 185.0 |
| 34 St-Herald Sq (B D F M N Q R W) | 15,330.7 | 154.4 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 11,245.8 | 94.7 |
| Canal St (6 J N Q R W Z) | 6,918.1 | 75.0 |
| 49 St (N R W) | 3,210.9 | 68.4 |
| 57 St-7 Av (N Q R W) | 4,428.2 | 59.3 |

Biggest winning flows (origin → destination):

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 23 St (R W) | 1,198.5 | -35.8 | -1.8 |
| 34 St-Herald Sq (B D F M N Q R W) | 8 St-NYU (R W) | 902.6 | -30.8 | -2.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 8 St-NYU (R W) | 879.0 | -26.8 | -1.8 |
| 34 St-Herald Sq (B D F M N Q R W) | 72 St (Q) | 2,349.7 | -22.4 | -0.6 |
| 23 St (R W) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 1,333.7 | -22.1 | -1.0 |
| 49 St (N R W) | 23 St (R W) | 677.9 | -20.8 | -1.8 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 72 St (Q) | 2,314.1 | -20.7 | -0.5 |
| 8 St-NYU (R W) | 34 St-Herald Sq (B D F M N Q R W) | 948.0 | -19.2 | -1.2 |
| 49 St (N R W) | 8 St-NYU (R W) | 571.0 | -18.8 | -2.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | Prince St (R W) | 554.1 | -18.6 | -2.0 |
| 34 St-Herald Sq (B D F M N Q R W) | Prince St (R W) | 472.6 | -17.7 | -2.2 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 28 St (R W) | 549.1 | -17.0 | -1.9 |

## Who loses under V1_sim

Origins with the most hours lost:

| origin | riders | hours_lost |
|---|---|---|
| 34 St-Herald Sq (B D F M N Q R W) | 36,041.9 | 440.6 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 32,318.7 | 311.1 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 29,251.1 | 287.8 |
| 57 St-7 Av (N Q R W) | 18,377.3 | 273.5 |
| 49 St (N R W) | 14,359.5 | 221.9 |
| Canal St (6 J N Q R W Z) | 18,938.3 | 193.9 |
| 59 St / Lexington Av/59 St (4 5 6 N R W) | 10,137.9 | 151.2 |
| 5 Av/59 St (N R W) | 7,516.2 | 140.2 |
| 8 Av (N) | 4,936.3 | 119.2 |
| Atlantic Av-Barclays Ctr (2 3 4 5 B D N Q R) | 10,935.1 | 101.9 |

Biggest losing flows:

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 14 St-Union Sq (4 5 6 L N Q R W) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 2,677.9 | 32.8 | 0.7 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 59 St / Lexington Av/59 St (4 5 6 N R W) | 1,434.9 | 26.2 | 1.1 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 34 St-Herald Sq (B D F M N Q R W) | 2,080.3 | 23.9 | 0.7 |
| 34 St-Herald Sq (B D F M N Q R W) | 14 St-Union Sq (4 5 6 L N Q R W) | 2,488.0 | 22.5 | 0.5 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 14 St-Union Sq (4 5 6 L N Q R W) | 3,025.3 | 22.4 | 0.4 |
| 34 St-Herald Sq (B D F M N Q R W) | Canal St (6 J N Q R W Z) | 1,230.7 | 22.4 | 1.1 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | Canal St (6 J N Q R W Z) | 1,358.7 | 21.4 | 0.9 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 5 Av/59 St (N R W) | 996.5 | 18.9 | 1.1 |
| 34 St-Herald Sq (B D F M N Q R W) | 59 St / Lexington Av/59 St (4 5 6 N R W) | 1,209.3 | 17.6 | 0.9 |
| Canal St (6 J N Q R W Z) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 1,404.0 | 16.5 | 0.7 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 49 St (N R W) | 866.6 | 13.7 | 0.9 |
| 34 St-Herald Sq (B D F M N Q R W) | 49 St (N R W) | 1,021.4 | 13.7 | 0.8 |

## Net hours by hour of the day (base weights)

| hour | V1_sched | V1_obs | V1_wkend | V2_sched | V2_obs | V4_obs | V5_obs | V1_sim |
|---|---|---|---|---|---|---|---|---|
| 5 | 18.2 | 35.7 | 61.2 | 20.3 | 32.1 | 59.3 | 0.0 | -4.1 |
| 6 | 116.7 | 162.9 | 223.5 | 81.0 | 152.8 | 134.2 | 0.0 | 100.0 |
| 7 | 126.6 | 265.1 | 355.7 | 90.5 | 228.2 | 249.8 | 0.0 | 152.9 |
| 8 | 11.3 | 247.2 | 382.3 | 1.4 | 197.4 | 278.1 | 0.0 | 156.3 |
| 9 | 49.1 | 153.8 | 241.8 | 7.9 | 135.7 | 147.3 | 38.9 | 96.3 |
| 10 | -4.8 | 85.3 | 165.1 | -6.6 | 70.1 | 112.4 | 85.1 | 56.3 |
| 11 | -21.9 | 75.3 | 147.7 | -24.9 | 54.4 | 78.6 | 76.2 | 44.9 |
| 12 | 11.1 | 95.1 | 147.8 | 29.2 | 119.7 | 100.1 | 93.3 | 69.1 |
| 13 | -26.8 | 77.6 | 158.2 | -21.8 | 95.6 | 94.8 | 80.4 | 66.2 |
| 14 | 18.9 | 121.6 | 255.6 | 9.4 | 172.8 | 143.0 | 130.2 | 145.8 |
| 15 | 32.2 | 243.0 | 456.5 | 21.8 | 189.6 | 127.3 | 203.8 | 194.2 |
| 16 | 66.6 | 384.9 | 589.5 | 36.6 | 269.2 | 198.9 | 16.2 | 273.5 |
| 17 | 179.3 | 389.7 | 599.0 | 128.9 | 423.4 | 227.6 | 0.0 | 468.7 |
| 18 | -100.3 | 215.1 | 406.1 | -71.1 | 106.2 | 258.6 | 38.6 | 113.5 |
| 19 | 58.4 | 196.6 | 285.0 | 54.1 | 156.1 | 156.8 | 153.4 | 137.0 |
| 20 | 26.1 | 50.8 | 103.7 | 1.8 | 68.6 | 116.7 | 50.8 | 119.1 |
| 21 | 59.8 | 70.6 | 125.5 | 30.6 | 92.2 | 117.2 | 70.6 | 100.9 |
| 22 | -14.2 | 46.7 | 100.4 | -6.5 | 71.7 | 58.0 | 46.7 | 32.0 |
| 23 | -23.5 | -5.3 | -1.6 | -12.2 | -0.3 | -24.3 | -5.3 | -20.2 |
