"""Minimal, dependency-light (numpy only) toolkit for the preliminary experiment.

Contents
- Standardizer
- KernelRidge (RBF) and Ridge regressors (closed form, fast for small n)
- metrics: MAE, Spearman rho
- kfold / repeated k-fold splitters
- RReliefF (Robnik-Sikonja & Kononenko, 2003, Machine Learning 53:23-69) for regression targets
- |Spearman| correlation filter
- Binary PSO for feature selection (Kennedy & Eberhart, 1997), sigmoid transfer
- Consensus selection over repeated BPSO runs
- Nogueira et al. (2018) stability index with an approximate 95% CI
"""
import numpy as np


# ---------------------------------------------------------------- utilities
class Standardizer:
    def fit(self, X):
        self.mu = X.mean(0)
        self.sd = X.std(0)
        self.sd[self.sd < 1e-12] = 1.0
        return self

    def transform(self, X):
        return (X - self.mu) / self.sd


def rank(a):
    """Average ranks (ties share the mean rank)."""
    a = np.asarray(a, float)
    order = a.argsort(kind="mergesort")
    r = np.empty(len(a))
    r[order] = np.arange(len(a), dtype=float)
    # average ties
    vals, inv, counts = np.unique(a, return_inverse=True, return_counts=True)
    if (counts > 1).any():
        sums = np.bincount(inv, weights=r)
        r = sums[inv] / counts[inv]
    return r


def spearman(a, b):
    ra, rb = rank(a), rank(b)
    ra -= ra.mean()
    rb -= rb.mean()
    d = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / d) if d > 0 else 0.0


def mae(y, p):
    return float(np.mean(np.abs(np.asarray(y) - np.asarray(p))))


def kfold(n, k, rng):
    idx = rng.permutation(n)
    folds = np.array_split(idx, k)
    for i in range(k):
        te = folds[i]
        tr = np.concatenate([folds[j] for j in range(k) if j != i])
        yield tr, te


# ---------------------------------------------------------------- models
class Ridge:
    def __init__(self, alpha=1.0):
        self.alpha = alpha

    def fit(self, X, y):
        self.ym = y.mean()
        A = X.T @ X + self.alpha * np.eye(X.shape[1])
        self.w = np.linalg.solve(A, X.T @ (y - self.ym))
        return self

    def predict(self, X):
        return X @ self.w + self.ym


class KernelRidge:
    """RBF kernel ridge regression. gamma='scale' -> 1/(d * var(X))."""

    def __init__(self, alpha=1.0, gamma="scale"):
        self.alpha, self.gamma = alpha, gamma

    def _k(self, A, B):
        sq = (A ** 2).sum(1)[:, None] + (B ** 2).sum(1)[None, :] - 2 * A @ B.T
        return np.exp(-self.g * np.maximum(sq, 0))

    def fit(self, X, y):
        self.X = X
        v = X.var()
        self.g = 1.0 / (X.shape[1] * v) if self.gamma == "scale" else self.gamma
        if not np.isfinite(self.g) or self.g <= 0:
            self.g = 1.0
        self.ym = y.mean()
        K = self._k(X, X)
        self.a = np.linalg.solve(K + self.alpha * np.eye(len(X)), y - self.ym)
        return self

    def predict(self, X):
        return self._k(X, self.X) @ self.a + self.ym


def cv_mae(X, y, model_fn, k=5, seed=0):
    """Inner-CV MAE (standardization fitted inside each fold)."""
    rng = np.random.default_rng(seed)
    errs = []
    for tr, te in kfold(len(y), k, rng):
        s = Standardizer().fit(X[tr])
        m = model_fn().fit(s.transform(X[tr]), y[tr])
        errs.append(mae(y[te], m.predict(s.transform(X[te]))))
    return float(np.mean(errs))


# ---------------------------------------------------------------- filters
def rrelieff(X, y, k_neighbors=10, m=None, seed=0):
    """RReliefF weights for a continuous target (Robnik-Sikonja & Kononenko 2003).
    X should be scaled to comparable ranges (we use min-max inside)."""
    rng = np.random.default_rng(seed)
    n, d = X.shape
    lo, hi = X.min(0), X.max(0)
    rngX = np.where(hi - lo > 1e-12, hi - lo, 1.0)
    Xs = (X - lo) / rngX
    yr = (y.max() - y.min()) or 1.0
    m = n if m is None else min(m, n)
    k = min(k_neighbors, n - 1)
    NdC = 0.0
    NdA = np.zeros(d)
    NdCdA = np.zeros(d)
    sigma = k / 3.0
    ranks = np.arange(1, k + 1)
    wrank = np.exp(-((ranks / sigma) ** 2))
    wrank /= wrank.sum()
    for i in rng.permutation(n)[:m]:
        dist = np.abs(Xs - Xs[i]).sum(1)
        dist[i] = np.inf
        nn = np.argsort(dist)[:k]
        dy = np.abs(y[nn] - y[i]) / yr          # (k,)
        dA = np.abs(Xs[nn] - Xs[i])             # (k, d)
        NdC += (wrank * dy).sum()
        NdA += (wrank[:, None] * dA).sum(0)
        NdCdA += (wrank[:, None] * dy[:, None] * dA).sum(0)
    if NdC <= 0 or m - NdC <= 0:
        return np.zeros(d)
    return NdCdA / NdC - (NdA - NdCdA) / (m - NdC)


def spearman_filter(X, y):
    return np.array([abs(spearman(X[:, j], y)) for j in range(X.shape[1])])


def select_topk_by_cv(X, y, scores, ks, model_fn, seed=0):
    """Choose k (top-k by filter score) via inner CV; returns boolean mask."""
    order = np.argsort(-scores)
    best = None
    for k in ks:
        k = min(k, X.shape[1])
        cols = order[:k]
        e = cv_mae(X[:, cols], y, model_fn, seed=seed)
        if best is None or e < best[0]:
            best = (e, k)
    mask = np.zeros(X.shape[1], bool)
    mask[order[: best[1]]] = True
    return mask


# ---------------------------------------------------------------- BPSO
def bpso_select(X, y, model_fn, n_particles=20, n_iter=30, lam=0.05,
                w=0.9, w_end=0.4, c1=2.0, c2=2.0, vmax=4.0, init_p=0.2,
                transfer="v", seed=0, inner_seed=0):
    """Binary PSO wrapper. fitness = innerCV-MAE / MAE(mean predictor) + lam * k/d.
    transfer='s': classic sigmoid BPSO (Kennedy & Eberhart 1997), bit = 1 with p=sigmoid(v).
    transfer='v': V-shaped (Mirjalili & Lewis 2013), bit flips with p=|tanh(v)|.
    The error term is normalised so lam has the same meaning across exercises.
    Returns (best_mask, best_fitness, history)."""
    rng = np.random.default_rng(seed)
    n, d = X.shape
    base = mae(y, np.full_like(y, y.mean())) or 1.0
    cache = {}

    def fit(mask):
        if not mask.any():
            return np.inf
        key = mask.tobytes()
        if key not in cache:
            e = cv_mae(X[:, mask], y, model_fn, seed=inner_seed)
            cache[key] = e / base + lam * mask.sum() / d
        return cache[key]

    pos = rng.random((n_particles, d)) < init_p
    vel = rng.uniform(-1, 1, (n_particles, d))
    pf = np.array([fit(p) for p in pos])
    pbest, pbest_f = pos.copy(), pf.copy()
    g = pbest_f.argmin()
    gbest, gbest_f = pbest[g].copy(), pbest_f[g]
    hist = [gbest_f]
    for t in range(n_iter):
        wt = w - (w - w_end) * t / max(1, n_iter - 1)
        r1, r2 = rng.random((n_particles, d)), rng.random((n_particles, d))
        vel = (wt * vel + c1 * r1 * (pbest.astype(float) - pos)
               + c2 * r2 * (gbest.astype(float) - pos))
        vel = np.clip(vel, -vmax, vmax)
        if transfer == "s":
            pos = rng.random((n_particles, d)) < 1 / (1 + np.exp(-vel))
        else:
            flip = rng.random((n_particles, d)) < np.abs(np.tanh(vel))
            pos = np.where(flip, ~pos, pos)
        f = np.array([fit(p) for p in pos])
        imp = f < pbest_f
        pbest[imp], pbest_f[imp] = pos[imp], f[imp]
        g = pbest_f.argmin()
        if pbest_f[g] < gbest_f:
            gbest, gbest_f = pbest[g].copy(), pbest_f[g]
        hist.append(gbest_f)
    return gbest, gbest_f, hist


def consensus(masks, thr=0.5):
    freq = np.mean(np.asarray(masks, float), 0)
    sel = freq >= thr
    if not sel.any():
        sel[freq.argmax()] = True
    return sel, freq


# ---------------------------------------------------------------- stability
def nogueira_stability(Z):
    """Nogueira, Sechidis & Brown (2018). Z: (M runs, d features) binary.
    Returns (phi, ci_low, ci_high) with the asymptotic 95% CI from the paper."""
    Z = np.asarray(Z, float)
    M, d = Z.shape
    if M < 2:
        return np.nan, np.nan, np.nan
    p = Z.mean(0)
    k = Z.sum(1)
    kbar = k.mean()
    denom = (kbar / d) * (1 - kbar / d)
    if denom <= 0:
        return 1.0, 1.0, 1.0
    s2 = M / (M - 1) * p * (1 - p)
    phi = 1 - s2.mean() / denom
    # variance estimate (Nogueira et al. 2018, Theorem / Eq. for phi_i)
    phis = np.zeros(M)
    for i in range(M):
        phis[i] = (1 / denom) * ((Z[i] * p).sum() / d - (k[i] * kbar) / d ** 2
                                 + (phi / 2) * ((2 * k[i] * kbar) / d ** 2
                                                       - k[i] / d - kbar / d + 1))
    phibar = phis.mean()
    var = 4 / M ** 2 * ((phis - phibar) ** 2).sum()
    half = 1.96 * np.sqrt(var)
    return float(phi), float(phi - half), float(phi + half)


# ---------------------------------------------------------------- stats
def wilcoxon_signed_rank(a, b):
    """Two-sided Wilcoxon signed-rank test, normal approximation with tie
    correction (adequate for n >= 10). Returns (W, z, p)."""
    from math import erf, sqrt
    dlt = np.asarray(a, float) - np.asarray(b, float)
    dlt = dlt[np.abs(dlt) > 1e-12]
    n = len(dlt)
    if n == 0:
        return 0.0, 0.0, 1.0
    r = rank(np.abs(dlt))
    wplus = r[dlt > 0].sum()
    mu = n * (n + 1) / 4
    _, counts = np.unique(np.abs(dlt), return_counts=True)
    sigma2 = n * (n + 1) * (2 * n + 1) / 24 - (counts ** 3 - counts).sum() / 48
    z = (wplus - mu) / np.sqrt(sigma2) if sigma2 > 0 else 0.0
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return float(wplus), float(z), float(p)
