# Preliminary experiment — KIMORE Exercise 1 (lifting of the arms)

Feasibility study for the UNESP DHT master's proposal: compact and **stable** feature
selection (binary PSO + consensus) for predicting clinicians' quality scores.

## Data
- KIMORE mirror on Zenodo: https://zenodo.org/records/20262128 (CC-BY 4.0).
  File `Kimore ex1-20260118T201447Z-1-001.zip`, 39,165,851 bytes, MD5 `949f4498b450d14e077fe581a939f6e2`.
- Original paper: Capecci et al. (2019), IEEE TNSRE 27(7):1436–1448, doi:10.1109/TNSRE.2019.2923060.
- Put the zip at `data_kimore/kimore_ex1.zip`.

## What the code does
1. `features.py` loads `Train_X.csv` (frames × 25 joints × x,y,z,state) and `Train_Y.csv` (one score per 100-frame window),
   infers person groups (score change, or position jump + different bone-length "fingerprint"; these are not documented participant identifiers), drops walking / badly tracked windows,
   and computes 92 upper-body kinematic features per person.
2. `fslib.py` (numpy only): Ridge / RBF kernel ridge, RReliefF, |Spearman| filter, binary PSO (V-shaped transfer),
   consensus selection, Nogueira (2018) stability index with 95% CI, Wilcoxon test.
3. `run_experiment.py`: person-level 5×5-fold CV, nested selection; methods: mean, all, all (kernel), RReliefF, Spearman, BPSO, consensus (10 runs);
   plus a leakage demo (window-level random split vs person-grouped split).
4. `run_consensus_scaling.py`: stability of consensus with 1/5/10/20/30 PSO runs and thresholds 30/50/70% (3×5 folds).
5. `report.py`: builds `results/report_ex1.html` (Arabic report, inline SVG charts) and `results/summary_ex1.md` (English).

## Reproduce (only numpy needed)
```bash
cd code
PYTHONPATH=$PWD python3 -P run_experiment.py ../data_kimore/kimore_ex1.zip ../results 5 10
PYTHONPATH=$PWD python3 -P run_consensus_scaling.py ../data_kimore/kimore_ex1.zip ../results 3 30
PYTHONPATH=$PWD python3 -P report.py ../results/results_ex1.json ../results
```
Runtime on a laptop: ~14 min + ~24 min.

## Main results (13 Nov 2026)
See `results/summary_ex1.md`. The optional HTML can be generated locally by `code/report.py`; it is not included in this source release.

## Extra check (14 Nov 2026)
`results/run_variability_ex1.txt`: on the same training data, 10 binary-PSO runs give similar error
(variation 5–17%) but two runs share only ~6–12% of their selected features.

## Interpretation boundary

The person groups in this exploratory KIMORE mirror were inferred. Scores from published studies with different data organisation and splits are not used to claim superiority here. The documented real-ID diagnostic is a separate experiment in `realid_confirm_2026-11-15/`.
