# PLAN8 results: adaptation with a different general model (MLP ensemble), 16–17 Nov 2026

**Plan:** `PLAN8.md`, sha256 `2308ac11…d008`, frozen 22:03 before any real data were run with the MLP.

**Run:** 3,413 s (≈ 57 min). **Sanity check passed:** GEN-LR recomputed for 138 person × repeat values in three cells, with maximum difference 0.0 from the saved PLAN5/PLAN6 values. Full table: `results/summary_plan8.md`. Raw data: `results/results_plan8.json`. Claude recomputed the S1, S2 and S4 means independently from the JSON, and they matched.

**Status:** development data (PHYTMO and GAITEX had already been analysed with logistic regression), so this is a **robustness analysis, not a confirmation**. No deviation from the plan.

## Pre-specified outcome
- **S2 (ADAPT-MLP − GEN-MLP ≥ 2 with CI > 0) held in 9 of the 9 cells** that had met the criterion with logistic regression. It also held in HAA/OPT, where the logistic-regression criterion had not been met (+4.2 [+1.4, +8.0]).
- **Median retained share S5 = 0.94.**
- **Verdict by the PLAN8 §4 wording: "benefit survives the stronger model".**

| Cell | S1: GEN-MLP − GEN-LR | S2: ADAPT-MLP − GEN-MLP | S3: vs donor (MLP) | S4: GEN-MLP − ADAPT-LR |
|---|---|---|---|---|
| SQT/IMU | −2.6 [−5.1, −0.3] | +4.5 [+1.2, +8.6] | +4.5 | −5.6 [−11.1, −1.0] |
| SQT/OPT | +3.9 [+0.7, +7.0] | +4.8 [+1.5, +8.9] | +5.0 | −3.3 [−9.3, +1.5] |
| HAA/IMU | −1.8 [−4.4, +0.7] | +3.5 [+1.4, +5.9] | +3.4 | −4.9 [−8.8, −1.9] |
| HAA/OPT | −3.6 [−9.0, +1.0] | +4.2 [+1.4, +8.0] | +2.5 | −4.5 [−9.5, −0.6] |
| SQZ/IMU | +0.5 [−4.1, +5.2] | +8.4 [+4.6, +12.8] | +8.6 | −8.4 [−13.4, −3.8] |
| SQZ/OPT | +2.1 [+0.2, +3.9] | +7.1 [+3.7, +10.8] | +6.6 | −6.1 [−9.8, −2.6] |
| EAH/IMU | +2.6 [+0.5, +5.5] | +3.9 [+0.8, +8.3] | +3.8 | −2.8 [−6.5, −0.2] |
| EAH/OPT | +0.6 [−1.9, +2.8] | +4.1 [+1.4, +7.5] | +4.2 | −3.7 [−6.9, −1.0] |
| GAITEX RD | −0.8 [−3.6, +2.1] | +7.1 [+3.3, +12.1] | +6.6 | −7.9 [−13.8, −3.7] |
| GAITEX RGS | +0.5 [−2.2, +3.2] | +12.5 [+7.5, +18.3] | +9.3 | −13.2 [−19.0, −8.2] |

## Honest reading
1. **The MLP was not a stronger model for new persons.** Its general accuracy was higher than logistic regression in 6 of 10 cells and lower in 4. Only 3 cells have a CI above 0 (SQT/OPT, SQZ/OPT, EAH/IMU), and one has a CI below 0 (SQT/IMU). The verdict wording "survives the stronger model" was written before the results, on the assumption that the MLP would generalise better. **That assumption did not hold.**
   - **What this run shows:** the benefit of adapting with the person's examples is **not specific to logistic regression**. It persisted with a different, non-linear model family on the same features (median retained share of the gain 0.94; this is a ratio of gains, not an accuracy, and it does not establish that the two models are equivalent).
   - **What it does not show:** that a **genuinely stronger** general model (one that is better on new persons, for example a temporal deep model trained on raw sequences or a pose-sequence foundation model) would not reduce the benefit. That remains open, and it is a master's question.
2. **S4: in 9 of 10 cells the MLP general model stayed below the adapted logistic regression** (CI below 0; SQT/OPT inconclusive). Within these model classes, a different general model did not replace calibration.
3. **S3: own examples beat the donor's examples with the MLP too** (all 10 cells; CIs in the summary). The same-session caveat applies unchanged: this cannot separate person from session effects.
4. **Limits:** development data; MLP hyperparameters fixed a priori and not tuned; summary features; same-session calibration; healthy adults; approximate CIs over 10 cells.

**Suggested wording for the proposal:** "A robustness check with a non-linear general model (an MLP ensemble on the same features), which was not consistently better than the logistic regression on new persons, still showed an adaptation benefit in all cells. Whether a general model that is genuinely better on new persons, such as a temporal deep model, would reduce the benefit has not been tested."
