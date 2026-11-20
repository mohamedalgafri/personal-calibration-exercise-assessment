# PLAN6 results: personal adaptation on GAITEX (inertial orientation), 16 Nov 2026

**Plan:** `PLAN6.md`, sha256 `3ead82b1…36e3`, frozen 12:05 EET before any sensor values were downloaded. It was posted in DEBATE.md.

**Code:** `code/run_plan6.py`; raw outputs `results/results_plan6.json` and `results/tuning_plan6.json`; summary `results/summary_plan6.md`; log `results/stdout_run.txt` (also restored into `results/run_log.txt`, see item 7). Training runtime was 2,325 s (≈ 39 min).

**Corrected 16 Nov (evening) after ChatGPT's audit** (`shared_dialogue/CODEX_PLAN6_RESULTS_CRITIQUE_AR_2026-11-16.md`): the Spearman values were corrected, the G1 units and wording were fixed, and three operational notes were added. The earlier text is kept as `results/RESULTS_PLAN6_v1_before_chatgpt_corrections.md`.

**Data:**
- 37 IMU files plus annotations, downloaded by range requests. **All 111 files match the archive's CRC-32** (`results/crc_check.txt`).
- The download was interrupted once by a network drop and resumed. The CRC check covers the resumed files.

## Deviations and operational notes (all reported; item 6 is a minor deviation from the written plan)
1. **The summary step crashed after all models had finished.** The T3 line looked up persons in tuning folds where they were not tested (KeyError).
   - Fixed by filtering to the person's own folds, in both `run_plan6.py` and the new `summarize_plan6.py`. The latter rebuilds the summary from the saved raw outputs with otherwise identical code.
   - No model was retrained, and no raw value changed.
2. **Exclusions, by the pre-specified rule (§4.3, at least 9 valid repetitions per variant):** RGS elodie (abduction 8), julia (stork 7) and latifah (stork 7). These variants have fewer recorded repetitions. An explicit frame-quality counter (added post hoc; `results/posthoc_quality_and_g1_audit.txt`) found **0 invalid frames out of 1,089,888** in all downloaded files, and no time gaps above 10.5 ms.
   - **RD n = 19; RGS n = 15** (Spilz et al. used 18 for RGS).
   - Full list: `results/exclusions.txt`.
3. **Seeds:** the tuning seed scheme in the plan does not include the exercise, so RD and RGS use the same random and PSO draws per fold. The objectives differ, so the selected settings differ.
4. **Independent recomputation** from the raw JSON (a separate short script) reproduced all primary numbers: means, medians, counts, and n per cell, with 2 repeats per person. ChatGPT's independent tool reproduced them as well: 136 fixed-setting records, 40 tuning records, ADAPT − GEN +7.105 [3.421, 11.579] and +13.667 [8.163, 20.337].
5. **Spearman (E4) was computed with `argsort(argsort)` ranks, which do not average ties.** Many persons are tied at GEN = 1.0, so this mattered. Average ranks are now used in `run_plan6.py` and `summarize_plan6.py`, and the summary was rebuilt from the saved scores without retraining.
   - RD: −0.88 → **−0.973 [−1.00, −0.86]**;
   - RGS: −0.99 → **−0.999 [−1.00, −0.99]**.
   - The old summary is kept as `results/summary_plan6_v1_argsort_spearman.md`.
   - The same rank code in PLAN5 was rechecked: the per-cell range (−0.20 to −0.78) is unchanged.
6. **Evaluation repetitions in the inner tuning objective:** PLAN6 §10 says "repetitions 6–10", while §6 and the code use the **last 5** of each variant, in both the outer evaluation and the inner tuning.
   - These are the same when a variant has 10 repetitions.
   - They differ for 6 eligible person × exercise cases with 9, 11, 12 or 15 repetitions in some variant: RD austra and rehema; RGS austra, etsuko, neves and rehema.
   - Calibration (first k) and evaluation (last 5) never share a repetition. One nominal boundary overlap of 0.00015 s (austra/RD/supination) contains no sensor frame (ChatGPT's annotation audit).
7. **`results/run_log.txt` was emptied** by the post hoc diagnostic script. That script executed the head of `run_plan6.py`, which opens the log in 'w' mode. The script is fixed, and the log was restored from `results/stdout_run.txt`, which had captured the same lines. Nothing was retrained.
8. **The diagnostic's per-person scores were not saved**; only its means are reported.

## Main results (primary: 4-class balanced accuracy, B = 16; points; 95% bootstrap CI over persons)
| Exercise | n | GEN | ADAPT16 | ADAPT − GEN | ADAPT − CTRL | ADAPT − CTRL-NEW | PERS − ADAPT | Persons +/−/= | Median Δ |
|---|---|---|---|---|---|---|---|---|---|
| RD | 19 | 0.922 | 0.993 | **+7.1 [+3.4, +11.6]** | +7.8 [+4.1, +11.8] | **+6.8 [+3.6, +10.9]** | −3.2 [−5.4, −1.2] | **12 / 0 / 7** | +5.0 |
| RGS | 15 | 0.862 | 0.998 | **+13.7 [+8.2, +20.3]** | +12.3 [+6.8, +19.0] | **+15.2 [+9.3, +21.8]** | −3.3 [−5.5, −1.2] | **12 / 0 / 3** | +12.5 |

**All budgets (4-class):**
- **ADAPT − GEN:**
  - RD: +5.0 (B = 4), +6.6 (B = 8), +7.1 (B = 16);
  - RGS: +10.5, +12.5, +13.7.
  - All CIs are above 0.
- **PERS − ADAPT:**
  - RD: −25.9 (B = 4), −10.9 (B = 8), −3.2 (B = 16);
  - RGS: −16.5, −7.0, −3.3.
  - All CIs are below 0. The gap narrows as the budget grows.

### Pre-stated expectations
| | RD | RGS |
|---|---|---|
| E1 (ADAPT − GEN ≥ 2, CI > 0) | ✅ | ✅ |
| E2 (> replay control) | ✅ | ✅ |
| E2b (> unseen donor) | ✅ | ✅ |
| E3 (PERS < ADAPT, CI < 0) | ✅ | ✅ |
| E4 (ρ(GEN, Δ) < 0; descriptive) | ✅ ρ = −0.973 [−1.00, −0.86] | ✅ ρ = −0.999 [−1.00, −0.99] |
| Verdict (§8) | **consistent with PHYTMO** | **consistent with PHYTMO** |
| Pattern (§8 rule) | **broad** (median +5.0; 12/19 with Δ ≥ 2) | **broad** (median +12.5; 12/15 with Δ ≥ 2) |

- Q1 across the two exercises: **2/2 consistent**.
- PERS did not beat ADAPT at any tested budget in either exercise.
- **No person got worse** under ADAPT16 in either exercise. The tied persons (7 in RD, 3 in RGS) are exactly those whom GEN already scored at 1.0.

**Per-person gains (4-class, B = 16):**
- RD:
  - erna +37.5 (GEN 0.60), rehema +22.5 (0.725), katee +17.5 (0.825);
  - others +2.5 to +10;
  - 7 persons at 0 (GEN = 1.0).
- RGS:
  - hamit +45 (GEN 0.55), austra and jung-hee +25 (0.75), gregers +22.5, laurel +20;
  - 3 persons at 0 (GEN = 1.0).

**Secondary, binary task (correct vs any error):**
- RD: ADAPT − GEN +4.7 [+1.9, +8.0]; vs donor +4.0 [+1.8, +6.7].
- RGS: GEN is already 0.979 (ceiling); ADAPT − GEN +2.1 [+0.4, +4.3]; median 0.

**Macro-F1 (4-class, for orientation only):**
- RD: GEN 0.915 → ADAPT16 0.993 (PERS16 0.961).
- RGS: 0.832 → 0.998 (PERS16 0.964).

### Q4: "adapt or not" rules (exploratory, pre-specified)
| Ex / B | Rule | vs GEN | vs ALWAYS | Adapt decisions (person × repeat) | Persons adapted ≥ 1 time / both times | Harmed | Missed gain |
|---|---|---|---|---|---|---|---|
| RD / 16 | G1 | +6.2 | −0.9 | 19/38 | 11/19 / 8/19 | 0 | 5 |
| RD / 16 | G2 | +6.2 | −0.9 | 19/38 | 11/19 / 8/19 | 0 | 5 |
| RGS / 16 | G1 | +13.3 | −0.3 | 24/30 | 14/15 / 10/15 | 0 | 1 |
| RGS / 16 | G2 | +13.0 | −0.7 | 23/30 | 14/15 / 9/15 | 0 | 2 |
| RD / 8 | G1 / G2 | +4.3 / +2.5 | −2.2 / −4.1 | 12/38 / 8/38 | 8/19 / 6/19 ≥ 1 time | 0 | 8 / 10 |
| RGS / 8 | G1 / G2 | +11.0 / +8.3 | −1.5 / −4.2 | 22/30 / 15/30 | 13/15 / 10/15 ≥ 1 time | 0 | 2 / 6 |

The decisions changed between the two outer repeats for 3–5 persons per row.

**Reading:**
- **ALWAYS adapting harmed nobody here.** So the expectation "the gate harms fewer persons than ALWAYS" **could not be tested** (0 vs 0).
- **"Keeps at least half of ALWAYS's gain":**
  - ✅ for G1 at both budgets (RD 87% / 65%; RGS 97% / 88%);
  - ✅ for G2 at B = 16;
  - ❌ for G2 on RD at B = 8 (38%).
- The simple rule "adapt if GEN gets any calibration repetition wrong" (G1) adapted in **19 of 38 person × repeat decisions** in RD at B = 16. That is 11 of 19 persons adapted at least once and 8 both times, so it is not "half of the persons" as a stable group. It lost 0.92 points of mean gain (RGS: 24/30 decisions, 0.33 points).
- **No saving in labelling was shown:** all 16 calibration repetitions were collected from everyone before the decision. The gate can reduce the number of adaptations, not, so far, the labelling effort.
- With 16 examples, the calibration repetitions **did** carry usable information about who needed adaptation in these data. This is a measured result for this dataset. It is not a general guarantee, and it is not "knowing the best strategy for each person".

### Q5: fair tuning and PSO (secondary; 4-class, B = 16; 30 evaluations per tuner)
| | T0 inner spread (median P90 − P10) | T1 RS − fixed | T2 PSO − RS | Inner best RS / PSO |
|---|---|---|---|---|
| RD ADAPT | 3.4 pts | +0.0 [−0.4, +0.4] | −0.3 [−0.9, +0.3] | 0.997 / 0.997 |
| RD PERS | 2.2 pts | +0.1 [−1.3, +2.1] | +0.1 [−0.4, +0.8] | 0.967 / 0.966 |
| RGS ADAPT | 4.0 pts | −0.5 [−1.0, +0.0] | +0.2 [−0.3, +0.7] | 0.998 / 0.998 |
| RGS PERS | 3.3 pts | +1.0 [−0.3, +2.5] | −0.5 [−1.8, +0.5] | 0.980 / 0.980 |

- **T3 (equal tuning) ADAPT_RS − PERS_RS:** RD +3.0 [+1.4, +4.7]; RGS +1.8 [+0.0, +4.0].
- **T0:** the spread is above 1 point, so settings *can* matter in the inner search.
- **T1:** tuned settings did **not** improve outer results over the fixed PLAN5 values. This means "no evidence of improvement here", not that tuning is useless in general.
- **T2: "no evidence that PSO adds value over random search here"**, by the pre-specified rule. Both tuners reached the same inner optimum. The inner objective sits at the ceiling (≈ 0.997–0.998), which leaves little room for any tuner.
- **T3:** the advantage of ADAPT over PERS **survives equal tuning in RD**. In RGS the CI lower bound is 0.0, so the advantage is **not established**. Equally, PERS does not beat ADAPT, so the reversal rule is not triggered.

## Post hoc diagnostic (after results; not in PLAN6): contralateral-leg and trunk sensors
- **Why it was run:** ADAPT16 reached BA = 1.0 for 16 of 19 RD persons and 14 of 15 RGS persons. Calibration and evaluation come from the same set, recorded in a fixed variant order.
- **What was done:** the primary RD analysis was repeated with **left-leg sensors only** (RD is a right-foot exercise), and with the sternum only. The same folds and seeds were used, and the interpretation rule was written in the script before it was run. Note that the rule (0.80 / 0.50) was itself chosen **after** the primary results had been seen, so it is a diagnostic convention, not a pre-registered test.
- The contralateral (standing) leg and the trunk are **not guaranteed information-free**: they can carry real posture or compensation that differs between variants, as well as order or drift effects.
- File: `results/posthoc_uninvolved_sensors_RD.md`.

| RD, 4-class, B = 16 | GEN | ADAPT16 | PERS16 | CTRL-NEW16 |
|---|---|---|---|---|
| Left leg only | 0.413 | **0.714** | **0.784** | 0.412 |
| Sternum only | 0.450 | 0.630 | 0.655 | 0.409 |
| All 9 sensors (reproduces PLAN6) | 0.922 | 0.993 | 0.962 | 0.925 |

The chance level is 0.25. **Verdict by the pre-written rule: inconclusive** (0.50 < ADAPT/PERS < 0.80).

**Meaning:**
- A person-specific model separates the four variants far above chance even from contralateral-leg or trunk sensors. The general model and the donor control on those sensors do not.
- Two explanations are possible, and this check **cannot separate** them:
  - real whole-body compensation that differs by variant;
  - a within-session signature (stance, drift, order).
- **Consequence:** the PLAN6 gains show that the person's own same-session repetitions are very informative. They **cannot** be attributed to learning the target movement alone.
- Separating person effects from session effects needs data and a design that allow it, such as calibration and evaluation from **separate sessions or days**, or a randomised variant order. GAITEX provides neither, and more diagnostics on the same data cannot do it.

## Honest reading
1. **On independent persons, laboratory, exercises and sensors, the PHYTMO conclusion held in both exercises** (2/2):
   - adapting with the person's own repetitions beat the general model, the replay control and an unseen donor;
   - the personal-only classifier never won.
   - The effect was larger than in PHYTMO and **broad**. In this sample no person was worse; this is not evidence that adaptation is safe for every person or on another day.
2. **Why the effects are this large:**
   - Labels are per repetition and instructed.
   - Calibration and evaluation come from the same set.
   - Personal models approach 100%.
   - The diagnostic shows that same-session information is available even away from the moving limb.

   **These are within-session results. They support the value of labelled calibration examples from the same session and task, may be optimistic for use in a different setting, and do not estimate the benefit on another day or in patients.** No monotonic relation to other-day performance has been shown, so they are not called an upper bound.
3. **E4 (larger gain for persons whom GEN assesses less well) is largely mechanical here.**
   - When ADAPT is near 1.0 for almost everyone, the gain ≈ 1 − GEN, so ρ is close to −1 by construction.
   - It is consistent with "adaptation helps those the general model fails". It is **not** an independent scientific success, not evidence of a mechanism, and not a way to identify beneficiaries in advance. Counting "five expectations met" should not be read as five independent findings.
4. **The adapt-or-not rule** (adapt only if GEN errs on a calibration example) kept most of the mean benefit while adapting in 19 of 38 RD decisions. Because always adapting harmed nobody here, the rule's protective value is **untested**. All calibration examples were collected from everyone, so no labelling saving was shown either.
5. **PSO:**
   - Fair tuning did not change the comparison against the general model. The advantage of ADAPT over PERS remained under equal tuning in RD, but is **not established** in RGS (CI [0.0, 4.0]).
   - There is no evidence that PSO adds value over random search under this test. This is not a general equivalence.
   - In this setting PSO does not add value. This is reported as it is.
   - Its role in the master's stays a **secondary, tested option**, relevant mainly when a task is not at ceiling.
6. **Not shown:**
   - transfer across days;
   - patients;
   - phone video;
   - that the model learned the target movement rather than session or person cues;
   - clinical benefit.
7. **Relation to the closest prior** (Spilz et al. 2026, same data, different design): their single-class fine-tuning of a CNN improved 7/19 (RD) and 6/18 (RGS) subjects and worsened some. Our numbers are **not comparable** with theirs (different model, features, split, metric and calibration content). No claim of superiority is made.
