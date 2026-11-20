# Pilot 4 results (plan PLAN4.md, sha256 5d1f22f7…c552). Runtime 156s

HAA: recordings with all sensors=223, persons with all four series=28, excluded files so far=0
SQZ: recordings with all sensors=118, persons with all four series=28, excluded files so far=0

## HAA (28 persons)

| method | balanced accuracy | simulated-session error (pts) | folds > SRC (bal. acc) |
|---|---|---|---|
| GEN | 0.906 | 8.9 | - |
| SRC | 0.905 | 8.9 | - |
| B8_f0.0 | 0.928 | 6.5 | 6 |
| B8_f0.25 | 0.932 | 6.1 | 9 |
| B8_f0.5 | 0.933 | 5.9 | 9 |
| B8_f0.75 | 0.926 | 6.2 | 10 |
| B16_f0.0 | 0.934 | 5.9 | 9 |
| B16_f0.25 | 0.943 | 5.1 | 9 |
| B16_f0.5 | 0.944 | 4.5 | 10 |
| B16_f0.75 | 0.936 | 5.3 | 10 |

- **H1, budget 8:** f=0.5 > f=0 in 8/10 folds; persons 11/28.
- **H1, budget 16:** f=0.5 > f=0 in 7/10 folds; persons 12/28.
- **H2:** SRC − GEN balanced accuracy = -0.0011.
- Short calibration pools (person×fold cases): 0.

## SQZ (28 persons)

| method | balanced accuracy | simulated-session error (pts) | folds > SRC (bal. acc) |
|---|---|---|---|
| GEN | 0.804 | 17.8 | - |
| SRC | 0.806 | 17.2 | - |
| B8_f0.0 | 0.821 | 15.7 | 6 |
| B8_f0.25 | 0.855 | 12.5 | 9 |
| B8_f0.5 | 0.862 | 11.9 | 10 |
| B8_f0.75 | 0.859 | 12.0 | 9 |
| B16_f0.0 | 0.822 | 15.9 | 5 |
| B16_f0.25 | 0.867 | 11.5 | 10 |
| B16_f0.5 | 0.880 | 10.4 | 10 |
| B16_f0.75 | 0.880 | 10.1 | 10 |

- **H1, budget 8:** f=0.5 > f=0 in 8/10 folds; persons 15/28.
- **H1, budget 16:** f=0.5 > f=0 in 8/10 folds; persons 15/28.
- **H2:** SRC − GEN balanced accuracy = +0.0015.
- Short calibration pools (person×fold cases): 26.

