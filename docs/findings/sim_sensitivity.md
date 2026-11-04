# Simulation sensitivity: surrogate model + Sobol indices

160 Latin-hypercube parameter sets × 6 observed weekdays × both directions × (baseline, V1). Outputs are mean seconds per train, 7 am–8 pm.

Parameter ranges: base_dwell_s 22–38; per_pax_s 0.06–0.16; block_target_s 35–55; hold 1.6–3.4; run_noise_sd 0.04–0.1; incident_prob 0–0.035

## V1 effects across all parameter sets, and the plausible ones

Plausible = baseline matches observed corridor times within 5% (94 of 160 sets).

| output | all_p10 | all_p50 | all_p90 | plausible_p10 | plausible_p50 | plausible_p90 |
|---|---|---|---|---|---|---|
| n_down_s | 136.3 | 171.8 | 194.1 | 129.8 | 178.0 | 201.9 |
| n_up_s | 97.1 | 109.8 | 133.2 | 101.1 | 119.1 | 138.4 |
| rw_knock_on_s | -7.6 | -1.3 | 7.0 | -10.2 | -0.5 | 7.9 |
| q_relief_s | 7.1 | 15.7 | 43.0 | 8.8 | 23.3 | 45.3 |

## Gaussian-process surrogate fit (5-fold cross-validated R²)

| output | cv_r2_mean | cv_r2_min | mean | sd |
|---|---|---|---|---|
| n_down_s | 0.726 | 0.69 | 169.331 | 22.657 |
| n_up_s | 0.733 | 0.637 | 112.614 | 14.8 |
| rw_knock_on_s | 0.119 | -0.304 | -0.776 | 7.249 |
| q_relief_s | 0.898 | 0.844 | 21.034 | 13.729 |
| baseline_error_pct | 0.866 | 0.68 | 4.939 | 1.762 |

## What drives each output (Sobol total-order indices, top 3)

Total-order index = share of the output's variance due to that parameter, including its interactions.

| output | parameter | first_order | total |
|---|---|---|---|
| q_relief_s | hold | 0.671 | 0.782 |
| q_relief_s | block_target_s | 0.175 | 0.273 |
| q_relief_s | incident_prob | 0.014 | 0.03 |
| n_down_s | block_target_s | 0.363 | 0.607 |
| n_down_s | hold | 0.223 | 0.426 |
| n_down_s | incident_prob | 0.105 | 0.149 |
| n_up_s | per_pax_s | 0.577 | 0.59 |
| n_up_s | incident_prob | 0.389 | 0.402 |
| n_up_s | run_noise_sd | 0.012 | 0.013 |
| rw_knock_on_s | incident_prob | 0.454 | 0.57 |
| rw_knock_on_s | block_target_s | 0.197 | 0.507 |
| rw_knock_on_s | hold | -0.009 | 0.172 |
