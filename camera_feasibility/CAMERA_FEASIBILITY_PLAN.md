# Camera feasibility plan (REHAB24-6): limited check before any camera experiment, 16 Nov 2026

**Status:**
- This is the plan for a **feasibility check**, not the camera experiment.
- It is fingerprinted (sha256) before the smoke test below is run.
- A later experiment plan (PLAN7) will be written only if the decision rule in §6 says GO.
- The large video download happens only after GO and after PLAN7 is frozen.

**Already read before this plan (no video or motion values):**
- the Zenodo description and `Segmentation.csv` (labels, person IDs, frame ranges, flags);
- the zip indexes of `videos.zip`, `2d_joints.zip` and `3d_joints.zip` (file names and sizes only);
- ChatGPT's label-count check (`shared_dialogue/CODEX_V18_Camera_Budget_Metadata_Check_2026-11-16.json`), which Claude reproduced.

## 1. The single question the eventual experiment would answer
On the **same REHAB24-6 persons, repetitions and correctness labels**, with an **identical feature and model pipeline**, does the result of personal adaptation change when the 2D body keypoints come from **markerless pose estimation on ordinary video** (MediaPipe Pose)? The comparison is with keypoints from **motion capture projected into the same camera** (provided by the dataset).

The result means ADAPT − GEN, and ADAPT vs the unseen-donor control and vs the personal classifier.

**What this design isolates, and what it does not:**
- Both arms use the same camera view, the same joints (a common 12-joint subset: shoulders, elbows, wrists, hips, knees, ankles), the same frames, features, model, split and labels. The only thing that differs is **where the keypoints come from**.
- It does **not** test home conditions or phones. The participants wear motion-capture suits with markers, in a laboratory, filmed by fixed RGB cameras.
- Any difference concerns this markerless pipeline on these videos.
- PLAN6 / OptiTrack results are **not** evidence that markerless pose works.

## 2. Persons, exercises and budget (from labels only; PLAN6's budget is **not** copied)
Task: binary correctness per repetition. Calibration uses the **first k repetitions of each class** in time order; evaluation uses the **last 5 of each class**. Eligible means at least k + 5 repetitions per class (`mocap_erroneous = 1` repetitions removed first).

| Exercise | Persons | Eligible k = 2 (B = 4) | Eligible k = 4 (B = 8) | Eligible k = 8 (B = 16) | Note |
|---|---|---|---|---|---|
| Ex1 arm abduction (right arm) | 9 | 8 | **8** | 0 | one side only |
| Ex2 arm V–W | 9 | 8 | **8** | 0 | no side issue |
| Ex3 push-ups | 9 | 0 | 0 | 0 | too few repetitions |
| Ex4 leg abduction | 9 | 8 | 8 | 1 | left/right legs mixed |
| Ex5 lunge | 8 | 7 | 7 | 0 | left/right front leg mixed |
| Ex6 | 9 | 4 | 4 | 0 | too few |

**Candidate scope:**
- **Ex1 and Ex2, budgets B = 4 and 8, about 8 persons each.** Ex4 is secondary, only if side can be handled by a rule fixed in advance.
- B = 16 is **not feasible** with 5 test repetitions per class.
- With n ≈ 8 per exercise, the general model is trained on about 7 persons (leave-one-person-out). The intervals will be wide, so the experiment is **descriptive and feasibility-level**, not confirmatory.

**Other notes:**
- Correct and incorrect repetitions are partly interleaved within videos (e.g. 1111101111110000), unlike GAITEX's fixed blocks. No time or order features will be used.
- The mistakes were chosen by the physiotherapist **per person**, so "incorrect" means different errors for different persons.

## 3. Camera choice (rule fixed now, from label flags only)
- **Camera 18** is preferred. Extra persons are noticeably visible (flag ≥ 2) in 8 repetitions in camera 18, against 269 in camera 17.
- Only **one camera** is used, so the two cameras of the same repetition never end up on different sides of a split.
- Camera 17 is used only if the smoke test shows framing or cropping failures in camera 18 for the needed joints.

## 4. Smoke test now (small download; not an experiment)
**Download (about 10 MB):**
- one Ex1 camera-18 video, `Ex1/PM_000-Camera18-30fps-transposed.mp4`, 9.2 MB, person 1, five correct repetitions;
- its `Ex1/PM_000-c18-30fps.npy` 2D joints, 0.5 MB;
- `joints_names.txt` (already downloaded).

**Tool:**
- MediaPipe Tasks Vision Pose Landmarker (JavaScript/WASM, pinned version from jsdelivr; model from Google's public model storage), run **in the built-in browser** on frames sampled at the video's frame times.
- The landmarks are saved to JSON through a small local server.
- The Python route is not available here (Python 3.14, no pip).

**Measured:**
1. **Processing speed**, in frames per second on this machine.
2. **Detection rate**: the share of frames inside the labelled repetitions where all 12 joints are returned with visibility ≥ 0.5.
3. **Agreement with the mocap 2D joints** on the 12 common joints, after the frame alignment is established. Measure: the median distance divided by the median shoulder-to-hip (torso) length. This is a sanity check, not a validation study.
4. **Frame alignment**: whether the video frame count matches the npy frame count, or a fixed offset is needed.

**What is seen:** the keypoints of person 1 in one Ex1 video. No correctness label is used and no classifier is trained. Person 1 stays eligible for the later experiment, because the smoke test only checks keypoint extraction. This is declared.

## 5. Cost estimates (to be updated with the measured speed)
**Downloads after GO:**
- camera-18 videos: Ex1 237 MB + Ex2 309 MB ≈ **546 MB**, about 2–4 h at 40–70 KB/s;
- matching 2D-joint files (30 fps): about 12 MB.
- Range requests per member, checked against the zip CRC.

**Extraction:** about 60,000 frames for Ex1 + Ex2 on one camera (estimate). At s frames per second, that takes 60,000 / s seconds (for example, 5 fps ≈ 3.3 h; 20 fps ≈ 50 min).

**Analysis:** minutes (linear model, about 8 persons).

## 6. GO / NO-GO rule (fixed now)
**GO** to writing PLAN7 if **all** of the following hold on the smoke video:
- (a) detection rate ≥ 90%;
- (b) speed ≥ 5 frames/s;
- (c) median normalised error for the arm joints (shoulders, elbows, wrists) ≤ 0.15 torso lengths;
- (d) frame alignment is determinable (equal counts or a constant offset).

**Otherwise:**
- **RESCOPE:** try camera 17 or the "full" model once, documented as a deviation.
- Or **NO-GO**: the camera arm stays a planned master's component, described positively (planned work with public video data). The reason is stated.

## 7. What the eventual experiment cannot claim
It cannot claim:
- phone use at home;
- clinical use;
- transfer across days (single session);
- superiority over the closest video prior.

Jánošová, Budikova & Sedmidubsky (SISAP 2024) come from the same group as REHAB24-6. Their paper must be **read** before any statement about what this adds.
