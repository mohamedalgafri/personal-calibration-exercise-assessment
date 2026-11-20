# Pilot 3 (PHYTMO): assessing physiotherapy exercises of NEW people with wearable sensors, with and without a short supervised first session — plan written BEFORE looking at any data values (15 Nov 2026)

## Clinical scenario
A therapist prescribes home exercises. In the first session (supervised) the patient performs a few correct repetitions and, guided by the therapist, a few typical wrong ones. At home, body-worn sensors record each session; the system should tell, for each session, **how much of the exercise was performed correctly**. Question: how well does a model trained on other people do this for a new person, and how much does the supervised first session help?

## Data
PHYTMO (García-de-Villa et al., Scientific Data 9:266, 2022; Zenodo 5052756, CC BY 4.0): 30 volunteers aged 20–69, healthy (wrong executions are performed on purpose; labels by an expert), IMUs at 100 Hz. Each person: **series 1 and 2 performed correctly (P=0), series 1 and 2 performed wrongly (P=1)**, ≥ 8 repetitions per series.
Exercises used in this pilot (chosen before seeing data, to limit download): **SQT** (squat; 4 IMUs on both legs), **KFE** (knee flexion-extension; the two IMUs on the moving leg; left- and right-leg recordings pooled, leg as a recording attribute), **EFE** (elbow flexion-extension; 4 IMUs on both arms).
Channels: accelerometer and gyroscope (x, y, z, magnitude); magnetometer excluded (depends on the room).
Pre-processing (fixed now): drop the first 25% and last 5% of each recording (synchronisation movements at the start); windows of 2.0 s with 1.0 s step; IMUs aligned by sample index after trimming (recordings already synchronised by the authors); per-window features for each IMU channel: mean, SD, min, max, range, mean absolute first difference.

## Split (the scenario)
- Outer: person-grouped 5-fold × 2 repeats, per exercise. Test persons never in training.
- For a test person: **series 1 (correct and wrong) = supervised first session (calibration pool); series 2 = home sessions (evaluation)**. Nothing from series 2 is ever used for training or calibration.

## Methods (same fixed logistic regression as previous pilots; no tuning)
1. GEN — trained on other people (both series).
2. CAL-k — GEN fine-tuned (warm start, 60 Adam steps) on 1,500 random training windows + the person's first k windows of each class (correct, wrong) from series 1, weighted ×20. k ∈ {3, 5, 10, all of series 1}. (k windows ≈ k+1 seconds of movement.)
3. PERS-all — model trained only on the person's series 1 (all windows), as the "personal only" reference.
4. For session estimates: classify-and-count (CC) with each model, and ACC (adjusted count) using the confusion matrix of GEN on the person's series-1 windows ("personal ACC").

## Outcomes
- O1 (window level): balanced accuracy (mean of sensitivity for correct and for wrong) on the person's series 2.
- O2 (session level): 30 simulated home sessions per person, each of 40 windows drawn from series 2 with a correct-share π ~ Uniform(0,1); absolute error |π̂ − π| in percentage points.
- O3: share of sessions where the "mostly wrong" flag (π < 0.5) is decided correctly.
- Reported per exercise: means over persons; folds where a method beats GEN (of 10); worst person.
No p-values.

## Pre-stated expectations (may be rejected)
- E1: GEN on new people has balanced accuracy clearly above 0.5 but below CAL-all for all three exercises.
- E2: CAL-10 improves balanced accuracy over GEN in ≥ 8/10 folds for at least 2 of 3 exercises.
- E3: CAL-10 reduces the session error (O2) relative to GEN-CC.
- E4: personal ACC (GEN + personal confusion) vs CC: no expectation (in the UCI HAR pilot it did not help).
- E5: PERS-all vs CAL-all: no expectation.
If E2 fails, the supervised-first-session argument is not supported on this data and must be dropped or narrowed.

## Known limitations (before running)
Healthy volunteers simulating errors; laboratory setting; one wrong pattern per exercise mostly (paper: most volunteers erred similarly); labels per series, not per repetition; small n per exercise (≤ 30 persons).

## Addendum A — written 15 Nov 2026 after a literature check, still BEFORE loading any data values
Newest closest work (verified):
- Spilz, Oppel & Munz, arXiv:2505.24415v2 (Jul 2026): IMU exercise evaluation on their own 4 datasets (15–19 participants), LOSO, **patient-specific fine-tuning from a few repetitions recorded and rated by a therapist at treatment onset**. Fine-tuning gains were modest and variable (e.g. macro-F1 0.79→0.82, 0.66→0.79, 0.56→0.58), with high between-subject variability. In their fine-tuning setting the few examples were from **a single class**.
- Burzer et al., BayaHAR, ISWC 2026 (doi:10.1145/3830727.3834833): one 3-s calibration window per activity improves macro-F1 on unseen users by +2.76 to +33.44 pp.
So "a short supervised calibration helps new users" is NOT new. This pilot is positioned as an independent test on a public dataset, plus two pre-specified additions:
1. **Correct-only calibration (realistic onset scenario):** CALC-k = GEN fine-tuned with only the first k CORRECT windows of series 1 (k ∈ {5, 10}). Expectation E6: CALC-k helps less than CAL-k (which also sees wrong examples) and may bias toward "correct"; no expectation on whether it beats GEN.
2. **Age:** PHYTMO spans 20–69 years (groups A–E). Exploratory: report GEN and CAL-10 balanced accuracy by age group; no hypothesis (≤ 10 persons per group).
The session-level outcome (share of correct movement per session, O2) is not evaluated in the works above and stays the main outcome of interest.
