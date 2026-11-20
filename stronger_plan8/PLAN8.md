# PLAN8: does the benefit of adaptation survive a stronger general model? (development data: PHYTMO and GAITEX)

**Written:** 16 Nov 2026, at Mohamed's request ("Stronger model first"), after the examiner/advisor review (`review_2026-11-16_v19/G2_…`) and ChatGPT's earlier critique named this as the main threat. The fingerprint (sha256) goes in `results/PLAN8.sha256` and in DEBATE before any real data are run.

**What had been done before this plan:** only a speed test of the new model on random synthetic data. No PHYTMO or GAITEX data were run with the new model.

**Status of the data:**
- PHYTMO (PLAN5) and GAITEX (PLAN6) have **already been analysed** with the logistic regression.
- So this is a **robustness analysis on development data**, not a blind or confirmatory test. It asks one question of data whose earlier results are known.

## 1. Question
All results so far used a multinomial logistic regression (LR) on summary features. Would a **stronger general model** assess new persons well enough that adaptation with the person's few labelled examples adds little or nothing? And does adaptation still help when it is applied to the stronger model?

## 2. The stronger model (fixed now; not tuned on these data)
**Architecture:** an ensemble of **3 multilayer perceptrons**, numpy (`code/mlp.py`):
- 2 hidden layers (128, 64), ReLU, softmax output;
- Adam, learning rate 10⁻³, L2 10⁻⁴, mini-batches of 256, **60 epochs**;
- class-balanced sample weights;
- seeds 0, 1 and 2; the class probabilities are averaged.

**Inputs:** exactly the same features as the LR in each dataset:
- PHYTMO: 6 statistics per channel on 2-s windows, IMU and OPT;
- GAITEX: 432 heading-free orientation features per repetition.

**Adaptation (ADAPT-MLP):**
- Warm-start fine-tuning of every member from GEN-MLP, keeping each member's scaler.
- 60 mini-batch steps at learning rate 5 × 10⁻⁴.
- Training rows: the same source replay as the LR (PHYTMO: the same 1,500 random source windows; GAITEX: all source repetitions) plus the person's calibration examples, with weight 20.

**Unseen-donor control (CTRL-NEW-MLP):** the same as ADAPT-MLP, with the donor's calibration examples (the donor rule as in PLAN5 Addendum A and PLAN6).

**Not included:** a personal-only MLP (16 examples are too few for an MLP; the LR personal classifier results already exist) and the replay control.

**Honest limit:** this is a stronger, non-linear general model on the same summary features. It is **not** a temporal deep network on raw sequences, such as the skeleton models of the Rehab-Pile benchmark (Ismail-Fawaz et al., 2026). PyTorch is not available here. A negative or positive result therefore concerns this model class only.

## 3. Design (identical to the earlier runs, so the results pair with the saved LR results)
**PHYTMO (PLAN5 design):**
- 4 exercises × {IMU, OPT};
- the same eligible persons;
- 5 folds × 2 repeats with permutation seeds 3000 + rep and test persons perm[fi::5];
- replay seed 5000 + 10·rep + fi;
- calibration B = 16 balanced windows from series 1; evaluation on series 2;
- binary balanced accuracy.

**GAITEX (PLAN6 design):**
- RD and RGS, the same eligible persons (19 / 15);
- 5 folds × 2 repeats with seeds 6000 + rep (array_split);
- calibration = the first 4 repetitions of each of the 4 variants (B = 16); evaluation = the last 5 of each;
- 4-class balanced accuracy.

**LR reference values:** GEN-LR and ADAPT-LR are taken from the saved `results_plan5.json` and `results_plan6.json` and paired by (rep, fold, person).
- **Sanity check:** for 3 cells (PHYTMO SQT/IMU, PHYTMO EAH/OPT, GAITEX RD), GEN-LR is recomputed in this run and must equal the saved values (|difference| < 10⁻⁹ for every person × repeat). If not, the run stops and this is reported.

**Only B = 16** (the primary budget in both earlier plans).

## 4. Outcomes and pre-stated decision rules (per cell; person = mean over repeats; points; percentile bootstrap over persons, 2,000 resamples, seed 0)
- **S1:** GEN-MLP − GEN-LR (does the stronger model generalise better to new persons?). Descriptive.
- **S2 (primary):** ADAPT-MLP − GEN-MLP. The adaptation benefit **holds in a cell** if it is ≥ +2 points with CI > 0.
- **S3:** ADAPT-MLP − CTRL-NEW-MLP > 0 with CI > 0 (own examples vs a donor's, on the stronger model).
- **S4:** GEN-MLP − ADAPT-LR (does a stronger general model, without calibration, reach the adapted simple model?). Descriptive, with CI.
- **S5:** the per-cell retained share (ADAPT-MLP − GEN-MLP) / (ADAPT-LR − GEN-LR), reported only where the denominator is ≥ 2 points. Descriptive.

**Verdict (10 cells: 8 PHYTMO + 2 GAITEX):**
- **"benefit survives the stronger model":** S2 holds in at least 7 of the 10 cells that met the LR criterion before (PHYTMO 7, GAITEX 2 = 9 cells; HAA/OPT did not), **and** the median S5 ≥ 0.5;
- **"benefit reduced":** S2 holds in 4–6 of those 9 cells, or the median S5 < 0.5;
- **"benefit does not survive":** S2 holds in ≤ 3 of those 9 cells.

**Also reported:**
- counts of persons improved, worse and tied under ADAPT-MLP vs GEN-MLP;
- persons at ceiling (GEN-MLP ≥ 0.98);
- runtime.

**Expectation (honest prior, not a hypothesis test):** GEN-MLP improves on GEN-LR in some cells, and the adaptation benefit shrinks but survives in most cells.

## 5. Limits declared now
- Development data whose LR results are known.
- One stronger model class (an MLP ensemble on summary features), with hyperparameters fixed a priori and not tuned. A tuned or temporal deep model could behave differently.
- Same-session calibration and evaluation.
- Healthy adults with instructed deviations.
- PHYTMO windows overlap.
- Approximate CIs over many cells, with no family-wise correction.

## 6. Outputs
- `results/results_plan8.json` (per person × repeat × cell: GEN_MLP, ADAPT_MLP, CTRLNEW_MLP, GEN_LR_recomputed where checked);
- `results/summary_plan8.md`, `results/run_log.txt`;
- `RESULTS_PLAN8.md`, with expectations marked exactly as defined and post hoc analyses labelled.
