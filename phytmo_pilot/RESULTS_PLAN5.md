# PLAN5 results: general vs adapted vs personal, IMU and optical motion capture (16 Nov 2026)

**Plan:** `PLAN5.md`.
- sha256 `034a1ab2…` at 00:17, before downloading the optical and EAH data.
- Addendum A: `510e87b8…` at 00:34, before any analysis of those data.
- Both fingerprints were posted in DEBATE.md.

**Code:** `code/run_plan5.py` (smoke-tested only on IMU SQT/HAA, which had been seen before).
**Outputs:** `results/plan5/summary_plan5.md`, `results_plan5.json`, `run_log.txt`. Runtime 17 min.

**Data quality:**
- 19 SQT optical files (persons A06, A07 and others) lack a rigid body and were excluded.
- 4 HAA optical files were excluded (missing body or non-finite values).
- **Eligible persons, the same for both modalities:** SQT 21, HAA 25, SQZ 27, EAH 29.

## Main results at B = 16 (8 standard + 8 deviation windows from series 1)
Differences are in balanced-accuracy points, with a bootstrap 95% CI over persons. Persons: improved / worse / tied.

| Exercise / modality | GEN | ADAPT − GEN | ADAPT − CTRL-NEW (another person's new examples) | PERS* − ADAPT | Persons ADAPT vs GEN (+/−/=), median |
|---|---|---|---|---|---|
| SQT / IMU (seen) | 0.921 | +3.0 [+0.5, +6.5] | +4.0 [+1.0, +7.9] | −9.7 [−15.8, −4.4] | 11/4/6, +0.7 |
| SQT / OPT | 0.709 | +7.2 [+3.0, +12.3] | +7.1 [+2.4, +12.1] | −9.9 | 15/4/2, +4.7 |
| HAA / IMU (seen) | 0.924 | +3.1 [+1.1, +5.5] | +3.1 [+1.0, +5.9] | −3.0 [−5.7, −0.6] | 16/4/5, +1.0 |
| HAA / OPT | 0.857 | **+0.9 [−1.5, +3.3]** | +1.5 [−1.0, +3.9] | −19.5 | **14/10/1**, +0.7 |
| SQZ / IMU (seen) | 0.792 | +9.0 [+5.6, +12.7] | +7.8 [+4.4, +11.3] | −0.5 [−4.4, +3.5] (tie) | 22/3/2, +5.0 |
| SQZ / OPT | 0.792 | +8.2 [+4.6, +12.1] | +8.2 [+4.6, +11.9] | −16.3 | 16/3/8, +4.5 |
| **EAH / IMU (unseen)** | 0.898 | **+5.4 [+1.6, +9.9]** | **+5.3 [+1.8, +9.7]** | −2.8 [−5.8, −0.3] | 16/5/8, +0.7 |
| **EAH / OPT (unseen)** | 0.897 | **+4.3 [+1.5, +7.6]** | **+4.7 [+2.3, +7.6]** | −10.1 | 16/4/9, +1.7 |

## Pre-stated expectations
- **E1** (ADAPT − GEN ≥ 2 with CI > 0): **IMU 4/4 ✅, OPT 3/4 ✅.** It fails for HAA/OPT, where 10 of 25 persons got worse.
- **E2** (ADAPT > CTRL, a matched control with already-seen examples): IMU 4/4, OPT 3/4 ✅.
- **E2b** (ADAPT > CTRL-NEW, new examples from another person): **IMU 4/4, OPT 3/4 ✅.**
  - On average, the person's own examples were more useful than the same number of new examples from a donor chosen by the stated rule (next test person in the fold). This does not show that any new data from other people would be useless. Calibration and evaluation come from the same session, with the same deliberately chosen deviation, so "own examples" cannot be separated from "matching the session" (logic audit L1).
  - CTRL-NEW stayed close to GEN everywhere.
- **E3** (descriptive): a weaker general model would favour the personal model. **Not supported.** Spearman ρ = +0.33 over 8 cells, opposite to the expected sign. This is descriptive only, not a statistical rejection or evidence of an opposite mechanism.
- **First tested budget (4/8/16) at which PERS* beats ADAPT:** none in any cell. PERS* − ADAPT was negative with CI < 0 in 7/8 cells. **SQZ/IMU at B = 16 is unresolved:** −0.5 [−4.4, +3.5], with no evidence for either side and no proof of equivalence. This does not exclude a crossover at other budgets or with other personal models, or for individual persons.
- **EAH**, unseen in both modalities, met E1 and E2b in **both** modalities.

## Honest reading
1. In this dataset at B = 16:
   - ADAPT beat GEN and the unseen-donor control CTRL-NEW in 7/8 cells.
   - The personal-only classifier PERS* was worse than ADAPT in 7/8 cells, and unresolved in SQZ/IMU.
   - All three conditions held together in 6/8 cells.
   - Strongest allowed statement: **the person's own examples were, on average, more useful than the same number of new examples from a donor chosen by the stated rule.** This does not show that any other person's new data would be useless.
2. **It is not universal:**
   - in some cells the median person gains under 1 point while the mean is driven by a subset;
   - 3–10 persons per cell got worse (counts: 4, 4, 4, 10, 3, 3, 5, 4; corrected 16 Nov);
   - in HAA/OPT there was no clear average gain (+0.9 [−1.5, +3.3]); this is not proof of zero effect.
3. Within the budgets tested (4, 8, 16), the personal classifier showed **no clear average advantage** over adaptation in any cell. The descriptive expectation E3 was not supported. **HAA/OPT:** +0.9 [−1.5, +3.3]. No clear average gain, but not proof of zero effect; 10/25 persons got worse.
4. **The findings repeat across the two modalities**, but that does not prove the cause is the movement rather than noise. The modalities are not time-aligned, and they share the labels and the selection policy.
5. **Limits:**
   - healthy volunteers performing deviations on purpose;
   - same laboratory, same participants and same day;
   - labels per series;
   - overlapping 2-s windows;
   - one linear model;
   - folds re-use persons;
   - IMU results for SQT, HAA and SQZ are not confirmatory.
6. **Novelty:** personalisation is established (Spilz et al. 2026; BayaHAR 2026; Jánošová et al. 2024).
   - This is a **controlled comparative evaluation on public data** (same participants and laboratory; **not an independent replication**), across two representations, with replay and unseen-donor controls.
   - It also includes a planned test on an exercise held back from the earlier analyses.
   - The CIs are approximate: 96 possible intervals, no family-wise guarantee, and the 2-point threshold is operational, not clinical.
   - **Whether this suffices for a master's is the advisor's decision.**

## Exploratory, post hoc (16 Nov, after the logic audit L1; not pre-registered)
- **The gain is concentrated in a few persons.** The top 5 persons carry 51–99% of the net gain (EAH/IMU 86%, SQT/IMU 99%).
- **Many persons were near ceiling under GEN** (BA ≥ 0.98): 1–10 per cell. These persons had no room to improve.
- **The gain goes mainly to persons whom GEN assesses poorly.** Spearman(GEN BA, ADAPT16 − GEN) was negative in all 8 cells (−0.20 to −0.78). Mean gain, lower half vs upper half of GEN BA:
  - SQT/IMU +6.1 vs +0.7
  - SQT/OPT +12.1 vs +2.8
  - HAA/IMU +6.3 vs +0.1
  - HAA/OPT +3.2 vs −1.3
  - SQZ/IMU +14.5 vs +3.8
  - SQZ/OPT +15.2 vs +1.7
  - EAH/IMU +10.3 vs +0.8
  - EAH/OPT +7.7 vs +1.1
  - Caveats: ceiling effects, and GEN and ADAPT were scored on the same evaluation set.
- **Five of the 8 cells had not been analysed before** (all OPT cells and EAH/IMU). E1 was met in 4 of these 5.
- **Idea for the master's (untested):** use the few labelled examples first to check GEN on this person, and adapt only when GEN fails on them.
- **All six PHYTMO exercises have now been analysed**, so PHYTMO can no longer give a confirmatory test. Confirmation needs independent data, ideally with separate sessions.

## Addendum (16 Nov 2026, later; post hoc, not pre-registered): per-cell distribution
Mohamed asked us not to generalise the statement "the gain went to a few people". The earlier bullet "the top 5 persons carry 51–99% of the net gain" was a share of the **net** gain, which is inflated when there are losses. It is replaced by a per-cell table computed from the saved `results_plan5.json`, with no retraining: `code/posthoc_plan5_distribution.py` → `results/plan5/posthoc_distribution_B16.md`.

| Cell | n | median Δ | improved / worse / tied | Δ ≥ +2 / Δ ≤ −2 | top-5 share of **gross** gain | GEN ≥ 0.98 | Pattern |
|---|---|---|---|---|---|---|---|
| SQT/IMU | 21 | +0.7 | 11 / 4 / 6 | 8 / 3 | 83% | 5 | concentrated |
| SQT/OPT | 21 | +4.7 | 15 / 4 / 2 | 15 / 2 | 66% | 1 | broad |
| HAA/IMU | 25 | +1.0 | 16 / 4 / 5 | 9 / 1 | 73% | 10 | concentrated |
| HAA/OPT | 25 | +0.7 | 14 / 10 / 1 | 7 / 7 | 81% | 3 | mixed (no clear mean gain) |
| SQZ/IMU | 27 | +5.0 | 22 / 3 / 2 | 20 / 1 | 50% | 2 | broad |
| SQZ/OPT | 27 | +4.5 | 16 / 3 / 8 | 16 / 2 | 53% | 7 | broad |
| EAH/IMU | 29 | +0.7 | 16 / 5 / 8 | 10 / 0 | 83% | 7 | concentrated |
| EAH/OPT | 29 | +1.7 | 16 / 4 / 9 | 13 / 3 | 67% | 7 | concentrated |

**Reading:**
- "Broad" and "concentrated" are labels applied after the fact.
- The broad cells are those where GEN was weakest on average (SQT/OPT 0.709; SQZ 0.792).
- The concentrated cells have many persons at or near ceiling.
- The lower-vs-upper-half comparison of GEN depends on the split rule when there are ties. For SQT/IMU it gives +5.6 for the lower 10 persons and +6.1 for the 9 persons strictly below the median (the latter was used above).
- The full list of the 23 excluded optical files is in `results/plan5/posthoc_full_exclusion_list.txt`. The run log printed only the first 6 names.

## Note (16 Nov, evening): Spearman ties rechecked
`run_plan5.py` ranks with `argsort(argsort)`, which does not average ties. This was rechecked after ChatGPT found the same issue in PLAN6. With average ranks, the per-cell Spearman(GEN, ADAPT16 − GEN) values are:
- SQT/IMU −0.38; SQT/OPT −0.29; HAA/IMU −0.78; HAA/OPT −0.20;
- SQZ/IMU −0.49; SQZ/OPT −0.64; EAH/IMU −0.59; EAH/OPT −0.54.

The range **−0.20 to −0.78 is unchanged**, and all signs are negative.
