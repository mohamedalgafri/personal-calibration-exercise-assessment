# Step 2: short personal calibration — plan written BEFORE running (15 Nov 2026)

## Why (honest history)
- Pre-registered pilot (PLAN.md) → **E1 held, E2 and E3-as-motivation failed**: classify-and-count (CC) beat ACC/PCC/PACC/EMQ/HDy in 10/10 folds, under both natural and simulated shifts. CC error did not grow with mix shift (corr 0.02).
- Post-hoc diagnostic (diag_posthoc.md, exploratory): per-person CC error correlates **0.90** with how much that person's own confusion matrix differs from the training confusion matrix. With the person's own confusion matrix ("oracle", not achievable in practice) ACC error ≈ 0. Interpretation: for new people the error is driven by **person-specific movement patterns** (violation of the label-shift assumption P(x|y) equal across people), not by activity-mix shift.
- Hence a practical question, decided now, before seeing any calibration result: **can a few seconds of labelled activity from the new person (a short calibration, like a field test at the start of a session) estimate that person's confusion well enough to correct the activity-time profile?**

## Data and split
Same UCI HAR files, same outer person partitions as run_quant.py (5 folds × 2 repeats, seeds 2026/2027), same fixed classifier (LogReg, 561 features).
For each held-out person and each class c: **calibration windows = the first k windows of class c in recording order**; the next window is discarded (UCI HAR windows overlap 50%); all later windows form the evaluation pool. k ∈ {3, 5, 10, 20} windows per class (≈ 5, 8, 14, 27 s per activity; 6 activities).

## Methods (all evaluated on the same evaluation pool)
1. CC — base classifier, count (reference; uses no calibration).
2. ACC_train — ACC with the training confusion (inner person-grouped 5-fold CV), as in the pilot.
3. ACC_personal — ACC with the confusion matrix estimated on the person's k calibration windows per class (base classifier).
4. ACC_shrink — ACC with M = (k·M_personal + m·M_train)/(k + m), m = 10 (fixed in advance, not tuned).
5. FT_CC — personalised classifier: base weights fine-tuned for 60 Adam steps on 1,500 random training windows + the calibration windows weighted ×20; then count. (Strong, standard competitor: personalisation of the classifier itself.)

## Conditions and outcomes
- Natural: the person's evaluation pool as recorded.
- Shifted: 20 samples × 300 windows per person drawn from the evaluation pool with flat-Dirichlet mixes (as in the pilot).
- Outcome: AE of 6-class proportions (and ×480 minutes per class per 8 h); worst-person AE (natural); folds better than CC (of 10).

## Pre-stated expectations (may be rejected)
- E5: ACC_personal or ACC_shrink with k ≥ 10 has lower AE than CC in ≥ 8/10 folds (natural and shifted).
- E6: the largest gains are in the worst persons (max AE reduced).
- E7: FT_CC is a strong competitor; no expectation about which wins. If FT_CC wins, the honest conclusion is "personal calibration helps, through the classifier rather than through quantification".
- E8: ACC_train remains worse than CC (replicates the pilot).
No p-values; means, ranges, and fold counts.
