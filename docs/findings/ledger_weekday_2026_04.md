# Scenario ledger: does an N stop at 8 St–NYU save riders time?

OD: `od_weekday_2026_04.parquet` (4,214,112 weekday trips between 5:00 and 24:00). Departures sampled every 120 s. `net_hours` keeps every rider's stations (fixed OD); `net_hours_flexible` lets riders to and from the 13 stations around campus switch to whichever station is cheapest for where they're going (`n8st.ledger.flex`).

Costs are generalized: in-train minutes + 2 × waiting + 2 × walking + 5 min per transfer (base weights). Negative net = riders save time overall.

## Headline (base weights, passenger-hours per weekday)

| variant | trips_changed | added_s_per_trip | hours_saved | hours_lost | net_hours | net_hours_flexible |
|---|---|---|---|---|---|---|
| V2 N local 14 St–Canal only, schedule timing | 241 | 90.0 | 2,121.0 | 2,548.0 | 427.0 | -306.0 |
| V1 N local 34 St–Canal, MTA weekend timing | 241 | 150.0 | 3,457.0 | 4,114.0 | 657.0 | -1.0 |
| V5 N local only 10–4 and 7–midnight | 132 | 210.0 | 1,601.0 | 2,735.0 | 1,134.0 | 843.0 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 241 | 185.0 | 3,790.0 | 6,180.0 | 2,390.0 | 1,764.0 |
| V2 N local 14 St–Canal only, observed timing | 241 | 110.0 | 1,625.0 | 4,310.0 | 2,684.0 | 2,005.0 |
| V4 Q local instead of the N | 273 | 210.0 | 3,185.0 | 5,880.0 | 2,696.0 | 1,729.0 |
| V1 N local 34 St–Canal, observed weekday timing | 241 | 210.0 | 2,838.0 | 5,832.0 | 2,993.0 | 2,418.0 |
| V1 N local 34 St–Canal, observed weekend timing | 241 | 262.0 | 2,318.0 | 7,082.0 | 4,764.0 | 4,210.0 |

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
| V5 N local only 10–4 and 7–midnight | 13 | 0 | 0 | 828.0 | 1,229.0 |
| V4 Q local instead of the N | 13 | 0 | 2 | 1,180.0 | 2,952.0 |
| V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on) | 13 | 0 | 0 | 1,427.0 | 3,189.0 |
| V2 N local 14 St–Canal only, observed timing | 13 | 0 | 0 | 2,062.0 | 3,254.0 |
| V1 N local 34 St–Canal, observed weekday timing | 13 | 0 | 0 | 2,249.0 | 3,283.0 |
| V1 N local 34 St–Canal, observed weekend timing | 13 | 0 | 0 | 3,858.0 | 5,458.0 |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (fixed stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | 2,381.0 | 2,070.0 | 1,779.0 | 1,548.0 |  |
| 2.0 | 2,797.0 | 2,390.0 | 2,054.0 | 1,830.0 | 1,427.0 |
| 2.5 | 3,189.0 | 2,716.0 | 2,352.0 | 2,115.0 |  |

## V1 N local 34 St–Canal, simulation timing (+185/+110 s, R/W knock-on): net hours by weight (riders can switch stations)

| wait & walk weight | transfer 0.0 min | transfer 5.0 min | transfer 10.0 min | transfer 15.0 min | transfer 30.0 min |
|---|---|---|---|---|---|
| 1.5 | 2,025.0 | 1,524.0 | 1,171.0 | 893.0 |  |
| 2.0 | 2,376.0 | 1,764.0 | 1,335.0 | 1,065.0 | 500.0 |
| 2.5 | 2,707.0 | 2,030.0 | 1,564.0 | 1,231.0 |  |

## Who gains under V1_sim (base weights)

Destinations with the most hours saved:

| destination | riders | hours_saved | avg_min_saved |
|---|---|---|---|
| 23 St (R W) | 14,425.8 | 444.2 | 1.8 |
| 8 St-NYU (R W) | 12,148.7 | 410.1 | 2.0 |
| Prince St (R W) | 8,698.7 | 309.1 | 2.1 |
| 28 St (R W) | 9,222.1 | 286.5 | 1.9 |
| 72 St (Q) | 17,844.0 | 178.0 | 0.6 |
| 86 St (Q) | 13,621.2 | 137.8 | 0.6 |
| 96 St (Q) | 9,342.5 | 93.1 | 0.6 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 4,813.0 | 57.5 | 0.7 |
| 8 Av (N) | 1,818.8 | 53.7 | 1.8 |
| Lexington Av/63 St (M Q) | 7,064.4 | 52.7 | 0.4 |

Origins with the most hours saved:

| origin | riders | hours_saved |
|---|---|---|
| 23 St (R W) | 13,819.9 | 347.3 |
| 8 St-NYU (R W) | 10,963.1 | 271.4 |
| 28 St (R W) | 8,792.7 | 220.1 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 15,890.2 | 189.0 |
| Prince St (R W) | 7,831.1 | 182.6 |
| 34 St-Herald Sq (B D F M N Q R W) | 15,889.6 | 153.9 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 10,964.6 | 90.2 |
| Canal St (6 J N Q R W Z) | 6,923.8 | 75.0 |
| 49 St (N R W) | 3,320.9 | 71.7 |
| 57 St-7 Av (N Q R W) | 4,708.8 | 62.4 |

Biggest winning flows (origin → destination):

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 23 St (R W) | 1,248.4 | -37.8 | -1.8 |
| 34 St-Herald Sq (B D F M N Q R W) | 8 St-NYU (R W) | 844.3 | -29.1 | -2.1 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 8 St-NYU (R W) | 852.0 | -26.6 | -1.9 |
| 23 St (R W) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 1,397.3 | -23.3 | -1.0 |
| 34 St-Herald Sq (B D F M N Q R W) | 72 St (Q) | 2,413.8 | -22.9 | -0.6 |
| 49 St (N R W) | 23 St (R W) | 704.2 | -21.8 | -1.9 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 72 St (Q) | 2,392.7 | -21.5 | -0.5 |
| 49 St (N R W) | 8 St-NYU (R W) | 580.6 | -19.5 | -2.0 |
| 8 St-NYU (R W) | 34 St-Herald Sq (B D F M N Q R W) | 913.0 | -18.5 | -1.2 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | Prince St (R W) | 520.7 | -17.5 | -2.0 |
| 34 St-Herald Sq (B D F M N Q R W) | Prince St (R W) | 458.5 | -17.2 | -2.2 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 28 St (R W) | 550.6 | -17.1 | -1.9 |

## Who loses under V1_sim

Origins with the most hours lost:

| origin | riders | hours_lost |
|---|---|---|
| 34 St-Herald Sq (B D F M N Q R W) | 36,649.4 | 440.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 32,770.2 | 312.1 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 28,846.2 | 288.1 |
| 57 St-7 Av (N Q R W) | 18,780.6 | 278.2 |
| 49 St (N R W) | 14,736.0 | 223.4 |
| Canal St (6 J N Q R W Z) | 19,362.1 | 201.3 |
| 59 St / Lexington Av/59 St (4 5 6 N R W) | 10,256.4 | 152.1 |
| 5 Av/59 St (N R W) | 7,998.1 | 149.7 |
| 8 Av (N) | 4,818.1 | 117.6 |
| Atlantic Av-Barclays Ctr (2 3 4 5 B D N Q R) | 10,911.2 | 101.2 |

Biggest losing flows:

| origin | destination | riders | hours | min_per_rider |
|---|---|---|---|---|
| 14 St-Union Sq (4 5 6 L N Q R W) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 2,695.8 | 33.0 | 0.7 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 59 St / Lexington Av/59 St (4 5 6 N R W) | 1,402.0 | 25.6 | 1.1 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 34 St-Herald Sq (B D F M N Q R W) | 1,980.8 | 22.6 | 0.7 |
| 34 St-Herald Sq (B D F M N Q R W) | Canal St (6 J N Q R W Z) | 1,171.2 | 21.4 | 1.1 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | Canal St (6 J N Q R W Z) | 1,320.5 | 20.9 | 1.0 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 14 St-Union Sq (4 5 6 L N Q R W) | 2,948.6 | 20.0 | 0.4 |
| 34 St-Herald Sq (B D F M N Q R W) | 14 St-Union Sq (4 5 6 L N Q R W) | 2,342.4 | 19.1 | 0.5 |
| 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 5 Av/59 St (N R W) | 964.0 | 18.6 | 1.2 |
| 34 St-Herald Sq (B D F M N Q R W) | 59 St / Lexington Av/59 St (4 5 6 N R W) | 1,246.6 | 18.0 | 0.9 |
| Canal St (6 J N Q R W Z) | 42 St-Port Authority Bus Terminal / Times Sq-42 St (1 2 3 7 A C E N Q R S W) | 1,413.3 | 16.6 | 0.7 |
| 34 St-Herald Sq (B D F M N Q R W) | 49 St (N R W) | 1,056.3 | 14.4 | 0.8 |
| 14 St-Union Sq (4 5 6 L N Q R W) | 49 St (N R W) | 875.3 | 13.5 | 0.9 |

## Net hours by hour of the day (base weights)

| hour | V1_sched | V1_obs | V1_wkend | V2_sched | V2_obs | V4_obs | V5_obs | V1_sim |
|---|---|---|---|---|---|---|---|---|
| 5 | 19.1 | 38.6 | 63.0 | 23.9 | 33.2 | 59.8 | 0.0 | -0.3 |
| 6 | 117.8 | 167.6 | 214.4 | 84.6 | 146.2 | 128.6 | 0.0 | 100.9 |
| 7 | 126.5 | 261.0 | 344.0 | 90.9 | 206.5 | 236.4 | 0.0 | 153.4 |
| 8 | 10.6 | 246.5 | 359.9 | -0.7 | 189.6 | 276.5 | 0.0 | 154.8 |
| 9 | 52.0 | 160.0 | 247.0 | 8.1 | 137.5 | 146.0 | 40.4 | 100.0 |
| 10 | -2.9 | 88.8 | 167.0 | -5.3 | 70.9 | 116.0 | 88.7 | 59.5 |
| 11 | -17.9 | 82.4 | 152.2 | -24.5 | 51.7 | 85.9 | 83.2 | 48.8 |
| 12 | 14.0 | 99.6 | 150.0 | 33.8 | 128.6 | 108.2 | 97.7 | 71.8 |
| 13 | -24.1 | 79.9 | 160.5 | -21.9 | 90.6 | 99.0 | 82.6 | 68.0 |
| 14 | 23.3 | 125.6 | 252.2 | 10.2 | 159.2 | 138.3 | 134.2 | 147.3 |
| 15 | 30.4 | 239.2 | 437.8 | 22.1 | 171.7 | 124.4 | 200.4 | 194.5 |
| 16 | 67.9 | 388.9 | 587.3 | 36.0 | 279.3 | 209.9 | 17.0 | 282.1 |
| 17 | 192.8 | 406.5 | 606.1 | 137.5 | 453.3 | 258.6 | 0.0 | 485.2 |
| 18 | -96.4 | 213.1 | 375.7 | -63.3 | 128.0 | 264.1 | 38.6 | 110.4 |
| 19 | 63.9 | 198.7 | 284.4 | 58.7 | 172.6 | 152.1 | 154.6 | 141.4 |
| 20 | 32.5 | 56.8 | 110.5 | 7.1 | 83.9 | 116.6 | 56.8 | 131.8 |
| 21 | 66.6 | 80.9 | 133.6 | 34.8 | 100.6 | 126.3 | 80.9 | 107.6 |
| 22 | 1.1 | 63.4 | 118.9 | 5.2 | 79.3 | 75.2 | 63.4 | 50.6 |
| 23 | -20.3 | -4.4 | -0.8 | -10.3 | 1.4 | -26.1 | -4.4 | -17.4 |
