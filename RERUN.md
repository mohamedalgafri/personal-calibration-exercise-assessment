# Reproducing the saved analyses

Use Python 3.11+, NumPy and Bash. Obtain the sensor data as described in [DATA.md](DATA.md), then run:

```bash
bash rerun_guide/setup_rerun.sh
bash rerun_guide/run_remaining.sh
```

The first command copies code into `rerun_workspace/` and links the downloaded inputs. The second includes PLAN5, the saved-score distribution analysis, Pilot 4, PLAN6, the contralateral-sensor diagnostic and PLAN8, in that order. Existing outputs are skipped so an interrupted run can resume. Move the workspace aside and set up a new one for a fresh run. Original saved results outside the workspace are not overwritten.

Camera analysis is added only if its reference data and keypoint inputs exist before setup. Obtain/extract these locally first if you want all nine comparisons. Downloaded or extracted data are not included in the repository and no unpublished Release is required.

```bash
python3 -P rerun_guide/compare_rerun.py
```

This writes `rerun_workspace/RERUN_REPORT.md`, comparing the nine recorded outputs with the user's reproduced outputs. Timing fields are excluded and the numeric tolerance is 1e-9. Matching NaNs are handled explicitly; unmatched non-finite values are failures. Missing or different outputs produce a nonzero exit code. Results may differ across NumPy, platform or hardware versions; this is reported rather than silently accepted.

The original run durations are described in individual reports. They are not a runtime guarantee for another computer. Model-training studies can take hours collectively; video download/decoding/extraction is separate and depends on hardware and network speed.

Not covered by the runner: Pilot 3, the PSO/identity/quantification studies and browser keypoint extraction. Their plans and scripts are included as separate studies. A repeated extraction must preserve the documented frame-quality and run-selection rules; it is not validated by merely creating JSON files.

Release packaging performed syntax, structure and source-content checks only; it did not retrain the models or generate a new completion report for the author.
