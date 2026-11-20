"""Pilot: activity-time quantification for NEW people on UCI HAR (see ../PLAN.md, written before running).
Usage: PYTHONPATH=<this dir> python3 -P run_quant.py <uci_har.zip> <out_dir>
numpy only."""
import sys, io, json, time, zipfile
import numpy as np

ZIP, OUT = sys.argv[1], sys.argv[2]
t0 = time.time()
CLASSES = ["WALKING", "UPSTAIRS", "DOWNSTAIRS", "SITTING", "STANDING", "LAYING"]
GROUPS = {"ambulatory": [0, 1, 2], "standing": [4], "sedentary": [3, 5]}
C = 6


# ---------------- data ----------------
def open_inner(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    if not any(n.endswith("X_train.txt") for n in names):
        inner = [n for n in names if n.endswith(".zip") and "MACOSX" not in n][0]
        z = zipfile.ZipFile(io.BytesIO(z.read(inner)))
    return z


def load(z, part):
    def get(suffix):
        n = [m for m in z.namelist() if m.endswith(f"{part}/{suffix}_{part}.txt") and "MACOSX" not in m][0]
        return z.read(n).decode()
    X = np.loadtxt(io.StringIO(get("X")))
    y = np.loadtxt(io.StringIO(get("y"))).astype(int) - 1
    s = np.loadtxt(io.StringIO(get("subject"))).astype(int)
    return X, y, s


z = open_inner(ZIP)
Xa, ya, sa = load(z, "train")
Xb, yb, sb = load(z, "test")
X = np.vstack([Xa, Xb]); y = np.concatenate([ya, yb]); subj = np.concatenate([sa, sb])
persons = np.unique(subj)
print(f"windows={len(y)} persons={len(persons)} features={X.shape[1]} load {time.time()-t0:.0f}s", flush=True)


# ---------------- classifier ----------------
def softmax(Z):
    Z = Z - Z.max(1, keepdims=True)
    E = np.exp(Z)
    return E / E.sum(1, keepdims=True)


class LogReg:
    """Multinomial logistic regression, L2, full-batch Adam. Fixed settings, no tuning."""
    def __init__(self, l2=1e-2, iters=400, lr=0.05):
        self.l2, self.iters, self.lr = l2, iters, lr

    def fit(self, X, y):
        self.mu = X.mean(0); self.sd = X.std(0); self.sd[self.sd < 1e-9] = 1.0
        Z = (X - self.mu) / self.sd
        n, d = Z.shape
        Y = np.eye(C)[y]
        W = np.zeros((d, C)); b = np.zeros(C)
        mW = np.zeros_like(W); vW = np.zeros_like(W); mb = np.zeros(C); vb = np.zeros(C)
        b1, b2, eps = 0.9, 0.999, 1e-8
        for t in range(1, self.iters + 1):
            P = softmax(Z @ W + b)
            G = (P - Y) / n
            gW = Z.T @ G + self.l2 * W; gb = G.sum(0)
            mW = b1 * mW + (1 - b1) * gW; vW = b2 * vW + (1 - b2) * gW ** 2
            mb = b1 * mb + (1 - b1) * gb; vb = b2 * vb + (1 - b2) * gb ** 2
            W -= self.lr * (mW / (1 - b1 ** t)) / (np.sqrt(vW / (1 - b2 ** t)) + eps)
            b -= self.lr * (mb / (1 - b1 ** t)) / (np.sqrt(vb / (1 - b2 ** t)) + eps)
        self.W, self.b = W, b
        return self

    def proba(self, X):
        return softmax(((X - self.mu) / self.sd) @ self.W + self.b)


def person_folds(persons, k, rng):
    p = rng.permutation(persons)
    return [p[i::k] for i in range(k)]


# ---------------- quantifiers ----------------
def proj_simplex(v):
    u = np.sort(v)[::-1]; css = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, len(v) + 1) > (css - 1))[0][-1]
    th = (css[rho] - 1) / (rho + 1.0)
    return np.maximum(v - th, 0)


def adjust(M, q, iters=2000):
    """min ||M p - q||^2 over the simplex, projected gradient."""
    p = np.full(C, 1.0 / C)
    L = np.linalg.norm(M, 2) ** 2 + 1e-12
    for _ in range(iters):
        p = proj_simplex(p - (M.T @ (M @ p - q)) / L)
    return p


def emq(P, prior_tr, iters=1000, tol=1e-8):
    p = prior_tr.copy()
    for _ in range(iters):
        R = P * (p / prior_tr)
        R /= R.sum(1, keepdims=True)
        new = R.mean(0)
        if np.abs(new - p).sum() < tol:
            p = new; break
        p = new
    return p


BINS = 10
EDGES = np.linspace(0, 1, BINS + 1)


def hists(P):
    """per-class posterior histograms -> (C, BINS), each row sums to 1."""
    H = np.stack([np.histogram(P[:, c], EDGES)[0] for c in range(C)]).astype(float)
    return H / max(len(P), 1)


def hd_objective(pmat, Hcond, Htest):
    """pmat (m, C) candidate prevalences; Hcond (C_true, C_score, BINS); Htest (C_score, BINS).
    returns mean over score-classes of Hellinger distance between test hist and mixture."""
    mix = np.einsum("mj,jcb->mcb", pmat, Hcond)
    bc = np.sqrt(mix * Htest[None]).sum(2)
    return np.sqrt(np.clip(1 - bc, 0, None)).mean(1)


def pso_simplex(f, rng, n_part=20, n_iter=50, w=0.72, c1=1.49, c2=1.49):
    """continuous PSO over logits, prevalence = softmax(logits). n_part*n_iter evaluations."""
    x = rng.normal(size=(n_part, C)); v = np.zeros_like(x)
    fx = f(softmax(x)); pb = x.copy(); pbf = fx.copy()
    g = pb[pbf.argmin()].copy(); gf = pbf.min()
    for _ in range(n_iter - 1):
        r1, r2 = rng.random(x.shape), rng.random(x.shape)
        v = w * v + c1 * r1 * (pb - x) + c2 * r2 * (g - x)
        x = x + v
        fx = f(softmax(x))
        imp = fx < pbf; pb[imp] = x[imp]; pbf[imp] = fx[imp]
        if pbf.min() < gf:
            gf = pbf.min(); g = pb[pbf.argmin()].copy()
    return softmax(g[None])[0], float(gf)


def random_search(f, rng, budget=1000):
    cand = rng.dirichlet(np.ones(C), size=budget)
    fv = f(cand)
    return cand[fv.argmin()], float(fv.min())


# ---------------- metrics ----------------
def ae(p, q): return float(np.abs(p - q).mean())


def rae(p, q, n):
    e = 1.0 / (2 * n)
    ps = (p + e) / (1 + e * C); qs = (q + e) / (1 + e * C)
    return float((np.abs(ps - qs) / ps).mean())


def kld(p, q, n):
    e = 1.0 / (2 * n)
    ps = (p + e) / (1 + e * C); qs = (q + e) / (1 + e * C)
    return float((ps * np.log(ps / qs)).sum())


def group_ae(p, q):
    return float(np.mean([abs(p[g].sum() - q[g].sum()) for g in GROUPS.values()]))


# ---------------- experiment ----------------
N_SAMPLE, PER_PERSON = 300, 20
METHODS = ["train_prior", "CC", "PCC", "ACC", "PACC", "EMQ", "HDy_PSO", "HDy_random"]
rows, fold_info = [], []
for rep in range(2):
    orng = np.random.default_rng(2026 + rep)
    for fi, test_p in enumerate(person_folds(persons, 5, orng)):
        te = np.isin(subj, test_p); tr = ~te
        Xtr, ytr, gtr = X[tr], y[tr], subj[tr]
        # inner person-grouped CV posteriors for calibration statistics
        Pin = np.zeros((tr.sum(), C))
        irng = np.random.default_rng(100 * rep + fi)
        for ip in person_folds(np.unique(gtr), 5, irng):
            m = np.isin(gtr, ip)
            Pin[m] = LogReg().fit(Xtr[~m], ytr[~m]).proba(Xtr[m])
        pred_in = Pin.argmax(1)
        M_cc = np.zeros((C, C)); M_pcc = np.zeros((C, C)); Hcond = np.zeros((C, C, BINS))
        for j in range(C):
            mj = ytr == j
            M_cc[:, j] = np.bincount(pred_in[mj], minlength=C) / mj.sum()
            M_pcc[:, j] = Pin[mj].mean(0)
            Hcond[j] = hists(Pin[mj])
        prior_tr = np.bincount(ytr, minlength=C) / len(ytr)
        model = LogReg().fit(Xtr, ytr)
        Pte = model.proba(X[te]); yte = y[te]; ste = subj[te]
        inner_acc = float((pred_in == ytr).mean()); outer_acc = float((Pte.argmax(1) == yte).mean())
        fold_info.append(dict(rep=rep, fold=fi, test_persons=[int(p) for p in test_p],
                              inner_window_acc=inner_acc, outer_window_acc=outer_acc))
        srng = np.random.default_rng(10_000 + 100 * rep + fi)

        def quantify(P, n):
            out = {"train_prior": prior_tr}
            cc = np.bincount(P.argmax(1), minlength=C) / n
            pcc = P.mean(0)
            out["CC"] = cc; out["PCC"] = pcc
            out["ACC"] = adjust(M_cc, cc); out["PACC"] = adjust(M_pcc, pcc)
            out["EMQ"] = emq(P, prior_tr)
            Ht = hists(P)
            f = lambda pm: hd_objective(pm, Hcond, Ht)
            out["HDy_PSO"], fp = pso_simplex(f, srng)
            out["HDy_random"], fr = random_search(f, srng)
            return out, fp, fr

        for p in test_p:
            idx_p = np.where(ste == p)[0]
            # natural condition: full recording as is
            true = np.bincount(yte[idx_p], minlength=C) / len(idx_p)
            est, fp, fr = quantify(Pte[idx_p], len(idx_p))
            for mth in METHODS:
                rows.append(dict(cond="natural", rep=rep, fold=fi, person=int(p), method=mth, n=len(idx_p),
                                 AE=ae(est[mth], true), RAE=rae(true, est[mth], len(idx_p)),
                                 KLD=kld(true, est[mth], len(idx_p)), AE3=group_ae(est[mth], true)))
            rows.append(dict(cond="natural", rep=rep, fold=fi, person=int(p), method="_hdy_obj", pso=fp, rnd=fr))
            # shifted condition: APP-style Dirichlet target mixes, resampled within the person
            by_c = [idx_p[yte[idx_p] == c] for c in range(C)]
            avail = np.array([len(b) > 0 for b in by_c])
            for s in range(PER_PERSON):
                target = srng.dirichlet(np.ones(C)) * avail; target /= target.sum()
                cnt = srng.multinomial(N_SAMPLE, target)
                idx = np.concatenate([srng.choice(by_c[c], cnt[c], replace=True) for c in range(C) if cnt[c] > 0])
                true = cnt / N_SAMPLE
                est, fp, fr = quantify(Pte[idx], N_SAMPLE)
                for mth in METHODS:
                    rows.append(dict(cond="shifted", rep=rep, fold=fi, person=int(p), sample=s, method=mth, n=N_SAMPLE,
                                     AE=ae(est[mth], true), RAE=rae(true, est[mth], N_SAMPLE),
                                     KLD=kld(true, est[mth], N_SAMPLE), AE3=group_ae(est[mth], true)))
                rows.append(dict(cond="shifted", rep=rep, fold=fi, person=int(p), sample=s, method="_hdy_obj", pso=fp, rnd=fr))
        print(f"rep{rep} fold{fi} inner_acc={inner_acc:.3f} outer_acc={outer_acc:.3f} {time.time()-t0:.0f}s", flush=True)

json.dump(dict(rows=rows, folds=fold_info, runtime_s=time.time() - t0), open(f"{OUT}/results_quant.json", "w"))

# ---------------- summary ----------------
out = [f"# Pilot results (UCI HAR, {len(persons)} persons, {len(y)} windows). Runtime {time.time()-t0:.0f}s.", ""]
out.append("Window-level accuracy of the fixed classifier (context only): inner CV mean "
           f"{np.mean([f['inner_window_acc'] for f in fold_info]):.3f}, outer (new people) mean "
           f"{np.mean([f['outer_window_acc'] for f in fold_info]):.3f}, range "
           f"{min(f['outer_window_acc'] for f in fold_info):.3f}-{max(f['outer_window_acc'] for f in fold_info):.3f}.")
for cond in ["shifted", "natural"]:
    R = [r for r in rows if r["cond"] == cond and not r["method"].startswith("_")]
    out += ["", f"## Condition: {cond}", "",
            "| method | AE (6 classes) | AE in min per class per 8 h | RAE | KLD | AE (3 intensity groups) | folds better than CC (of 10) |",
            "|---|---|---|---|---|---|---|"]
    fold_mean = {}
    for mth in METHODS:
        rr = [r for r in R if r["method"] == mth]
        for rep in range(2):
            for fi in range(5):
                fold_mean[(mth, rep, fi)] = np.mean([r["AE"] for r in rr if r["rep"] == rep and r["fold"] == fi])
    for mth in METHODS:
        rr = [r for r in R if r["method"] == mth]
        a = np.mean([r["AE"] for r in rr])
        wins = sum(fold_mean[(mth, rep, fi)] < fold_mean[("CC", rep, fi)] for rep in range(2) for fi in range(5))
        out.append(f"| {mth} | {a:.4f} | {a*480:.1f} | {np.mean([r['RAE'] for r in rr]):.3f} | "
                   f"{np.mean([r['KLD'] for r in rr]):.4f} | {np.mean([r['AE3'] for r in rr]):.4f} | "
                   f"{'-' if mth == 'CC' else wins} |")
    H = [r for r in rows if r["cond"] == cond and r["method"] == "_hdy_obj"]
    out.append(f"\nHDy objective (lower = better fit), same budget 1000 evaluations: PSO mean {np.mean([h['pso'] for h in H]):.5f}, "
               f"random search mean {np.mean([h['rnd'] for h in H]):.5f}; PSO lower in "
               f"{sum(h['pso'] < h['rnd'] for h in H)}/{len(H)} samples.")
open(f"{OUT}/summary_quant.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
