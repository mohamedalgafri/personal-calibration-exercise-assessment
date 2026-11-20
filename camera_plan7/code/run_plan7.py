"""PLAN7 (../PLAN7.md, sha256 65de095d…2e): keypoint source (MediaPipe video vs mocap 2D, camera 17) and the
GEN / ADAPT / PERS / CTRL / CTRL-NEW comparison on REHAB24-6 Ex1 and Ex2. numpy only.
Usage: python3 -P run_plan7.py [--front]   (--front = Addendum D front-view sensitivity analysis; reads results/extraction_log.jsonl to choose the run per video, §4.4)"""
import os, sys, json, csv, time
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SEG = os.path.join(ROOT, '..', 'feasibility_2026-11-16', 'rehab24', 'Segmentation.csv')
OUT = os.path.join(ROOT, 'results')
FRONT = '--front' in sys.argv          # Addendum D
SUF = '_front' if FRONT else ''
BS = (4,) if FRONT else (4, 8)
BM = BS[-1]
LOGF = open(os.path.join(OUT, f'run_log{SUF}.txt'), 'w')
T0 = time.time()


def say(s):
    s = f'[{time.time() - T0:6.0f}s] {s}'; print(s, flush=True); LOGF.write(s + '\n'); LOGF.flush()


MPI = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]      # L/R shoulder, elbow, wrist, hip, knee, ankle
MCI = [7, 12, 8, 13, 9, 14, 16, 21, 17, 22, 18, 23]
ANG = [(6, 0, 2), (7, 1, 3), (0, 2, 4), (1, 3, 5), (0, 6, 8), (1, 7, 9), (6, 8, 10), (7, 9, 11)]  # (a, vertex, b): shoulders, elbows, hips, knees


def angles(X):
    out = []
    for a, v, b in ANG:
        u, w = X[:, a] - X[:, v], X[:, b] - X[:, v]
        out.append(np.arctan2(np.abs(u[:, 0] * w[:, 1] - u[:, 1] * w[:, 0]), (u * w).sum(1)))  # unsigned (Addendum A.1)
    return np.stack(out, 1)


def stats6(X):
    return np.concatenate([X.mean(0), X.std(0), X.min(0), X.max(0), X.max(0) - X.min(0), np.abs(np.diff(X, axis=0)).mean(0)])


def rep_features(K):
    """K: (t, 12, 2) keypoints with NaN for missing. -> 192 features, or None if >20% frames missing (§4.5)."""
    miss = ~np.isfinite(K).all((1, 2))
    if miss.mean() > 0.20 or len(K) < 5:
        return None
    t = np.arange(len(K))
    K = K.copy()
    for j in range(12):
        for c in range(2):
            y = K[:, j, c]; ok = np.isfinite(y); K[:, j, c] = np.interp(t, t[ok], y[ok])
    hip = (K[:, 6] + K[:, 7]) / 2; sh = (K[:, 0] + K[:, 1]) / 2
    scale = np.median(np.linalg.norm(sh - hip, axis=1))
    Z = (K - hip[:, None, :]) / max(scale, 1e-6)
    ch = np.hstack([Z.reshape(len(Z), -1), angles(Z)])
    return stats6(ch)


# ---------------- model (as run_phytmo / run_plan6; class-balanced, C classes) ----------------
def softmax(Z):
    Z = Z - Z.max(1, keepdims=True); E = np.exp(Z); return E / E.sum(1, keepdims=True)


def class_balance(y, w, C):
    w = w.astype(float).copy(); tot = w.sum()
    for c in range(C):
        s = w[y == c].sum()
        if s > 0:
            w[y == c] *= tot / (C * s)
    return w


class LogReg:
    def __init__(self, C=2, l2=1e-2, iters=400, lr=0.05):
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


def adapt(gen, Xs, ys, Xc, yc):
    m = LogReg(2, iters=60, lr=0.02); m.mu, m.sd = gen.mu, gen.sd
    w = np.concatenate([np.ones(len(ys)), np.full(len(yc), 20.0)])
    return m.fit(np.vstack([Xs, Xc]), np.concatenate([ys, yc]), w, init=(gen.W, gen.b), keep_scaler=True)


def pers(gen, Xc, yc):
    m = LogReg(2); m.mu, m.sd = gen.mu, gen.sd
    return m.fit(Xc, yc, keep_scaler=True)


def bal_acc(p, y):
    return float(np.mean([(p[y == c] == c).mean() for c in np.unique(y)]))


# ---------------- data ----------------
SEGR = list(csv.DictReader(open(SEG), delimiter=';'))
used_run = {}
for line in open(os.path.join(OUT, 'extraction_log.jsonl')):
    r = json.loads(line)
    used_run.setdefault(r['id'], []).append(r)
excl = []
REPS = {}   # (ex, person) -> list of dict(order, y, fv, fm)
for vid, recs in sorted(used_run.items()):
    first = [r for r in recs if r['attempt'] == 'jpg1']    # Addendum C: frame-exact attempts only
    second = [r for r in recs if r['attempt'] == 'jpg2']
    if not first:
        continue
    use = first[-1]
    if first[-1]['rerun_trigger']:
        if not second:
            excl.append(f'{vid}\trerun triggered but no rerun found'); continue
        use = second[-1]
        if use['rerun_trigger']:
            excl.append(f'{vid}\texcluded: detection < 50% in both attempts'); continue
    if not (use['timestamps_ok'] and use.get('presented_match_raw', use['presented_match']) >= 0.99 and use['presented_dups'] == 0):
        excl.append(f'{vid}\texcluded: displayed-frame / timestamp check failed {use}'); continue
    if abs(use['lag_best']) > 2:
        excl.append(f'{vid}\texcluded: wrist lag {use["lag_best"]} frames'); continue
    P = json.load(open(os.path.join(OUT, f'{vid}_{use["attempt"]}.json')))
    M = np.load(os.path.join(ROOT, 'data', 'raw', f'{vid}-c17-30fps.npy'))
    V = np.full((P['n_frames'], 12, 2), np.nan)
    okshown = np.ones(P['n_frames'], bool)   # Addendum C: frame index = image index (Addendum A.4 check not needed)
    for i, f in enumerate(P['frames']):
        if f is not None and okshown[i]:
            for k, j in enumerate(MPI):
                if f[j][2] >= 0.5:
                    V[i, k] = f[j][:2]
    Mc = M[:, MCI, :].astype(float)
    for r in [r for r in SEGR if r['video_id'] == vid]:
        a, b = int(r['first_frame']), int(r['last_frame']) + 1
        key = (r['exercise_id'], r['person_id'])
        if FRONT and r['cam17_orientation'] != 'front':
            continue
        if r['mocap_erroneous'] == '1':
            excl.append(f'{vid}\trep {r["repetition_number"]}: mocap_erroneous'); continue
        fv, fm = rep_features(V[a:b]), rep_features(Mc[a:b])
        if fv is None or fm is None:
            excl.append(f'{vid}\trep {r["repetition_number"]}: >20% missing keypoints (video {fv is None}, mocap {fm is None})'); continue
        REPS.setdefault(key, []).append(dict(order=(vid, int(r['repetition_number'])), y=1 - int(r['correctness']), fv=fv, fm=fm,
                                              ori=r['cam17_orientation']))
# y: 0 = correct, 1 = incorrect
RES = []
for ex in ('1', '2'):
    persons = sorted({p for (e, p) in REPS if e == ex}, key=int)
    elig = []
    for p in persons:
        R = sorted(REPS[(ex, p)], key=lambda d: d['order'])
        n0 = sum(d['y'] == 0 for d in R); n1 = sum(d['y'] == 1 for d in R)
        groups = sorted({d['ori'] for d in R})   # Addendum B: eligibility per orientation group
        if FRONT:
            ok_b = min(n0, n1) >= 2 + 3   # Addendum D
        elif len(groups) == 1:
            ok_b = min(n0, n1) >= 4 + 5
        else:
            ok_b = all(sum(1 for d in R if d['y'] == c and d['ori'] == o) >= 2 + 3 for c in (0, 1) for o in groups)
        if ok_b:
            elig.append(p)
        else:
            excl.append(f'Ex{ex}\tperson {p}: not eligible ({"Addendum D, front only" if FRONT else "Addendum B"}; correct {n0}, incorrect {n1}, orientation groups {groups})')
    say(f'Ex{ex}: eligible persons {len(elig)}: {elig}')
    for src in ('mocap', 'video'):
        fk = 'fm' if src == 'mocap' else 'fv'

        def split(p, k):
            R = sorted(REPS[(ex, p)], key=lambda d: d['order'])
            cal, ev = [], []
            groups = sorted({d['ori'] for d in R})   # Addendum B: split within each orientation group
            for c in (0, 1):
                if FRONT:
                    rc = [d for d in R if d['y'] == c]
                    cal += rc[:k]; ev += rc[-3:]
                elif len(groups) == 1:
                    rc = [d for d in R if d['y'] == c]
                    cal += rc[:k]; ev += rc[-5:]
                else:
                    for o in groups:
                        rc = [d for d in R if d['y'] == c and d['ori'] == o]
                        cal += rc[:k // 2]; ev += rc[-3:]
            return (np.array([d[fk] for d in cal]), np.array([d['y'] for d in cal]),
                    np.array([d[fk] for d in ev]), np.array([d['y'] for d in ev]))

        for ip, p in enumerate(elig):
            q = elig[(ip + 1) % len(elig)]
            train = [x for x in elig if x not in (p, q)]
            Xs = np.vstack([np.array([d[fk] for d in REPS[(ex, t)]]) for t in train])
            ys = np.concatenate([np.array([d['y'] for d in REPS[(ex, t)]]) for t in train])
            gen = LogReg(2).fit(Xs, ys)
            row = dict(ex=ex, src=src, person=p, donor=q)
            for B in BS:
                k = B // 2
                Xc, yc, Xe, ye = split(p, k)
                Xq, yq, _, _ = split(q, k)
                rng = np.random.default_rng(8000 + ip)   # Addendum A.7: person index
                oc = np.concatenate([rng.choice(np.where(ys == c)[0], k, replace=False) for c in (0, 1)])
                if B == 4:
                    row['GEN'] = bal_acc(gen.pred(Xe), ye)
                ad = adapt(gen, Xs, ys, Xc, yc)
                row[f'ADAPT{B}'] = bal_acc(ad.pred(Xe), ye)
                row[f'CTRL{B}'] = bal_acc(adapt(gen, Xs, ys, Xs[oc], ys[oc]).pred(Xe), ye)
                row[f'CTRLNEW{B}'] = bal_acc(adapt(gen, Xs, ys, Xq, yq).pred(Xe), ye)
                row[f'PERS{B}'] = bal_acc(pers(gen, Xc, yc).pred(Xe), ye)
                g1 = bool((gen.pred(Xc) != yc).any())
                row[f'G1dec{B}'] = g1; row[f'G1_{B}'] = row[f'ADAPT{B}'] if g1 else row['GEN']
            RES.append(row)
        say(f'Ex{ex} {src}: done')
open(os.path.join(OUT, f'exclusions{SUF}.txt'), 'w').write('\n'.join(excl) + ('\n' if excl else 'none\n'))
json.dump(dict(results=RES), open(os.path.join(OUT, f'results_plan7{SUF}.json'), 'w'), indent=1)

# ---------------- summary ----------------
def boot_ci(d):
    rng = np.random.default_rng(0); d = np.asarray(d)
    m = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def fmt(d):
    lo, hi = boot_ci(d); return f'{d.mean():+.1f} [{lo:+.1f}, {hi:+.1f}]'


L = [('# PLAN7 FRONT-VIEW SENSITIVITY (Addendum D; post hoc, pre-outcome; descriptive) — ' if FRONT else '# ') + 'PLAN7 results (REHAB24-6 Ex1/Ex2, camera 17; plan sha256 65de095d…)\n',
     'Binary balanced accuracy in points; bootstrap 95% CI over persons (2,000, seed 0). Ex1 and Ex2 reported separately (mostly the same persons).\n']
C3 = {}
for ex in ('1', '2'):
    for src in ('mocap', 'video'):
        rows = sorted([r for r in RES if r['ex'] == ex and r['src'] == src], key=lambda r: int(r['person']))
        if not rows:
            continue
        g = np.array([r['GEN'] for r in rows])
        L.append(f'\n## Ex{ex} / {src} (n = {len(rows)}); GEN mean {g.mean():.3f}\n')
        L.append('| B | ADAPT − GEN | ADAPT − CTRL | ADAPT − CTRL-NEW | PERS − ADAPT | +/−/= | G1: adapted, harmed (G1 / ALWAYS) |')
        L.append('|---|---|---|---|---|---|---|')
        for B in BS:
            a = np.array([r[f'ADAPT{B}'] for r in rows]); c = np.array([r[f'CTRL{B}'] for r in rows])
            cn = np.array([r[f'CTRLNEW{B}'] for r in rows]); pe = np.array([r[f'PERS{B}'] for r in rows])
            g1 = np.array([r[f'G1_{B}'] for r in rows]); dec = np.array([r[f'G1dec{B}'] for r in rows])
            d = (a - g) * 100
            L.append(f'| {B} | {fmt(d)} | {fmt((a - c) * 100)} | {fmt((a - cn) * 100)} | {fmt((pe - a) * 100)} | '
                     f'{(d > .5).sum()}/{(d < -.5).sum()}/{(abs(d) <= .5).sum()} | {dec.sum()}/{len(dec)}, {((g1 - g) * 100 < -.5).sum()} / {((a - g) * 100 < -.5).sum()} |')
            if B == BM:
                C3[(ex, src)] = dict(d=d, g=g, persons=[r['person'] for r in rows])
L.append(f'\n## Pre-stated expectations (B = {BM})\n')
verd = 0; nex = 0
for ex in ('1', '2'):
    if (ex, 'mocap') not in C3 or (ex, 'video') not in C3:
        continue
    m, v = C3[(ex, 'mocap')], C3[(ex, 'video')]
    assert m['persons'] == v['persons']
    D = v['d'] - m['d']; gd = (v['g'] - m['g']) * 100
    cat = lambda x: 'positive' if x > 0.5 else ('negative' if x < -0.5 else 'null')   # Addendum A.3
    cm, cv = cat(m['d'].mean()), cat(v['d'].mean())
    applicable = not (cm == 'null' and cv == 'null')
    c3 = bool(cm == cv and cm != 'null' and abs(D.mean()) <= 5)
    nex += 1; verd += c3; nna = globals().get('nna', 0) + (not applicable); globals()['nna'] = nna
    ceil_m, ceil_v = int((m['g'] >= 0.999).sum()), int((v['g'] >= 0.999).sum())
    L.append(f'- **Ex{ex}**: C1 GEN_video − GEN_mocap {fmt(gd)} {"✅" if gd.mean() <= 0 else "❌"}; '
             f'C2 ADAPT{BM} − GEN (mocap) {fmt(m["d"])} {"✅" if m["d"].mean() > 0 else "❌"}; '
             f'(video) {fmt(v["d"])}; D = video − mocap {fmt(D)}; categories mocap/video {cm}/{cv}; '
             f'**C3 {"✅" if c3 else ("not applicable (no effect in either source)" if not applicable else "❌")}**; '
             f'persons at GEN = 1.0: mocap {ceil_m}, video {ceil_v}')
word = {2: 'carried over', 1: 'partly', 0: 'did not carry over'}.get(verd, f'{verd}/{nex}') if nex == 2 else f'{verd}/{nex} exercises analysed'
L.append(f'\n**Verdict (§6, Addendum A.3): the comparison {word} to markerless video ({verd}/{nex}).** No equivalence claim (n ≈ 8).'
         + (f' C3 was not applicable in {globals().get("nna", 0)} exercise(s): no adaptation effect in either source.' if globals().get('nna', 0) else ''))
# Addendum A.8: H5 testability and extraction rates
L.append(f'\n## H5 (G1 gate) testability, B = {BM}\n')
for ex in ('1', '2'):
    for src in ('mocap', 'video'):
        rows = [r for r in RES if r['ex'] == ex and r['src'] == src]
        if not rows:
            continue
        g = np.array([r['GEN'] for r in rows]); a = np.array([r[f'ADAPT{BM}'] for r in rows]); g1 = np.array([r[f'G1_{BM}'] for r in rows])
        ha, hg = int(((a - g) * 100 < -.5).sum()), int(((g1 - g) * 100 < -.5).sum())
        L.append(f'- Ex{ex}/{src}: harmed by ALWAYS {ha}, by G1 {hg} → ' + ('**H5 untestable** (ALWAYS harms nobody)' if ha == 0 else f'H5 {"✅" if hg < ha else "❌"}'))
logs = [json.loads(x) for x in open(os.path.join(OUT, 'extraction_log.jsonl'))]
first = [r for r in logs if r['attempt'] == 'jpg1']; reruns = [r for r in logs if r['attempt'] == 'jpg2']
L.append(f'\n## Extraction\n\n- videos with a completed first attempt: {len(first)}; first-attempt rerun trigger: {sum(r["rerun_trigger"] for r in first)}; '
         f'reruns: {len(reruns)}, recovered: {sum(not r["rerun_trigger"] for r in reruns)}; videos passing all checks: {sum(bool(r.get("pass")) for r in logs)}')
open(os.path.join(OUT, f'summary_plan7{SUF}.md'), 'w').write('\n'.join(L) + '\n')
say('summary written')
