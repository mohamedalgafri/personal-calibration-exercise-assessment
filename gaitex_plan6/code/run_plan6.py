"""PLAN6 (../PLAN6.md, sha256 3ead82b1...36e3): personal adaptation on GAITEX RD/RGS (inertial orientation).
Usage: python3 -P run_plan6.py <raw_dir> <out_dir> [--smoke]
numpy only. Model code = run_phytmo.LogReg/finetune generalised to C classes (same optimiser, same defaults)."""
import sys, os, json, glob, time, csv
import numpy as np

RAW, OUT = sys.argv[1], sys.argv[2]
SMOKE = '--smoke' in sys.argv
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
LOG = open(os.path.join(OUT, 'run_log.txt' if not SMOKE else 'smoke_log.txt'), 'w')


def say(s):
    s = f'[{time.time()-T0:6.0f}s] {s}'; print(s, flush=True); LOG.write(s + '\n'); LOG.flush()


VARS = {'rd': ['rd_correct', 'rd_toes', 'rd_supination', 'rd_pronation'],
        'rgs': ['rgs_correct', 'rgs_flexion', 'rgs_abduction', 'rgs_stork']}
BUDGETS = [4, 8, 16]          # = 4k, k in {1,2,4} per variant (PLAN6 §6)
N_EVAL = 5                    # last 5 repetitions per variant
MIN_REPS = 9                  # PLAN6 §4 rule 3
FS = 100.0


# ---------------- quaternion features (PLAN6 §5) ----------------
def qmul(a, b):
    w1, x1, y1, z1 = a.T; w2, x2, y2, z2 = b.T
    return np.stack([w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2,
                     w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2], 1)


def conj(q):
    return q * np.array([1, -1, -1, -1.0])


def sensor_channels(q):
    """q (T,4) unit quaternions (w,x,y,z), sensor->world. Returns (T,8) heading-free channels."""
    w, x, y, z = q.T
    g = np.stack([2*(x*z - w*y), 2*(y*z + w*x), 1 - 2*(x*x + y*y)], 1)       # world z in sensor frame
    dq = qmul(conj(q[:-1]), q[1:])
    dq = dq * np.where(dq[:, :1] < 0, -1.0, 1.0)                               # q ~ -q
    vn = np.linalg.norm(dq[:, 1:], axis=1)
    ang = 2 * np.arctan2(vn, dq[:, 0])
    om = np.where(vn[:, None] > 1e-12, dq[:, 1:] / np.maximum(vn, 1e-12)[:, None] * ang[:, None], 0.0) * FS
    om = np.vstack([om, om[-1:]])
    rel = 2 * np.arccos(np.clip(np.abs(q @ q[0]), 0, 1))[:, None]
    return np.hstack([g, om, np.linalg.norm(om, axis=1, keepdims=True), rel])


def stats6(X):
    return np.concatenate([X.mean(0), X.std(0), X.min(0), X.max(0), X.max(0) - X.min(0),
                           np.abs(np.diff(X, axis=0)).mean(0)])


def load_person(ex, pdir, excl):
    """-> {class_index: [feature vectors in repetition order]} or None (with reasons appended to excl)."""
    p = os.path.basename(pdir)
    fi = os.path.join(pdir, ex, f'xsens_imu_data_{p}_{ex}.csv')
    ft = os.path.join(pdir, ex, f'timestamps_{p}_{ex}.csv')
    if not (os.path.exists(fi) and os.path.exists(ft)):
        excl.append(f'{ex}\t{p}\tfiles missing'); return None
    with open(fi) as fh:
        hdr = fh.readline().strip().split(',')
    A = np.loadtxt(fi, delimiter=',', skiprows=1)
    t = A[:, 0]
    sens = sorted({c.rsplit('_', 1)[0] for c in hdr[1:]})
    Q = {s: A[:, [hdr.index(f'{s}_Q{k}') for k in 'WXYZ']] for s in sens}
    bad = np.zeros(len(t), bool)
    for s in sens:
        n = np.linalg.norm(Q[s], axis=1)
        bad |= ~np.isfinite(Q[s]).all(1) | (n < 0.9) | (n > 1.1)
    reps = {c: [] for c in range(4)}
    rows = list(csv.reader(open(ft)))[1:]
    by = {v: sorted([(float(r[1]), float(r[2])) for r in rows if r[0] == v]) for v in VARS[ex]}
    for c, v in enumerate(VARS[ex]):
        for i, (a, b) in enumerate(by[v]):
            m = (t >= a) & (t < b)
            nb = int((m & bad).sum()); nf = int(m.sum())
            if nf < 50 or nb > 0.05 * nf:
                excl.append(f'{ex}\t{p}\t{v} rep {i+1}: dropped ({nf} frames, {nb} invalid)'); continue
            m &= ~bad
            feats = [stats6(sensor_channels(Q[s][m] / np.linalg.norm(Q[s][m], axis=1, keepdims=True))) for s in sens]
            reps[c].append(np.concatenate(feats))
    short = [VARS[ex][c] for c in range(4) if len(reps[c]) < MIN_REPS]
    if short:
        excl.append(f'{ex}\t{p}\tEXCLUDED from exercise: fewer than {MIN_REPS} valid reps in {short} '
                    f'(counts {[len(reps[c]) for c in range(4)]})'); return None
    return {c: np.array(reps[c]) for c in range(4)}


# ---------------- model (run_phytmo.LogReg generalised to C classes) ----------------
def softmax(Z):
    Z = Z - Z.max(1, keepdims=True); E = np.exp(Z); return E / E.sum(1, keepdims=True)


def class_balance(y, w, C):
    w = w.astype(float).copy()
    tot = w.sum()
    for c in range(C):
        s = w[y == c].sum()
        if s > 0:
            w[y == c] *= tot / (C * s)
    return w


class LogReg:
    def __init__(self, C, l2=1e-2, iters=400, lr=0.05):
        self.C, self.l2, self.iters, self.lr = C, l2, int(iters), lr

    def fit(self, X, y, w=None, init=None, keep_scaler=False):
        C = self.C
        if not keep_scaler:
            self.mu = X.mean(0); self.sd = X.std(0); self.sd[self.sd < 1e-9] = 1.0
        Z = (X - self.mu) / self.sd; n, d = Z.shape; Y = np.eye(C)[y]
        w = class_balance(y, np.ones(n) if w is None else w, C); ws = w.sum()
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


FIX_A = dict(w=20.0, iters=60, lr=0.02, l2=1e-2)     # PLAN5 values
FIX_P = dict(iters=400, lr=0.05, l2=1e-2)


def adapt(gen, Xs, ys, Xc, yc, prm, C):
    m = LogReg(C, l2=prm['l2'], iters=prm['iters'], lr=prm['lr']); m.mu, m.sd = gen.mu, gen.sd
    w = np.concatenate([np.ones(len(ys)), np.full(len(yc), prm['w'])])
    return m.fit(np.vstack([Xs, Xc]), np.concatenate([ys, yc]), w, init=(gen.W, gen.b), keep_scaler=True)


def pers(gen, Xc, yc, prm, C):
    m = LogReg(C, l2=prm['l2'], iters=prm['iters'], lr=prm['lr']); m.mu, m.sd = gen.mu, gen.sd
    return m.fit(Xc, yc, keep_scaler=True)


def bal_acc(p, y):
    return float(np.mean([(p[y == c] == c).mean() for c in np.unique(y)]))


def macro_f1(p, y):
    f = []
    for c in np.unique(y):
        tp = ((p == c) & (y == c)).sum(); fp = ((p == c) & (y != c)).sum(); fn = ((p != c) & (y == c)).sum()
        f.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(f))


# ---------------- data views ----------------
def all_reps(D, ps, binary=False):
    X = np.vstack([D[p][c] for p in ps for c in range(4)])
    y = np.concatenate([np.full(len(D[p][c]), c) for p in ps for c in range(4)])
    return X, (y > 0).astype(int) if binary else y


def cal(D, p, k, binary=False, idx=None):
    """first k reps of each variant (or the reps with 0-based indices idx)."""
    sel = range(k) if idx is None else idx
    X = np.vstack([D[p][c][list(sel)] for c in range(4)])
    y = np.concatenate([np.full(len(list(sel)), c) for c in range(4)])
    return X, (y > 0).astype(int) if binary else y


def evl(D, p, binary=False):
    X = np.vstack([D[p][c][-N_EVAL:] for c in range(4)])
    y = np.concatenate([np.full(N_EVAL, c) for c in range(4)])
    return X, (y > 0).astype(int) if binary else y


# ---------------- tuning (PLAN6 §10) ----------------
SPACE_A = [('w', 1, 100, 'log'), ('iters', 10, 200, 'int'), ('lr', 1e-3, 1e-1, 'log'), ('l2', 1e-4, 1e-1, 'log')]
SPACE_P = [('iters', 50, 800, 'int'), ('lr', 1e-3, 1e-1, 'log'), ('l2', 1e-4, 1.0, 'log')]


def decode(u, space):
    out = {}
    for v, (n, lo, hi, kind) in zip(u, space):
        if kind == 'log':
            out[n] = float(10 ** (np.log10(lo) + v * (np.log10(hi) - np.log10(lo))))
        else:
            out[n] = int(round(lo + v * (hi - lo)))
    return out


def make_objective(D, train_p, strat, seed):
    rng = np.random.default_rng(seed)
    perm = list(rng.permutation(sorted(train_p)))
    inner = [list(f) for f in np.array_split(perm, 3)]
    cache = []
    for f in inner:
        tr = [p for p in train_p if p not in f]
        Xs, ys = all_reps(D, tr)
        g = LogReg(4).fit(Xs, ys)
        cache.append((g, Xs, ys, [(cal(D, p, 4), evl(D, p)) for p in f]))
    space = SPACE_A if strat == 'ADAPT' else SPACE_P

    def obj(u):
        prm = decode(u, space); s = []
        for g, Xs, ys, items in cache:
            for (Xc, yc), (Xe, ye) in items:
                m = adapt(g, Xs, ys, Xc, yc, prm, 4) if strat == 'ADAPT' else pers(g, Xc, yc, prm, 4)
                s.append(bal_acc(m.pred(Xe), ye))
        return float(np.mean(s))
    return obj, space


def random_search(obj, dim, seed, n=30):
    rng = np.random.default_rng(seed); U = rng.random((n, dim)); vals = [obj(u) for u in U]
    i = int(np.argmax(vals)); return U[i], vals[i], vals


def pso(obj, dim, seed, n_part=6, n_iter=5, wi=0.7, c1=1.5, c2=1.5, vmax=0.2):
    rng = np.random.default_rng(seed)
    X = rng.random((n_part, dim)); V = rng.uniform(-vmax, vmax, (n_part, dim))
    F = np.array([obj(x) for x in X]); P, PF = X.copy(), F.copy(); gi = int(np.argmax(PF)); evals = list(F)
    for it in range(n_iter - 1):
        r1, r2 = rng.random((n_part, dim)), rng.random((n_part, dim))
        V = np.clip(wi * V + c1 * r1 * (P - X) + c2 * r2 * (P[gi] - X), -vmax, vmax)
        X = np.clip(X + V, 0, 1)
        F = np.array([obj(x) for x in X]); evals += list(F)
        imp = F > PF; P[imp], PF[imp] = X[imp], F[imp]; gi = int(np.argmax(PF))
    assert len(evals) == n_part * n_iter
    return P[gi], float(PF[gi]), evals


# ---------------- load ----------------
excl = []
DATA = {}
for ex in VARS:
    D = {}
    for pdir in sorted(glob.glob(os.path.join(RAW, '*'))):
        if not os.path.isdir(os.path.join(pdir, ex)):
            continue
        r = load_person(ex, pdir, excl)
        if r is not None:
            D[os.path.basename(pdir)] = r
        if SMOKE and D:
            p = next(iter(D)); X, y = all_reps(D, [p])
            say(f'SMOKE {ex}/{p}: reps per class {[len(D[p][c]) for c in range(4)]}, feature matrix {X.shape}, '
                f'finite={np.isfinite(X).all()}')
            g = LogReg(4).fit(X, y); say(f'SMOKE GEN fit on own reps OK, W {g.W.shape} (no metric computed)')
            say('SMOKE exclusions so far: ' + ('; '.join(excl) if excl else 'none'))
            sys.exit(0)
    DATA[ex] = D
    say(f'{ex}: eligible persons {len(D)}: {sorted(D)}')
open(os.path.join(OUT, 'exclusions.txt'), 'w').write('\n'.join(excl) + ('\n' if excl else 'none\n'))
say(f'exclusions: {len(excl)} lines (results/exclusions.txt)')

# ---------------- outer loop ----------------
RES, TUNE = [], []
for ex, D in DATA.items():
    persons = sorted(D)
    for rep in range(2):
        rng0 = np.random.default_rng(6000 + rep)
        folds = [sorted(f) for f in np.array_split(list(rng0.permutation(persons)), 5)]
        for fi, test_p in enumerate(folds):
            train_p = [p for p in persons if p not in test_p]
            rng = np.random.default_rng(5000 + 10 * rep + fi)
            models = {}
            for task, C, binary in (('4class', 4, False), ('binary', 2, True)):
                Xs, ys = all_reps(D, train_p, binary)
                gen = LogReg(C).fit(Xs, ys); models[task] = (gen, Xs, ys)
                for ip, p in enumerate(test_p):
                    q = test_p[(ip + 1) % len(test_p)]
                    Xe, ye = evl(D, p, binary)
                    r = dict(ex=ex, task=task, rep=rep, fold=fi, person=p, donor=q,
                             GEN=bal_acc(gen.pred(Xe), ye), GEN_F1=macro_f1(gen.pred(Xe), ye))
                    for B in BUDGETS:
                        k = B // 4
                        Xc, yc = cal(D, p, k, binary)
                        ad = adapt(gen, Xs, ys, Xc, yc, FIX_A, C)
                        oc = np.concatenate([rng.choice(np.where(all_reps(D, train_p)[1] == c)[0], k, replace=False)
                                             for c in range(4)])
                        ct = adapt(gen, Xs, ys, Xs[oc], ys[oc], FIX_A, C)
                        Xq, yq = cal(D, q, k, binary)
                        cn = adapt(gen, Xs, ys, Xq, yq, FIX_A, C)
                        pe = pers(gen, Xc, yc, FIX_P, C)
                        r[f'ADAPT{B}'] = bal_acc(ad.pred(Xe), ye); r[f'CTRL{B}'] = bal_acc(ct.pred(Xe), ye)
                        r[f'CTRLNEW{B}'] = bal_acc(cn.pred(Xe), ye); r[f'PERS{B}'] = bal_acc(pe.pred(Xe), ye)
                        if B == 16:
                            r['ADAPT16_F1'] = macro_f1(ad.pred(Xe), ye); r['PERS16_F1'] = macro_f1(pe.pred(Xe), ye)
                        if task == '4class' and B in (8, 16):
                            # G1: GEN errs on >= 1 calibration rep
                            g1 = bool((gen.pred(Xc) != yc).any())
                            # G2: internal CV by repetition number
                            diffs = []
                            for j in range(k):
                                tr_idx = [i for i in range(k) if i != j]
                                Xa, ya = cal(D, p, k, idx=tr_idx); Xh, yh = cal(D, p, k, idx=[j])
                                mcv = adapt(gen, Xs, ys, Xa, ya, FIX_A, C)
                                diffs.append(bal_acc(mcv.pred(Xh), yh) - bal_acc(gen.pred(Xh), yh))
                            g2 = bool(np.mean(diffs) > 0)
                            r[f'G1dec{B}'], r[f'G2dec{B}'] = g1, g2
                            r[f'G1_{B}'] = r[f'ADAPT{B}'] if g1 else r['GEN']
                            r[f'G2_{B}'] = r[f'ADAPT{B}'] if g2 else r['GEN']
                    RES.append(r)
            # ---- tuning (4-class, B=16) ----
            gen, Xs, ys = models['4class']
            for strat in ('ADAPT', 'PERS'):
                seed = 7000 + fi * 10 + rep + (0 if strat == 'ADAPT' else 500)
                obj, space = make_objective(D, train_p, strat, seed)
                u_rs, f_rs, all_rs = random_search(obj, len(space), seed)
                u_ps, f_ps, all_ps = pso(obj, len(space), seed + 1)
                tr = dict(ex=ex, rep=rep, fold=fi, strat=strat, rs_best=f_rs, pso_best=f_ps, rs_all=all_rs,
                          pso_all=all_ps, rs_params=decode(u_rs, space), pso_params=decode(u_ps, space))
                for p in test_p:
                    Xe, ye = evl(D, p); Xc, yc = cal(D, p, 4)
                    for tag, u in (('RS', u_rs), ('PSO', u_ps)):
                        prm = decode(u, space)
                        m = adapt(gen, Xs, ys, Xc, yc, prm, 4) if strat == 'ADAPT' else pers(gen, Xc, yc, prm, 4)
                        tr[f'{p}_{tag}'] = bal_acc(m.pred(Xe), ye)
                TUNE.append(tr)
            say(f'{ex} rep{rep} fold{fi}: test {test_p} done')
json.dump(dict(results=RES), open(os.path.join(OUT, 'results_plan6.json'), 'w'))
json.dump(dict(tuning=TUNE), open(os.path.join(OUT, 'tuning_plan6.json'), 'w'))
say('raw outputs written; summarising')

# ---------------- summary (PLAN6 §8-§10) ----------------
BOOT = 2000


def boot_ci(d):
    rng = np.random.default_rng(0); d = np.asarray(d)
    m = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(BOOT)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def per_person(rows, key):
    P = sorted({r['person'] for r in rows})
    return P, np.array([np.mean([r[key] for r in rows if r['person'] == p]) for p in P])


def avg_rank(v):
    """ranks 0..n-1 with ties given their average rank (fixed 16 Nov after ChatGPT's audit; was argsort(argsort))."""
    v = np.asarray(v, float); o = np.argsort(v, kind='mergesort'); r = np.empty(len(v)); r[o] = np.arange(len(v))
    for u in np.unique(v):
        m = v == u
        if m.sum() > 1:
            r[m] = r[m].mean()
    return r


def spearman(a, b):
    ra, rb = avg_rank(a), avg_rank(b)
    if ra.std() == 0 or rb.std() == 0:
        return float('nan')
    return float(np.corrcoef(ra, rb)[0, 1])


L = ['# PLAN6 results (GAITEX; plan sha256 3ead82b1…36e3)\n']
L.append('Exclusions: see exclusions.txt. Differences in balanced-accuracy points (×100), person = mean over 2 repeats, '
         '95% percentile bootstrap over persons (2,000, seed 0).\n')
VERD = {}
for ex in VARS:
    for task in ('4class', 'binary'):
        rows = [r for r in RES if r['ex'] == ex and r['task'] == task]
        if not rows:
            continue
        P, gen = per_person(rows, 'GEN')
        L.append(f'\n## {ex.upper()} / {task} (n = {len(P)})\n')
        L.append(f'GEN mean BA = {gen.mean():.3f}\n')
        L.append('| B | ADAPT | ADAPT−GEN | ADAPT−CTRL | ADAPT−CTRL-NEW | PERS−ADAPT | +/−/= (ADAPT vs GEN) |')
        L.append('|---|---|---|---|---|---|---|')
        for B in BUDGETS:
            _, a = per_person(rows, f'ADAPT{B}'); _, c = per_person(rows, f'CTRL{B}')
            _, cn = per_person(rows, f'CTRLNEW{B}'); _, pe = per_person(rows, f'PERS{B}')
            cell = []
            for d in ((a - gen) * 100, (a - c) * 100, (a - cn) * 100, (pe - a) * 100):
                lo, hi = boot_ci(d); cell.append(f'{d.mean():+.1f} [{lo:+.1f}, {hi:+.1f}]')
            dd = (a - gen) * 100
            cnt = f'{(dd > .5).sum()}/{(dd < -.5).sum()}/{(np.abs(dd) <= .5).sum()}, median {np.median(dd):+.1f}'
            L.append(f'| {B} | {a.mean():.3f} | ' + ' | '.join(cell) + f' | {cnt} |')
            if B == 16:
                VERD[(ex, task)] = dict(d_gen=dd, d_ctrl=(a - c) * 100, d_new=(a - cn) * 100, d_pers=(pe - a) * 100,
                                        gen=gen, a=a)
        if task == '4class':
            _, f1g = per_person(rows, 'GEN_F1'); _, f1a = per_person(rows, 'ADAPT16_F1'); _, f1p = per_person(rows, 'PERS16_F1')
            L.append(f'\nMacro-F1 (orientation only): GEN {f1g.mean():.3f}, ADAPT16 {f1a.mean():.3f}, PERS16 {f1p.mean():.3f}\n')

L.append('\n## Pre-stated expectations (primary: 4-class, B = 16)\n')
for ex in VARS:
    v = VERD[(ex, '4class')]
    ci = {k: boot_ci(v[k]) for k in ('d_gen', 'd_ctrl', 'd_new', 'd_pers')}
    e1 = v['d_gen'].mean() >= 2 and ci['d_gen'][0] > 0
    e2 = v['d_ctrl'].mean() > 0 and ci['d_ctrl'][0] > 0
    e2b = v['d_new'].mean() > 0 and ci['d_new'][0] > 0
    e3 = v['d_pers'].mean() < 0 and ci['d_pers'][1] < 0
    rho = spearman(v['gen'], v['d_gen'])
    rng = np.random.default_rng(0); n = len(v['gen']); rb = []
    for _ in range(BOOT):
        i = rng.integers(0, n, n)
        if np.std(v['gen'][i]) > 0 and np.std(v['d_gen'][i]) > 0:
            s_ = spearman(v['gen'][i], v['d_gen'][i])
            if np.isfinite(s_):
                rb.append(s_)
    e4 = rho < 0
    verdict = 'consistent with PHYTMO' if (e1 and e2b) else ('partly consistent' if (e1 or e2b) else 'not consistent')
    d = v['d_gen']; worse = (d < -.5).sum(); pos = d[d > 0].sum(); top5 = np.sort(d)[::-1][:5].sum()
    if worse >= n / 3:
        pat = 'mixed'
    elif np.median(d) >= 2 and (d >= 2).sum() >= n / 2:
        pat = 'broad'
    elif pos > 0 and top5 / pos >= 0.6:
        pat = 'concentrated'
    else:
        pat = 'small/none'
    L.append(f'- **{ex.upper()}**: E1 {"✅" if e1 else "❌"} ({d.mean():+.1f} [{ci["d_gen"][0]:+.1f}, {ci["d_gen"][1]:+.1f}]); '
             f'E2 {"✅" if e2 else "❌"}; E2b {"✅" if e2b else "❌"}; E3 {"✅" if e3 else "❌"}; '
             f'E4 ρ = {rho:+.2f} [{np.percentile(rb, 2.5):+.2f}, {np.percentile(rb, 97.5):+.2f}] {"✅" if e4 else "❌"}; '
             f'**verdict: {verdict}**; pattern: **{pat}** (improved/worse/tied {(d > .5).sum()}/{worse}/{(np.abs(d) <= .5).sum()}, '
             f'Δ≥+2: {(d >= 2).sum()}, Δ≤−2: {(d <= -2).sum()}, best {d.max():+.1f}, worst {d.min():+.1f}, '
             f'top-5 share of gross gain {100 * top5 / pos if pos > 0 else float("nan"):.0f}%, GEN≥0.98: {(v["gen"] >= .98).sum()})')
for ex in VARS:
    rows = [r for r in RES if r['ex'] == ex and r['task'] == '4class']
    for B in BUDGETS:
        P, a = per_person(rows, f'ADAPT{B}'); _, pe = per_person(rows, f'PERS{B}')
        lo, hi = boot_ci((pe - a) * 100)
        if (pe - a).mean() > 0 and lo > 0:
            L.append(f'- {ex.upper()}: first budget where PERS beats ADAPT: {B}'); break
    else:
        L.append(f'- {ex.upper()}: PERS did not beat ADAPT (CI > 0) at any tested budget')

L.append('\n## Q4: adapt-or-not rules (exploratory, pre-specified; 4-class)\n')
L.append('| Ex / B | rule | mean BA | vs GEN | vs ALWAYS | adapted | harmed (rule < GEN) | harmed by ALWAYS | missed gain (ALWAYS > rule) |')
L.append('|---|---|---|---|---|---|---|---|---|')
for ex in VARS:
    rows = [r for r in RES if r['ex'] == ex and r['task'] == '4class']
    _, gen = per_person(rows, 'GEN')
    for B in (8, 16):
        _, al = per_person(rows, f'ADAPT{B}')
        for g in ('G1', 'G2'):
            _, gv = per_person(rows, f'{g}_{B}'); _, dec = per_person(rows, f'{g}dec{B}')
            L.append(f'| {ex.upper()} / {B} | {g} | {gv.mean():.3f} | {(gv - gen).mean() * 100:+.1f} | {(gv - al).mean() * 100:+.1f} | '
                     f'{dec.mean() * 100:.0f}% of decisions | {((gv - gen) * 100 < -.5).sum()} | {((al - gen) * 100 < -.5).sum()} | '
                     f'{((al - gv) * 100 > .5).sum()} |')

L.append('\n## Q5: tuning (4-class, B = 16; 30 evaluations per tuner)\n')
for ex in VARS:
    rows = [r for r in RES if r['ex'] == ex and r['task'] == '4class']
    P, afix = per_person(rows, 'ADAPT16'); _, pfix = per_person(rows, 'PERS16')
    for strat, fix in (('ADAPT', afix), ('PERS', pfix)):
        T = [t for t in TUNE if t['ex'] == ex and t['strat'] == strat]
        val = {tag: np.array([np.mean([t[f'{p}_{tag}'] for t in T if f'{p}_{tag}' in t]) for p in P]) for tag in ('RS', 'PSO')}
        spread = [np.percentile(t['rs_all'], 90) - np.percentile(t['rs_all'], 10) for t in T]
        d1 = (val['RS'] - fix) * 100; d2 = (val['PSO'] - val['RS']) * 100
        c1, c2 = boot_ci(d1), boot_ci(d2)
        L.append(f'- **{ex.upper()} {strat}**: T0 inner spread (P90−P10 over 30 random settings) median {np.median(spread) * 100:.1f} pts '
                 f'(range {min(spread) * 100:.1f}–{max(spread) * 100:.1f}); T1 RS−fixed {d1.mean():+.1f} [{c1[0]:+.1f}, {c1[1]:+.1f}]; '
                 f'T2 PSO−RS {d2.mean():+.1f} [{c2[0]:+.1f}, {c2[1]:+.1f}]; inner best RS {np.mean([t["rs_best"] for t in T]):.3f} '
                 f'vs PSO {np.mean([t["pso_best"] for t in T]):.3f}')
    Ta = [t for t in TUNE if t['ex'] == ex and t['strat'] == 'ADAPT']; Tp = [t for t in TUNE if t['ex'] == ex and t['strat'] == 'PERS']
    ars = np.array([np.mean([t[f'{p}_RS'] for t in Ta if f'{p}_RS' in t]) for p in P])
    prs = np.array([np.mean([t[f'{p}_RS'] for t in Tp if f'{p}_RS' in t]) for p in P])
    d3 = (ars - prs) * 100; c3 = boot_ci(d3)
    L.append(f'- **{ex.upper()}** T3 ADAPT_RS − PERS_RS {d3.mean():+.1f} [{c3[0]:+.1f}, {c3[1]:+.1f}]')
open(os.path.join(OUT, 'summary_plan6.md'), 'w').write('\n'.join(L) + '\n')
say('summary written')
