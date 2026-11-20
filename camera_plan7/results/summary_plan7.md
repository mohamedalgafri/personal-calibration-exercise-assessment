# PLAN7 results (REHAB24-6 Ex1/Ex2, camera 17; plan sha256 65de095d…)

Binary balanced accuracy in points; bootstrap 95% CI over persons (2,000, seed 0). Ex1 and Ex2 reported separately (mostly the same persons).


## Ex2 / mocap (n = 3); GEN mean 0.583

| B | ADAPT − GEN | ADAPT − CTRL | ADAPT − CTRL-NEW | PERS − ADAPT | +/−/= | G1: adapted, harmed (G1 / ALWAYS) |
|---|---|---|---|---|---|---|
| 4 | +5.6 [-8.3, +16.7] | +5.6 [-8.3, +16.7] | +13.9 [+8.3, +16.7] | -11.1 [-25.0, +8.3] | 2/1/0 | 3/3, 1 / 1 |
| 8 | +19.4 [+16.7, +25.0] | +11.1 [-8.3, +25.0] | +19.4 [+0.0, +41.7] | -8.3 [-33.3, +16.7] | 3/0/0 | 3/3, 0 / 0 |

## Ex2 / video (n = 3); GEN mean 0.722

| B | ADAPT − GEN | ADAPT − CTRL | ADAPT − CTRL-NEW | PERS − ADAPT | +/−/= | G1: adapted, harmed (G1 / ALWAYS) |
|---|---|---|---|---|---|---|
| 4 | -19.4 [-25.0, -16.7] | -16.7 [-16.7, -16.7] | -13.9 [-16.7, -8.3] | +2.8 [-16.7, +25.0] | 0/3/0 | 3/3, 3 / 3 |
| 8 | +0.0 [-8.3, +8.3] | +2.8 [+0.0, +8.3] | +0.0 [-8.3, +8.3] | +2.8 [+0.0, +8.3] | 1/1/1 | 3/3, 1 / 1 |

## Pre-stated expectations (B = 8)

- **Ex2**: C1 GEN_video − GEN_mocap +13.9 [+0.0, +25.0] ❌; C2 ADAPT8 − GEN (mocap) +19.4 [+16.7, +25.0] ✅; (video) +0.0 [-8.3, +8.3]; D = video − mocap -19.4 [-25.0, -8.3]; categories mocap/video positive/null; **C3 ❌**; persons at GEN = 1.0: mocap 0, video 0

**Verdict (§6, Addendum A.3): the comparison 0/1 exercises analysed to markerless video (0/1).** No equivalence claim (n ≈ 8).

## H5 (G1 gate) testability, B = 8

- Ex2/mocap: harmed by ALWAYS 0, by G1 0 → **H5 untestable** (ALWAYS harms nobody)
- Ex2/video: harmed by ALWAYS 1, by G1 1 → H5 ❌

## Extraction

- videos with a completed first attempt: 25; first-attempt rerun trigger: 0; reruns: 0, recovered: 0; videos passing all checks: 26
