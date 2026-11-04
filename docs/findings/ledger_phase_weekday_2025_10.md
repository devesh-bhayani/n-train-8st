# Phase-averaged ledger

OD `od_weekday_2025_10.parquet`; N trips shifted by [-540, -420, -300, -180, -60, 60, 180, 300, 420, 540] s in both baseline and scenario, results averaged; riders sampled every 180 s with jitter, 5 am–midnight. `se` = standard error of the phase average.

Columns: `net_hours` keeps today's stations; `flex_upper` lets every rider around campus take the cheapest station (upper bound on switching, which overpredicts the weekend switch about tenfold); `flex_calibrated` scales that switching benefit by observed ÷ predicted switching on weekends (difference-in-differences, central estimate); `flex_calibrated_raw` uses the raw weekend shift.

## Base weights

| scenario | net_hours | net_hours_sd_across_offsets | hours_saved | hours_lost | net_hours_flex_upper | net_hours_flex_calibrated | net_hours_flex_calibrated_raw | se |
|---|---|---|---|---|---|---|---|---|
| V1_sim | 851.0 | 748.0 | 4,328.0 | 5,178.0 | 288.0 | 802.0 | 773.0 | 236.0 |
| V2_sched | -52.0 | 420.0 | 2,461.0 | 2,409.0 | -663.0 | -104.0 | -136.0 | 133.0 |

## Across the 13-cell weight grid

| scenario | cells | cells_saving | cells_saving_flex_upper | cells_saving_flex_calibrated | cells_saving_flex_calibrated_raw | best | worst |
|---|---|---|---|---|---|---|---|
| V1_sim | 13 | 1 | 7 | 1 | 1 | -91.0 | 1,274.0 |
| V2_sched | 13 | 9 | 13 | 11 | 11 | -409.0 | 224.0 |
