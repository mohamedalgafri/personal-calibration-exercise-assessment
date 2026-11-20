# Camera smoke test: MediaPipe Pose vs motion-capture 2D joints (same camera, same frames)

- Video `PM_000` camera 18 (1080×1920), model **lite** (tasks-vision@0.10.14), frames 1304; mocap 2D frames 1304.
- Processing speed (seek + detect, CPU/WASM in the browser): **8.0 frames/s** (163 s).
- Frames inside labelled repetitions: 1086; with all 12 joints detected at visibility ≥ 0.5: **0.0%**.
- Best alignment: offset 6 frames, left/right as named (median error 0.170 vs offset 0 as named 0.170).
- Torso length (mocap, median): 291 px.
- Per-joint share of repetition frames with MediaPipe visibility ≥ 0.5: L shoulder 100%, R shoulder 100%, L elbow 100%, R elbow 0%, L wrist 100%, R wrist 0%, L hip 100%, R hip 100%, L knee 100%, R knee 0%, L ankle 100%, R ankle 100%.
- Errors below use ALL frames with a detected pose (no frame passed the visibility rule; descriptive only).
- **Median error / torso length: all 12 joints 0.170; arm joints 0.570** (frames used 1086).

| Joint | median error / torso | 90th percentile |
|---|---|---|
| L shoulder | 0.234 | 0.253 |
| R shoulder | 0.239 | 0.285 |
| L elbow | 0.764 | 0.890 |
| R elbow | 0.459 | 0.671 |
| L wrist | 1.587 | 1.694 |
| R wrist | 0.895 | 1.400 |
| L hip | 0.032 | 0.041 |
| R hip | 0.012 | 0.023 |
| L knee | 0.034 | 0.045 |
| R knee | 0.064 | 0.074 |
| L ankle | 0.166 | 0.170 |
| R ankle | 0.052 | 0.061 |

**Criteria (§6):** (a) detection ≥ 90%: ❌; (b) ≥ 5 fps: ✅; (c) arm error ≤ 0.15: ❌; (d) alignment determinable: ✅ (video 1304 frames = mocap 1304 frames).

**Verdict: NOT GO (see §6: rescope or NO-GO)**

Note: this is a sanity check of keypoint extraction on one video of one person, not a validation of the pose estimator. Mocap 2D joints are the dataset authors' projection of a skeleton fitted to markers, not ground truth for MediaPipe's own joint definitions, so part of the error is a definition offset.
