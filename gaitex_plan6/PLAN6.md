# PLAN6: personal adaptation on independent data (GAITEX, inertial orientation), with fair tuning and a pre-specified "adapt or not" rule

**Written:** 16 Nov 2026, before any GAITEX sensor values were downloaded or seen.

**What had been read before this plan (structure only):**
- the Zenodo record and the zip index (file names and sizes);
- the data paper's Methods section;
- for one person (`austra`), the RD and RGS repetition boundary files (`timestamps_*.csv`: labels with start and end times) and the RD metadata JSON;
- the **column header only** of one IMU file. It contains `time [s]` and 9 × 4 orientation-quaternion columns (W, X, Y, Z); **no raw accelerometer or gyroscope data are released**.

**Status:**
- This plan is the protocol. Any later change is a dated addendum, and any analysis decided after results is labelled post hoc.
- The fingerprint (sha256) is saved in `results/PLAN6.sha256` and posted in `shared_dialogue/DEBATE.md` before the download starts.
- A local hash records the plan's timing. It is **not** an institutional pre-registration.

**ChatGPT's conditions included** (DEBATE.md, 16 Nov, "v17 and PLAN6 feasibility"):
- the fixed-settings comparison is primary and tuning/PSO is secondary;
- matched tuning budgets, with inner tuning on source persons only;
- no leakage between repetitions and no absolute timing or order cues;
- the adapt-or-not rule uses only calibration labels, predictions from outside the data that trained the adaptation, a fixed sequence, and comparison with always and never adapting, with the harm shown;
- the difference from the closest prior study, which used this dataset, is stated;
- single-session data do **not** test transfer across days.

---

## 1. Questions
- **Q1 (primary).** Under the frozen PHYTMO protocol, does adapting a general model (GEN) with a few labelled repetitions of a new person (ADAPT) beat:
  - GEN itself;
  - a replay control (CTRL);
  - the same number of new repetitions from another person (CTRL-NEW)?

  This is asked on new persons, a new laboratory, new exercises and a new sensor system.
- **Q2.** Does a personal classifier (PERS) beat ADAPT at any tested budget?
- **Q3.** How are gains and losses distributed across persons? Is the gain larger for persons whom GEN assesses less well?

  This last point was a post hoc observation on PHYTMO; here it is a **pre-specified prediction**.
- **Q4 (exploratory, pre-specified).** Can the person's calibration repetitions alone decide whether to adapt, compared with always and never adapting?
- **Q5 (secondary).** Does tuning the settings of ADAPT and PERS by person-grouped inner validation change the conclusions? Does PSO beat random search at an equal number of evaluations?

## 2. Relation to the closest prior study, which used these data
Spilz, Oppel & Munz (*AI* 2026, doi:10.3390/ai7090381; arXiv:2505.24415v2, §2.1, §2.3.7, §3.6 read) used GAITEX RD (19 persons) and RGS (18 persons).

**Their design:**
- a CNN on IMU-derived orientation data, evaluated leave-one-subject-out with 4-class macro-F1;
- patient-specific fine-tuning of the dense layers with **7 of the person's own repetitions from a single class** (5 for training, 2 for validation);
- the classes the person did not perform were supplied with other subjects' real data or with simulated data;
- fine-tuning was applied to everyone, "since subject-specific performance cannot be known a priori";
- they report per-subject ups and downs (RD without augmentation: 7 improved, 2 declined, 10 unchanged; RGS: 6 / 5 / 7).

**PLAN6 differs as follows. This is a positioning statement, not a claim of superiority:**
1. Calibration contains the person's own repetitions of **all four variants**, at budgets of 4, 8 and 16.
2. There are **matched controls**: a replay control with equal extra training, and an unseen-donor control with the same number of new repetitions from another person.
3. There is a **personal-classifier** baseline.
4. A simple linear model on hand-crafted features.
5. Person-level paired intervals and pre-defined distribution patterns.
6. A **pre-specified rule that decides from calibration repetitions whether to adapt**. This directly tests their premise that subject-specific performance cannot be known beforehand.
7. A fair tuning comparison.

Our numbers are **not directly comparable** to theirs (different model, features, split and metric).

## 3. Data and download
**Source:**
- GAITEX, Zenodo 15729056, CC BY 4.0, `data.zip`.
- Members fetched by HTTP range requests using the saved zip index `feasibility_2026-11-16/gaitex_zip_index.json`.

**Members:** for every person and for `rd` and `rgs`:
- `xsens_imu_data_<p>_<ex>.csv` (raw sensor orientation; not the segment-registered version);
- `timestamps_<p>_<ex>.csv`;
- `metadata_<p>_<ex>.json`.

In total 37 IMU files (0.79 GB) plus small files. Markers and the gait tasks are **not** downloaded.

**Integrity checks:**
- the byte size equals the index size;
- the CSV parses;
- the column header is identical across files.

**Repetitions:**
- Each row of `timestamps` is one repetition with label ∈ {correct, error A, error B, error C}.
- Repetitions are ordered by start time within each label and numbered 1..n.
- Frames with time in [start, end) belong to that repetition.

## 4. Data-quality rules (fixed now)
1. A frame is invalid if any quaternion value is non-finite or any quaternion norm is outside [0.9, 1.1].
2. A repetition is dropped if more than 5% of its frames are invalid or it has fewer than 50 frames. Otherwise invalid frames are removed.
3. A person is **excluded from an exercise** if any of the 4 variants has fewer than 9 valid repetitions. This guarantees that calibration and evaluation repetitions do not overlap.
4. Every exclusion is listed **in full** (file, person, reason) in `results/exclusions.txt`.

## 5. Features
The unit is **one whole repetition**: no windows and no overlap between repetitions.

**Per sensor (9 sensors), from the quaternion series q(t) of the repetition only:**
1. **Gravity direction in the sensor frame** (3 channels): R(q)ᵀ·[0, 0, 1]. This is inclination and does not depend on heading.
2. **Angular velocity in the sensor frame** (3 channels) and its norm (1 channel), from consecutive frames: Δq = q(t)⁻¹ q(t+1), rotation vector × 100 Hz. Signs are handled so that q and −q give the same result.
3. **Rotation angle relative to the first frame of the repetition** (1 channel): the angle of q(t₀)⁻¹ q(t).

**Statistics:**
- Per channel: mean, standard deviation, minimum, maximum, range, and mean absolute first difference. These are the same 6 statistics as PHYTMO.
- Total: 9 × 8 × 6 = 432 features.

**Excluded by design:**
- absolute heading;
- raw quaternions;
- time stamps, repetition index or position in the recording;
- repetition duration as a separate feature;
- markers;
- magnetometer data (not released).

**Known residual confound (stated, not removable):** the variants were recorded in a fixed order, correct first. Slow drift or fatigue could therefore correlate with class. The inclination features are heading-free but not drift-proof.

## 6. Tasks and split
**Primary task:** 4-class classification (correct + 3 named errors), the dataset's native label.
- Metric: **balanced accuracy** (mean recall over 4 classes) in points.
- Macro-F1 is also reported, for orientation only.

**Secondary task:** binary correct vs any error, with fixed settings only, for comparability with PHYTMO. Class-balanced weights are used, because the classes are 1 : 3.

**Calibration and evaluation within a person:**
- Calibration budget B = 4k repetitions with **k ∈ {1, 2, 4} per variant** (B = 4, 8, 16). These are the **first k** repetitions of each variant.
- **Evaluation:** the **last 5** repetitions of each variant (20 repetitions). The evaluation set is the same for every condition and budget.
- The calibration and evaluation repetitions never overlap. They come from the same set and session.
- Granularity: one person's balanced accuracy moves in steps of 5 points per run.

**Outer split:**
- 5 person-grouped folds × 2 repeats (seeds 6000 + repeat).
- A person's score is the mean over the 2 repeats.
- A test person never enters GEN training, scaling, tuning or the choice of rule.

## 7. Strategies (fixed settings = PLAN5 values; classes weighted equally)
- **GEN:** multinomial logistic regression trained on all repetitions of the training persons. The scaler is fitted on those persons only. Settings: L2 = 0.01, 400 Adam steps, learning rate 0.05.
- **ADAPT_B:** start from GEN and keep its scaler. Fine-tune on all source repetitions plus the person's B calibration repetitions, each with weight 20. Settings: 60 steps, learning rate 0.02.
- **CTRL_B (replay control):** the same as ADAPT, but the B extra repetitions are already-seen **source** repetitions (k per class from the training persons).
- **CTRL-NEW_B (unseen-donor control):** the same as ADAPT, but with the B calibration repetitions of **another test person in the same fold** (the next one in sorted order). The donor is not in GEN training.
- **PERS_B:** logistic regression trained **only** on the person's B calibration repetitions, using GEN's scaler. Settings: L2 = 0.01, 400 steps, learning rate 0.05. It is named "personal classifier with source-derived scaling".

## 8. Expectations and decision rules (from PHYTMO; primary = budget 16, 4-class)
- **E1:** ADAPT16 − GEN ≥ +2 points with 95% CI > 0.
- **E2:** ADAPT16 − CTRL16 > 0 with CI > 0.
- **E2b:** ADAPT16 − CTRL-NEW16 > 0 with CI > 0.
- **E3:** PERS16 − ADAPT16 < 0 with CI < 0. We also report the first budget (4, 8 or 16) at which PERS beats ADAPT with CI > 0, if any.
- **Overall verdict for Q1, per exercise:**
  - **"consistent with PHYTMO"** if E1 and E2b both hold;
  - **"partly consistent"** if one of them holds;
  - **"not consistent"** if neither holds.

  Across the two exercises we report 2/2, 1/2 or 0/2. The word **confirmation** is not used.
- **Primary family:** E1 and E2b × 2 exercises (4 intervals), with no family-wise correction. All other contrasts are secondary or exploratory.
- **E4 (Q3, pre-specified prediction):** Spearman ρ(GEN, ADAPT16 − GEN) < 0 in both exercises. A bootstrap CI is reported; this is descriptive.
- **Distribution pattern per exercise (rules fixed now; Δ = ADAPT16 − GEN; worse/improved = beyond ±0.5):**
  1. **mixed:** the number of worse persons is at least one third of n;
  2. otherwise **broad:** median Δ ≥ 2 and at least half of the persons have Δ ≥ 2;
  3. otherwise **concentrated:** the top 5 persons hold ≥ 60% of the gross gain;
  4. otherwise **small/none**.

  We also report counts of improved, worse and tied persons; Δ ≥ +2 and Δ ≤ −2; the best and worst person; and the number of persons at ceiling (GEN ≥ 0.98).
- **Statistics:**
  - paired differences per person;
  - percentile bootstrap over persons, 2,000 resamples, seed 0;
  - the bootstrap is conditional on the folds and models, so the CIs are approximate.

## 9. Q4: "adapt or not" rules (exploratory, pre-specified; budgets 8 and 16)
The rules use only the person's calibration labels. They have **no tuned threshold**, so neither source nor test persons are used to choose them.

- **G1 (no parameters):** adapt if GEN misclassifies at least one of the person's B calibration repetitions; otherwise keep GEN. GEN never trained on these repetitions.
- **G2 (internal cross-validation):**
  - Split the calibration repetitions into k folds by repetition number. Each fold holds one repetition per variant (k = 2 at B = 8; k = 4 at B = 16).
  - For each fold, fine-tune ADAPT on the other folds and predict the held-out fold. Compare its balanced accuracy with GEN on the **same held-out repetitions**.
  - Adapt if the mean (ADAPT_cv − GEN_cv) > 0. A tie keeps GEN.
- **Fixed sequence:** decide first. If the decision is "adapt", the final model is ADAPT_B trained on all B calibration repetitions (the same model as in §7). The evaluation repetitions are never seen before scoring.
- **Report** for GATE vs ALWAYS (= ADAPT_B) vs NEVER (= GEN):
  - mean and median;
  - the number of persons **harmed** (GATE < GEN by more than 0.5);
  - persons where the gate **missed** a gain (ALWAYS > GATE by more than 0.5);
  - the share of persons adapted.
- **Expectation (descriptive):** the gate harms fewer persons than ALWAYS and keeps at least half of ALWAYS's mean gain. We do **not** claim it picks the best strategy for each person.

## 10. Q5: fair tuning and PSO (secondary; 4-class, B = 16)
- **What is tuned (justified ranges: about ±1 order of magnitude around the PLAN5 values; normalised to [0, 1]):**
  - ADAPT: weight w ∈ [1, 100] (log scale), steps ∈ [10, 200], learning rate ∈ [10⁻³, 10⁻¹] (log), L2 ∈ [10⁻⁴, 10⁻¹] (log).
  - PERS: steps ∈ [50, 800], learning rate ∈ [10⁻³, 10⁻¹] (log), L2 ∈ [10⁻⁴, 1] (log).
  - GEN is not tuned; it is the common starting point.
- **Inner objective:**
  - Inside each outer fold, the **training persons only** are split into 3 person-grouped inner folds.
  - For each inner fold: train an inner GEN on the inner-training persons. Then adapt (or train PERS) for each inner-held-out person with their calibration repetitions 1–4 and score them on their repetitions 6–10.
  - Objective = mean balanced accuracy over inner-held-out persons.
  - Outer test persons are never used.
- **Tuners, each with exactly 30 objective evaluations per strategy per outer fold:**
  - **Fixed:** PLAN5 values (0 evaluations).
  - **Random search:** 30 uniform samples. Seed 7000 + fold × 10 + repeat.
  - **PSO:**
    - 6 particles × 5 iterations;
    - inertia 0.7, c₁ = c₂ = 1.5;
    - velocity clamp 0.2;
    - positions clipped to [0, 1];
    - same seed scheme + 1.
- The best setting found by each tuner is applied to the outer test persons, with the outer protocol of §6–§7.
- **Report:**
  - **T0 sensitivity:** the spread (10th–90th percentile) of the inner objective over the 30 random settings, per exercise and strategy.
  - **T1:** ADAPT_RS − ADAPT_fixed and PERS_RS − PERS_fixed on outer persons.
  - **T2:** ADAPT_PSO − ADAPT_RS and PERS_PSO − PERS_RS on outer persons. The best inner objective of each tuner is shown separately (search efficiency is not the same as generalisation).
  - **T3:** ADAPT_RS − PERS_RS (the strategy comparison under equal tuning).
- **Decision rules:**
  - If the T0 spread is < 1 point for ADAPT in an exercise, "tuning cannot matter much here".
  - **PSO adds value** only if ADAPT_PSO − ADAPT_RS ≥ +1 point with CI > 0 in at least one exercise, and its CI lower bound is > −1 in the other. Otherwise the result is "no evidence that PSO adds value over random search here". The same rule is reported for PERS.
  - If T3 reverses E3 (PERS ≥ ADAPT with CI > 0), the PHYTMO conclusion on PERS is reported as **not robust to tuning**.

## 11. Smoke test before the real run
- On the **first downloaded person only**: parse, extract features and fit one GEN on that person's repetitions.
- Print **only shapes, counts and timing**; no performance metric.
- No result file is written.

## 12. Outputs
- `results/summary_plan6.md`, `results/results_plan6.json` (per person × repeat × strategy × budget), `results/tuning_plan6.json`, `results/exclusions.txt`, `results/run_log.txt`.
- Then `RESULTS_PLAN6.md` with:
  - all expectations marked ✅/❌ exactly as defined;
  - negative or mixed results written as they are;
  - post hoc analyses labelled as such.

## 13. Limits declared now
- Healthy adults performing **instructed** variants. The label is the intended condition, not a rated quality.
- One session: calibration and evaluation come from the same set, close in time. "Own repetitions" cannot be separated from matching the session. Nothing here tests transfer across days or to patients.
- n = 19 / 18, so the intervals will be wide.
- The evaluation granularity is coarse (5 per variant).
- Fixed variant order (possible drift or fatigue confound).
- One linear model on hand-crafted orientation features.
- The closest prior study used the same data, so a new analysis of GAITEX is not a test on data unused by others.
- The person-level gains of the adapt-or-not rules are known only **after** evaluation. The rule's quality is measured, not assumed.
