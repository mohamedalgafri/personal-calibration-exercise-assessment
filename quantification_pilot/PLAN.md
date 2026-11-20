# Pilot: estimating time in activity classes for NEW people (quantification) — plan written BEFORE running (15 Nov 2026)

## Question
From smartphone/wearable motion data, a researcher wants each person's **share of time** in activity classes (e.g. lying / sitting / standing / walking), not a label for every 2.56-s window. Standard practice: classify each window, then count ("classify-and-count", CC). When a new person's activity mix differs from the training people's mix (prior/label shift), CC is known to be biased toward the training mix. Quantification methods correct this. **Pilot question:** on held-out people with shifted activity mixes, do quantification methods estimate the activity-time profile more accurately than CC?

## Data
UCI HAR (Anguita et al. 2013, CC BY 4.0): 30 adults, smartphone on waist, 6 activities, 561 provided features per 2.56-s window, documented subject IDs. Train+test files merged; split **by person** only.
Classes used: 6 original (WALKING, UPSTAIRS, DOWNSTAIRS, SITTING, STANDING, LAYING). Secondary view: 3 intensity groups (sedentary = sitting+lying, standing = light-stationary, ambulatory = walking+stairs) obtained by summing estimated shares.

## Design (fixed in advance)
- Outer: leave-persons-out, 5 folds of 6 people, × 2 repeats (different person partitions). 10 outer folds.
- Classifier (fixed, no tuning): multinomial logistic regression on standardized features (numpy, L2 = 1e-2, full-batch gradient descent, fixed iterations). Same classifier for every method.
- Quantifier calibration statistics (confusion rates / posteriors on training data) come from an **inner person-grouped 5-fold CV** on the training people — never from training predictions (avoid optimistic rates).
- Test samples ("simulated days"): for each held-out person, draw target prevalence vectors from a flat Dirichlet (APP-style, the standard quantification protocol), then sample that person's windows with replacement to n = 300 windows per sample. 20 samples per person per fold → 6 × 20 = 120 samples per fold, 1,200 total per repeat set.
  - Additional "natural" condition: each held-out person's full, unresampled recording (prevalence as recorded; small shift — reported separately).
- Methods:
  1. CC — classify and count.
  2. PCC — average posterior probabilities.
  3. ACC — adjusted CC (invert confusion matrix; constrained least squares projected to the simplex).
  4. PACC — probabilistic ACC.
  5. EMQ / SLD — Saerens-Latinne-Decaestecker EM re-weighting of posteriors.
  6. HDy-style distribution matching solved by **PSO** (continuous PSO over the simplex via softmax parameterisation; minimises Hellinger distance between the test posterior histogram and a mixture of class-conditional training histograms). The same objective solved by **random search with the same budget of evaluations** as the control for "is PSO needed".
  7. Train-prevalence baseline (always predict the training mix) — the "do nothing" reference.
- Primary metric: **mean absolute error of the 6-class prevalence vector (AE)**, also reported in **minutes per 8 h** (AE × 6 classes × 480 min / 2 gives total misallocated minutes; reported as mean absolute minutes per class = AE × 480).
- Secondary: Relative AE (smoothed); KLD; 3-group AE; window-level accuracy of the classifier (for context only).
- No p-values (folds overlap across repeats). Report means, and the share of outer folds where a method beats CC.

## Pre-stated expectations (may be rejected)
- E1: CC beats the train-prevalence baseline (classifier is useful).
- E2: Under simulated shift, at least one of ACC/PACC/EMQ has lower AE than CC in ≥ 8/10 outer folds.
- E3: On the natural (unshifted) recordings, the gain of correction methods over CC is small or absent.
- E4: PSO and random search with equal budget reach similar HDy objective values (no claim that PSO is better). If PSO is clearly better, report it; if not, report it.
If E2 fails, the main motivation of the proposal ("CC is not enough for activity-time profiles of new people") is not supported on this data and must be weakened.

## Known limitations (stated before running)
- Scripted lab protocol, 30 young adults, waist smartphone: NOT free-living, NOT older adults; activity mixes are simulated by resampling.
- Simulated "days" of 300 windows ≈ 12.8 min, not a real day.
- Windows overlap 50% in UCI HAR; resampling with replacement within a person.
- Results show feasibility of the evaluation pipeline, not clinical validity.
