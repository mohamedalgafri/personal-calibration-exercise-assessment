"""Preliminary experiment: KIMORE Exercise 1, subject-level, nested repeated CV.

Methods compared (all with Ridge regression on standardized features):
  mean      : predicts the training-set mean (sanity baseline)
  all       : all features
  relieff   : RReliefF top-k, k chosen by inner CV
  spearman  : |Spearman| top-k, k chosen by inner CV
  bpso      : one binary-PSO run (V-shaped transfer)
  consensus : features chosen in >= 50% of R binary-PSO runs
Also: all features with RBF kernel ridge, and a leakage demo (window-level random split
vs subject-grouped split).

Usage: python run_experiment.py <zip_path> <out_dir> [n_repeats] [n_runs]
"""
import sys, json, time
import numpy as np
import fslib as F
import features as FE

ZIP, OUT = sys.argv[1], sys.argv[2]
N_REP = int(sys.argv[3]) if len(sys.argv) > 3 else 5
N_RUNS = int(sys.argv[4]) if len(sys.argv) > 4 else 10
K_OUT = 5
ALPHAS = [0.1, 1.0, 10.0, 100.0]
KS = [3, 5, 8, 12, 20]
PSO = dict(n_particles=30, n_iter=60, lam=0.5, init_p=0.1, transfer="v")

t0 = time.time()
Xf, y, names, info, meta = FE.build_dataset(ZIP)
n, d = Xf.shape
print(f"subjects={n} features={d} windows={meta['n_windows']} rows={meta['n_rows']}", flush=True)
print(f"score range {y.min():.2f}-{y.max():.2f} mean {y.mean():.2f} sd {y.std():.2f}", flush=True)
print("windows per subject:", [i['windows'] for i in info], flush=True)
assert all(i["score_const"] for i in info)


def tune_alpha(X, y, seed):
    errs = [F.cv_mae(X, y, lambda a=a: F.Ridge(a), seed=seed) for a in ALPHAS]
    return ALPHAS[int(np.argmin(errs))]


def fit_predict(Xtr, ytr, Xte, mask, alpha):
    s = F.Standardizer().fit(Xtr[:, mask])
    m = F.Ridge(alpha).fit(s.transform(Xtr[:, mask]), ytr)
    return m.predict(s.transform(Xte[:, mask]))


methods = ["mean", "all", "all_krr", "relieff", "spearman", "bpso", "consensus"]
oof = {m: np.zeros((N_REP, n)) for m in methods}
fold_mae = {m: [] for m in methods}
masks = {m: [] for m in ["relieff", "spearman", "bpso", "consensus"]}
cons_freq = []
bpso_runs_by_fold = []

for r in range(N_REP):
    rng = np.random.default_rng(1000 + r)
    for fi, (tr, te) in enumerate(F.kfold(n, K_OUT, rng)):
        Xtr, ytr, Xte, yte = Xf[tr], y[tr], Xf[te], y[te]
        seed = 100 * r + fi
        full = np.ones(d, bool)
        alpha = tune_alpha(Xtr, ytr, seed)
        mf = lambda: F.Ridge(alpha)
        preds = {}
        preds["mean"] = np.full(len(te), ytr.mean())
        preds["all"] = fit_predict(Xtr, ytr, Xte, full, alpha)
        # kernel ridge on all features (alpha tuned)
        kerr = [F.cv_mae(Xtr, ytr, lambda a=a: F.KernelRidge(a), seed=seed) for a in [0.01, 0.1, 1.0]]
        ka = [0.01, 0.1, 1.0][int(np.argmin(kerr))]
        s = F.Standardizer().fit(Xtr)
        preds["all_krr"] = F.KernelRidge(ka).fit(s.transform(Xtr), ytr).predict(s.transform(Xte))
        # filters (scores computed on training fold only)
        Ztr = F.Standardizer().fit(Xtr).transform(Xtr)
        m_rel = F.select_topk_by_cv(Xtr, ytr, F.rrelieff(Ztr, ytr, seed=seed), KS, mf, seed=seed)
        m_spe = F.select_topk_by_cv(Xtr, ytr, F.spearman_filter(Xtr, ytr), KS, mf, seed=seed)
        preds["relieff"] = fit_predict(Xtr, ytr, Xte, m_rel, alpha)
        preds["spearman"] = fit_predict(Xtr, ytr, Xte, m_spe, alpha)
        # BPSO runs (inside training fold only)
        runs = []
        for k in range(N_RUNS):
            mk, fk, _ = F.bpso_select(Xtr, ytr, mf, seed=10_000 * r + 100 * fi + k,
                                      inner_seed=seed, **PSO)
            runs.append(mk)
        m_bpso = runs[0]
        m_cons, freq = F.consensus(runs, 0.5)
        preds["bpso"] = fit_predict(Xtr, ytr, Xte, m_bpso, alpha)
        preds["consensus"] = fit_predict(Xtr, ytr, Xte, m_cons, alpha)
        for m in methods:
            oof[m][r, te] = preds[m]
            fold_mae[m].append(F.mae(yte, preds[m]))
        masks["relieff"].append(m_rel); masks["spearman"].append(m_spe)
        masks["bpso"].append(m_bpso); masks["consensus"].append(m_cons)
        cons_freq.append(freq)
        bpso_runs_by_fold.append(F.nogueira_stability(np.array(runs))[0])
        print(f"rep {r} fold {fi} | " + " ".join(f"{m}={fold_mae[m][-1]:.2f}" for m in methods)
              + f" | sizes rel={m_rel.sum()} spe={m_spe.sum()} bpso={m_bpso.sum()} cons={m_cons.sum()}"
              + f" | {time.time()-t0:.0f}s", flush=True)

res = {"n_subjects": n, "n_features": d, "feature_names": names,
       "score": {"min": float(y.min()), "max": float(y.max()), "mean": float(y.mean()), "sd": float(y.std())},
       "windows_per_subject": [i["windows"] for i in info],
       "inferred_frac_mean": float(np.mean([i["inferred_frac"] for i in info])),
       "protocol": {"outer": f"{N_REP}x{K_OUT}-fold subject-level", "inner": "5-fold", "bpso_runs": N_RUNS, "pso": PSO,
                    "alphas": ALPHAS, "ks": KS},
       "methods": {}}
for m in methods:
    maes = [F.mae(y, oof[m][r]) for r in range(N_REP)]
    rhos = [F.spearman(y, oof[m][r]) for r in range(N_REP)]
    entry = {"mae_mean": float(np.mean(maes)), "mae_sd": float(np.std(maes)),
             "rho_mean": float(np.mean(rhos)), "rho_sd": float(np.std(rhos)),
             "fold_mae": fold_mae[m]}
    if m in masks:
        Z = np.array(masks[m])
        sizes = Z.sum(1)
        phi, lo, hi = F.nogueira_stability(Z)
        entry.update({"size_mean": float(sizes.mean()), "size_sd": float(sizes.std()),
                      "stability": phi, "stab_lo": lo, "stab_hi": hi,
                      "freq": Z.mean(0).tolist()})
    else:
        entry.update({"size_mean": float(d) if m.startswith("all") else 0.0})
    res["methods"][m] = entry
res["bpso_within_fold_stability_mean"] = float(np.nanmean(bpso_runs_by_fold))
res["bpso_within_fold_stability"] = [float(v) for v in bpso_runs_by_fold]

# Wilcoxon on per-fold MAE vs "all"
res["wilcoxon_vs_all"] = {}
for m in ["mean", "all_krr", "relieff", "spearman", "bpso", "consensus"]:
    W, z, p = F.wilcoxon_signed_rank(fold_mae[m], fold_mae["all"])
    res["wilcoxon_vs_all"][m] = {"W": W, "z": z, "p": p,
                                 "median_diff": float(np.median(np.array(fold_mae[m]) - np.array(fold_mae["all"])))}

# ---- leakage demo: window-level samples, random vs subject-grouped split
Xraw, Yraw = FE.load_zip(ZIP)
Jw = Xraw.reshape(len(Xraw), 25, 4)
groups = FE.group_subjects(Jw, Yraw)
gid = np.zeros(len(Yraw), int)
for g_i, g in enumerate(groups):
    gid[g] = g_i
Wf = np.array([[v for v in FE.features(Jw[w * 100:(w + 1) * 100, :, :3]).values()] for w in range(len(Yraw))])
leak = {"random": [], "grouped": []}
for r in range(N_REP):
    rng = np.random.default_rng(5000 + r)
    for tr, te in F.kfold(len(Yraw), K_OUT, rng):
        leak["random"].append(F.mae(Yraw[te], fit_predict(Wf[tr], Yraw[tr], Wf[te], np.ones(Wf.shape[1], bool), 10.0)))
    rng = np.random.default_rng(6000 + r)
    for trg, teg in F.kfold(len(groups), K_OUT, rng):
        tr, te = np.isin(gid, trg), np.isin(gid, teg)
        leak["grouped"].append(F.mae(Yraw[te], fit_predict(Wf[tr], Yraw[tr], Wf[te], np.ones(Wf.shape[1], bool), 10.0)))
res["leakage_demo"] = {k: {"mae_mean": float(np.mean(v)), "mae_sd": float(np.std(v))} for k, v in leak.items()}
res["leakage_demo"]["n_windows"] = int(len(Yraw))
res["runtime_s"] = time.time() - t0
json.dump(res, open(f"{OUT}/results_ex1.json", "w"), indent=1)
print("LEAKAGE", res["leakage_demo"], flush=True)
print("DONE", round(res["runtime_s"]), "s", flush=True)
