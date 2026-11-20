# PLAN6 results (GAITEX; plan sha256 3ead82b1…36e3)

Exclusions: see exclusions.txt. Differences in balanced-accuracy points (×100), person = mean over 2 repeats, 95% percentile bootstrap over persons (2,000, seed 0).


## RD / 4class (n = 19)

GEN mean BA = 0.922

| B | ADAPT | ADAPT−GEN | ADAPT−CTRL | ADAPT−CTRL-NEW | PERS−ADAPT | +/−/= (ADAPT vs GEN) |
|---|---|---|---|---|---|---|
| 4 | 0.972 | +5.0 [+2.4, +8.0] | +5.0 [+2.5, +7.6] | +4.9 [+2.2, +7.9] | -25.9 [-33.6, -18.7] | 9/0/10, median +0.0 |
| 8 | 0.988 | +6.6 [+3.2, +10.5] | +6.4 [+3.4, +9.9] | +6.4 [+3.3, +10.4] | -10.9 [-17.4, -4.9] | 12/0/7, median +2.5 |
| 16 | 0.993 | +7.1 [+3.4, +11.6] | +7.8 [+4.1, +11.8] | +6.8 [+3.6, +10.9] | -3.2 [-5.4, -1.2] | 12/0/7, median +5.0 |

Macro-F1 (orientation only): GEN 0.915, ADAPT16 0.993, PERS16 0.961


## RD / binary (n = 19)

GEN mean BA = 0.925

| B | ADAPT | ADAPT−GEN | ADAPT−CTRL | ADAPT−CTRL-NEW | PERS−ADAPT | +/−/= (ADAPT vs GEN) |
|---|---|---|---|---|---|---|
| 4 | 0.963 | +3.8 [+1.7, +6.3] | +4.3 [+2.2, +6.8] | +3.0 [+1.1, +5.3] | -22.1 [-31.8, -12.6] | 8/1/10, median +0.0 |
| 8 | 0.971 | +4.6 [+1.6, +8.0] | +4.5 [+1.2, +8.2] | +4.2 [+1.4, +7.4] | -12.5 [-21.0, -4.5] | 8/1/10, median +0.0 |
| 16 | 0.973 | +4.7 [+1.9, +8.0] | +5.7 [+2.5, +9.2] | +4.0 [+1.8, +6.7] | -3.2 [-6.0, -0.6] | 8/0/11, median +0.0 |

## RGS / 4class (n = 15)

GEN mean BA = 0.862

| B | ADAPT | ADAPT−GEN | ADAPT−CTRL | ADAPT−CTRL-NEW | PERS−ADAPT | +/−/= (ADAPT vs GEN) |
|---|---|---|---|---|---|---|
| 4 | 0.967 | +10.5 [+5.2, +17.5] | +10.0 [+4.5, +17.2] | +8.7 [+3.5, +15.8] | -16.5 [-22.3, -10.8] | 10/0/5, median +7.5 |
| 8 | 0.987 | +12.5 [+7.5, +18.8] | +11.8 [+6.8, +18.3] | +12.0 [+6.8, +18.5] | -7.0 [-11.8, -2.2] | 12/0/3, median +12.5 |
| 16 | 0.998 | +13.7 [+8.2, +20.3] | +12.3 [+6.8, +19.0] | +15.2 [+9.3, +21.8] | -3.3 [-5.5, -1.2] | 12/0/3, median +12.5 |

Macro-F1 (orientation only): GEN 0.832, ADAPT16 0.998, PERS16 0.964


## RGS / binary (n = 15)

GEN mean BA = 0.979

| B | ADAPT | ADAPT−GEN | ADAPT−CTRL | ADAPT−CTRL-NEW | PERS−ADAPT | +/−/= (ADAPT vs GEN) |
|---|---|---|---|---|---|---|
| 4 | 0.988 | +0.9 [+0.1, +1.9] | +1.2 [+0.2, +2.4] | +0.8 [+0.0, +1.7] | -5.2 [-14.7, +1.7] | 4/0/11, median +0.0 |
| 8 | 0.986 | +0.7 [-2.3, +3.6] | +1.8 [-1.7, +5.6] | +0.7 [-2.3, +3.6] | -4.1 [-12.1, +2.0] | 4/2/9, median +0.0 |
| 16 | 1.000 | +2.1 [+0.4, +4.3] | +3.4 [+0.8, +7.0] | +2.2 [+0.6, +4.3] | -5.7 [-13.0, +0.0] | 6/0/9, median +0.0 |

## Pre-stated expectations (primary: 4-class, B = 16)

- **RD**: E1 ✅ (+7.1 [+3.4, +11.6]); E2 ✅; E2b ✅; E3 ✅; E4 ρ = -0.97 [-1.00, -0.86] ✅; **verdict: consistent with PHYTMO**; pattern: **broad** (improved/worse/tied 12/0/7, Δ≥+2: 12, Δ≤−2: 0, best +37.5, worst +0.0, top-5 share of gross gain 72%, GEN≥0.98: 7)
- **RGS**: E1 ✅ (+13.7 [+8.2, +20.3]); E2 ✅; E2b ✅; E3 ✅; E4 ρ = -1.00 [-1.00, -0.99] ✅; **verdict: consistent with PHYTMO**; pattern: **broad** (improved/worse/tied 12/0/3, Δ≥+2: 12, Δ≤−2: 0, best +45.0, worst +0.0, top-5 share of gross gain 67%, GEN≥0.98: 3)
- RD: PERS did not beat ADAPT (CI > 0) at any tested budget
- RGS: PERS did not beat ADAPT (CI > 0) at any tested budget

## Q4: adapt-or-not rules (exploratory, pre-specified; 4-class)

| Ex / B | rule | mean BA | vs GEN | vs ALWAYS | adapted | harmed (rule < GEN) | harmed by ALWAYS | missed gain (ALWAYS > rule) |
|---|---|---|---|---|---|---|---|---|
| RD / 8 | G1 | 0.966 | +4.3 | -2.2 | 32% of decisions | 0 | 0 | 8 |
| RD / 8 | G2 | 0.947 | +2.5 | -4.1 | 21% of decisions | 0 | 0 | 10 |
| RD / 16 | G1 | 0.984 | +6.2 | -0.9 | 50% of decisions | 0 | 0 | 5 |
| RD / 16 | G2 | 0.984 | +6.2 | -0.9 | 50% of decisions | 0 | 0 | 5 |
| RGS / 8 | G1 | 0.972 | +11.0 | -1.5 | 73% of decisions | 0 | 0 | 2 |
| RGS / 8 | G2 | 0.945 | +8.3 | -4.2 | 50% of decisions | 0 | 0 | 6 |
| RGS / 16 | G1 | 0.995 | +13.3 | -0.3 | 80% of decisions | 0 | 0 | 1 |
| RGS / 16 | G2 | 0.992 | +13.0 | -0.7 | 77% of decisions | 0 | 0 | 2 |

## Q5: tuning (4-class, B = 16; 30 evaluations per tuner)

- **RD ADAPT**: T0 inner spread (P90−P10 over 30 random settings) median 3.4 pts (range 1.8–6.4); T1 RS−fixed +0.0 [-0.4, +0.4]; T2 PSO−RS -0.3 [-0.9, +0.3]; inner best RS 0.997 vs PSO 0.997
- **RD PERS**: T0 inner spread (P90−P10 over 30 random settings) median 2.2 pts (range 1.0–5.2); T1 RS−fixed +0.1 [-1.3, +2.1]; T2 PSO−RS +0.1 [-0.4, +0.8]; inner best RS 0.967 vs PSO 0.966
- **RD** T3 ADAPT_RS − PERS_RS +3.0 [+1.4, +4.7]
- **RGS ADAPT**: T0 inner spread (P90−P10 over 30 random settings) median 4.0 pts (range 1.7–6.3); T1 RS−fixed -0.5 [-1.0, +0.0]; T2 PSO−RS +0.2 [-0.3, +0.7]; inner best RS 0.998 vs PSO 0.998
- **RGS PERS**: T0 inner spread (P90−P10 over 30 random settings) median 3.3 pts (range 1.5–6.7); T1 RS−fixed +1.0 [-0.3, +2.5]; T2 PSO−RS -0.5 [-1.8, +0.5]; inner best RS 0.980 vs PSO 0.980
- **RGS** T3 ADAPT_RS − PERS_RS +1.8 [+0.0, +4.0]
