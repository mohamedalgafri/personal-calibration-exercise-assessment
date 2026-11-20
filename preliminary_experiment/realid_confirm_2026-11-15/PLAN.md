# Confirmatory check with REAL subject IDs — plan written BEFORE running (15 Nov 2026)

Purpose: answer ChatGPT's main objection to P5 (inferred, partly circular person IDs; alpha/k confounds; uniform chance baseline; overlapping-fold p-values) on a dataset with documented subject IDs and a target that varies within a person.

## Data
UCI Parkinson's Telemonitoring (UCI id 189), member `telemonitoring/parkinsons_updrs.data` from ChatGPT's verified archive (sha256 f2c7d5…dd39). 42 documented subjects, 5875 rows (101–168 per subject). Target: `motor_UPDRS` (varies over time within a person; note it is linearly interpolated between clinical visits per the dataset description — a known limitation). Excluded from inputs: subject#, test_time, total_UPDRS, motor_UPDRS.
To keep kernel ridge fast: 20 rows per subject, evenly spaced in test_time (840 rows). Same subsample for every arm.

## Features
- 16 voice features (task-related candidates).
- 2 real person-constant attributes: age, sex (kept, reported separately — NOT treated as noise, since they may be legitimately predictive).
- 6 SYNTHETIC person codes: for each code seed, each subject gets 6 random N(0,1) values, constant over that subject's rows, generated independently of everything else (generative definition as ChatGPT required). 3 code seeds.
Total d = 24.

## Design (fixed in advance)
- Outer: person-grouped 3-fold × 2 repeats (6 outer folds). Held-out persons identical across arms.
- FIXED final predictor for every list: RBF kernel ridge, alpha = 0.1, gamma = 1/(d_sel·var) — no tuning, so arm differences come only from the selected list.
- Arms:
  1. Spearman top-6 (deterministic, no internal CV): expected IDENTICAL lists under both internal protocols → implementation sanity check, not an arm.
  2. RReliefF top-6, standard neighbours vs cross-person-only neighbours (no CV involved; compares neighbour definitions).
  3. Binary PSO (V-shaped, 15 particles × 20 iterations, λ = 0.5, init_p 0.15) with kernel-ridge fitness; inner 3-fold CV either RECORD-wise (person-ignoring) or PERSON-grouped. Same PSO seed for both protocols.
- Control: for each selected list, 100 random lists of the SAME size (reduced from 200 for runtime before any result was seen) from the same 24 features → expected synthetic-code share and external MAE under random selection of that size.

## Primary outcomes (decided now)
- O1: share of synthetic codes in the selected list vs the size-matched random expectation (6/24 = 0.25 for uniform; reported per list size).
- O2: external MAE on held-out persons with the fixed predictor.
- O3: list size; Jaccard between protocols for the same outer fold.
No p-values (folds overlap across repeats); report means and the range across the 3 code seeds × 6 folds.

## Pre-stated expectations (may be rejected)
- E1: PSO with record-wise inner CV selects synthetic codes ABOVE the size-matched random expectation; with person-grouped inner CV, at or below it.
- E2: Standard RReliefF selects synthetic codes above random expectation; cross-person RReliefF does not.
- E3: Lists with more synthetic codes have equal or worse external MAE.
If E1/E2 fail with real IDs, the P5 identity findings are not supported and v9's mechanism claim must be dropped or narrowed.
