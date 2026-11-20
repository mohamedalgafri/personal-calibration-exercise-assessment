# Pilot 4 — confirmatory test on two UNSEEN exercises: how to split a fixed calibration budget (written 15 Nov 2026, BEFORE downloading these exercises)

## Why
Pilot 3 (SQT, KFE, EFE) suggested that calibration examples containing both standard and deviating execution help more than standard-only examples, but the original comparison used unequal budgets (ChatGPT, CODEX_V13_REVIEW). A matched-budget re-check on SQT (post hoc, by ChatGPT) supported it (5.5 vs 10.3 points). This pilot tests the claim on exercises whose data neither assistant has seen: **HAA** (hip abduction; IMUs on the moving leg's shin and thigh; L and R recordings pooled as for KFE) and **SQZ** (squeezing; 4 upper-limb IMUs). PHYTMO, CC BY 4.0. Healthy volunteers; deviations performed on purpose; labels per series.

## Fixed in advance
- Pre-processing identical to Pilot 3 (`code/run_phytmo.py`): drop recordings with any missing value; trim first 25% / last 5%; 2-s windows, 1-s step; acc + gyro (+ magnitudes); 6 statistics per channel. A data-quality report (excluded files, persons with all four series) is printed before any model is trained.
- Outer: person-grouped 5 folds × 2 repeats (seeds 3000/3001, as in Pilot 3). Fixed classifier (logistic regression, same settings).
- **Evaluation set fixed for every condition:** all windows of the person's series 2 (and the same 30 simulated 40-window mixtures per person, secondary).
- **Calibration pool:** the person's series 1. Budget B ∈ {8, 16} windows. Deviation share f ∈ {0, 0.25, 0.5, 0.75}: n_dev = round(f·B) first windows of the wrong series, n_std = B − n_dev first windows of the correct series. If a pool is too short, use what exists and report it.
- Calibration = warm-start fine-tuning, 60 Adam steps, 1,500 random source windows (weight 1) + calibration windows (weight 20) — same as Pilot 3.
- **Control SRC:** the same fine-tuning on the 1,500 source windows only (no personal data). Baseline GEN: no fine-tuning.

## Outcomes
- Primary: balanced accuracy on series 2.
- Secondary: simulated-session error (|estimated − true correct share|, points); persons improved vs SRC; worst person.

## Pre-stated expectations (may be rejected)
- **H1 (confirmatory):** at each budget, f = 0.5 has higher balanced accuracy than f = 0 in ≥ 8/10 folds, for **both** exercises.
- H2: SRC ≈ GEN (difference < 0.01 balanced accuracy on average), i.e. gains come from personal data, not from extra training steps.
- H3 (descriptive, no expectation): shape of the curve over f; whether f = 0.25 or 0.75 is best.
- **Decision rule:** if H1 fails for both exercises, the claim "mixed examples beat standard-only examples at equal budget" is not confirmed and will not be made. If it holds for one, it is reported as exercise-dependent.

No p-values (folds re-use persons). All outputs saved under `results/pilot4/`.
