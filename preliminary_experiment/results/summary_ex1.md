# Preliminary experiment — KIMORE Exercise 1 (lifting of the arms)

Data: KIMORE (Zenodo mirror, CC-BY 4.0). 70 people after grouping windows by person; 92 kinematic features.
Protocol: 5x5-fold subject-level cross-validation, nested feature selection, Ridge regression, 10 PSO runs per fold.

| Method | MAE | Spearman | # features | Stability [95% CI] | p vs all |
|---|---|---|---|---|---|
| Mean predictor | 6.84 ± 0.03 | — | 0 | — | 0.493 |
| All features | 6.52 ± 0.39 | 0.53 | 92.0 | — | — |
| All features (kernel) | 5.32 ± 0.14 | 0.57 | 92.0 | — | <0.001 |
| RReliefF top-k | 6.71 ± 0.24 | 0.48 | 16.0 | 0.54 [0.48, 0.59] | 0.367 |
| Spearman top-k | 6.15 ± 0.25 | 0.51 | 13.3 | 0.58 [0.53, 0.63] | 0.221 |
| Binary PSO (1 run) | 6.73 ± 0.27 | 0.48 | 12.6 | 0.03 [0.01, 0.06] | 0.109 |
| PSO consensus | 6.79 ± 0.43 | 0.41 | 5.8 | 0.15 [0.10, 0.20] | 0.065 |

Leakage demo (window-level samples, all features): random split MAE 4.90 vs person-grouped split MAE 6.62.
Mean PSO stability across runs on the same training data: 0.11.
