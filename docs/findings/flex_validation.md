# Validating destination flexibility against the weekend N

Predicted share of Sea Beach (N) riders bound for campus-area stations who use 8 St–NYU, weekday OD, 6 am–10 pm, today and with the weekday N running local.

## Deterministic choice (everyone takes the cheapest station)

| weights | today_pct | with_V1_pct | shift_pts |
|---|---|---|---|
| w1.5_k1.5_x0 | 5.951 | 30.36 | 24.41 |
| w1.5_k1.5_x5 | 6.064 | 39.34 | 33.27 |
| w1.5_k1.5_x10 | 0 | 40.48 | 40.48 |
| w1.5_k1.5_x15 | 0 | 41.59 | 41.59 |
| w2_k2_x0 | 5.932 | 28.77 | 22.84 |
| w2_k2_x5 | 6.086 | 35.72 | 29.63 |
| w2_k2_x10 | 3.412 | 40.47 | 37.06 |
| w2_k2_x15 | 0.00979 | 40.15 | 40.14 |
| w2.5_k2.5_x0 | 5.926 | 27.99 | 22.06 |
| w2.5_k2.5_x5 | 6.043 | 33.83 | 27.79 |
| w2.5_k2.5_x10 | 6.12 | 39.14 | 33.02 |
| w2.5_k2.5_x15 | 0.3097 | 39.2 | 38.89 |
| w2_k2_x30 | 0.9521 | 41.28 | 40.33 |

Observed (weekends, when the N runs local): **+4.09 points** raw, **+2.54** net of the West End comparison. Deterministic choice overpredicts switching roughly tenfold, so it is only an upper bound.

## Logit choice, calibrated

P(station) ∝ exp(−θ × cost). Smaller θ (larger 1/θ) = noisier, stickier choices. Predicted shift at base weights:

| theta_per_s | one_over_theta_s | predicted_shift_pts |
|---|---|---|
| 0.01667 | 60 | 30.84 |
| 0.008333 | 120 | 30.25 |
| 0.005556 | 180 | 28.39 |
| 0.003333 | 300 | 23.68 |
| 0.002222 | 450 | 18.73 |
| 0.001667 | 600 | 15.1 |
| 0.001111 | 900 | 10.46 |
| 0.0008333 | 1200 | 7.811 |
| 0.0005556 | 1800 | 5.074 |
| 0.0003704 | 2700 | 3.281 |
| 0.0002778 | 3600 | 2.413 |

Calibrated 1/θ: **3469 s** to match the difference-in-differences (+2.54), **2294 s** to match the raw weekend shift (+4.09).

A logit this noisy gives every rider a few percent chance of every station near campus, so its logsum benefit credits the 8 St improvement to almost everyone (in tests it exceeded even the deterministic upper bound). The ledger therefore uses a simpler, transparent calibration: the deterministic switching benefit scaled by observed ÷ predicted switching, **0.086** (difference-in-differences) to **0.138** (raw).
