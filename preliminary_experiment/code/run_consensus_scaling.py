"""Follow-up for H2: does consensus selection become more stable as the number of
PSO runs grows (1 -> 10 -> 30)? Same outer splits as run_experiment.py (repeats 0..N_REP-1).
Usage: python run_consensus_scaling.py <zip_path> <out_dir> [n_repeats] [max_runs]"""
import sys, json, time
import numpy as np
import fslib as F
import features as FE

ZIP, OUT = sys.argv[1], sys.argv[2]
N_REP = int(sys.argv[3]) if len(sys.argv) > 3 else 3
MAXR = int(sys.argv[4]) if len(sys.argv) > 4 else 30
K_OUT, ALPHAS = 5, [0.1, 1.0, 10.0, 100.0]
PSO = dict(n_particles=30, n_iter=60, lam=0.5, init_p=0.1, transfer="v")
RUNS = [1, 5, 10, 20, 30]
THR = [0.3, 0.5, 0.7]

t0 = time.time()
Xf, y, names, info, meta = FE.build_dataset(ZIP)
n, d = Xf.shape
masks = {(r, t): [] for r in RUNS for t in THR}
maes = {(r, t): [] for r in RUNS for t in THR}
within = []
for rep in range(N_REP):
    rng = np.random.default_rng(1000 + rep)
    for fi, (tr, te) in enumerate(F.kfold(n, K_OUT, rng)):
        Xtr, ytr, Xte, yte = Xf[tr], y[tr], Xf[te], y[te]
        seed = 100 * rep + fi
        errs = [F.cv_mae(Xtr, ytr, lambda a=a: F.Ridge(a), seed=seed) for a in ALPHAS]
        alpha = ALPHAS[int(np.argmin(errs))]
        mf = lambda: F.Ridge(alpha)
        runs = [F.bpso_select(Xtr, ytr, mf, seed=10_000 * rep + 100 * fi + k, inner_seed=seed, **PSO)[0]
                for k in range(MAXR)]
        within.append(F.nogueira_stability(np.array(runs))[0])
        for r in RUNS:
            for t in THR:
                m, _ = F.consensus(runs[:r], t)
                s = F.Standardizer().fit(Xtr[:, m])
                p = F.Ridge(alpha).fit(s.transform(Xtr[:, m]), ytr).predict(s.transform(Xte[:, m]))
                masks[(r, t)].append(m)
                maes[(r, t)].append(F.mae(yte, p))
        print(f"rep {rep} fold {fi} done {time.time()-t0:.0f}s", flush=True)

out = {"n_repeats": N_REP, "runs": RUNS, "thresholds": THR, "within_fold_stability_30runs": float(np.mean(within)),
       "rows": []}
for r in RUNS:
    for t in THR:
        Z = np.array(masks[(r, t)])
        phi, lo, hi = F.nogueira_stability(Z)
        out["rows"].append({"runs": r, "thr": t, "stability": phi, "lo": lo, "hi": hi,
                            "size": float(Z.sum(1).mean()), "fold_mae": float(np.mean(maes[(r, t)]))})
        print(f"runs={r:2d} thr={t} stab={phi:.2f} [{lo:.2f},{hi:.2f}] size={Z.sum(1).mean():.1f} foldMAE={np.mean(maes[(r,t)]):.2f}")
out["runtime_s"] = time.time() - t0
json.dump(out, open(f"{OUT}/consensus_scaling_ex1.json", "w"), indent=1)
print("DONE", round(out["runtime_s"]), "s")
