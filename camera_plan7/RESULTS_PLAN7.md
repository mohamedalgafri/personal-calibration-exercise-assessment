# RESULTS — PLAN7: does the adaptation comparison carry over from motion capture to markerless video? (17 Nov 2026)

**Plan:** `PLAN7.md`, fingerprinted after the feasibility smoke test and before the main extraction. Addenda A–C were written before the analysis was run. Addendum D was written after the primary run and its exclusion counts. The primary run had already written its (n = 3) performance file, but **performance output was not inspected before Addendum D was hashed**. Hashes are in `results/PLAN7.sha256`. All analyses were AI-assisted.

**Data:** REHAB24-6, Ex1 and Ex2, camera 17.
- **Video keypoints:** MediaPipe Pose Landmarker lite, run in the browser on every decoded frame (Addendum C).
- **Comparison:** 2D motion capture projected to the same camera.

**Code:** `code/run_plan7.py` runs the primary analysis. `code/run_plan7.py --front` runs the Addendum D sensitivity analysis. The primary output was reproduced byte-identically after the `--front` option was added.

## 1. Extraction (keypoint quality)
- **25/25 videos** were extracted frame-exactly (`jpg1`). All 25 passed every pre-specified check:
  - timestamps;
  - image count equal to the raw frame count;
  - pose detected in 100% of repetition frames;
  - wrist lag against motion capture of −1 or 0 frames;
  - correlation of 0.969–0.9997.
- No re-run was triggered.
- Equivalence with the earlier frame-presentation method was checked on PM_013: median torso keypoint difference 0.0047 (`results/equivalence_PM013.txt`).

## 2. Primary result (as pre-specified): not feasible under the quality rules
The rule excludes a repetition if any of the 12 joints is missing (visibility < 0.5) in more than 20% of frames.

**By camera view:**
- **Front view:** 0 of 197 repetitions failed.
- **Half-profile view:** the far (left) elbow failed in 54% of 189 repetitions, and the far wrist in 38%.

The view-balanced split of Addendum B therefore left **0 eligible persons in Ex1 and 3 in Ex2**. The n = 3 output (`results/summary_plan7_primary.md`) is uninformative and is not interpreted.

**Feasibility finding:** a single half-profile laboratory camera with the lite pose model loses the far arm too often for this protocol. Front placement, multiple views or a stronger pose model are candidates to test, not demonstrated remedies. This is a methods result in its own right.

## 3. Sensitivity analysis: front-view repetitions only (Addendum D; post hoc, pre-outcome, descriptive)
**Design:**
- B = 4 (the first 2 of each class);
- evaluation on the last 3 of each class, so 6 repetitions per person;
- balanced accuracy therefore moves in steps of about 17 points;
- all other settings unchanged.

**Persons:** Ex1 n = 8, Ex2 n = 7 (`results/summary_plan7_front.md`).

| | GEN mean | ADAPT − GEN | ADAPT − CTRL-NEW (another person's examples) | better/worse/equal |
|---|---|---|---|---|
| Ex1 motion capture | 0.875 | +8.3 [−2.1, +18.8] | +14.6 [+0.0, +29.2] | 4/1/3 |
| Ex1 video | 0.750 | +14.6 [+4.2, +27.1] | +10.4 [+4.1, +18.8] | 4/0/4 |
| Ex2 motion capture | 0.619 | +21.4 [+7.1, +38.1] | +23.8 [+9.5, +38.1] | 4/0/3 |
| Ex2 video | 0.524 | +26.2 [+4.8, +45.2] | +11.9 [−11.9, +31.0] | 5/1/1 |

Bootstrap 95% CI over persons (2000 resamples, seed 0). Key means were recomputed independently from `results_plan7_front.json` and match.

**Pre-stated expectations, applied at B = 4.** The ticks are the plan's descriptive criteria on means. They are not established effects: both C1 intervals and the Ex1 motion-capture adaptation interval include 0.
- **C1 (video general model ≤ motion capture):** ✅ in both exercises (−12.5 and −9.5 points; the intervals include 0).
- **C2 (adaptation > general model on motion capture):** ✅ in both.
- **C3 (same direction, |video − motion-capture difference| ≤ 5 points):**
  - Ex2 ✅ (D = +4.8);
  - Ex1 ❌ only on the margin rule: both sources were positive, and D = +6.2 > 5.
  - The verdict rule therefore gives **"partly carried over" (1/2)**.
- **H5 (the G1 gate reduces harm):** untestable or not supported. Adaptation harmed at most 1 person per cell, and G1 did not prevent it.

## 4. Honest reading
- **In front view, the direction of the result carried over to markerless video (descriptively).** In all four cells, the mean after adaptation with 4 of the person's own examples was higher than the general model. Against 4 examples from another person, all four means also favoured adaptation, but only two intervals exclude 0 (Ex1 video and Ex2 motion capture).
- **The video general model was weaker** (C1). The gain after adaptation was correspondingly larger: in Ex2 video the general model was at chance level (0.52). This is **consistent with** the PLAN8 reading (larger gains where the general model is weaker), but these summaries do not demonstrate it. This is why the master's question is posed against a qualified stronger general model.
- **Limits:**
  - very few persons (7–8) and only 6 evaluation repetitions each;
  - laboratory video with participants in marker suits;
  - a single session;
  - labels requested by a physiotherapist;
  - a post hoc view restriction;
  - no equivalence claim.

  **This is not evidence for phones or home use.**

## 5. Deviations and exclusions
- **Addenda:**
  - A: angle computation and audit fixes;
  - B: view-balanced split;
  - C: frame-exact extraction;
  - D: front-view sensitivity analysis.
- **Exclusion files:**
  - `results/exclusions_primary.txt`: 103 repetitions with more than 20% missing keypoints; mocap-erroneous repetitions; ineligible persons;
  - `results/exclusions_front.txt`.
- The summary line "videos passing all checks: 26" counts one earlier passing attempt with the superseded method as well; the frame-exact attempts are 25/25.
- **Re-runs:** see RERUN_STATUS.md in the repository root.

## 6. External critique (Codex, read-only, 17 Nov; `../codex_reviews/codex_plan7_results.md`)
- **No bug** in split, eligibility, donor or calibration–evaluation leakage. Codex reconstructed n = 8/7 and found 4 calibration and 6 evaluation repetitions with zero overlap.
- **Corrections applied:**
  - chronology wording;
  - ticks described as descriptive;
  - donor comparison: 2 of 4 intervals exclude 0, not 3;
  - "tracks GEN weakness" rewritten as "consistent with";
  - remedies described as candidates;
  - front-mode exclusion message, which previously named Addendum B.
- The front summary was re-run after the message fix and is unchanged.
