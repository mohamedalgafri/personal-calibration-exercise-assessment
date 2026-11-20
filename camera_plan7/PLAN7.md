# PLAN7: does the source of body keypoints (markerless video vs motion capture) change the personal-adaptation comparison? REHAB24-6, staged plan

**Written:** 16 Nov 2026, before downloading any Ex2 video or any further Ex1 video, and before any correctness label was used with keypoints. The fingerprint (sha256) goes in `results/PLAN7.sha256` and DEBATE before Stage A. A local hash is not an institutional registration.

**Already seen before this plan:**
- Ex1 `PM_000` (person 1), cameras 17 and 18: MediaPipe and mocap 2D keypoints, from the feasibility smoke test (`camera_feasibility/`). No label was combined with keypoints, and no classifier was trained.
- All labels and metadata in `Segmentation.csv`.

**ChatGPT's conditions included** (DEBATE, "نقد كاميرا17 وقرار PLAN7", and `Camera17_PLAN7_Decision_Review_AR_2026-11-16.md`):
- a genuine frame-alignment check;
- the view chosen from metadata only;
- one rerun, triggered by extraction quality only;
- a one-video gate before the batch;
- no pooling of Ex1 and Ex2 into 16 independent persons;
- the limit of the simple model stated;
- the closest video prior addressed.

## 1. Question (one)
On the same REHAB24-6 persons, repetitions, labels and camera view, with **identical** features, model, split and budgets: does the comparison GEN vs ADAPT vs PERS vs controls change when the 2D keypoints come from **MediaPipe Pose (markerless, ordinary RGB video)**? The alternative source is the **motion-capture skeleton projected into the same camera** (provided by the dataset).

**What it isolates:** the keypoint source, through the whole extraction pipeline (detector, joint definitions, missing frames). It does **not** isolate the sensor alone, and it says **nothing** about home conditions, phones, clothing or lighting outside this laboratory. Participants wear motion-capture suits.

The task is binary correctness per repetition. "Incorrect" means a mistake suggested by the physiotherapist, which **differs between persons**.

## 2. Data, view and download
**Exercises:**
- **Ex1** (arm abduction, right arm) and **Ex2** (arm V–W).
- Each is analysed and reported **separately**. Most persons appear in both, so they are **not** 16 independent persons.
- Ex3–Ex6 are excluded (too few repetitions, or mixed sides).

**View rule (from metadata only, fixed now):**
- Use the camera to which the person faces **front or half-profile in every repetition** of the recording. In Ex1 and Ex2, `cam17_orientation` is front or half-profile for every repetition and never profile. So the rule selects **camera 17 for all Ex1/Ex2 recordings**.
- Orientation changes between front and half-profile within some recordings. This is accepted and reported; no recording is split.
- Camera 18 would show a side view for the front repetitions; the smoke test showed that a side view can hide the moving arm.
- **Both sources use camera 17:** the mocap 2D file `*-c17-30fps.npy` and the MediaPipe output from `*-Camera17-30fps.mp4`.
- The choice does not depend on classification results, adaptation gains or mocap error.

**Download:**
- 25 camera-17 videos (Ex1: 13, Ex2: 12) plus their c17 2D-joint files, about **600 MB** in total.
- Range requests per member, resumable (`camera_feasibility/tools/fetch_member.py`), with sizes checked against the zip index.

**Eligibility (labels only, fixed now):**
- A person is eligible for an exercise if, after removing `mocap_erroneous = 1` repetitions and the extraction exclusions of §4, they have at least **k + 5 repetitions per class** (k = 4 for B = 8; k = 2 for B = 4).
- Repetitions are ordered in time by video_id, then repetition_number.
- Expected before extraction: Ex1 8, Ex2 8. The final counts are reported.

## 3. Stage A gate (one Ex2 video, before the batch)
**Video:** Ex2 `PM_013` (person 2; 4 repetitions; 13.5 MB), the smallest Ex2 file. It is chosen by size only.

**Steps:** download, re-encode, extract, then the alignment and quality checks of §4.

**Proceed to Stage B (all other videos) only if:**
- in-repetition detection (all 12 joints, visibility ≥ 0.5) ≥ 90%;
- the displayed-frame check passes (§4.2);
- the motion cross-correlation lag is within ±2 frames (§4.3).

**If it fails,** stop and report. The camera arm then stays a candidate that needs a proven fix, not a promise.

## 4. Extraction, alignment and quality (identical for every video)
1. **Re-encoding** with ffmpeg so that every frame is a keyframe, at the same resolution, CFR 30 fps.
   - Check with ffprobe that the source and the re-encoded file have the **same number of frames** and timestamps i/30.
   - Log both.
2. **Displayed-frame check:** the extractor records, for every frame i, the media time of the frame actually presented (`requestVideoFrameCallback` metadata, or `currentTime` after `seeked` if that is unavailable).
   - **Pass:** round(30 × time) = i for at least 99% of frames, and no frame is used twice.
3. **Independent temporal alignment:**
   - For each video, cross-correlate the vertical trajectory of the wrists (Ex1: right wrist; Ex2: the mean of both wrists) between MediaPipe and mocap 2D, over lags −15..+15 frames, inside the repetitions.
   - **Pass:** the lag of maximum correlation is within ±2 frames. The analysis then uses **lag 0** (not tuned).
   - **Fail:** the video is excluded from the primary analysis and reported.
   - The ±6 offset search of the smoke test was diagnostic only.
4. **Detection and one rerun:**
   - **Trigger (quality only):** frames with a detected pose make up less than 50% of the in-repetition frames.
   - **One rerun** with the same settings, after reloading the page (a fresh session).
   - **Both outputs are kept.** The rerun is used **only** if the trigger fired. If the rerun also triggers, the video is excluded.
   - **Reported:** the first-attempt success rate, the recovery rate and the coverage per person.
   - The cause of the smoke test's 0-detection run is unknown, so it is **not** called a proven glitch.
5. **Missing keypoints:**
   - A frame's joint is missing if there is no pose or its visibility is < 0.5 (MediaPipe), or its value is non-finite (mocap). Missing values are filled by linear interpolation inside the repetition.
   - A repetition is excluded **from both sources** if more than 20% of its frames have any missing joint in either source, or if `mocap_erroneous = 1`.
6. **Model:** MediaPipe Pose Landmarker **lite**, tasks-vision 0.10.14, CPU/WASM, `numPoses` = 1, default thresholds. These are the smoke-test settings, unchanged.

## 5. Features and models (identical for both sources)
**Joints:** 12 common joints (shoulders, elbows, wrists, hips, knees, ankles). MediaPipe indices 11–16 and 23–28 are mapped to the REHAB24-6 skeleton indices 7, 12, 8, 13, 9, 14, 16, 21, 17, 22, 18 and 23.

**Normalisation (per frame):** origin at the mid-hip; scale by the median torso length (mid-shoulder to mid-hip) within the repetition.

**Channels:** 24 coordinates plus 8 2D joint angles (elbows, shoulders, knees, hips), so 32 channels. The same 6 statistics as PHYTMO and GAITEX give **192 features per repetition**. No time, index or duration feature.

**Split:**
- For each person p (sorted), the donor q is the next person in sorted order.
- GEN is trained on all repetitions of the **other n − 2 persons**, so neither p nor q is in GEN.
- Calibration: the first k repetitions of each class of p. Evaluation: the last 5 of each class of p.

**Strategies (fixed PLAN5 settings, class-balanced):**
- GEN; ADAPT; PERS (with source scaling); CTRL (replay; seed 8000 + person index); CTRL-NEW (the donor's first k per class).
- **Budgets:** B = 4 (k = 2) and **B = 8 (k = 4; primary)**.
- **Gate G1:** adapt if GEN misclassifies at least one calibration repetition.
- **Run:** a single deterministic run. Statistics: balanced accuracy in points; bootstrap over persons (2,000, seed 0); average ranks for any Spearman.

## 6. Pre-stated expectations (descriptive; n ≈ 8 per exercise, so the intervals will be wide)
- **C1:** GEN_video − GEN_mocap ≤ 0 on average (markerless keypoints are not better than mocap for the general model). Descriptive.
- **C2:** ADAPT8 − GEN > 0 for the mocap source. Sign and interval reported.
- **C3 (main):** in each exercise, ADAPT8 − GEN has the **same sign** for both sources, and the per-person source difference D = (ADAPT8 − GEN)_video − (ADAPT8 − GEN)_mocap has |mean| ≤ 5 points.
  - **Verdict:**
    - "the comparison **carried over** to markerless video": C3 holds in 2/2 exercises;
    - "partly": 1/2;
    - "did not carry over": 0/2.
  - **No equivalence claim**, because n is far too small.
- **H5 (pre-specified here, on data fixed before results):** G1 harms fewer persons than ALWAYS (harm = more than 0.5 points below GEN). If ALWAYS harms nobody in a source × exercise, H5 is **untestable** there and is reported as such.
- **Also reported:**
  - counts of persons improved, worse and tied;
  - ADAPT8 − CTRL-NEW8 and PERS8 − ADAPT8;
  - the B = 4 results;
  - the exclusions per step.

## 7. Limits and what is not claimed
- **Laboratory, marker suits, RGB cameras, healthy adults, a single session, instructed mistakes chosen per person, n ≈ 8.**
- **The simple model's limit:** a logistic regression on summary features. Improvement after adaptation does **not** show that a stronger general model (for example a temporal network or a modern pose-sequence model) would not reach the same accuracy without calibration. Testing a stronger competitor is proposed for the master's and is **not** part of PLAN7.
- **The closest video prior:** Jánošová, Budikova & Sedmidubsky (SISAP 2024; same group as REHAB24-6). They use MediaPipe Pose on monocular video with similarity models **personalised** to the patient. Only fragments of the abstract were read, because the full text is behind Springer's login; whether they used REHAB24-6 is not verified. PLAN7 does not propose a new pose estimator or a new personalised model. It asks whether the **source of keypoints** changes a controlled general/adapted/personal comparison. No claim of novelty or superiority.
- **Not claimed:** phone or home use, clinical use, cross-day transfer.

## 8. Outputs
- `results/stageA_report.md`;
- `results/extraction_log.json` (per video: attempts, detection, displayed-frame check, lag, used run);
- `results/exclusions.txt`;
- `results/results_plan7.json`;
- `results/summary_plan7.md`;
- then `RESULTS_PLAN7.md` (expectations marked exactly as defined; post hoc analyses labelled as such).

## 9. Cost
- **Download:** about 600 MB, about 3–5 h at 15–70 KB/s.
- **Re-encoding:** about 20 min.
- **Extraction:** about 6 frames/s × about 60,000 frames, about 3 h. The browser pane must stay available.
- **Analysis:** minutes.

---
## Addendum A (16 Nov 2026, 21:50): code fixes before any PLAN7 analysis
**Timing:** written after an independent code audit (`review_2026-11-16_v19/C1_plan7_code_audit.md`) and **before** `run_plan7.py` was run on any data. At this point only Stage A's extraction checks had been run. No correctness label had yet been combined with keypoints, and no classifier had been trained.

**Changes:**
1. **Angles are unsigned:** `arctan2(|cross|, dot)` ∈ [0, π]. The signed version flipped between +179° and −179° for straight joints. On Stage A `PM_013`, repetition 1, the hip and knee angle SD was 65–176° in video and 1–176° in mocap; it becomes 1–3° unsigned. This would have biased the source comparison (C1, D, C3).
2. **`check_extraction.py` Ex1 bug fixed:** a missing pose crashed the Ex1 wrist trajectory because of the if/else grouping. Also, non-finite mocap or video samples are now masked in the cross-correlation.
3. **C3 sign rule made explicit:**
   - The mean ADAPT8 − GEN per source is classified as **positive (> +0.5), negative (< −0.5) or null**.
   - C3 holds only if both sources fall in the **same non-null** category and |mean D| ≤ 5.
   - If both are null, C3 is "not applicable (no adaptation effect in either source)" and does **not** count as "carried over".
4. **Video frames** whose presented frame index is unknown or different from i are set to missing, so they go through the interpolation and > 20% rule, which is applied to both sources.
5. **The presented-frame pass rule** (≥ 99%) is evaluated on the unrounded value.
6. **B = 4 is analysed on the same persons as B = 8** (the B = 8-eligible persons), to keep the budgets paired. The separate k = 2 eligibility mentioned in §2 is not used.
7. **The CTRL replay seed** is 8000 + the person's index in the sorted eligible list, as §5 states. The code had used the person id.
8. **The summary also reports:** H5 marked "untestable" where ALWAYS harms nobody; extraction first-attempt success and recovery rates; persons at ceiling (GEN = 1.0).
9. **`serve.py`** no longer overwrites an existing results file; it appends a timestamp.

**Unchanged:** the question, data, view rule, budgets, features (other than the angle formula), models, thresholds and expectations.

---
## Addendum B (17 Nov 2026, before any run_plan7.py analysis): calibration and evaluation balanced by viewing angle
**Timing:** written after the methods review (`review_2026-11-17_foundation/R3_methods_statistics.md`). Claude checked it from `Segmentation.csv`.

**Problem:** within a recording, the person faces camera 17 first in one orientation (mostly front) and later in another (half-profile). With "first k per class for calibration, last 5 per class for evaluation", **every eligible person in Ex1 and Ex2 (8/8 each) had calibration and evaluation drawn from different orientations**. This confounds the keypoint-source comparison, because markerless pose is view-sensitive.

**No PLAN7 analysis had been run;** only Stage A extraction checks.

**Change (replaces the split in §5):**
- For each person, class and orientation group (front; half-profile), repetitions are ordered in time.
- **B = 8 (primary):** calibration = the first **2** repetitions of each class **in each orientation group** the person has in that exercise; evaluation = the last **3** of each class in each orientation group.
- **B = 4:** the first 1 per class per orientation; the same evaluation set.
- If a person has only one orientation group in an exercise: calibration = the first 4 per class (B = 8) or the first 2 (B = 4), and evaluation = the last 5 per class (the original rule).
- **Eligibility:** at least 5 repetitions of each class in every orientation group the person has (and at least 9 per class if only one group).
- **Expected from labels** (before extraction exclusions): Ex1 6 persons, Ex2 7 persons.
- The donor's calibration uses the same rule.

**Reporting:** the change is reported as a deviation. The intervals become wider; the results stay descriptive.

**Unchanged:** question, view rule (camera 17), features (with Addendum A), models, expectations, thresholds.

---
## Addendum C (17 Nov 2026, 13:01, before any run_plan7.py analysis): frame-exact extraction from numbered images
**Timing:** no PLAN7 analysis has been run, and no correctness label has been combined with keypoints.

**Observation:** extraction was parallelised in several browser tabs to save time. The presented-frame check (§4.2) then failed for 3 of the first 4 videos:
- PM_000: 37.9% of frames had an unknown presented time, and 50 were presented at a different index;
- PM_001: 7.3% unknown, 9 at a different index;
- PM_002: 24.9% unknown, 4 at a different index.

The cause is that `requestVideoFrameCallback` only fires in a tab that is being rendered. Background or hidden tabs do not render, so the frame actually analysed cannot be confirmed. The wrist cross-correlation still gave lag 0 (r ≥ 0.998) for all of them, but frame-level identity is not guaranteed.

**Change (replaces the video-seeking extraction of §4.2–4.4 for all videos, including Stage A's PM_013):**
1. Every frame of the re-encoded video is decoded by ffmpeg into numbered JPEG files: `data/frames/<id>/%06d.jpg`, quality 2, same resolution.
2. **Check:** the number of image files must equal the ffprobe frame count of the source video.
3. MediaPipe Pose Landmarker lite (tasks-vision 0.10.14, VIDEO mode, the same settings) processes image i with timestamp i·1000/30 ms. **The frame index is the file index by construction**, so the presented-frame check is replaced by the file-count check.
4. **Unchanged:** the wrist cross-correlation lag check (pass if within ±2), the detection rule (rerun trigger below 50%; one rerun after a fresh page session, keeping both outputs), and all other rules, features, models and expectations.
5. **Equivalence check before the batch:** PM_013 is extracted with the new method and compared with its passing Stage A extraction (median keypoint difference / torso length). Expected to be small; any difference is reported.

**Earlier extractions** (`*_attempt1.json` from video seeking) are kept but not used. Attempts of the new method are named `jpg1` and `jpg2`.

---
## Addendum D (17 Nov 2026, 17:20): primary analysis infeasible by the quality rules; pre-outcome front-view sensitivity analysis
**What happened:** `run_plan7.py` ran with Addenda A–C. The pre-specified rule excludes a repetition if any of the 12 joints is missing (visibility < 0.5) in more than 20% of its frames, from both sources. It excluded 103 repetitions.

- **Front-view repetitions:** 0 of 197 had a joint missing in more than 20% of frames.
- **Half-profile repetitions:** the far (left) elbow and wrist were missing in more than 20% of frames in 54% and 38% of 189 repetitions.

With the view-balanced split of Addendum B, **eligible persons fell to 0 (Ex1) and 3 (Ex2)**.

**Primary result, as pre-specified:** the keypoint-source comparison is **not feasible** under the plan's quality rules. A single half-profile laboratory camera loses the far arm too often. This is reported as a feasibility finding (camera placement or multiple views are needed). The n = 3 output for Ex2 is reported only for completeness.

**Sensitivity analysis.** It was decided at this point, after seeing exclusion counts and **before viewing any performance result**, so it is post hoc with respect to the plan and pre-outcome. **Front-view repetitions only:**
- calibration: the first 2 of each class (B = 4);
- evaluation: the last 3 of each class;
- eligibility: at least 5 per class in front view. From labels: Ex1 8 persons, Ex2 7;
- everything else unchanged (features, models, donor rule, statistics, C1–C3 and H5 definitions, applied at B = 4).

It is **descriptive**. Six evaluation repetitions per person give very coarse balanced accuracy (steps of about 17 points). It is reported separately from the primary result and cannot change it.
