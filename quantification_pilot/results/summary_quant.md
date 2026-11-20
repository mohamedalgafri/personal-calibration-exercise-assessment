# Pilot results (UCI HAR, 30 persons, 10299 windows). Runtime 639s.

Window-level accuracy of the fixed classifier (context only): inner CV mean 0.916, outer (new people) mean 0.933, range 0.876-0.975.

## Condition: shifted

| method | AE (6 classes) | AE in min per class per 8 h | RAE | KLD | AE (3 intensity groups) | folds better than CC (of 10) |
|---|---|---|---|---|---|---|
| train_prior | 0.1133 | 54.4 | 3.948 | 0.3462 | 0.1421 | 0 |
| CC | 0.0198 | 9.5 | 0.477 | 0.0529 | 0.0181 | - |
| PCC | 0.0254 | 12.2 | 0.660 | 0.0501 | 0.0225 | 0 |
| ACC | 0.0295 | 14.2 | 0.532 | 0.1038 | 0.0253 | 0 |
| PACC | 0.0338 | 16.2 | 0.602 | 0.1171 | 0.0285 | 0 |
| EMQ | 0.0253 | 12.2 | 0.406 | 0.0807 | 0.0221 | 0 |
| HDy_PSO | 0.0356 | 17.1 | 0.512 | 0.1053 | 0.0383 | 0 |
| HDy_random | 0.0483 | 23.2 | 0.830 | 0.1152 | 0.0538 | 0 |

HDy objective (lower = better fit), same budget 1000 evaluations: PSO mean 0.12774, random search mean 0.13526; PSO lower in 1200/1200 samples.

## Condition: natural

| method | AE (6 classes) | AE in min per class per 8 h | RAE | KLD | AE (3 intensity groups) | folds better than CC (of 10) |
|---|---|---|---|---|---|---|
| train_prior | 0.0152 | 7.3 | 0.092 | 0.0067 | 0.0288 | 6 |
| CC | 0.0186 | 8.9 | 0.111 | 0.0447 | 0.0171 | - |
| PCC | 0.0214 | 10.3 | 0.129 | 0.0330 | 0.0184 | 1 |
| ACC | 0.0272 | 13.1 | 0.165 | 0.0711 | 0.0234 | 0 |
| PACC | 0.0313 | 15.0 | 0.190 | 0.0784 | 0.0271 | 0 |
| EMQ | 0.0300 | 14.4 | 0.179 | 0.0824 | 0.0286 | 0 |
| HDy_PSO | 0.0383 | 18.4 | 0.233 | 0.0985 | 0.0406 | 0 |
| HDy_random | 0.0475 | 22.8 | 0.287 | 0.0943 | 0.0509 | 0 |

HDy objective (lower = better fit), same budget 1000 evaluations: PSO mean 0.10684, random search mean 0.11127; PSO lower in 60/60 samples.
