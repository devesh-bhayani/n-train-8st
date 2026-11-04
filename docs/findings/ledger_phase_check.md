# Phase-averaged ledger (check: pure shifts)

OD `od_weekday_2026_04.parquet`; N trips shifted by [-540, -420, -300, -180, -60, 60, 180, 300, 420, 540] s in both baseline and scenario, results averaged; riders sampled every 300 s with jitter, 5 am–midnight. `se` = standard error of the phase average.

Columns: `net_hours` keeps today's stations; `flex_upper` lets every rider around campus take the cheapest station (upper bound on switching, which overpredicts the weekend switch about tenfold); `flex_calibrated` scales that switching benefit by observed ÷ predicted switching on weekends (difference-in-differences, central estimate); `flex_calibrated_raw` uses the raw weekend shift.

## Base weights

| scenario | net_hours | net_hours_sd_across_offsets | hours_saved | hours_lost | se |
|---|---|---|---|---|---|
| pure_shift_180s | 88.0 | 2,624.0 | 5,466.0 | 5,554.0 | 830.0 |
| pure_shift_60s | 24.0 | 1,065.0 | 3,491.0 | 3,515.0 | 337.0 |

## Across the 13-cell weight grid

| scenario | cells | cells_saving | best | worst |
|---|---|---|---|---|
| pure_shift_180s | 13 | 0 | 69.0 | 125.0 |
| pure_shift_60s | 13 | 0 | 18.0 | 39.0 |
