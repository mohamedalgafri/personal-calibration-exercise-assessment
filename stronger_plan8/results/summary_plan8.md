# PLAN8 results: stronger general model (MLP ensemble) vs logistic regression, B = 16 (plan sha256 2308ac11…)

Sanity check: GEN-LR recomputed for 138 person × repeat values, max |difference| vs saved = 0.0e+00.

Points; person = mean over 2 repeats; bootstrap 95% CI over persons (2,000, seed 0).

| Cell | n | GEN-LR | GEN-MLP | S1 GEN-MLP − GEN-LR | ADAPT-LR − GEN-LR | **S2 ADAPT-MLP − GEN-MLP** | S3 ADAPT-MLP − CTRL-NEW-MLP | S4 GEN-MLP − ADAPT-LR | S5 retained | +/−/= (ADAPT-MLP vs GEN-MLP) | GEN-MLP ≥ 0.98 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EAH/IMU | 29 | 0.898 | 0.924 | +2.6 [+0.5, +5.5] | +5.4 [+1.8, +10.1] | **+3.9 [+0.8, +8.3]** ✅ | +3.8 [+0.8, +8.0] | -2.8 [-6.5, -0.2] | 0.73 | 16/2/11 | 8 |
| EAH/OPT | 29 | 0.897 | 0.903 | +0.6 [-1.9, +2.8] | +4.3 [+1.5, +7.6] | **+4.1 [+1.4, +7.5]** ✅ | +4.2 [+1.6, +7.5] | -3.7 [-6.9, -1.0] | 0.97 | 17/1/11 | 11 |
| HAA/IMU | 25 | 0.924 | 0.906 | -1.8 [-4.4, +0.7] | +3.1 [+1.2, +5.5] | **+3.5 [+1.4, +5.9]** ✅ | +3.4 [+1.3, +6.0] | -4.9 [-8.8, -1.9] | 1.12 | 14/3/8 | 9 |
| HAA/OPT (LR criterion not met) | 25 | 0.857 | 0.821 | -3.6 [-9.0, +1.0] | +0.9 [-1.4, +3.4] | **+4.2 [+1.4, +8.0]** ✅ | +2.5 [+0.4, +5.7] | -4.5 [-9.5, -0.6] | nan | 17/4/4 | 4 |
| SQT/IMU | 21 | 0.921 | 0.896 | -2.6 [-5.1, -0.3] | +3.0 [+0.4, +6.3] | **+4.5 [+1.2, +8.6]** ✅ | +4.5 [+1.2, +8.6] | -5.6 [-11.1, -1.0] | 1.49 | 11/1/9 | 7 |
| SQT/OPT | 21 | 0.709 | 0.749 | +3.9 [+0.7, +7.0] | +7.2 [+3.1, +12.3] | **+4.8 [+1.5, +8.9]** ✅ | +5.0 [+1.6, +9.4] | -3.3 [-9.3, +1.5] | 0.67 | 12/4/5 | 3 |
| SQZ/IMU | 27 | 0.792 | 0.797 | +0.5 [-4.1, +5.2] | +9.0 [+5.6, +12.6] | **+8.4 [+4.6, +12.8]** ✅ | +8.6 [+4.8, +12.9] | -8.4 [-13.4, -3.8] | 0.94 | 20/1/6 | 3 |
| SQZ/OPT | 27 | 0.792 | 0.812 | +2.1 [+0.2, +3.9] | +8.2 [+4.5, +12.0] | **+7.1 [+3.7, +10.8]** ✅ | +6.6 [+3.1, +10.6] | -6.1 [-9.8, -2.6] | 0.86 | 16/4/7 | 8 |
| RD/4class | 19 | 0.922 | 0.914 | -0.8 [-3.6, +2.1] | +7.1 [+3.4, +11.6] | **+7.1 [+3.3, +12.1]** ✅ | +6.6 [+3.0, +11.3] | -7.9 [-13.8, -3.7] | 1.00 | 12/1/6 | 7 |
| RGS/4class | 15 | 0.862 | 0.867 | +0.5 [-2.2, +3.2] | +13.7 [+8.2, +20.3] | **+12.5 [+7.5, +18.3]** ✅ | +9.3 [+4.3, +14.8] | -13.2 [-19.0, -8.2] | 0.91 | 13/0/2 | 2 |

**S2 held in 9 of the 9 cells that met the LR criterion; median S5 (retained share) = 0.94. Verdict (PLAN8 §4): benefit survives the stronger model.**

Runtime 3413 s.

---
**Note added 17 Nov 2026 (after ChatGPT's and R3's reviews; the plan's verdict wording above is kept for the record):** the verdict "benefit survives the stronger model" assumed that the MLP would generalise better than logistic regression. **That condition was not met:**
- S1's mean was positive in 6 of 10 cells;
- its CI was above 0 in 3 of 10 cells and below 0 in 1.

The supported reading is narrower: **with a non-linear model (an MLP ensemble) on the same features, the adaptation benefit persisted in all cells.** This shows that the benefit is not specific to logistic regression. It does **not** show that it survives a genuinely stronger general model.

"Retained share 0.94" is a ratio of gains, not an accuracy. The run took 3,413 s (≈ 57 min).
