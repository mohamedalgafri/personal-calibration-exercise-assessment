# PLAN7 Stage A report: one Ex2 video (`PM_013`, person 2, camera 17), 16 Nov 2026

**Gate result: PASS. Stage B (the remaining 24 Ex1/Ex2 camera-17 videos) is allowed by PLAN7 §3.**

| Check (PLAN7 §4) | Result | Pass rule |
|---|---|---|
| Source vs re-encoded frames and timestamps (ffprobe) | 1,455 = 1,455 frames, timestamps i/30 | equal, CFR | ✅ |
| Presented-frame check | 99.86% of frames presented at their own index (2 frames near the end had no presented time recorded); 0 duplicates | ≥ 99%, no duplicates | ✅ |
| In-repetition frames with a pose / with all 12 joints at visibility ≥ 0.5 | 100% / 100% | ≥ 90%; rerun trigger < 50% | ✅ (no rerun) |
| Wrist-height cross-correlation, MediaPipe vs mocap 2D | best lag **0** frames (r = 0.999) | lag within ±2 | ✅ |
| Speed | 5.4 frames/s | — | — |

The mocap file has 1,456 frames and the video 1,455. Frames are aligned by index from 0, and the lag 0 above supports this.

**Deviations and fixes during Stage A (reported, none changes a criterion):**
1. **The local server did not support HTTP Range requests.** The first extraction attempt stalled with the video stuck seeking (readyState 1) and produced **no output file**.
   - The server (`code/serve.py`) now supports Range requests (206 responses, tested).
   - The extractor now waits until a frame is decoded and logs any frame that is not ready (`not_ready_frames`; here 0).
   - The run after the fix is counted as attempt 1, the first completed extraction.
   - **Probable but unproven:** the same server limitation may explain the smoke test's camera-17 run that returned 0 detections. That run used the same kind of server on an 88 MB file.
2. **A bug in the presented-frame check.** Browsers report the frame's media time rounded to 6 decimals (for example 0.133333 s), so `floor(30·t)` returned 3 instead of 4 for every third frame (66.6% "match", 484 "duplicates"). The index is now `round(30·t)`, which gives 99.86% and 0 duplicates. The pass rule (≥ 99%, no duplicates) was not changed.
3. **Viewed:** no video frame was viewed in Stage A. No correctness label was used.

**Files:**
- `results/PM_013_attempt1.json` (keypoints, presented times);
- `results/extraction_log.jsonl`;
- `code/check_extraction.py`, `code/extract.html`, `code/serve.py`.
