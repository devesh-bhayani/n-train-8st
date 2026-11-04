# Scenario ledger: does an N stop at 8 St–NYU save riders time?

> **Superseded.** This first run used one timetable alignment and grid-aligned rider sampling, both of which bias the result (see `docs/how-it-works.md`, "Three traps"). The current numbers are in [`ledger_phase_weekday_2026_04.md`](ledger_phase_weekday_2026_04.md). Kept for the record.

OD: `od_weekday_2026_04.parquet` (4,214,112 weekday trips between 5:00 and 24:00). Departures sampled every 120 s. `net_hours` keeps every rider's stations (fixed OD); `net_hours_flexible` lets riders to and from the 13 stations around campus switch to whichever station is cheapest for where they're going (`n8st.ledger.flex`).

Costs are generalized: in-train minutes + 2 × waiting + 2 × walking + 5 min per transfer (base weights). Negative net = riders save time overall.

## Headline (base weights, passenger-hours per weekday)

| variant | trips_changed | added_s_per_trip | hours_saved | hours_lost | net_hours | net_hours_flexible |
|---|---|---|---|---|---|---|
| V2 N local 14 St–Canal only, schedule timing | 241 | 90.0 | 2,121.0 | 2,548.0 | 427.0 | -306.0 |
| V1 N local 34 St–Canal, MTA weekend timing | 241 | 150.0 | 3,457.0 | 4,114.0 | 657.0 | -1.0 |
| V5 N local only 10–4 and 7–midnight | 132 | 210.0 | 1,606.0 | 2,735.0 | 1,129.0 | 838.0 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 241 | 185.0 | 3,782.0 | 6,177.0 | 2,395.0 | 1,751.0 |
| V4 Q local instead of the N | 273 | 210.0 | 3,198.0 | 5,849.0 | 2,651.0 | 1,685.0 |
| V2 N local 14 St–Canal only, observed timing | 241 | 110.0 | 1,562.0 | 4,256.0 | 2,694.0 | 2,018.0 |
| V1 N local 34 St–Canal, observed weekday timing | 241 | 210.0 | 2,834.0 | 5,824.0 | 2,990.0 | 2,417.0 |
| V1 N local 34 St–Canal, observed weekend timing | 241 | 262.0 | 2,266.0 | 7,148.0 | 4,882.0 | 4,336.0 |

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
| V1 N local 34 St–Canal, MTA weekend timing | 13 | 1 | 8 | -13.0 | 1,040.0 |
| V2 N local 14 St–Canal only, schedule timing | 13 | 0 | 11 | 4.0 | 697.0 |
| V5 N local only 10–4 and 7–midnight | 13 | 0 | 0 | 823.0 | 1,223.0 |
| V4 Q local instead of the N | 13 | 0 | 2 | 1,146.0 | 2,904.0 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 13 | 0 | 0 | 1,431.0 | 3,197.0 |
| V2 N local 14 St–Canal only, observed timing | 13 | 0 | 0 | 2,008.0 | 3,305.0 |
| V1 N local 34 St–Canal, observed weekday timing | 13 | 0 | 0 | 2,240.0 | 3,283.0 |
| V1 N local 34 St–Canal, observed weekend timing | 13 | 0 | 0 | 3,936.0 | 5,607.0 |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (fixed stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | 2,378.0 | 2,069.0 | 1,781.0 | 1,550.0 |  |
| 2.0 | 2,800.0 | 2,395.0 | 2,060.0 | 1,834.0 | 1,431.0 |
| 2.5 | 3,197.0 | 2,725.0 | 2,360.0 | 2,122.0 |  |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (riders can switch stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | 2,007.0 | 1,508.0 | 1,161.0 | 885.0 |  |
| 2.0 | 2,363.0 | 1,751.0 | 1,324.0 | 1,056.0 | 491.0 |
| 2.5 | 2,698.0 | 2,020.0 | 1,553.0 | 1,220.0 |  |

## Who gains under V1_sim (base weights)

Destinations with the most hours saved:

| destination | riders | hours_saved | avg_min_saved |
|---|---|---|---|
| 23 St (R W) | 14,425.6 | 439.2 | 1.8 |
| 8 St-NYU (R W) | 12,146.5 | 409.2 | 2.0 |
| Prince St (R W) | 8,685.6 | 311.5 | 2.2 |
| 28 St (R W) | 9,221.0 | 284.7 | 1.9 |
| 72 St (Q) | 17,844.0 | 178.0 | 0.6 |
| 86 St (Q) | 13,621.2 | 137.8 | 0.6 |
| 96 St (Q) | 9,342.5 | 93.0 | 0.6 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 4,465.7 | 57.6 | 0.8 |
| 8 Av (N) | 1,839.3 | 54.4 | 1.8 |
| Lexington Av/63 St (M Q) | 7,063.8 | 52.7 | 0.4 |

Origins with the most hours saved:

| origin | riders | hours_saved |
|---|---|---|
| 23 St (R W) | 13,714.3 | 333.0 |
| 8 St-NYU (R W) | 11,046.0 | 279.4 |
| 28 St (R W) | 8,779.8 | 214.4 |
| Prince St (R W) | 7,805.8 | 188.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 15,728.8 | 187.8 |
| 34 St-Herald Sq (B D F M N Q R W) | 15,607.8 | 152.0 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 11,001.7 | 91.2 |
| Canal St (6 J N Q R W Z) | 6,980.5 | 75.2 |
| 49 St (N R W) | 3,320.0 | 70.9 |
| 57 St-7 Av (N Q R W) | 4,605.6 | 61.4 |

Biggest winning flows (origin → destination):

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 23 St (R W) | 1,248.4 | -37.3 | -1.8 |
| 34 St-Herald Sq (B D F M N Q R W) | 8 St-NYU (R W) | 844.3 | -28.6 | -2.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 8 St-NYU (R W) | 852.0 | -26.1 | -1.8 |
| 23 St (R W) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 1,397.3 | -23.3 | -1.0 |
| 34 St-Herald Sq (B D F M N Q R W) | 72 St (Q) | 2,413.8 | -22.9 | -0.6 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 72 St (Q) | 2,392.7 | -21.5 | -0.5 |
| 49 St (N R W) | 23 St (R W) | 704.2 | -21.4 | -1.8 |
| 49 St (N R W) | 8 St-NYU (R W) | 580.6 | -19.2 | -2.0 |
| 8 St-NYU (R W) | 34 St-Herald Sq (B D F M N Q R W) | 913.0 | -18.5 | -1.2 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | Prince St (R W) | 520.7 | -17.4 | -2.0 |
| 34 St-Herald Sq (B D F M N Q R W) | Prince St (R W) | 458.5 | -17.0 | -2.2 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 28 St (R W) | 550.6 | -17.0 | -1.9 |

## Who loses under V1_sim

Origins with the most hours lost:

| origin | riders | hours_lost |
|---|---|---|
| 34 St-Herald Sq (B D F M N Q R W) | 36,656.2 | 450.9 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 32,884.2 | 314.9 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 28,789.9 | 282.6 |
| 57 St-7 Av (N Q R W) | 18,870.7 | 280.6 |
| 49 St (N R W) | 14,740.0 | 226.8 |
| Canal St (6 J N Q R W Z) | 19,310.8 | 199.9 |
| 59 St / Lexington Av/59 St (4 5 6 N R W) | 10,256.4 | 151.1 |
| 5 Av/59 St (N R W) | 8,012.9 | 150.7 |
| 8 Av (N) | 4,794.1 | 116.7 |
| Atlantic Av-Barclays Ctr (2 3 4 5 B D N Q R) | 10,904.2 | 101.1 |

Biggest losing flows:

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 14 St-Union Sq (4 5 6 L N Q R W) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 2,695.8 | 32.8 | 0.7 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 59 St / Lexington Av/59 St (4 5 6 N R W) | 1,402.0 | 25.6 | 1.1 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 34 St-Herald Sq (B D F M N Q R W) | 1,980.8 | 22.7 | 0.7 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 14 St-Union Sq (4 5 6 L N Q R W) | 2,948.6 | 22.0 | 0.4 |
| 34 St-Herald Sq (B D F M N Q R W) | Canal St (6 J N Q R W Z) | 1,171.2 | 21.4 | 1.1 |
| 34 St-Herald Sq (B D F M N Q R W) | 14 St-Union Sq (4 5 6 L N Q R W) | 2,342.4 | 21.2 | 0.5 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | Canal St (6 J N Q R W Z) | 1,320.5 | 20.9 | 1.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 5 Av/59 St (N R W) | 964.0 | 18.6 | 1.2 |
| 34 St-Herald Sq (B D F M N Q R W) | 59 St / Lexington Av/59 St (4 5 6 N R W) | 1,246.6 | 18.0 | 0.9 |
| Canal St (6 J N Q R W Z) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 1,413.3 | 16.6 | 0.7 |
| 34 St-Herald Sq (B D F M N Q R W) | 49 St (N R W) | 1,056.3 | 14.4 | 0.8 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 49 St (N R W) | 875.3 | 13.5 | 0.9 |

## Net hours by hour of the day (base weights)

| hour | V1_sched | V1_obs | V1_wkend | V2_sched | V2_obs | V4_obs | V5_obs | V1_sim |
|---|---|---|---|---|---|---|---|---|
| 5 | 19.1 | 36.0 | 62.8 | 23.9 | 36.3 | 59.5 | 0.0 | -0.6 |
| 6 | 117.8 | 162.8 | 222.7 | 84.6 | 155.7 | 130.3 | 0.0 | 100.6 |
| 7 | 126.5 | 261.4 | 345.3 | 90.9 | 225.1 | 238.3 | 0.0 | 151.6 |
| 8 | 10.6 | 246.5 | 380.9 | -0.7 | 195.0 | 275.9 | 0.0 | 155.5 |
| 9 | 52.0 | 159.4 | 249.0 | 8.1 | 139.3 | 143.8 | 40.3 | 100.2 |
| 10 | -2.9 | 88.1 | 168.5 | -5.3 | 71.1 | 114.7 | 88.1 | 59.7 |
| 11 | -17.9 | 81.4 | 154.4 | -24.5 | 56.2 | 84.9 | 82.4 | 49.0 |
| 12 | 14.0 | 99.0 | 151.9 | 33.8 | 124.4 | 106.8 | 97.2 | 72.0 |
| 13 | -24.1 | 78.9 | 160.7 | -21.9 | 95.7 | 97.4 | 81.8 | 68.2 |
| 14 | 23.3 | 124.5 | 259.4 | 10.2 | 171.9 | 136.4 | 133.1 | 147.3 |
| 15 | 30.4 | 236.7 | 444.9 | 22.1 | 184.7 | 120.8 | 197.0 | 191.3 |
| 16 | 67.9 | 392.0 | 595.1 | 36.0 | 268.0 | 205.2 | 16.9 | 279.0 |
| 17 | 192.8 | 406.0 | 618.4 | 137.5 | 434.7 | 235.8 | 0.0 | 485.3 |
| 18 | -96.4 | 220.3 | 411.1 | -63.3 | 111.7 | 256.2 | 39.5 | 116.4 |
| 19 | 63.9 | 203.2 | 293.0 | 58.7 | 163.2 | 153.5 | 159.5 | 144.0 |
| 20 | 32.5 | 56.2 | 111.8 | 7.1 | 77.3 | 120.1 | 56.2 | 133.8 |
| 21 | 66.6 | 79.1 | 137.0 | 34.8 | 98.3 | 126.5 | 79.1 | 110.4 |
| 22 | 1.1 | 62.7 | 116.1 | 5.2 | 84.1 | 69.5 | 62.7 | 48.5 |
| 23 | -20.3 | -4.4 | -0.7 | -10.3 | 1.7 | -24.8 | -4.4 | -17.4 |
