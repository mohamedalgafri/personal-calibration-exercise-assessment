# Pilot 3 (PHYTMO) — results and honest reading (15 Nov 2026)

**Plan:** `PLAN3.md` (written before loading data) + Addendum A (written after the literature check, still before loading data).
**Code:** `code/run_phytmo.py`. **Outputs:** `results/summary_phytmo.md`, `results/results_phytmo.json`.

## Deviation (reported openly)
The first run (`results/v1_before_nan_fix/`) gave chance-level results for the knee exercise (KFE). Diagnosis: the 4 left-shin KFE files of person C02 contain ~40% missing values (NaN), which corrupted model training. A data-quality rule was added: **recordings with missing values are excluded** (only those 4 files). The plan was not changed. SQT and EFE results were identical before and after the fix. Post-hoc per-leg KFE analyses are in `results/posthoc_kfe_per_leg/v2/` (exploratory).

## Main results (series 2 of each held-out person; 5-fold × 2 person-grouped)
| | SQT squat (26) | KFE knee (30) | EFE elbow (27) |
|---|---|---|---|
| General model (GEN): balanced accuracy | 0.876 | 0.922 | 0.915 |
| GEN: session error (share correct, percentage points) | 10.4 | 6.5 | 7.9 |
| GEN: worst person session error | 51 | 42 | 55 |
| **CAL-3** (≈ 4 s each of correct and wrong, from the first session) | 6.4 (8/10 folds) | 4.7 (10/10) | 4.9 (9/10) |
| **CAL-10** (≈ 11 s each) | 4.9 (8/10) | 3.7 (10/10) | 4.1 (10/10) |
| CAL-all (whole first session) | 4.1 | 3.1 | 2.7 |
| Worst person with CAL-10 | 15 | 16 | 18 |
| CALC-10 (correct examples only) | 9.6 (7/10) | 5.6 (4/10) | 6.8 (4/10) |
| PERS-all (personal model only) | 8.9 | 5.3 | 4.4 |
| GEN + personal ACC (quantification correction) | 11.8 (3/10) | 8.9 (1/10) | 9.2 (2/10) |
Persons with session error > 15 points: GEN 5 / 4 / 3 → CAL-3 1 / 3 / 1. Median person: CAL-3 7.1→6.5, 4.25→3.17, 5.0→4.42; **CAL-10 7.1→3.92, 4.25→2.31, 5.0→2.63** (corrected 15 Nov after advisor-review agent). Improved/worse/tied with CAL-10: 15/8/3, 18/4/8, 15/2/10.

## Pre-stated expectations
- E1 ✅ GEN well above chance and below CAL-all in all three exercises.
- E2 ✅ CAL-10 better than GEN in ≥ 8/10 folds in all three exercises.
- E3 ✅ CAL-10 reduces the session error in all three.
- E4 (no expectation): this ACC variant (person-specific confusion from series 1) was **worse** than plain counting in all three.
- E5 (no expectation): CAL-all better than PERS-all in all three (general knowledge + personal data beats personal data alone).
- E6 ✅ correct-only calibration helped less — but with half the windows (unequal budget; see matched-budget check in point 2).
- Age (exploratory): no consistent pattern with 4–10 persons per group; no claim.

## What this means
1. A model trained on other people assesses many new people well, but **a few people (3–5 of 26–30) are assessed badly** (session errors of 15–55 points) — the same "individual minority" pattern as in the UCI HAR pilot.
2. Calibration with correct and wrong examples reduced the mean and worst-person error; 15/26, 18/30, 15/27 persons improved (8, 4, 2 got worse); with CAL-10 the median person's error roughly halved. The CALC comparison also used fewer windows; a matched-budget check on SQT by ChatGPT (CODEX_V13_REVIEW) gave mixed 5.5 vs correct-only 10.3 points. **Correction:** Spilz et al. (§2.3.7) did not assume 'correct only' examples — their single class may be any consistent level, and missing classes are completed with real or simulated examples. No claim of going beyond them.
3. **The tested ACC variant (GEN + person-specific confusion) did not improve the mean.** MC-SQ/MC-MQ/MetaQuant/PSO were NOT implemented in this pilot; `acc_share` falls back to CC when tpr−fpr<1e−6 (including negative values) — to be revisited. Session = simulated mixtures of overlapping 2-s windows; series 1/2 = separate same-day recordings, not a later home session. CAL-10 ≈ 11 s per class (≈ 22 s total).

## Limits
Healthy volunteers performing errors on purpose; labels per series, not per repetition; calibration and evaluation on the same day; 2-s windows, not segmented repetitions; one simple model; 26–30 persons per exercise.
