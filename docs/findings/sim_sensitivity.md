# Simulation sensitivity: surrogate model + Sobol indices

8 Latin-hypercube parameter sets × 2 observed weekdays × both directions × (baseline, V1). Outputs are mean seconds per train, 7 am–8 pm.

Parameter ranges: base_dwell_s 20–40; per_pax_s 0.06–0.18; block_target_s 35–60; hold 2–4; run_noise_sd 0.04–0.12; incident_prob 0–0.04

## V1 effects across all parameter sets, and the plausible ones

Plausible = baseline matches observed corridor times within 5% (3 of 8 sets).

| output | all_p10 | all_p50 | all_p90 | plausible_p10 | plausible_p50 | plausible_p90 |
|---|---|---|---|---|---|---|
| n_down_s | -830.9 | 173.8 | 195.0 | 126.8 | 170.9 | 176.7 |
| n_up_s | 95.3 | 105.5 | 132.0 | 95.3 | 100.6 | 105.6 |
| rw_knock_on_s | -258.6 | -2.0 | 8.3 | -5.4 | -3.4 | -0.7 |
| q_relief_s | 20.2 | 37.4 | 70.9 | 20.2 | 27.3 | 40.9 |

## Gaussian-process surrogate fit (5-fold cross-validated R²)

| output | cv_r2_mean | cv_r2_min | mean | sd |
|---|---|---|---|---|
| n_down_s | nan | nan | -157.641 | 601.293 |
| n_up_s | nan | nan | 94.849 | 73.298 |
| rw_knock_on_s | nan | nan | -104.563 | 206.423 |
| q_relief_s | nan | nan | 63.532 | 78.535 |
| baseline_error_pct | nan | nan | 33.373 | 51.824 |

## What drives each output (Sobol total-order indices, top 3)

Total-order index = share of the output's variance due to that parameter, including its interactions.

| output | parameter | first_order | total |
|---|---|---|---|
| rw_knock_on_s | hold | 0.824 | 0.934 |
| rw_knock_on_s | run_noise_sd | 0.061 | 0.175 |
| rw_knock_on_s | per_pax_s | 0.0 | 0.0 |
| n_down_s | hold | 0.731 | 0.903 |
| n_down_s | run_noise_sd | 0.091 | 0.268 |
| n_down_s | base_dwell_s | -0.0 | 0.0 |
| n_up_s | incident_prob | 0.624 | 0.816 |
| n_up_s | per_pax_s | 0.178 | 0.359 |
| n_up_s | run_noise_sd | 0.002 | 0.026 |
| q_relief_s | base_dwell_s | 0.374 | 0.722 |
| q_relief_s | incident_prob | 0.274 | 0.628 |
| q_relief_s | run_noise_sd | 0.0 | 0.0 |
