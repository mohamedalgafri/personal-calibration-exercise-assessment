"""Pilot 3 (see ../PLAN3.md, written before looking at data values).
Usage: python3 -P run_phytmo.py <raw_dir (contains inertial/)> <out_dir> [exercises...]
numpy only."""
import sys, os, re, glob, json, time, collections
import numpy as np

RAW, OUT = sys.argv[1], sys.argv[2]
EXS = sys.argv[3:] or ["SQT", "KFE", "EFE"]
t0 = time.time()
BAD = []
pat = re.compile(r"([A-E])(\d\d)([A-Z]{3})([LR]?)([01])_(\d)\.csv$")
FS, WIN, STEP = 100, 200, 100
C = 2  # 0 = correct, 1 = wrong


# ---------------- loading & features ----------------
def load_recordings(ex):
    legf = None
    if "-" in ex:  # POST-HOC variant, e.g. KFE-L: one leg only
        ex, legf = ex.split("-")
    rec = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(RAW, "inertial", "*", "*", "*", f"*{ex.split(chr(45))[0]}*.csv")):
        m = pat.search(f)
        if not m or m.group(3) != ex.split("-")[0]:
            continue
        g, nn, _, leg, P, S = m.groups()
        seg = f.split(os.sep)[-2]
        if ex == "KFE" and seg[0] != leg:
            continue
        if legf and leg != legf:
            continue
        A = np.genfromtxt(f, delimiter=",", skip_header=1, usecols=range(1, 7))  # gyro xyz, acc xyz
        if not np.isfinite(A).all():  # data-quality rule added after a bug (NaN in C02 KFE-L files): drop the recording
            BAD.append(f); continue
        sname = seg[1:] if ex.startswith("KFE") else seg  # KFE: side-agnostic (moving leg only); others: keep L/R
        rec[(g + nn, leg, int(P), int(S))][sname] = A
    return rec


def features(sensors):
    names = sorted(sensors)
    n = min(len(sensors[s]) for s in names)
    a, b = int(0.25 * n), int(0.95 * n)
    chans = []
    for s in names:
        A = sensors[s][a:b]
        gy, ac = A[:, :3], A[:, 3:]
        chans += [gy, np.linalg.norm(gy, axis=1, keepdims=True), ac, np.linalg.norm(ac, axis=1, keepdims=True)]
    X = np.hstack(chans)  # (T, 8 * n_sensors)
    rows = []
    for st in range(0, len(X) - WIN + 1, STEP):
        w = X[st:st + WIN]
        rows.append(np.concatenate([w.mean(0), w.std(0), w.min(0), w.max(0), w.max(0) - w.min(0),
                                    np.abs(np.diff(w, axis=0)).mean(0)]))
    return np.array(rows), names


# ---------------- model ----------------
def softmax(Z):
    Z = Z - Z.max(1, keepdims=True); E = np.exp(Z); return E / E.sum(1, keepdims=True)


class LogReg:
    def __init__(self, l2=1e-2, iters=400, lr=0.05):
        self.l2, self.iters, self.lr = l2, iters, lr

    def fit(self, X, y, w=None, init=None, keep_scaler=False):
        if not keep_scaler:
            self.mu = X.mean(0); self.sd = X.std(0); self.sd[self.sd < 1e-9] = 1.0
        Z = (X - self.mu) / self.sd; n, d = Z.shape; Y = np.eye(C)[y]
        w = np.ones(n) if w is None else w; ws = w.sum()
        W, b = (np.zeros((d, C)), np.zeros(C)) if init is None else (init[0].copy(), init[1].copy())
        mW = np.zeros_like(W); vW = np.zeros_like(W); mb = np.zeros(C); vb = np.zeros(C)
        for t in range(1, self.iters + 1):
            G = (softmax(Z @ W + b) - Y) * w[:, None] / ws
            gW = Z.T @ G + self.l2 * W; gb = G.sum(0)
            mW = .9 * mW + .1 * gW; vW = .999 * vW + .001 * gW ** 2; mb = .9 * mb + .1 * gb; vb = .999 * vb + .001 * gb ** 2
            W -= self.lr * (mW / (1 - .9 ** t)) / (np.sqrt(vW / (1 - .999 ** t)) + 1e-8)
            b -= self.lr * (mb / (1 - .9 ** t)) / (np.sqrt(vb / (1 - .999 ** t)) + 1e-8)
        self.W, self.b = W, b
        return self

    def pred(self, X):
        return (((X - self.mu) / self.sd) @ self.W + self.b).argmax(1)


def finetune(base, X, y, w):
    m = LogReg(iters=60, lr=0.02); m.mu, m.sd = base.mu, base.sd
    return m.fit(X, y, w, init=(base.W, base.b), keep_scaler=True)


def bal_acc(p, y):
    return float(np.mean([(p[y == c] == c).mean() for c in range(C) if (y == c).any()]))


def acc_share(cc_wrong, M):
    """binary adjusted count: M[i,j] = P(pred=i | true=j); returns estimated share of class 1 (wrong)."""
    tpr, fpr = M[1, 1], M[1, 0]
    if tpr - fpr < 1e-6:
        return cc_wrong
    return float(np.clip((cc_wrong - fpr) / (tpr - fpr), 0, 1))


def confusion(p, y):
    M = np.zeros((C, C))
    for j in range(C):
        if (y == j).any():
            M[:, j] = np.bincount(p[y == j], minlength=C) / (y == j).sum()
        else:
            M[j, j] = 1
    return M


# ---------------- experiment ----------------
KS = [3, 5, 10, "all"]
N_SESS, SESS_LEN = 30, 40
summary = {}
for ex in EXS:
    rec = load_recordings(ex)
    W = {}  # (person, leg, P, S) -> features
    for key, sens in rec.items():
        need = 2 if ex.startswith("KFE") else 4
        if len(sens) < need:
            continue
        W[key] = features(sens)[0]
    persons = sorted({k[0] for k in W})
    # keep persons with all four series (P0/P1 x S1/S2)
    persons = [p for p in persons if all(any(k[0] == p and k[2] == P and k[3] == S for k in W) for P in (0, 1) for S in (1, 2))]
    print(f"{ex}: recordings={len(W)} persons_complete={len(persons)} {time.time()-t0:.0f}s", flush=True)

    def stack(p, S):
        Xs, ys = [], []
        for k, F in sorted(W.items()):
            if k[0] == p and k[3] == S:
                Xs.append(F); ys.append(np.full(len(F), k[2]))
        return np.vstack(Xs), np.concatenate(ys)

    data = {p: {S: stack(p, S) for S in (1, 2)} for p in persons}
    rows = []
    for rep in range(2):
        rng = np.random.default_rng(3000 + rep)
        perm = rng.permutation(persons)
        for fi in range(5):
            test_p = perm[fi::5]; train_p = [p for p in persons if p not in set(test_p)]
            Xtr = np.vstack([data[p][S][0] for p in train_p for S in (1, 2)])
            ytr = np.concatenate([data[p][S][1] for p in train_p for S in (1, 2)])
            gen = LogReg().fit(Xtr, ytr)
            srng = np.random.default_rng(4000 + 10 * rep + fi)
            sub = srng.choice(len(ytr), min(1500, len(ytr)), replace=False)
            for p in test_p:
                X1, y1 = data[p][1]; X2, y2 = data[p][2]
                models = {"GEN": gen}
                for k in KS:
                    if k == "all":
                        cal = np.arange(len(y1))
                    else:
                        cal = np.concatenate([np.where(y1 == c)[0][:k] for c in range(C)])
                    models[f"CAL-{k}"] = finetune(gen, np.vstack([Xtr[sub], X1[cal]]), np.concatenate([ytr[sub], y1[cal]]),
                                                  np.concatenate([np.ones(len(sub)), np.full(len(cal), 20.0)]))
                for k in (5, 10):
                    calc = np.where(y1 == 0)[0][:k]
                    models[f"CALC-{k}"] = finetune(gen, np.vstack([Xtr[sub], X1[calc]]), np.concatenate([ytr[sub], y1[calc]]),
                                                   np.concatenate([np.ones(len(sub)), np.full(len(calc), 20.0)]))
                models["PERS-all"] = LogReg().fit(X1, y1)
                M_pers = confusion(gen.pred(X1), y1)
                preds = {m: mod.pred(X2) for m, mod in models.items()}
                c_idx, w_idx = np.where(y2 == 0)[0], np.where(y2 == 1)[0]
                sess = []
                for s in range(N_SESS):
                    pi = srng.random(); nc = int(round(pi * SESS_LEN))
                    idx = np.concatenate([srng.choice(c_idx, nc), srng.choice(w_idx, SESS_LEN - nc)])
                    sess.append((nc / SESS_LEN, idx))
                for m, pr in preds.items():
                    errs, flags = [], []
                    for true_c, idx in sess:
                        est_c = 1 - pr[idx].mean()
                        errs.append(abs(est_c - true_c)); flags.append((est_c < .5) == (true_c < .5))
                    rows.append(dict(rep=rep, fold=fi, person=p, method=m, bal_acc=bal_acc(pr, y2),
                                     sess_err=float(np.mean(errs)), flag_acc=float(np.mean(flags))))
                errs, flags = [], []
                for true_c, idx in sess:
                    est_c = 1 - acc_share(preds["GEN"][idx].mean(), M_pers)
                    errs.append(abs(est_c - true_c)); flags.append((est_c < .5) == (true_c < .5))
                rows.append(dict(rep=rep, fold=fi, person=p, method="GEN+personalACC", bal_acc=float("nan"),
                                 sess_err=float(np.mean(errs)), flag_acc=float(np.mean(flags))))
            print(f"  {ex} rep{rep} fold{fi} {time.time()-t0:.0f}s", flush=True)
    summary[ex] = dict(persons=persons, n_windows={p: [int(len(data[p][S][1])) for S in (1, 2)] for p in persons}, rows=rows)

summary["_excluded_files_nonfinite"] = BAD
json.dump(summary, open(f"{OUT}/results_phytmo.json", "w"))
METHODS = ["GEN", "CAL-3", "CAL-5", "CAL-10", "CAL-all", "CALC-5", "CALC-10", "PERS-all", "GEN+personalACC"]
out = [f"# Pilot 3 results (PHYTMO; plan PLAN3.md). Runtime {time.time()-t0:.0f}s", "",
       "Window = 2 s (step 1 s). CAL-k = first k windows of each class (correct, wrong) from the person's series 1 (≈ k+1 s of each). Evaluation on series 2 only.",
       "Session error = |estimated − true share of correct movement| in percentage points (40-window sessions, true share uniform 0–100%).", ""]
out.append(f"Excluded recordings with missing values (data-quality rule): {len(BAD)} files: " + ", ".join(os.path.basename(b) for b in BAD) + "")
out.append("")
for ex, S in summary.items():
    if ex.startswith("_"):
        continue
    R = S["rows"]
    out += [f"## {ex} ({len(S['persons'])} persons)", "",
            "| method | balanced accuracy (new people) | session error (pp) | 'mostly wrong' flag correct | worst person: bal. acc / session err | folds better than GEN (bal. acc / session) |",
            "|---|---|---|---|---|---|"]
    for m in METHODS:
        rr = [r for r in R if r["method"] == m]
        if not rr:
            continue
        per = collections.defaultdict(list)
        for r in rr:
            per[r["person"]].append(r)
        ba = np.nanmean([r["bal_acc"] for r in rr]) if m != "GEN+personalACC" else float("nan")
        worst_ba = min(np.mean([r["bal_acc"] for r in v]) for v in per.values()) if m != "GEN+personalACC" else float("nan")
        worst_se = max(np.mean([r["sess_err"] for r in v]) for v in per.values())

        def fm(mm, key, rp, f):
            return np.mean([r[key] for r in R if r["method"] == mm and r["rep"] == rp and r["fold"] == f])
        if m == "GEN":
            wins = "-"
        else:
            wb = "-" if m == "GEN+personalACC" else sum(fm(m, "bal_acc", rp, f) > fm("GEN", "bal_acc", rp, f) for rp in range(2) for f in range(5))
            ws = sum(fm(m, "sess_err", rp, f) < fm("GEN", "sess_err", rp, f) for rp in range(2) for f in range(5))
            wins = f"{wb} / {ws}"
        out.append(f"| {m} | {ba:.3f} | {100*np.mean([r['sess_err'] for r in rr]):.1f} | {100*np.mean([r['flag_acc'] for r in rr]):.0f}% | "
                   f"{worst_ba:.2f} / {100*worst_se:.0f} | {wins} |")
    out.append("")
    out.append("Exploratory (Addendum A): balanced accuracy by age group (A=20s … E=60s), GEN vs CAL-10:")
    for g in "ABCDE":
        gg = [r for r in R if r["person"].startswith(g)]
        if gg:
            out.append(f"- {g}: n={len({r['person'] for r in gg})}, GEN {np.mean([r['bal_acc'] for r in gg if r['method']=='GEN']):.3f}, CAL-10 {np.mean([r['bal_acc'] for r in gg if r['method']=='CAL-10']):.3f}")
    out.append("")
open(f"{OUT}/summary_phytmo.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
