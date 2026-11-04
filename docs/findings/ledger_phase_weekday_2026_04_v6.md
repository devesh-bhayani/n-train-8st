# Phase-averaged ledger

OD `od_weekday_2026_04.parquet`; N trips shifted by [-540, -420, -300, -180, -60, 60, 180, 300, 420, 540] s in both baseline and scenario, results averaged; riders sampled every 180 s with jitter, 5 am–midnight. `se` = standard error of the phase average.

Columns: `net_hours` keeps today's stations; `flex_upper` lets every rider around campus take the cheapest station (upper bound on switching, which overpredicts the weekend switch about tenfold); `flex_calibrated` scales that switching benefit by observed ÷ predicted switching on weekends (difference-in-differences, central estimate); `flex_calibrated_raw` uses the raw weekend shift.

## Base weights

| scenario | net_hours | net_hours_sd_across_offsets | hours_saved | hours_lost | net_hours_flex_upper | net_hours_flex_calibrated | net_hours_flex_calibrated_raw | se |
|---|---|---|---|---|---|---|---|---|
| V6_W | -522.0 | 28.0 | 528.0 | 6.0 | -524.0 | -522.0 | -522.0 | 9.0 |

## Across the 13-cell weight grid

| scenario | cells | cells_saving | cells_saving_flex_upper | cells_saving_flex_calibrated | cells_saving_flex_calibrated_raw | best | worst |
|---|---|---|---|---|---|---|---|
| V6_W | 13 | 13 | 13 | 13 | 13 | -897.0 | -373.0 |
