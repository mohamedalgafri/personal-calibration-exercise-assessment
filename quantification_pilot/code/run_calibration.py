"""Step 2: short personal calibration (see ../PLAN2_calibration.md, written before running).
Usage: PYTHONPATH=<code dir> python3 -P run_calibration.py <zip> <out_dir>"""
import sys, io, json, time, contextlib
import numpy as np
ZIP, OUT = sys.argv[1], sys.argv[2]
src = open(__file__.replace("run_calibration.py", "run_quant.py")).read().split("# ---------------- experiment ----------------")[0]
g = {"__name__": "rq"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "run_quant.py", "exec"), g)
X, y, subj, persons, C = g["X"], g["y"], g["subj"], g["persons"], g["C"]
LogReg, person_folds, adjust, ae, softmax = g["LogReg"], g["person_folds"], g["adjust"], g["ae"], g["softmax"]
t0 = time.time()
KS = [3, 5, 10, 20]
M_SHRINK = 10
N_SAMPLE, PER_PERSON = 300, 20


def finetune(base, Xa, ya, wa, steps=60, lr=0.02):
    """warm-start Adam fine-tuning of base LogReg on weighted data (base standardisation kept)."""
    Z = (Xa - base.mu) / base.sd; Y = np.eye(C)[ya]; wsum = wa.sum()
    W = base.W.copy(); b = base.b.copy()
    mW = np.zeros_like(W); vW = np.zeros_like(W); mb = np.zeros(C); vb = np.zeros(C)
    for t in range(1, steps + 1):
        G = (softmax(Z @ W + b) - Y) * wa[:, None] / wsum
        gW = Z.T @ G + base.l2 * W; gb = G.sum(0)
        mW = .9 * mW + .1 * gW; vW = .999 * vW + .001 * gW ** 2; mb = .9 * mb + .1 * gb; vb = .999 * vb + .001 * gb ** 2
        W -= lr * (mW / (1 - .9 ** t)) / (np.sqrt(vW / (1 - .999 ** t)) + 1e-8)
        b -= lr * (mb / (1 - .9 ** t)) / (np.sqrt(vb / (1 - .999 ** t)) + 1e-8)
    m = LogReg(); m.mu, m.sd, m.W, m.b, m.l2 = base.mu, base.sd, W, b, base.l2
    return m


def confusion(pred, yy):
    M = np.zeros((C, C))
    for j in range(C):
        if (yy == j).any():
            M[:, j] = np.bincount(pred[yy == j], minlength=C) / (yy == j).sum()
        else:
            M[j, j] = 1.0
    return M


rows = []
for rep in range(2):
    orng = np.random.default_rng(2026 + rep)
    for fi, test_p in enumerate(person_folds(persons, 5, orng)):
        te = np.isin(subj, test_p); tr = ~te
        Xtr, ytr, gtr = X[tr], y[tr], subj[tr]
        Pin = np.zeros((tr.sum(), C)); irng = np.random.default_rng(100 * rep + fi)
        for ip in person_folds(np.unique(gtr), 5, irng):
            m = np.isin(gtr, ip); Pin[m] = LogReg().fit(Xtr[~m], ytr[~m]).proba(Xtr[m])
        M_train = confusion(Pin.argmax(1), ytr)
        base = LogReg().fit(Xtr, ytr)
        srng = np.random.default_rng(20_000 + 100 * rep + fi)
        sub = srng.choice(len(ytr), 1500, replace=False)
        for p in test_p:
            idx = np.where(subj == p)[0]  # file order = recording order within person
            for k in KS:
                cal, drop = [], set()
                for c in range(C):
                    ic = idx[y[idx] == c]
                    cal.extend(ic[:k]); drop.update(ic[k:k + 1].tolist())
                cal = np.array(cal)
                pool = np.array([i for i in idx if i not in set(cal.tolist()) and i not in drop])
                Pc = base.proba(X[cal]).argmax(1)
                M_pers = confusion(Pc, y[cal])
                M_shr = (k * M_pers + M_SHRINK * M_train) / (k + M_SHRINK)
                ft = finetune(base, np.vstack([Xtr[sub], X[cal]]), np.concatenate([ytr[sub], y[cal]]),
                              np.concatenate([np.ones(len(sub)), np.full(len(cal), 20.0)]))
                pred_base = base.proba(X[pool]).argmax(1); pred_ft = ft.proba(X[pool]).argmax(1); ypool = y[pool]

                def est(sel):
                    n = len(sel)
                    cc = np.bincount(pred_base[sel], minlength=C) / n
                    return {"CC": cc, "ACC_train": adjust(M_train, cc), "ACC_personal": adjust(M_pers, cc),
                            "ACC_shrink": adjust(M_shr, cc), "FT_CC": np.bincount(pred_ft[sel], minlength=C) / n}

                allsel = np.arange(len(pool))
                true = np.bincount(ypool, minlength=C) / len(pool)
                for mth, v in est(allsel).items():
                    rows.append(dict(cond="natural", rep=rep, fold=fi, person=int(p), k=k, method=mth, AE=ae(v, true)))
                by_c = [np.where(ypool == c)[0] for c in range(C)]
                avail = np.array([len(b) > 0 for b in by_c])
                for s in range(PER_PERSON):
                    tgt = srng.dirichlet(np.ones(C)) * avail; tgt /= tgt.sum()
                    cnt = srng.multinomial(N_SAMPLE, tgt)
                    sel = np.concatenate([srng.choice(by_c[c], cnt[c]) for c in range(C) if cnt[c] > 0])
                    tr_ = cnt / N_SAMPLE
                    for mth, v in est(sel).items():
                        rows.append(dict(cond="shifted", rep=rep, fold=fi, person=int(p), k=k, method=mth, AE=ae(v, tr_)))
        print(f"rep{rep} fold{fi} {time.time()-t0:.0f}s", flush=True)

json.dump(dict(rows=rows, runtime_s=time.time() - t0), open(f"{OUT}/results_calibration.json", "w"))
METHODS = ["CC", "ACC_train", "ACC_personal", "ACC_shrink", "FT_CC"]
out = [f"# Step 2: short personal calibration (UCI HAR, plan PLAN2_calibration.md). Runtime {time.time()-t0:.0f}s", "",
       "AE = mean absolute error of the 6-class proportions; min = AE×480 (minutes per activity per 8 h). Folds better than CC of 10.", ""]
for cond in ["natural", "shifted"]:
    out += [f"## {cond}", "", "| k (windows per activity ≈ seconds) | " + " | ".join(METHODS) + " |", "|---" * (len(METHODS) + 1) + "|"]
    for k in KS:
        R = [r for r in rows if r["cond"] == cond and r["k"] == k]
        cells = []
        for m in METHODS:
            a = np.mean([r["AE"] for r in R if r["method"] == m])
            fm = lambda mm, rp, f: np.mean([r["AE"] for r in R if r["method"] == mm and r["rep"] == rp and r["fold"] == f])
            wins = sum(fm(m, rp, f) < fm("CC", rp, f) for rp in range(2) for f in range(5))
            extra = ""
            if cond == "natural":
                per = {}
                for r in R:
                    if r["method"] == m:
                        per.setdefault(r["person"], []).append(r["AE"])
                extra = f", worst person {max(np.mean(v) for v in per.values())*480:.0f} min"
            cells.append(f"{a:.4f} ({a*480:.1f} min{extra}){'' if m == 'CC' else f' [{wins}/10]'}")
        out.append(f"| {k} (≈{(k+1)*1.28:.0f} s) | " + " | ".join(cells) + " |")
    out.append("")
open(f"{OUT}/summary_calibration.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
