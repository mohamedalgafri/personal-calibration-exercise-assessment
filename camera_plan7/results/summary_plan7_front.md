# PLAN7 FRONT-VIEW SENSITIVITY (Addendum D; post hoc, pre-outcome; descriptive) — PLAN7 results (REHAB24-6 Ex1/Ex2, camera 17; plan sha256 65de095d…)

Binary balanced accuracy in points; bootstrap 95% CI over persons (2,000, seed 0). Ex1 and Ex2 reported separately (mostly the same persons).


## Ex1 / mocap (n = 8); GEN mean 0.875

| B | ADAPT − GEN | ADAPT − CTRL | ADAPT − CTRL-NEW | PERS − ADAPT | +/−/= | G1: adapted, harmed (G1 / ALWAYS) |
|---|---|---|---|---|---|---|
| 4 | +8.3 [-2.1, +18.8] | +8.3 [-2.1, +18.8] | +14.6 [+0.0, +29.2] | -4.2 [-8.3, +0.0] | 4/1/3 | 5/8, 1 / 1 |

## Ex1 / video (n = 8); GEN mean 0.750

| B | ADAPT − GEN | ADAPT − CTRL | ADAPT − CTRL-NEW | PERS − ADAPT | +/−/= | G1: adapted, harmed (G1 / ALWAYS) |
|---|---|---|---|---|---|---|
| 4 | +14.6 [+4.2, +27.1] | +12.5 [+0.0, +31.2] | +10.4 [+4.1, +18.8] | +0.0 [-6.2, +6.3] | 4/0/4 | 5/8, 0 / 0 |

## Ex2 / mocap (n = 7); GEN mean 0.619

| B | ADAPT − GEN | ADAPT − CTRL | ADAPT − CTRL-NEW | PERS − ADAPT | +/−/= | G1: adapted, harmed (G1 / ALWAYS) |
|---|---|---|---|---|---|---|
| 4 | +21.4 [+7.1, +38.1] | +21.4 [+7.1, +38.1] | +23.8 [+9.5, +38.1] | -7.1 [-16.7, +0.0] | 4/0/3 | 6/7, 0 / 0 |

## Ex2 / video (n = 7); GEN mean 0.524

| B | ADAPT − GEN | ADAPT − CTRL | ADAPT − CTRL-NEW | PERS − ADAPT | +/−/= | G1: adapted, harmed (G1 / ALWAYS) |
|---|---|---|---|---|---|---|
| 4 | +26.2 [+4.8, +45.2] | +28.6 [+4.8, +52.4] | +11.9 [-11.9, +31.0] | -0.0 [-7.1, +7.1] | 5/1/1 | 7/7, 1 / 1 |

## Pre-stated expectations (B = 4)

- **Ex1**: C1 GEN_video − GEN_mocap -12.5 [-31.2, +6.3] ✅; C2 ADAPT4 − GEN (mocap) +8.3 [-2.1, +18.8] ✅; (video) +14.6 [+4.2, +27.1]; D = video − mocap +6.2 [-8.3, +20.8]; categories mocap/video positive/positive; **C3 ❌**; persons at GEN = 1.0: mocap 4, video 2
- **Ex2**: C1 GEN_video − GEN_mocap -9.5 [-23.8, +4.8] ✅; C2 ADAPT4 − GEN (mocap) +21.4 [+7.1, +38.1] ✅; (video) +26.2 [+4.8, +45.2]; D = video − mocap +4.8 [-14.3, +23.8]; categories mocap/video positive/positive; **C3 ✅**; persons at GEN = 1.0: mocap 1, video 0

**Verdict (§6, Addendum A.3): the comparison partly to markerless video (1/2).** No equivalence claim (n ≈ 8).

## H5 (G1 gate) testability, B = 4

- Ex1/mocap: harmed by ALWAYS 1, by G1 1 → H5 ❌
- Ex1/video: harmed by ALWAYS 0, by G1 0 → **H5 untestable** (ALWAYS harms nobody)
- Ex2/mocap: harmed by ALWAYS 0, by G1 0 → **H5 untestable** (ALWAYS harms nobody)
- Ex2/video: harmed by ALWAYS 1, by G1 1 → H5 ❌

## Extraction

- videos with a completed first attempt: 25; first-attempt rerun trigger: 0; reruns: 0, recovered: 0; videos passing all checks: 26
