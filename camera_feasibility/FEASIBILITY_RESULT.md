# Camera feasibility result (REHAB24-6 smoke test), 16 Nov 2026

**Plan:** `CAMERA_FEASIBILITY_PLAN.md`, sha256 `f6d04baa…457f`, frozen 18:10 before any video or motion values were downloaded.

**Verdict by the plan's rule (§6): GO, on camera 17, after the one rescope the plan allows.** This permits writing an experiment plan (PLAN7). It is **not** a validation of the pose estimator: it covers one video of one person.

## What was done
- **Downloaded** (each member size-checked against the zip index): Ex1 video `PM_000` from camera 18 (9.2 MB) and camera 17 (11.1 MB), with their 30-fps mocap 2D-joint files.
- **Pose extraction:** MediaPipe Tasks Vision Pose Landmarker **lite**, version 0.10.14, JavaScript/WASM on the CPU in the built-in browser, run on every frame. Tools: `tools/pose_extract.html`, `tools/serve.py`; comparison `tools/compare_smoke.py`.
- **No correctness label was used and no classifier was trained.**

## Results
| | Camera 18 (planned first choice) | Camera 17 (rescope, §6) |
|---|---|---|
| View of this person | side (the moving right arm on the far side) | front |
| Speed | 8.0 frames/s | 5.9 frames/s |
| (a) Frames in repetitions with all 12 joints at visibility ≥ 0.5 | **0%** (right elbow, right wrist and right knee never visible) | **100%** |
| (c) Median error of the arm joints / torso length (vs mocap 2D, same camera) | 0.57 (descriptive, all frames) | **0.085** |
| All 12 joints | 0.17 | 0.091 |
| (d) Frame alignment | 1,304 = 1,304 frames | 1,304 = 1,304 frames (best offset 1 frame) |
| Verdict | NOT GO | **GO** |

Per-joint tables: `results/SMOKE_RESULT_cam18.md` and `results/SMOKE_RESULT_cam17.md`. In camera 17 the moving right wrist has the largest arm error (median 0.128, 90th percentile 0.196); the hips are about 0.14, partly a difference in how the joints are defined.

## Deviations and problems (reported as they happened)
1. **Video re-encoding.** Seeking frame by frame in the original H.264 files ran at about 2 frames/s. The videos were therefore re-encoded locally with ffmpeg, with every frame a keyframe (same resolution and the same 1,304 frames; about 25 s per video). This step becomes part of the pipeline and of its cost.
2. **Camera 18 failed for this exercise and person** because of the viewing angle. The plan's rule chose camera 18 from extra-person flags only. **Lesson for PLAN7:** choose the camera per recording by the person's **orientation** (`cam17_orientation` in the labels: front, half-profile or profile), so that the moving limb faces the camera. The extra-person flags come second.
3. **The first camera-17 extraction returned no pose in any frame.** It was diagnosed before rerunning:
   - the decoded frames are normal (mean brightness 58);
   - single-frame detection in image mode found the person, with arm visibility 0.86–1.00;
   - a fresh video-mode test on frames 300–329 found the person in 30 of 30.

   The full extraction was rerun unchanged and found the person in 1,304 of 1,304 frames. **The cause of the failed first run is unknown** (it may be a transient state in the browser pane). Both outputs are kept (`results/smoke_pose_lite_cam17.json` = failed run; `..._run2.json` = the run used). **PLAN7 must log detections per video and allow one automatic rerun of a video with less than 50% detection, reporting it.**
4. **One video frame was viewed** during diagnosis, to check that the frames were not black. The person's identity is irrelevant and is not described.
5. **Single person, single video, lights-off recording.** The extra-person flag for camera 17 was 3 in this video, yet only the target person was tracked (low error). This may not hold elsewhere.

## Costs for PLAN7 (updated with measured speed)
- **Extraction:** about 6 frames/s (camera 17, landscape) to 8 frames/s (camera 18, portrait).
  - Ex1 + Ex2 on one camera per recording is about 60,000 frames, roughly **2.5–3 h** of extraction.
  - Plus re-encoding (about 50 frames/s, roughly 20 min).
- **Downloads:** Ex1 + Ex2 videos are about 500–650 MB, depending on the per-recording camera choice, plus about 25 MB of 2D-joint files. That is **3–5 h** at the current 15–70 KB/s, with a resumable per-member download (`tools/fetch_member.py`).
- **Analysis:** minutes.

## What this shows and what it does not
- **Shows:**
  - markerless 2D keypoints can be extracted on this machine at a usable speed;
  - with a front view, they track this person's arm close to the mocap projection;
  - a side view can hide the moving limb.
- **Does not show:**
  - accuracy for other persons, exercises or lighting;
  - anything about classification;
  - home or phone use.

  The participants wear motion-capture suits in a laboratory.
