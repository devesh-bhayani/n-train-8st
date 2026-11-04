# Scenario ledger: does an N stop at 8 St–NYU save riders time?

> **Superseded.** This first run used one timetable alignment and grid-aligned rider sampling, both of which bias the result (see `docs/how-it-works.md`, "Three traps"). The current numbers are in [`ledger_phase_weekday_2026_09.md`](ledger_phase_weekday_2026_09.md). Kept for the record.

OD: `od_weekday_2026_09.parquet` (4,192,711 weekday trips between 5:00 and 24:00). Departures sampled every 120 s. `net_hours` keeps every rider's stations (fixed OD); `net_hours_flexible` lets riders to and from the 13 stations around campus switch to whichever station is cheapest for where they're going (`n8st.ledger.flex`).

Costs are generalized: in-train minutes + 2 × waiting + 2 × walking + 5 min per transfer (base weights). Negative net = riders save time overall.

## Headline (base weights, passenger-hours per weekday)

| variant | trips_changed | added_s_per_trip | hours_saved | hours_lost | net_hours | net_hours_flexible |
|---|---|---|---|---|---|---|
| V2 N local 14 St–Canal only, schedule timing | 241 | 90.0 | 2,123.0 | 2,480.0 | 357.0 | -381.0 |
| V1 N local 34 St–Canal, MTA weekend timing | 241 | 150.0 | 3,412.0 | 3,994.0 | 581.0 | -81.0 |
| V5 N local only 10–4 and 7–midnight | 132 | 210.0 | 1,593.0 | 2,657.0 | 1,064.0 | 772.0 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 241 | 185.0 | 3,756.0 | 6,003.0 | 2,247.0 | 1,600.0 |
| V2 N local 14 St–Canal only, observed timing | 241 | 110.0 | 1,579.0 | 4,123.0 | 2,544.0 | 1,863.0 |
| V4 Q local instead of the N | 273 | 210.0 | 3,163.0 | 5,875.0 | 2,712.0 | 1,733.0 |
| V1 N local 34 St–Canal, observed weekday timing | 241 | 210.0 | 2,797.0 | 5,652.0 | 2,854.0 | 2,280.0 |
| V1 N local 34 St–Canal, observed weekend timing | 241 | 262.0 | 2,240.0 | 6,944.0 | 4,704.0 | 4,157.0 |

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
| V1 N local 34 St–Canal, MTA weekend timing | 13 | 2 | 9 | -63.0 | 961.0 |
| V2 N local 14 St–Canal only, schedule timing | 13 | 2 | 11 | -61.0 | 630.0 |
| V5 N local only 10–4 and 7–midnight | 13 | 0 | 0 | 765.0 | 1,151.0 |
| V4 Q local instead of the N | 13 | 0 | 1 | 1,301.0 | 2,930.0 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 13 | 0 | 0 | 1,315.0 | 3,024.0 |
| V2 N local 14 St–Canal only, observed timing | 13 | 0 | 0 | 1,893.0 | 3,127.0 |
| V1 N local 34 St–Canal, observed weekday timing | 13 | 0 | 0 | 2,128.0 | 3,135.0 |
| V1 N local 34 St–Canal, observed weekend timing | 13 | 0 | 0 | 3,799.0 | 5,404.0 |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (fixed stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | 2,244.0 | 1,941.0 | 1,664.0 | 1,442.0 |  |
| 2.0 | 2,646.0 | 2,247.0 | 1,922.0 | 1,705.0 | 1,315.0 |
| 2.5 | 3,024.0 | 2,558.0 | 2,202.0 | 1,972.0 |  |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (riders can switch stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | 1,873.0 | 1,379.0 | 1,037.0 | 769.0 |  |
| 2.0 | 2,209.0 | 1,600.0 | 1,177.0 | 919.0 | 363.0 |
| 2.5 | 2,523.0 | 1,847.0 | 1,386.0 | 1,057.0 |  |

## Who gains under V1_sim (base weights)

Destinations with the most hours saved:

| destination | riders | hours_saved | avg_min_saved |
|---|---|---|---|
| 23 St (R W) | 13,973.3 | 427.6 | 1.8 |
| 8 St-NYU (R W) | 11,873.8 | 396.5 | 2.0 |
| Prince St (R W) | 9,651.3 | 344.9 | 2.1 |
| 28 St (R W) | 8,857.9 | 271.2 | 1.8 |
| 72 St (Q) | 17,486.2 | 174.4 | 0.6 |
| 86 St (Q) | 13,362.0 | 134.1 | 0.6 |
| 96 St (Q) | 9,243.2 | 92.3 | 0.6 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 4,418.5 | 56.9 | 0.8 |
| Lexington Av/63 St (M Q) | 7,713.0 | 56.6 | 0.4 |
| 8 Av (N) | 1,810.5 | 53.1 | 1.8 |

Origins with the most hours saved:

| origin | riders | hours_saved |
|---|---|---|
| 23 St (R W) | 13,166.8 | 320.5 |
| 8 St-NYU (R W) | 10,543.3 | 270.4 |
| Prince St (R W) | 8,484.7 | 204.4 |
| 28 St (R W) | 8,296.3 | 202.2 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 15,401.1 | 184.8 |
| 34 St-Herald Sq (B D F M N Q R W) | 15,759.9 | 154.1 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 11,248.3 | 94.0 |
| Canal St (6 J N Q R W Z) | 7,177.6 | 77.0 |
| 49 St (N R W) | 3,097.4 | 67.2 |
| 57 St-7 Av (N Q R W) | 4,451.8 | 58.9 |

Biggest winning flows (origin → destination):

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 23 St (R W) | 1,155.3 | -34.2 | -1.8 |
| 34 St-Herald Sq (B D F M N Q R W) | 8 St-NYU (R W) | 829.3 | -27.9 | -2.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 8 St-NYU (R W) | 803.2 | -24.7 | -1.8 |
| 34 St-Herald Sq (B D F M N Q R W) | 72 St (Q) | 2,424.7 | -23.0 | -0.6 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | Prince St (R W) | 651.0 | -22.0 | -2.0 |
| 23 St (R W) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 1,324.8 | -22.0 | -1.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 72 St (Q) | 2,288.4 | -20.5 | -0.5 |
| 49 St (N R W) | 23 St (R W) | 655.5 | -19.7 | -1.8 |
| 34 St-Herald Sq (B D F M N Q R W) | Prince St (R W) | 519.3 | -19.3 | -2.2 |
| 49 St (N R W) | 8 St-NYU (R W) | 548.6 | -18.1 | -2.0 |
| 8 St-NYU (R W) | 34 St-Herald Sq (B D F M N Q R W) | 876.4 | -17.8 | -1.2 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 28 St (R W) | 527.9 | -16.5 | -1.9 |

## Who loses under V1_sim

Origins with the most hours lost:

| origin | riders | hours_lost |
|---|---|---|
| 34 St-Herald Sq (B D F M N Q R W) | 35,954.3 | 438.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 32,571.2 | 307.7 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 28,503.9 | 278.7 |
| 57 St-7 Av (N Q R W) | 17,875.2 | 264.0 |
| 49 St (N R W) | 13,395.2 | 205.8 |
| Canal St (6 J N Q R W Z) | 19,719.2 | 203.6 |
| 59 St / Lexington Av/59 St (4 5 6 N R W) | 9,934.3 | 146.8 |
| 5 Av/59 St (N R W) | 7,744.7 | 144.1 |
| 8 Av (N) | 4,538.8 | 111.4 |
| Atlantic Av-Barclays Ctr (2 3 4 5 B D N Q R) | 11,090.7 | 102.6 |

Biggest losing flows:

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 14 St-Union Sq (4 5 6 L N Q R W) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 2,592.2 | 31.8 | 0.7 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 59 St / Lexington Av/59 St (4 5 6 N R W) | 1,295.2 | 23.7 | 1.1 |
| 34 St-Herald Sq (B D F M N Q R W) | Canal St (6 J N Q R W Z) | 1,251.9 | 22.7 | 1.1 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | Canal St (6 J N Q R W Z) | 1,447.9 | 22.7 | 0.9 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 34 St-Herald Sq (B D F M N Q R W) | 1,968.6 | 22.7 | 0.7 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 14 St-Union Sq (4 5 6 L N Q R W) | 2,862.4 | 21.3 | 0.4 |
| 34 St-Herald Sq (B D F M N Q R W) | 14 St-Union Sq (4 5 6 L N Q R W) | 2,312.0 | 20.8 | 0.5 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 5 Av/59 St (N R W) | 924.3 | 17.9 | 1.2 |
| Canal St (6 J N Q R W Z) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 1,474.1 | 17.2 | 0.7 |
| 34 St-Herald Sq (B D F M N Q R W) | 59 St / Lexington Av/59 St (4 5 6 N R W) | 1,147.2 | 16.4 | 0.9 |
| Flushing-Main St (7) | Canal St (6 J N Q R W Z) | 492.5 | 13.3 | 1.6 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 49 St (N R W) | 839.6 | 13.3 | 1.0 |

## Net hours by hour of the day (base weights)

| hour | V1_sched | V1_obs | V1_wkend | V2_sched | V2_obs | V4_obs | V5_obs | V1_sim |
|---|---|---|---|---|---|---|---|---|
| 5 | 19.8 | 36.3 | 61.7 | 22.3 | 34.2 | 57.9 | 0.0 | 1.0 |
| 6 | 113.9 | 159.3 | 218.8 | 79.9 | 149.7 | 133.7 | 0.0 | 97.1 |
| 7 | 123.7 | 254.6 | 339.8 | 87.1 | 218.7 | 239.8 | 0.0 | 150.0 |
| 8 | 11.0 | 237.6 | 366.3 | -0.3 | 188.9 | 277.3 | 0.0 | 147.0 |
| 9 | 44.5 | 148.8 | 235.9 | 4.0 | 129.0 | 153.6 | 37.0 | 90.5 |
| 10 | -6.4 | 84.1 | 162.1 | -8.8 | 65.6 | 115.0 | 83.6 | 52.8 |
| 11 | -22.4 | 72.2 | 144.2 | -27.0 | 49.7 | 84.1 | 73.1 | 42.7 |
| 12 | 8.6 | 92.0 | 144.3 | 30.5 | 117.2 | 106.3 | 90.3 | 65.3 |
| 13 | -26.8 | 74.5 | 155.1 | -24.7 | 90.0 | 98.0 | 77.3 | 61.5 |
| 14 | 13.8 | 113.2 | 243.5 | 2.4 | 160.3 | 143.3 | 121.5 | 132.5 |
| 15 | 28.2 | 231.8 | 438.1 | 17.5 | 178.8 | 129.6 | 193.7 | 185.7 |
| 16 | 57.6 | 375.4 | 572.9 | 26.9 | 252.1 | 201.6 | 15.7 | 262.9 |
| 17 | 180.1 | 387.1 | 592.9 | 129.3 | 414.0 | 242.0 | 0.0 | 459.3 |
| 18 | -97.0 | 213.0 | 398.3 | -63.9 | 102.3 | 260.2 | 38.7 | 111.6 |
| 19 | 61.5 | 198.2 | 286.9 | 55.5 | 158.3 | 166.1 | 156.9 | 139.1 |
| 20 | 30.0 | 52.3 | 105.8 | 4.1 | 70.2 | 127.0 | 52.3 | 126.1 |
| 21 | 61.6 | 74.0 | 128.4 | 32.1 | 91.7 | 131.0 | 74.0 | 105.4 |
| 22 | -1.5 | 55.5 | 110.2 | -0.2 | 71.9 | 69.7 | 55.5 | 35.6 |
| 23 | -19.0 | -5.4 | -1.7 | -9.7 | 1.5 | -24.6 | -5.4 | -19.0 |
