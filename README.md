# Personal Adaptation for Motion-Based Exercise Assessment in Sport and Rehabilitation

*A Controlled Study Using Wearable Sensors with a Markerless Video Extension*

Preparatory, exploratory analyses for a proposed master's research project by **Mohammed Alghifari**.

**Question:** what do a few of a new person's labelled exercise examples add beyond a general model and fair alternatives, and how does predictive performance change across people?

Personal adaptation is an established technique. This repository documents comparisons, limitations and negative results; it does not introduce a new personalisation algorithm or establish clinical validity.

**Repository scope.** This source release contains the completed preparatory studies below. The proposed master's design additionally compares classifier adaptation with simpler calibration using the same labels after source-person model selection. That future comparison, including the proposed eight-example primary budget, is not claimed as an implemented or completed study in this release.

Repository: [mohamedalgafri/personal-calibration-exercise-assessment](https://github.com/mohamedalgafri/personal-calibration-exercise-assessment).

## Studies and interpretation

| Study | Evidence and boundary | Report |
|---|---|---|
| PHYTMO / PLAN5 | Adaptation versus a general model, a personal classifier, replay and donor controls, across four exercises and two measurement types. Mean gains met the combined point-estimate/CI criterion against the general model in 7/8 cells; not every person improved. | [PLAN5 results](phytmo_pilot/RESULTS_PLAN5.md) |
| PHYTMO / Pilot 4 | Correct-only calibration improved performance in the tested exercises; superiority of mixed calibration was not consistent under the eligibility checks. | [Pilot 4](phytmo_pilot/RESULTS_PILOT4.md) |
| GAITEX / PLAN6 | Adapted minus general: +7.1 and +13.7 balanced-accuracy points in the two exercises. Near-ceiling within-session results and recording-order effects limit interpretation. | [PLAN6 results](gaitex_plan6/RESULTS_PLAN6.md) |
| MLP / PLAN8 | The MLP general model was not consistently stronger on new people. This robustness check does not settle comparison with a qualified stronger general model. | [PLAN8 results](stronger_plan8/RESULTS_PLAN8.md) |
| Laboratory camera / PLAN7 | The planned view-balanced analysis was not feasible under the quality rules. Front-view analysis is descriptive and post hoc; it does not establish phone or home performance. | [PLAN7 results](camera_plan7/RESULTS_PLAN7.md) |
| PSO and quantification | PSO improved an HDy search objective and mean estimation error relative to random search, but classify-and-count remained more accurate. GAITEX tuning showed no evidence of PSO superiority. | [PSO study](preliminary_experiment/README.md), [quantification results](quantification_pilot/results/summary_quant.md) |

In PLAN5, a mean gain of at least two points plus a CI excluding zero is not the same as a confidence interval whose lower bound exceeds two points. Consult the reports for full criteria, uncertainty and eligibility.

Calibration and evaluation primarily use the same session. Participants perform controlled or instructed deviations; dataset execution labels are not a universal clinical standard. The datasets have already been analysed and are development data. Later checks and protocol changes are identified in the reports.

## Getting started

Requirements: **Python 3.11+**, NumPy, Bash and curl. The `-P` flag in the commands requires Python 3.11 or later. Chrome and ffmpeg are only needed for optional video extraction. Several GB of local disk space are needed for downloaded data.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
bash get_data.sh phytmo
bash get_data.sh gaitex
bash rerun_guide/setup_rerun.sh
bash rerun_guide/run_remaining.sh
```

The setup creates an isolated workspace and the runner includes PLAN5, its distribution check, Pilot 4, PLAN6, the other-leg diagnostic and PLAN8. Camera reproduction is optional and requires locally acquired reference data and extracted keypoints first; see [DATA.md](DATA.md) and [RERUN.md](RERUN.md). A comparison with missing camera outputs reports those omissions rather than claiming that all nine outputs matched.

There is **no required GitHub Release asset**. Videos, sensor recordings, source annotations and extracted keypoint arrays are obtained separately and are not included in this source release.

## Repository map

| Folder | Contents |
|---|---|
| `phytmo_pilot/` | Plans, code and saved metrics for PHYTMO pilots and PLAN5 |
| `gaitex_plan6/` | GAITEX plan, code, diagnostics and saved metrics |
| `stronger_plan8/` | MLP implementation and robustness analysis |
| `camera_feasibility/`, `camera_plan7/` | Feasibility/extraction tools, plans, quality checks and saved assessment metrics |
| `preliminary_experiment/`, `quantification_pilot/` | Separate PSO, identity-diagnostic and activity-quantification studies |
| `feasibility_2026-11-16/` | Archive indexes used for selective acquisition, not raw recordings |
| `rerun_guide/`, `tools/` | Isolated reproduction and on-demand data-acquisition helpers |
| `portfolio/` | Saved plots and optional figure-generation code |

## Provenance and reproducibility

The author chose the research direction and questions, ran and checked the preparatory experiments on his own computer with AI coding assistance, and decided which design changes to accept. AI tools supported code, analysis and editing; automated reviews are not human peer review. Some historical plans and reports mention the AI assistants used (Claude, ChatGPT/Codex) and internal review notes that are not part of this repository; those files are kept unchanged so that their recorded fingerprints remain valid.

Historical plans and their fingerprint records are preserved. Some fingerprint lines refer to earlier plan snapshots before documented addenda, rather than the final file. [PROVENANCE.md](PROVENANCE.md) explains the release audit. [RERUN_STATUS.md](RERUN_STATUS.md) records the author's completion statement; fresh numerical comparisons describe the reproducer's own workspace. Version and numeric differences can occur across software/hardware environments; the helper uses the documented tolerance and reports mismatches.

## Data, licence and citation

Original datasets are not redistributed. See [DATA.md](DATA.md) for original records, licences and citations. Code is under the [MIT licence](LICENSE); third-party dataset rights are separate. Please cite the repository and each original dataset used, as described in [CITATION.cff](CITATION.cff).
