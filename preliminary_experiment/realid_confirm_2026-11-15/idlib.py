"""Helpers for the v8 identity-leakage experiment (numpy only).

The selectors/learners are the pilot's (fslib.py, copied unchanged next to this file).
The only additions are:
- identity (anthropometric / camera-position) features per window,
- a person-grouped inner CV, and copies of fslib.bpso_select / select_topk_by_cv /
  alpha tuning that accept the inner-CV function as a parameter (so protocol B can
  use grouped inner CV). With cv=fslib.cv_mae they are line-for-line the pilot logic.
"""
import numpy as np
import fslib as F
import features as FE
from features import (SPINE_BASE, SPINE_SH, HEAD, SH_L, EL_L, WR_L, SH_R, EL_R, WR_R,
                      HIP_L, KN_L, AN_L, FO_L, HIP_R, KN_R, AN_R, FO_R)

ID_NAMES = ["id_upperarm_L", "id_upperarm_R", "id_forearm_L", "id_forearm_R",
            "id_trunk_len", "id_shoulder_width", "id_neck_head", "id_hip_width",
            "id_height_bones", "id_vertical_span", "id_cam_z", "id_cam_x"]


def _blen(P, a, b):
    return float(np.median(np.linalg.norm(P[:, a] - P[:, b], axis=1)))


def identity_features(P):
    """P: (T, 25, 3). Per-window anthropometric and camera-position features (metres)."""
    f = {}
    f["id_upperarm_L"] = _blen(P, SH_L, EL_L)
    f["id_upperarm_R"] = _blen(P, SH_R, EL_R)
    f["id_forearm_L"] = _blen(P, EL_L, WR_L)
    f["id_forearm_R"] = _blen(P, EL_R, WR_R)
    f["id_trunk_len"] = _blen(P, SPINE_BASE, SPINE_SH)
    f["id_shoulder_width"] = _blen(P, SH_L, SH_R)
    f["id_neck_head"] = _blen(P, SPINE_SH, HEAD)
    f["id_hip_width"] = _blen(P, HIP_L, HIP_R)
    thigh = (_blen(P, HIP_L, KN_L) + _blen(P, HIP_R, KN_R)) / 2
    shank = (_blen(P, KN_L, AN_L) + _blen(P, KN_R, AN_R)) / 2
    # posture-independent stature proxy (sum of segment lengths)
    f["id_height_bones"] = f["id_neck_head"] + f["id_trunk_len"] + thigh + shank
    # posture-dependent vertical span head-to-feet (lower for seated participants)
    feet_y = np.minimum(P[:, FO_L, 1], P[:, FO_R, 1])
    f["id_vertical_span"] = float(np.median(P[:, HEAD, 1] - feet_y))
    f["id_cam_z"] = float(P[:, SPINE_BASE, 2].mean())   # distance from the sensor
    f["id_cam_x"] = float(P[:, SPINE_BASE, 0].mean())   # lateral position in the room
    return f


def build_windows(zip_path):
    X, Y = FE.load_zip(zip_path)
    J = X.reshape(len(X), 25, 4)
    groups = FE.group_subjects(J, Y)
    groups, dropped = FE.clean_groups(J, groups)
    rows, y, pid, widx = [], [], [], []
    for gi, g in enumerate(groups):
        for w in g:
            P = J[w * FE.WIN:(w + 1) * FE.WIN, :, :3]
            r = FE.features(P)
            r.update(identity_features(P))
            rows.append(r)
            y.append(Y[w])
            pid.append(gi)
            widx.append(w)
    names = list(rows[0].keys())
    Xw = np.array([[r[n] for n in names] for r in rows], float)
    is_id = np.array([n in ID_NAMES for n in names])
    return Xw, np.array(y), np.array(pid), names, is_id, {"n_raw_windows": len(Y), "dropped": len(dropped)}


# ------------------------------------------------------------------ CV variants
def grouped_kfold(groups, k, rng):
    ug = np.unique(groups)
    for trg, teg in F.kfold(len(ug), k, rng):
        yield np.where(np.isin(groups, ug[trg]))[0], np.where(np.isin(groups, ug[teg]))[0]


def make_grouped_cv(groups):
    """Return cv(X, y, model_fn, seed) -> inner MAE with person-grouped folds."""
    def cv(X, y, model_fn, k=5, seed=0):
        rng = np.random.default_rng(seed)
        errs = []
        for tr, te in grouped_kfold(groups, k, rng):
            s = F.Standardizer().fit(X[tr])
            m = model_fn().fit(s.transform(X[tr]), y[tr])
            errs.append(F.mae(y[te], m.predict(s.transform(X[te]))))
        return float(np.mean(errs))
    return cv


def random_cv(X, y, model_fn, k=5, seed=0):
    return F.cv_mae(X, y, model_fn, k=k, seed=seed)


def tune(X, y, cv, grid, ctor, seed):
    errs = [cv(X, y, lambda a=a: ctor(a), seed=seed) for a in grid]
    return grid[int(np.argmin(errs))]


def select_topk_by_cv(X, y, scores, ks, model_fn, cv, seed=0):
    order = np.argsort(-scores)
    best = None
    for k in ks:
        k = min(k, X.shape[1])
        e = cv(X[:, order[:k]], y, model_fn, seed=seed)
        if best is None or e < best[0]:
            best = (e, k)
    mask = np.zeros(X.shape[1], bool)
    mask[order[:best[1]]] = True
    return mask


def topk(scores, k):
    m = np.zeros(len(scores), bool)
    m[np.argsort(-scores)[:k]] = True
    return m


def bpso_select(X, y, model_fn, cv, n_particles=20, n_iter=30, lam=0.05,
                w=0.9, w_end=0.4, c1=2.0, c2=2.0, vmax=4.0, init_p=0.2,
                transfer="v", seed=0, inner_seed=0):
    """Copy of fslib.bpso_select with the inner-CV function as a parameter."""
    rng = np.random.default_rng(seed)
    n, d = X.shape
    base = F.mae(y, np.full_like(y, y.mean())) or 1.0
    cache = {}

    def fit(mask):
        if not mask.any():
            return np.inf
        key = mask.tobytes()
        if key not in cache:
            e = cv(X[:, mask], y, model_fn, seed=inner_seed)
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


# ------------------------------------------------------------------ analysis helpers
def icc1(x, groups):
    """One-way random-effects ICC(1) with unequal group sizes (share of variance
    between persons). High ICC = the feature mostly identifies the person."""
    ug = np.unique(groups)
    N, k = len(x), len(ug)
    gm = np.array([x[groups == g].mean() for g in ug])
    ni = np.array([(groups == g).sum() for g in ug])
    grand = x.mean()
    ssb = (ni * (gm - grand) ** 2).sum()
    ssw = sum(((x[groups == g] - x[groups == g].mean()) ** 2).sum() for g in ug)
    msb, msw = ssb / (k - 1), ssw / (N - k)
    n0 = (N - (ni ** 2).sum() / N) / (k - 1)
    den = msb + (n0 - 1) * msw
    return float((msb - msw) / den) if den > 0 else 0.0


def jaccard(a, b):
    u = (a | b).sum()
    return float((a & b).sum() / u) if u else 1.0


def nn1_id_loo(X, pid):
    """Leave-one-window-out 1-NN person identification accuracy (global z-score).
    Windows whose person has only one window are skipped as queries."""
    s = F.Standardizer().fit(X)
    Z = s.transform(X)
    sq = (Z ** 2).sum(1)
    D = sq[:, None] + sq[None, :] - 2 * Z @ Z.T
    np.fill_diagonal(D, np.inf)
    counts = np.bincount(pid)
    q = counts[pid] > 1
    pred = pid[D.argmin(1)]
    return float((pred[q] == pid[q]).mean())


def nn1_id_fold(Xtr, ptr, Xte, pte):
    """1-NN person identification of held-out windows from training windows
    (only test windows whose person is present in training are scored)."""
    s = F.Standardizer().fit(Xtr)
    A, B = s.transform(Xtr), s.transform(Xte)
    D = (B ** 2).sum(1)[:, None] + (A ** 2).sum(1)[None, :] - 2 * B @ A.T
    pred = ptr[D.argmin(1)]
    q = np.isin(pte, ptr)
    return float((pred[q] == pte[q]).mean()) if q.any() else np.nan, int(q.sum())
