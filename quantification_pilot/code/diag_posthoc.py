"""POST-HOC diagnostic (written AFTER seeing results of run_quant.py; exploratory, not pre-registered).
Question: is the activity-time error for new people driven by person-specific confusion (violation of the
label-shift assumption P(x|y) equal across people) rather than by prior shift?
For each held-out person (rep 0, 5 folds): compare the person's own confusion matrix with the training (inner-CV)
confusion matrix; compute 'oracle ACC' (ACC using the person's own confusion matrix) as an upper bound.
Also: same comparison with a WEAKER classifier (only 20 randomly chosen features) to see whether corrections help
when window accuracy is lower.
Usage: PYTHONPATH=<code dir> python3 -P diag_posthoc.py <zip> <out_dir>"""
import sys, json, io, contextlib
import numpy as np
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2]]
ZIP, OUT = sys.argv[1], sys.argv[2]
# reuse loaders/models from run_quant without running its experiment: exec the top part only
src = open(__file__.replace("diag_posthoc.py", "run_quant.py")).read().split("# ---------------- experiment ----------------")[0]
g = {"__name__": "rq", "__file__": "run_quant.py"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "run_quant.py", "exec"), g)
X, y, subj, persons, C = g["X"], g["y"], g["subj"], g["persons"], g["C"]
LogReg, person_folds, adjust, emq, ae = g["LogReg"], g["person_folds"], g["adjust"], g["emq"], g["ae"]

res = {}
frng = np.random.default_rng(7)
weak_feats = np.sort(frng.choice(X.shape[1], 20, replace=False))
for variant, cols in [("full_561", np.arange(X.shape[1])), ("weak_20", weak_feats)]:
    Xv = X[:, cols]
    rows = []
    orng = np.random.default_rng(2026)  # same person partition as rep 0 of run_quant
    for fi, test_p in enumerate(person_folds(persons, 5, orng)):
        te = np.isin(subj, test_p); tr = ~te
        Xtr, ytr, gtr = Xv[tr], y[tr], subj[tr]
        Pin = np.zeros((tr.sum(), C)); irng = np.random.default_rng(fi)
        for ip in person_folds(np.unique(gtr), 5, irng):
            m = np.isin(gtr, ip); Pin[m] = LogReg().fit(Xtr[~m], ytr[~m]).proba(Xtr[m])
        M = np.zeros((C, C))
        for j in range(C):
            M[:, j] = np.bincount(Pin[ytr == j].argmax(1), minlength=C) / (ytr == j).sum()
        prior = np.bincount(ytr, minlength=C) / len(ytr)
        P = LogReg().fit(Xtr, ytr).proba(Xv[te]); yte, ste = y[te], subj[te]
        for p in test_p:
            k = ste == p; Pp, yp = P[k], yte[k]
            true = np.bincount(yp, minlength=C) / len(yp)
            cc = np.bincount(Pp.argmax(1), minlength=C) / len(yp)
            Mp = np.zeros((C, C))
            for j in range(C):
                if (yp == j).any():
                    Mp[:, j] = np.bincount(Pp[yp == j].argmax(1), minlength=C) / (yp == j).sum()
            rows.append(dict(fold=fi, person=int(p), acc=float((Pp.argmax(1) == yp).mean()),
                             conf_diff=float(np.abs(Mp - M).mean()),
                             AE_train_prior=ae(prior, true), AE_CC=ae(cc, true), AE_ACC=ae(adjust(M, cc), true),
                             AE_EMQ=ae(emq(Pp, prior), true), AE_oracleACC=ae(adjust(Mp, cc), true)))
        print(variant, "fold", fi, flush=True)
    res[variant] = rows

out = ["# POST-HOC diagnostic (exploratory; written after seeing the pilot results)", "",
       "Natural recordings, rep 0 (30 held-out persons). AE = mean absolute error of the 6-class proportions; ×480 = minutes per class per 8 h.", "",
       "| classifier | window acc. | mean |own − training confusion| | train prior | CC | ACC | EMQ | oracle ACC (person's own confusion) | corr(CC error, confusion diff) |",
       "|---|---|---|---|---|---|---|---|---|"]
for v, rows in res.items():
    f = lambda k: np.mean([r[k] for r in rows])
    c = np.corrcoef([r["AE_CC"] for r in rows], [r["conf_diff"] for r in rows])[0, 1]
    out.append(f"| {v} | {f('acc'):.3f} | {f('conf_diff'):.4f} | {f('AE_train_prior'):.4f} | {f('AE_CC'):.4f} ({f('AE_CC')*480:.1f} min) | "
               f"{f('AE_ACC'):.4f} | {f('AE_EMQ'):.4f} | {f('AE_oracleACC'):.4f} | {c:.2f} |")
    worst = sorted(rows, key=lambda r: -r["AE_CC"])[:3]
    out.append(f"|  worst 3 persons (CC) | " + "; ".join(f"p{r['person']}: acc {r['acc']:.2f}, CC {r['AE_CC']*480:.0f} min, oracle {r['AE_oracleACC']*480:.0f} min" for r in worst) + " | | | | | | | |")
json.dump(res, open(f"{OUT}/diag_posthoc.json", "w"), indent=1)
open(f"{OUT}/diag_posthoc.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
