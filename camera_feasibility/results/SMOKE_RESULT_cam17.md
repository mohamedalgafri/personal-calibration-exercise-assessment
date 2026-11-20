# Camera smoke test: MediaPipe Pose vs motion-capture 2D joints (same camera, same frames)

- Video `PM_000` camera 17 (1920×1080), model **lite** (tasks-vision@0.10.14), frames 1304; mocap 2D frames 1304.
- Processing speed (seek + detect, CPU/WASM in the browser): **5.9 frames/s** (223 s).
- Frames inside labelled repetitions: 1086; with all 12 joints detected at visibility ≥ 0.5: **100.0%**.
- Best alignment: offset 1 frames, left/right as named (median error 0.091 vs offset 0 as named 0.091).
- Torso length (mocap, median): 210 px.
- Per-joint share of repetition frames with MediaPipe visibility ≥ 0.5: L shoulder 100%, R shoulder 100%, L elbow 100%, R elbow 100%, L wrist 100%, R wrist 100%, L hip 100%, R hip 100%, L knee 100%, R knee 100%, L ankle 100%, R ankle 100%.
- Errors below use frames passing the visibility rule.
- **Median error / torso length: all 12 joints 0.091; arm joints 0.085** (frames used 1086).

| Joint | median error / torso | 90th percentile |
|---|---|---|
| L shoulder | 0.042 | 0.126 |
| R shoulder | 0.084 | 0.108 |
| L elbow | 0.087 | 0.118 |
| R elbow | 0.092 | 0.176 |
| L wrist | 0.082 | 0.153 |
| R wrist | 0.128 | 0.196 |
| L hip | 0.140 | 0.155 |
| R hip | 0.141 | 0.161 |
| L knee | 0.040 | 0.052 |
| R knee | 0.046 | 0.055 |
| L ankle | 0.089 | 0.101 |
| R ankle | 0.108 | 0.157 |

**Criteria (§6):** (a) detection ≥ 90%: ✅; (b) ≥ 5 fps: ✅; (c) arm error ≤ 0.15: ✅; (d) alignment determinable: ✅ (video 1304 frames = mocap 1304 frames).

**Verdict: GO**

Note: this is a sanity check of keypoint extraction on one video of one person, not a validation of the pose estimator. Mocap 2D joints are the dataset authors' projection of a skeleton fitted to markers, not ground truth for MediaPipe's own joint definitions, so part of the error is a definition offset.
