# PLAN5: general vs adapted vs personal model, for new people, in two measurement modalities

Written 16 Nov 2026, **before** downloading any optical data or EAH data.

## Question (adopted by Mohamed, 16 Nov)
When only a very small, balanced set of labelled examples can be collected from a new person, which is better for assessing exercise execution (standard vs deviation):
- the **general** model (GEN);
- the general model **adapted** with the person's examples (ADAPT);
- a **personal** model trained only on those examples (PERS)?

Does the answer depend on the exercise and on the measurement modality: body-worn **IMU** versus marker-based optical motion capture (**OPT**, OptiTrack, in the same PHYTMO recordings)?

OPT is laboratory motion capture with markers. It is **not** a phone camera, and no claim about phone or RGB cameras will be made.

## Data (PHYTMO, CC BY 4.0; healthy volunteers; deviations performed on purpose; labels per series)
- **Exercises:**
  - SQT, HAA and SQZ. Their IMU data were already analysed in Pilots 3/4, and the audit also computed PERS-16 on IMU. **IMU results for these three are therefore not confirmatory.** Their OPT data are unseen.
  - **EAH** (extension of arms over head): **both modalities unseen.** This is the cleanest confirmatory exercise.
- **IMU:** the same files and features as Pilots 3/4 (accelerometer and gyroscope plus magnitudes; 6 statistics per channel).
  - Unilateral exercises (HAA) use the two IMUs of the moving leg.
- **OPT:** `optical interp/rigid_bodies` files.
  - Per rigid body, the channels are:
    - position, centred by the recording median;
    - velocity (first difference × 100 Hz) and speed;
    - orientation quaternion, sign-normalised so that w ≥ 0;
    - angular speed, from consecutive quaternions.
  - Markers are ignored.
  - HAA uses the two rigid bodies of the moving leg ("shin/thigh" = right, "shin2/thigh2" = left, per the paper). Bilateral exercises use all four.
- **Same pre-processing for both modalities:**
  - drop a recording with any non-finite value;
  - trim the first 25% and last 5%;
  - 2-s windows with a 1-s step;
  - per-window mean, SD, min, max, range and mean absolute first difference of each channel.

## Design
- **Outer split:** person-grouped 5 folds × 2 repeats (seeds 3000/3001).
- **Persons included:** for each exercise, persons with all four series in **both** modalities and ≥ 8 windows of each class in series 1 in both modalities. The same persons are used for every budget and modality, and their number is reported.
- **Calibration examples (from series 1 only):** B ∈ {4, 8, 16}, always balanced (B/2 standard + B/2 deviation). They are the first windows in time of each class.
  - For HAA they alternate between the left-leg and right-leg recordings: half from each, fixing the leg imbalance found by the audit.
- **Evaluation:** all windows of series 2 (fixed for every condition).
- **Strategies** (same logistic regression as before; no tuning):
  - **GEN:** trained on the other persons (series 1 and 2).
  - **CTRL** (non-personal matched control, addressing ChatGPT's point on weighting): GEN fine-tuned exactly like ADAPT, with the same counts, class composition, weight (×20) and 60 steps. Its "calibration" windows are B random windows of the right classes from **other training persons**, plus the same 1,500 source windows.
  - **ADAPT:** GEN fine-tuned on 1,500 source windows (weight 1) plus the person's B windows (weight 20), 60 Adam steps.
  - **PERS:** logistic regression trained only on the person's B windows. It uses the source scaler, because B is too small to fit a scaler.

## Analysis (person = unit)
- For each person, average balanced accuracy (BA) on series 2 over the 2 repeats.
- Paired differences with a **bootstrap 95% CI over persons** (10,000 resamples), reported with mean, median and improved/worse/tied counts (tie = |diff| < 0.5 BA points).
- **Minimal meaningful effect:** 2 BA points.
- **Primary contrasts at each B, per exercise × modality:**
  - ADAPT − GEN;
  - ADAPT − CTRL;
  - PERS − ADAPT.
- **Crossover:** the smallest B at which PERS − ADAPT has a CI lower bound > 0. If there is none, "no crossover up to 16".

## Pre-stated expectations (may be rejected)
- **E1:** at B = 16, ADAPT − GEN ≥ 2 points with CI lower bound > 0 in at least 3 of 4 exercises, in each modality.
- **E2:** at B = 16, ADAPT − CTRL > 0 (CI lower bound > 0) in at least 3 of 4 exercises, in each modality. This means the gain comes from the person's own examples, not from the weighting or the extra steps.
- **E3** (descriptive, 8 exercise × modality cells): the weaker GEN is in a cell, the more PERS − ADAPT at B = 16 favours PERS (Spearman ρ < 0). No significance claim; this is a mechanism hint to test in the master's.
- **E4:** EAH is reported in full whatever the outcome.
- **Decision rule:**
  - If E1 fails in a modality, adaptation is not supported there.
  - If E2 fails, we cannot claim that the person's examples carry the benefit.
  - If OPT and IMU disagree, that is reported as a modality effect, not hidden.

## Out of scope here
Simulated deviations; quantification and PSO; age analysis (planned separately, descriptive); phone or RGB cameras; fusion of modalities.

## Addendum A — 16 Nov 2026, after ChatGPT's PLAN5 review. Written BEFORE any PLAN5 run on OPT or EAH data
Status when written: the EAH IMU files and part of the OPT files are downloaded, but none has been opened or analysed. Only the smoke test was run, on IMU data of SQT and HAA, which had already been seen.

1. **New-data, non-personal control (CTRL-NEW).** CTRL replays windows the general model has already seen, whereas the person's windows are new to it. CTRL-NEW uses B balanced windows from series 1 of **another test person of the same fold** (q ≠ p). That person is not in GEN's training data. The windows are taken by the same first-in-time and leg policy, with the same weights and steps as ADAPT; q is the next test person in sorted order. **ADAPT − CTRL-NEW** separates the benefit of the person's own examples from the benefit of any new data. **E2b** (added): at B = 16, ADAPT − CTRL-NEW has a CI lower bound > 0 in at least 3 of 4 exercises, per modality. CTRL is kept as defined.
2. **Naming:** PERS is a "personal classifier with source-derived feature scaling", not fully independent of other people.
3. **"Crossover"** is renamed "**first tested budget (of 4, 8, 16) with evidence that PERS beats ADAPT**". It is not a general minimum number of examples.
4. **Agreement between IMU and OPT** will not be interpreted as proof that movement, rather than noise, is the cause. The two modalities are not time-aligned in this pipeline.
5. **EAH** is an additional exercise from the same participants and laboratory, not independent validation on patients or at home.
6. Novelty remains unresolved. Prior personalisation work includes Spilz et al. 2026 (IMU), BayaHAR 2026 and **Jánošová, Budikova & Sedmidubsky, SISAP 2024 (LNCS), "Personalized Similarity Models for Evaluating Rehabilitation Exercises from Monocular Videos", doi:10.1007/978-3-031-75823-2_7** (camera-based; verified via Crossref).
