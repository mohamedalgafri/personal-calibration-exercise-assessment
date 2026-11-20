"""Pilot 4 (see ../PLAN4.md, written and hashed before downloading HAA/SQZ).
Reuses loading/features/model code of run_phytmo.py unchanged (exec of its top part).
Usage: python3 -P run_pilot4.py <raw_dir> <out_dir> [exercises]"""
import sys, os, io, json, time, contextlib, collections
import numpy as np

RAW, OUT = sys.argv[1], sys.argv[2]
EXS = sys.argv[3:] or ["HAA", "SQZ"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_phytmo.py")).read()
src = src.split("# ---------------- experiment ----------------")[0]
g = {"__name__": "rp", "__file__": "run_phytmo.py"}
sys.argv = [sys.argv[0], RAW, OUT]
exec(compile(src, "run_phytmo.py", "exec"), g)
load_recordings, features, LogReg, finetune, bal_acc, C, BAD = (g[k] for k in
    ["load_recordings", "features", "LogReg", "finetune", "bal_acc", "C", "BAD"])
t0 = time.time()
BUDGETS, FS = [8, 16], [0.0, 0.25, 0.5, 0.75]
N_SESS, SESS_LEN = 30, 40
os.makedirs(OUT, exist_ok=True)
report, summary = [], {}

for ex in EXS:
    # HAA is unilateral like KFE: load_recordings handles the moving-leg rule only for names starting with KFE,
    # so we apply the same rule here explicitly.
    rec = collections.defaultdict(dict)
    import glob, re
    pat = re.compile(r"([A-E])(\d\d)([A-Z]{3})([LR]?)([01])_(\d)\.csv$")
    for f in glob.glob(os.path.join(RAW, "inertial", "*", "*", "*", f"*{ex}*.csv")):
        m = pat.search(f)
        if not m or m.group(3) != ex:
            continue
        gg, nn, _, leg, P, S = m.groups()
        seg = f.split(os.sep)[-2]
        if ex == "HAA" and seg[0] != leg:
            continue
        A = np.genfromtxt(f, delimiter=",", skip_header=1, usecols=range(1, 7))
        if not np.isfinite(A).all():
            BAD.append(f); continue
        rec[(gg + nn, leg, int(P), int(S))][seg[1:] if ex == "HAA" else seg] = A
    need = 2 if ex == "HAA" else 4
    W = {k: features(v)[0] for k, v in rec.items() if len(v) >= need}
    persons = sorted({k[0] for k in W})
    persons = [p for p in persons if all(any(k[0] == p and k[2] == P and k[3] == S for k in W) for P in (0, 1) for S in (1, 2))]
    report.append(f"{ex}: recordings with all sensors={len(W)}, persons with all four series={len(persons)}, "
                  f"excluded files so far={len(BAD)}")
    print(report[-1], flush=True)

    def stack(p, S):
        Xs, ys = [], []
        for k, F in sorted(W.items()):
            if k[0] == p and k[3] == S:
                Xs.append(F); ys.append(np.full(len(F), k[2]))
        return np.vstack(Xs), np.concatenate(ys)

    data = {p: {S: stack(p, S) for S in (1, 2)} for p in persons}
    rows = []
    for rep in range(2):
        perm = np.random.default_rng(3000 + rep).permutation(persons)
        for fi in range(5):
            test_p = set(perm[fi::5]); train_p = [p for p in persons if p not in test_p]
            Xtr = np.vstack([data[p][S][0] for p in train_p for S in (1, 2)])
            ytr = np.concatenate([data[p][S][1] for p in train_p for S in (1, 2)])
            gen = LogReg().fit(Xtr, ytr)
            srng = np.random.default_rng(4000 + 10 * rep + fi)
            sub = srng.choice(len(ytr), min(1500, len(ytr)), replace=False)
            src_ctrl = g["LogReg"](iters=60, lr=0.02); src_ctrl.mu, src_ctrl.sd = gen.mu, gen.sd
            src_ctrl.fit(Xtr[sub], ytr[sub], np.ones(len(sub)), init=(gen.W, gen.b), keep_scaler=True)
            for p in sorted(test_p):
                X1, y1 = data[p][1]; X2, y2 = data[p][2]
                std_i, dev_i = np.where(y1 == 0)[0], np.where(y1 == 1)[0]
                models = {"GEN": gen, "SRC": src_ctrl}
                short = []
                for B in BUDGETS:
                    for f in FS:
                        nd = int(round(f * B)); ns = B - nd
                        cal = np.concatenate([std_i[:ns], dev_i[:nd]])
                        if len(std_i) < ns or len(dev_i) < nd:
                            short.append((B, f))
                        models[f"B{B}_f{f}"] = finetune(gen, np.vstack([Xtr[sub], X1[cal]]), np.concatenate([ytr[sub], y1[cal]]),
                                                       np.concatenate([np.ones(len(sub)), np.full(len(cal), 20.0)]))
                c_idx, w_idx = np.where(y2 == 0)[0], np.where(y2 == 1)[0]
                sess = []
                for s in range(N_SESS):
                    nc = int(round(srng.random() * SESS_LEN))
                    sess.append((nc / SESS_LEN, np.concatenate([srng.choice(c_idx, nc), srng.choice(w_idx, SESS_LEN - nc)])))
                for m, mod in models.items():
                    pr = mod.pred(X2)
                    err = float(np.mean([abs((1 - pr[idx].mean()) - tc) for tc, idx in sess]))
                    rows.append(dict(rep=rep, fold=fi, person=p, method=m, bal_acc=bal_acc(pr, y2), sess_err=err, short=short))
            print(f"  {ex} rep{rep} fold{fi} {time.time()-t0:.0f}s", flush=True)
    summary[ex] = dict(persons=persons, rows=rows)

summary["_excluded_files_nonfinite"] = BAD
json.dump(summary, open(f"{OUT}/results_pilot4.json", "w"))
out = [f"# Pilot 4 results (plan PLAN4.md, sha256 5d1f22f7…c552). Runtime {time.time()-t0:.0f}s", ""] + report + [""]
for ex in EXS:
    R = summary[ex]["rows"]
    def fm(m, k, rp, f): return np.mean([r[k] for r in R if r["method"] == m and r["rep"] == rp and r["fold"] == f])
    def mean(m, k): return np.mean([r[k] for r in R if r["method"] == m])
    out += [f"## {ex} ({len(summary[ex]['persons'])} persons)", "",
            "| method | balanced accuracy | simulated-session error (pts) | folds > SRC (bal. acc) |", "|---|---|---|---|"]
    for m in ["GEN", "SRC"] + [f"B{B}_f{f}" for B in BUDGETS for f in FS]:
        w = "-" if m in ("GEN", "SRC") else sum(fm(m, "bal_acc", rp, f) > fm("SRC", "bal_acc", rp, f) for rp in range(2) for f in range(5))
        out.append(f"| {m} | {mean(m,'bal_acc'):.3f} | {100*mean(m,'sess_err'):.1f} | {w} |")
    out.append("")
    for B in BUDGETS:
        wins = sum(fm(f"B{B}_f0.5", "bal_acc", rp, f) > fm(f"B{B}_f0.0", "bal_acc", rp, f) for rp in range(2) for f in range(5))
        per = collections.defaultdict(dict)
        for r in R:
            per[r["person"]].setdefault(r["method"], []).append(r["bal_acc"])
        better = sum(np.mean(v[f"B{B}_f0.5"]) > np.mean(v[f"B{B}_f0.0"]) for v in per.values())
        out.append(f"- **H1, budget {B}:** f=0.5 > f=0 in {wins}/10 folds; persons {better}/{len(per)}.")
    out.append(f"- **H2:** SRC − GEN balanced accuracy = {mean('SRC','bal_acc') - mean('GEN','bal_acc'):+.4f}.")
    sh = sum(1 for r in R if r["short"] and r["method"] == "GEN")
    out.append(f"- Short calibration pools (person×fold cases): {sh}.")
    out.append("")
open(f"{OUT}/summary_pilot4.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
