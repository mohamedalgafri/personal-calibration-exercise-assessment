# POST HOC: per-cell distribution of ADAPT16 − GEN (from saved results; no retraining)

Person score = mean over saved repetitions. Differences in balanced-accuracy points. Improved/worse = beyond ±0.5 point.

| Cell | n | GEN mean | mean Δ | median Δ | improved / worse / tied | Δ ≥ +2 | Δ ≤ −2 | best / worst person | gross gain / gross loss / net (pts·persons) | top-5 share of gross gain | mean Δ lower vs upper half of GEN | GEN ≥ 0.98 | median GEN of the worse |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| SQT/IMU | 21 | 0.921 | +3.0 | +0.7 | 11 / 4 / 6 | 8 | 3 | +29.2 / -4.8 | 76 / -13 / 63 | 83% | +5.6 vs +0.7 | 5 | 0.900 |
| SQT/OPT | 21 | 0.709 | +7.2 | +4.7 | 15 / 4 / 2 | 15 | 2 | +41.3 / -6.9 | 168 / -17 / 151 | 66% | +12.1 vs +2.8 | 1 | 0.880 |
| HAA/IMU | 25 | 0.924 | +3.1 | +1.0 | 16 / 4 / 5 | 9 | 1 | +23.1 / -2.9 | 83 / -6 / 77 | 73% | +6.3 vs +0.1 | 10 | 0.993 |
| HAA/OPT | 25 | 0.857 | +0.9 | +0.7 | 14 / 10 / 1 | 7 | 7 | +14.5 / -13.3 | 66 / -43 / 22 | 81% | +3.2 vs -1.3 | 3 | 0.864 |
| SQZ/IMU | 27 | 0.792 | +9.0 | +5.0 | 22 / 3 / 2 | 20 | 1 | +36.5 / -2.5 | 247 / -5 / 242 | 50% | +14.5 vs +3.8 | 2 | 0.558 |
| SQZ/OPT | 27 | 0.792 | +8.2 | +4.5 | 16 / 3 / 8 | 16 | 2 | +28.8 / -5.4 | 230 / -9 / 221 | 53% | +15.2 vs +1.7 | 7 | 0.958 |
| EAH/IMU | 29 | 0.898 | +5.4 | +0.7 | 16 / 5 / 8 | 10 | 0 | +41.9 / -1.8 | 161 / -5 / 156 | 83% | +10.3 vs +0.8 | 7 | 0.952 |
| EAH/OPT | 29 | 0.897 | +4.3 | +1.7 | 16 / 4 / 9 | 13 | 3 | +36.2 / -8.0 | 138 / -14 / 124 | 67% | +7.7 vs +1.1 | 7 | 0.901 |
