"""Confirmatory check with real subject IDs (see PLAN.md, written before running).
Usage: PYTHONPATH=<dir with fslib.py, idlib.py> python3 -P run_realid.py <parkinsons.zip> <out_dir>"""
import sys, io, json, time, zipfile
import numpy as np
import fslib as F
import idlib as I

ZIP, OUT = sys.argv[1], sys.argv[2]
t0 = time.time()
with zipfile.ZipFile(ZIP) as z:
    name = [n for n in z.namelist() if n.endswith("parkinsons_updrs.data")][0]
    txt = z.read(name).decode()
lines = txt.strip().splitlines()
header = lines[0].split(",")
A = np.array([[float(v) for v in l.split(",")] for l in lines[1:]])
col = {h: i for i, h in enumerate(header)}
subj = A[:, col["subject#"]].astype(int)
# 20 rows per subject, evenly spaced in test_time
keep = []
for s in np.unique(subj):
    idx = np.where(subj == s)[0]
    idx = idx[np.argsort(A[idx, col["test_time"]])]
    keep.extend(idx[np.linspace(0, len(idx) - 1, 20).round().astype(int)])
keep = np.array(sorted(keep))
A, subj = A[keep], subj[keep]
y = A[:, col["motor_UPDRS"]]
voice = [h for h in header if h not in ("subject#", "age", "sex", "test_time", "motor_UPDRS", "total_UPDRS")]
Xv = A[:, [col[h] for h in voice]]
Xa = A[:, [col["age"], col["sex"]]]
print(f"rows={len(y)} subjects={len(np.unique(subj))} voice={len(voice)}", flush=True)

ALPHA = 0.1
def model_fn():
    return F.KernelRidge(alpha=ALPHA)

def fit_eval(Xtr, ytr, Xte, yte):
    s = F.Standardizer().fit(Xtr)
    m = model_fn().fit(s.transform(Xtr), ytr)
    return F.mae(yte, m.predict(s.transform(Xte)))

def relieff_cross(X, y, groups, k_neighbors=10, seed=0):
    """RReliefF with neighbours restricted to OTHER persons."""
    rng = np.random.default_rng(seed)
    n, d = X.shape
    lo, hi = X.min(0), X.max(0)
    Xs = (X - lo) / np.where(hi - lo > 1e-12, hi - lo, 1.0)
    yr = (y.max() - y.min()) or 1.0
    k = min(k_neighbors, n - 1)
    ranks = np.arange(1, k + 1); w = np.exp(-((ranks / (k / 3.0)) ** 2)); w /= w.sum()
    NdC = 0.0; NdA = np.zeros(d); NdCdA = np.zeros(d)
    for i in rng.permutation(n):
        dist = np.abs(Xs - Xs[i]).sum(1)
        dist[groups == groups[i]] = np.inf
        nn = np.argsort(dist)[:k]
        dy = np.abs(y[nn] - y[i]) / yr
        dA = np.abs(Xs[nn] - Xs[i])
        NdC += (w * dy).sum(); NdA += (w[:, None] * dA).sum(0); NdCdA += (w[:, None] * dy[:, None] * dA).sum(0)
    if NdC <= 0 or n - NdC <= 0:
        return np.zeros(d)
    return NdCdA / NdC - (NdA - NdCdA) / (n - NdC)

def random_baseline(size, d, code_idx, Xtr, ytr, Xte, yte, rng, n=100):
    shares, maes = [], []
    for _ in range(n):
        m = np.zeros(d, bool); m[rng.choice(d, size, replace=False)] = True
        shares.append(m[code_idx].sum() / size)
        maes.append(fit_eval(Xtr[:, m], ytr, Xte[:, m], yte))
    return float(np.mean(shares)), float(np.mean(maes)), float(np.percentile(maes, 25)), float(np.percentile(maes, 75))

rows = []
PSO = dict(n_particles=15, n_iter=20, lam=0.5, init_p=0.15, transfer="v")
for code_seed in range(3):
    crng = np.random.default_rng(1000 + code_seed)
    us = np.unique(subj)
    codes_per_subj = {s: crng.normal(size=6) for s in us}
    Xc = np.array([codes_per_subj[s] for s in subj])
    X = np.hstack([Xv, Xa, Xc])
    d = X.shape[1]
    names = voice + ["age", "sex"] + [f"code{j}" for j in range(6)]
    code_idx = np.arange(len(voice) + 2, d)
    real_idx = np.array([len(voice), len(voice) + 1])
    for rep in range(2):
        orng = np.random.default_rng(50 + rep)
        for fi, (tr, te) in enumerate(I.grouped_kfold(subj, 3, orng)):
            Xtr, ytr, gtr, Xte, yte = X[tr], y[tr], subj[tr], X[te], y[te]
            seed = 100 * code_seed + 10 * rep + fi
            Ztr = F.Standardizer().fit(Xtr).transform(Xtr)
            lists = {}
            lists["spearman_top6"] = I.topk(F.spearman_filter(Xtr, ytr), 6)
            lists["relieff_std_top6"] = I.topk(F.rrelieff(Ztr, ytr, seed=seed), 6)
            lists["relieff_cross_top6"] = I.topk(relieff_cross(Ztr, ytr, gtr, seed=seed), 6)
            cv_rec = I.random_cv
            cv_grp = I.make_grouped_cv(gtr)
            def cv_rec3(X_, y_, mf, k=3, seed=0): return cv_rec(X_, y_, mf, k=3, seed=seed)
            def cv_grp3(X_, y_, mf, k=3, seed=0): return cv_grp(X_, y_, mf, k=3, seed=seed)
            lists["bpso_recordwise"] = I.bpso_select(Xtr, ytr, model_fn, cv_rec3, seed=seed, inner_seed=seed, **PSO)[0]
            lists["bpso_personwise"] = I.bpso_select(Xtr, ytr, model_fn, cv_grp3, seed=seed, inner_seed=seed, **PSO)[0]
            brng = np.random.default_rng(seed + 7)
            for arm, m in lists.items():
                m = np.asarray(m, bool)
                size = int(m.sum())
                mae = fit_eval(Xtr[:, m], ytr, Xte[:, m], yte)
                rs, rmae, rq1, rq3 = random_baseline(size, d, code_idx, Xtr, ytr, Xte, yte, brng)
                rows.append(dict(code_seed=code_seed, rep=rep, fold=fi, arm=arm, size=size,
                                 code_share=float(m[code_idx].sum() / size), code_share_random=rs,
                                 real_attr_share=float(m[real_idx].sum() / size),
                                 mae=mae, mae_random=rmae, mae_random_q1=rq1, mae_random_q3=rq3,
                                 selected=[names[j] for j in np.where(m)[0]]))
            full = np.ones(d, bool); voice_only = np.zeros(d, bool); voice_only[:len(voice)] = True
            rows.append(dict(code_seed=code_seed, rep=rep, fold=fi, arm="all_features", size=d,
                             code_share=6 / d, mae=fit_eval(Xtr, ytr, Xte, yte)))
            rows.append(dict(code_seed=code_seed, rep=rep, fold=fi, arm="voice_only", size=len(voice),
                             code_share=0.0, mae=fit_eval(Xtr[:, voice_only], ytr, Xte[:, voice_only], yte)))
            jac = I.jaccard(np.asarray(lists["bpso_recordwise"], bool), np.asarray(lists["bpso_personwise"], bool))
            rows.append(dict(code_seed=code_seed, rep=rep, fold=fi, arm="jaccard_bpso_rec_vs_person", value=float(jac)))
            print(f"seed{code_seed} rep{rep} fold{fi} done {time.time()-t0:.0f}s", flush=True)

json.dump(dict(rows=rows, runtime_s=time.time() - t0), open(f"{OUT}/results_realid.json", "w"), indent=1)

# summary
import collections
agg = collections.defaultdict(list)
for r in rows:
    agg[r["arm"]].append(r)
out = ["| arm | size | code share | random code share (same size) | age/sex share | external MAE | random-list MAE (same size) |", "|---|---|---|---|---|---|---|"]
for arm, rr in agg.items():
    if arm.startswith("jaccard"):
        continue
    f = lambda k: np.mean([r[k] for r in rr if k in r]) if any(k in r for r in rr) else float("nan")
    rng_ = lambda k: (min(r[k] for r in rr), max(r[k] for r in rr))
    out.append(f"| {arm} | {f('size'):.1f} | {f('code_share'):.3f} (range {rng_('code_share')[0]:.2f}–{rng_('code_share')[1]:.2f}) | "
               f"{f('code_share_random'):.3f} | {f('real_attr_share'):.3f} | {f('mae'):.2f} (range {rng_('mae')[0]:.2f}–{rng_('mae')[1]:.2f}) | {f('mae_random'):.2f} |")
jj = [r["value"] for r in agg["jaccard_bpso_rec_vs_person"]]
out.append(f"\nJaccard BPSO record-wise vs person-wise (same outer fold): mean {np.mean(jj):.2f}, range {min(jj):.2f}–{max(jj):.2f}")
same = all(r1["selected"] == r2["selected"] for r1, r2 in zip(agg["spearman_top6"], agg["spearman_top6"]))
out.append(f"Runtime {time.time()-t0:.0f}s; rows={len(y)}, subjects=42, d={d}.")
open(f"{OUT}/summary_realid.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
