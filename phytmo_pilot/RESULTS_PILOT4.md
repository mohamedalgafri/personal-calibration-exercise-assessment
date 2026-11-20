# Pilot 4 — confirmatory test on two unseen exercises (15 Nov 2026)

**Plan:** `PLAN4.md`. sha256 `5d1f22f7…c552`, recorded at 21:48 EET and posted in DEBATE.md before HAA/SQZ were downloaded. Neither assistant had seen these data before.
**Code:** `code/run_pilot4.py`. It reuses Pilot 3's loading, feature and model code. A smoke test on SQT, which was already-seen data, was run to check the code and is not part of the confirmation.
**Outputs:** `results/pilot4/summary_pilot4.md`, `results_pilot4.json`, `run_log.txt`.
**Data quality:**
- No files with missing values.
- HAA: 223 complete recordings, 28 persons with all four series.
- SQZ: 118 complete recordings, 28 persons.
- SQZ had 26 person×fold cases where the series-1 pool was shorter than the requested budget. All available windows were used, as the plan states.

## Results (balanced accuracy on series 2 of held-out persons; 5 folds × 2)
| | HAA (hip abduction) | SQZ (wrist squeeze) |
|---|---|---|
| GEN (no adaptation) | 0.906 | 0.804 |
| SRC control (same extra training, no personal data) | 0.905 | 0.806 |
| Budget 8: standard only (f=0) → mixed (f=0.5) | 0.928 → 0.933 | 0.821 → 0.862 |
| Budget 16: standard only → mixed | 0.934 → 0.944 | 0.822 → 0.880 |
| Best f (descriptive) | 0.5 | 0.5–0.75 |
| Simulated-session error, budget 16: GEN → f=0 → f=0.5 (points) | 8.9 → 5.9 → 4.5 | 17.8 → 15.9 → 10.4 |

## Pre-stated expectations
- **H1** (f=0.5 > f=0 in ≥ 8/10 folds at each budget, for both exercises):
  - **SQZ:** 8/10 and 8/10 in the original analysis. **But** at budget 16, 13 of 28 persons could not supply the full budget in f=0 or f=0.5. Restricted to persons with full budgets (15), it was **6/10** (8 improved, 5 worse, 2 tied; mean +5.3 points). This was ChatGPT's sensitivity check, declared before seeing its result, and Claude re-computed it with identical numbers. At budget 8: 27 persons, 8/10.
  - **HAA ✗:** 8/10 at budget 8 but only 7/10 at budget 16. The difference is small (+0.005 and +0.010).
  - **Corrected reading:** H1 was met in 3 of 4 cells in the original analysis and in 2 of 4 cells with full budgets. **The broad expectation is not confirmed.** Mixed examples improved the average, but not consistently, and some persons got worse.
- **H2 ✅** SRC − GEN = −0.001 (HAA) and +0.002 (SQZ). The gains come from the person's examples, not from extra training steps.
- **H3** (descriptive): adaptation with any personal examples beat SRC. Among the adapted models, standard-only (f=0) was the weakest in both exercises. Mixed budgets (f=0.25–0.75) were similar to each other.
- **Persons:** f=0.5 beat f=0 for 11–12 of 28 persons (HAA) and 15 of 28 (SQZ). The advantage is not universal and is concentrated in some persons.

## Combined honest reading (Pilots 3 + 4, PHYTMO)
- Adapting a general model with a few of the person's own examples improves assessment of new people. Known from the literature (Spilz et al., 2026; BayaHAR, 2026); replicated here on public data.
- At an equal budget, including deviation examples helped a lot for some exercises:
  - SQZ: large average gain, not consistent at budget 16 with full budgets;
  - SQT, ChatGPT's post-hoc matched-budget check.
- It helped little for others: HAA (not confirmed at budget 16).
- **Which exercises benefit, and why, is an open question for the master's.** Possibly it depends on how different the deviation is from the standard movement in the sensor signal.
- **Limits:** healthy volunteers performing deviations on purpose; labels per series; same-day recordings; overlapping 2-s windows; one simple model; 28 persons per exercise; folds re-use persons.
