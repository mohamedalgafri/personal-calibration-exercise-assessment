"""PLAN8 (../PLAN8.md, sha256 2308ac11…d008): stronger general model (MLP ensemble) on PHYTMO (PLAN5 design) and GAITEX
(PLAN6 design), B = 16. Reuses the data/fold code of run_plan5.py and run_plan6.py unchanged (executed in separate
namespaces). numpy only.
Usage: python3 -P run_plan8.py [--smoke]   (--smoke: one fold of PHYTMO SQT/IMU and GAITEX RD, prints shapes/timing only)"""
import os, sys, json, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, '..', 'results')
SMOKE = '--smoke' in sys.argv
sys.path.insert(0, HERE)
from mlp import Ensemble  # noqa: E402

LOG = open(os.path.join(OUT, 'smoke_log.txt' if SMOKE else 'run_log.txt'), 'w')
T0 = time.time()


def say(s):
    s = f'[{time.time() - T0:6.0f}s] {s}'; print(s, flush=True); LOG.write(s + '\n'); LOG.flush()


def load_ns(path, cut, argv):
    src = open(path).read(); src = src[:src.index(cut)]
    old = sys.argv; sys.argv = argv
    ns = {'__name__': 'plan8_import', '__file__': path}
    try:
        exec(compile(src, path, 'exec'), ns)
    finally:
        sys.argv = old
    return ns


# ---------------- PHYTMO (PLAN5 design) ----------------
P5 = load_ns(os.path.join(ROOT, 'phytmo_pilot', 'code', 'run_plan5.py'), 'results, cells = {}, []',
             ['run_plan5.py', os.path.join(ROOT, 'phytmo_pilot', 'data', 'raw'), os.path.join(OUT, 'plan5_tmp')])
saved5 = json.load(open(os.path.join(ROOT, 'phytmo_pilot', 'results', 'plan5', 'results_plan5.json')))['results']
RES = []
CHECK = {('SQT', 'IMU'), ('EAH', 'OPT')}
for ex in (['SQT'] if SMOKE else ['SQT', 'HAA', 'SQZ', 'EAH']):
    uni = ex in P5['UNILATERAL']
    data = {}
    for mod in ('IMU', 'OPT'):
        W, bad = (P5['load_imu'] if mod == 'IMU' else P5['load_opt'])(ex)
        data[mod] = W
    persons = sorted(set.intersection(*[{k[0] for k in data[m]} for m in ('IMU', 'OPT')]))
    persons = [p for p in persons if all(P5['eligible'](data[m], p, uni) for m in ('IMU', 'OPT'))]
    say(f'PHYTMO {ex}: eligible persons {len(persons)}')
    for mod in (['IMU'] if SMOKE else ['IMU', 'OPT']):
        W = data[mod]; cell = f'{ex}/{mod}'
        sv = {(r['rep'], r['fold'], r['person']): r for r in saved5[cell]}
        for rep in range(2):
            perm = np.random.default_rng(3000 + rep).permutation(persons)
            for fi in range(5):
                test_p = set(perm[fi::5]); train_p = [p for p in persons if p not in test_p]
                tr = [P5['stackS'](W, p, S) for p in train_p for S in (1, 2)]
                Xtr = np.vstack([x for x, _ in tr]); ytr = np.concatenate([y for _, y in tr])
                if SMOKE:
                    say(f'SMOKE {cell}: Xtr {Xtr.shape}'); t = time.time()
                gen = Ensemble(2).fit(Xtr, ytr)
                if SMOKE:
                    say(f'SMOKE GEN-MLP fit {time.time() - t:.1f}s (no metric printed)')
                genlr = P5['LogReg']().fit(Xtr, ytr) if (ex, mod) in CHECK else None
                rng = np.random.default_rng(5000 + 10 * rep + fi)
                sub = rng.choice(len(ytr), min(1500, len(ytr)), replace=False)
                tl = sorted(test_p)
                for ip, p in enumerate(tl):
                    q = tl[(ip + 1) % len(tl)]
                    X2, y2 = P5['stackS'](W, p, 2)
                    Xc, yc = P5['pick_cal'](W, p, 16, uni); Xq, yq = P5['pick_cal'](W, q, 16, uni)
                    w = np.concatenate([np.ones(len(sub)), np.full(16, 20.0)])
                    ad = gen.adapt(np.vstack([Xtr[sub], Xc]), np.concatenate([ytr[sub], yc]), w)
                    cn = gen.adapt(np.vstack([Xtr[sub], Xq]), np.concatenate([ytr[sub], yq]), w)
                    s = sv[(rep, fi, p)]
                    r = dict(data='PHYTMO', cell=cell, rep=rep, fold=fi, person=p,
                             GEN_MLP=P5['bal_acc'](gen.pred(X2), y2), ADAPT_MLP=P5['bal_acc'](ad.pred(X2), y2),
                             CTRLNEW_MLP=P5['bal_acc'](cn.pred(X2), y2), GEN_LR=s['GEN'], ADAPT_LR=s['ADAPT16'])
                    if genlr is not None:
                        r['GEN_LR_recomputed'] = P5['bal_acc'](genlr.pred(X2), y2)
                    RES.append(r)
                    if SMOKE:
                        break
                if SMOKE:
                    break
                say(f'{cell} rep{rep} fold{fi} done')
            if SMOKE:
                break

# ---------------- GAITEX (PLAN6 design) ----------------
P6 = load_ns(os.path.join(ROOT, 'gaitex_plan6', 'code', 'run_plan6.py'), '# ---------------- load ----------------',
             ['run_plan6.py', os.path.join(ROOT, 'gaitex_plan6', 'data', 'raw'), os.path.join(OUT, 'plan6_tmp')])
P6['LOG'] = open(os.devnull, 'w')
saved6 = [r for r in json.load(open(os.path.join(ROOT, 'gaitex_plan6', 'results', 'results_plan6.json')))['results'] if r['task'] == '4class']
import glob  # noqa: E402
for ex in (['rd'] if SMOKE else ['rd', 'rgs']):
    D = {}; excl = []
    for pdir in sorted(glob.glob(os.path.join(ROOT, 'gaitex_plan6', 'data', 'raw', '*'))):
        if os.path.isdir(os.path.join(pdir, ex)):
            rr = P6['load_person'](ex, pdir, excl)
            if rr is not None:
                D[os.path.basename(pdir)] = rr
    persons = sorted(D)
    say(f'GAITEX {ex}: eligible persons {len(persons)}')
    sv = {(r['rep'], r['fold'], r['person']): r for r in saved6 if r['ex'] == ex}
    for rep in range(2):
        rng0 = np.random.default_rng(6000 + rep)
        folds = [sorted(f) for f in np.array_split(list(rng0.permutation(persons)), 5)]
        for fi, test_p in enumerate(folds):
            train_p = [p for p in persons if p not in test_p]
            Xs, ys = P6['all_reps'](D, train_p)
            gen = Ensemble(4).fit(Xs, ys)
            genlr = P6['LogReg'](4).fit(Xs, ys) if ex == 'rd' else None
            for ip, p in enumerate(test_p):
                q = test_p[(ip + 1) % len(test_p)]
                Xe, ye = P6['evl'](D, p); Xc, yc = P6['cal'](D, p, 4); Xq, yq = P6['cal'](D, q, 4)
                w = np.concatenate([np.ones(len(ys)), np.full(len(yc), 20.0)])
                ad = gen.adapt(np.vstack([Xs, Xc]), np.concatenate([ys, yc]), w)
                cn = gen.adapt(np.vstack([Xs, Xq]), np.concatenate([ys, yq]), w)
                s = sv[(rep, fi, str(p))]
                r = dict(data='GAITEX', cell=f'{ex.upper()}/4class', rep=rep, fold=fi, person=str(p),
                         GEN_MLP=P6['bal_acc'](gen.pred(Xe), ye), ADAPT_MLP=P6['bal_acc'](ad.pred(Xe), ye),
                         CTRLNEW_MLP=P6['bal_acc'](cn.pred(Xe), ye), GEN_LR=s['GEN'], ADAPT_LR=s['ADAPT16'])
                if genlr is not None:
                    r['GEN_LR_recomputed'] = P6['bal_acc'](genlr.pred(Xe), ye)
                RES.append(r)
                if SMOKE:
                    break
            if SMOKE:
                break
            say(f'GAITEX {ex} rep{rep} fold{fi} done')
        if SMOKE:
            break

if SMOKE:
    say(f'SMOKE done: {len(RES)} rows; keys {sorted(RES[0])}')
    sys.exit(0)

# ---------------- sanity check (PLAN8 §3) ----------------
chk = [r for r in RES if 'GEN_LR_recomputed' in r]
maxdiff = max(abs(r['GEN_LR_recomputed'] - r['GEN_LR']) for r in chk)
say(f'sanity: {len(chk)} GEN-LR values recomputed, max |difference| vs saved = {maxdiff:.2e}')
json.dump(dict(results=RES, sanity_maxdiff=maxdiff), open(os.path.join(OUT, 'results_plan8.json'), 'w'), indent=1)
if maxdiff >= 1e-9:
    say('SANITY CHECK FAILED: stopping before the summary (PLAN8 §3)'); sys.exit(2)


# ---------------- summary (PLAN8 §4) ----------------
def boot_ci(d):
    rng = np.random.default_rng(0); d = np.asarray(d)
    m = [d[rng.integers(0, len(d), len(d))].mean() for _ in range(2000)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def fmt(d):
    lo, hi = boot_ci(d); return f'{d.mean():+.1f} [{lo:+.1f}, {hi:+.1f}]'


L = ['# PLAN8 results: stronger general model (MLP ensemble) vs logistic regression, B = 16 (plan sha256 2308ac11…)\n',
     f'Sanity check: GEN-LR recomputed for {len(chk)} person × repeat values, max |difference| vs saved = {maxdiff:.1e}.\n',
     'Points; person = mean over 2 repeats; bootstrap 95% CI over persons (2,000, seed 0).\n',
     '| Cell | n | GEN-LR | GEN-MLP | S1 GEN-MLP − GEN-LR | ADAPT-LR − GEN-LR | **S2 ADAPT-MLP − GEN-MLP** | S3 ADAPT-MLP − CTRL-NEW-MLP | S4 GEN-MLP − ADAPT-LR | S5 retained | +/−/= (ADAPT-MLP vs GEN-MLP) | GEN-MLP ≥ 0.98 |',
     '|---|---|---|---|---|---|---|---|---|---|---|---|']
held, s5s, base_cells = 0, [], 0
for cell in sorted({r['cell'] for r in RES}, key=lambda c: (c.split('/')[0] in ('RD', 'RGS'), c)):
    rows = [r for r in RES if r['cell'] == cell]
    P = sorted({r['person'] for r in rows})
    m = {k: np.array([np.mean([r[k] for r in rows if r['person'] == p]) for p in P]) for k in ('GEN_LR', 'ADAPT_LR', 'GEN_MLP', 'ADAPT_MLP', 'CTRLNEW_MLP')}
    s1 = (m['GEN_MLP'] - m['GEN_LR']) * 100; dlr = (m['ADAPT_LR'] - m['GEN_LR']) * 100
    s2 = (m['ADAPT_MLP'] - m['GEN_MLP']) * 100; s3 = (m['ADAPT_MLP'] - m['CTRLNEW_MLP']) * 100
    s4 = (m['GEN_MLP'] - m['ADAPT_LR']) * 100
    lo2, _ = boot_ci(s2); ok2 = s2.mean() >= 2 and lo2 > 0
    lo_lr, _ = boot_ci(dlr); base = dlr.mean() >= 2 and lo_lr > 0
    s5 = s2.mean() / dlr.mean() if dlr.mean() >= 2 else float('nan')
    if base:
        base_cells += 1; held += ok2
        if np.isfinite(s5):
            s5s.append(s5)
    L.append(f'| {cell}{"" if base else " (LR criterion not met)"} | {len(P)} | {m["GEN_LR"].mean():.3f} | {m["GEN_MLP"].mean():.3f} | {fmt(s1)} | {fmt(dlr)} | '
             f'**{fmt(s2)}** {"✅" if ok2 else "❌"} | {fmt(s3)} | {fmt(s4)} | {s5:.2f} | '
             f'{(s2 > .5).sum()}/{(s2 < -.5).sum()}/{(abs(s2) <= .5).sum()} | {(m["GEN_MLP"] >= .98).sum()} |')
med5 = float(np.median(s5s)) if s5s else float('nan')
if held >= 7 and med5 >= 0.5:
    verdict = 'benefit survives the stronger model'
elif held <= 3:
    verdict = 'benefit does not survive the stronger model'
else:
    verdict = 'benefit reduced with the stronger model'
L.append(f'\n**S2 held in {held} of the {base_cells} cells that met the LR criterion; median S5 (retained share) = {med5:.2f}. '
         f'Verdict (PLAN8 §4): {verdict}.**')
L.append(f'\nRuntime {time.time() - T0:.0f} s.')
open(os.path.join(OUT, 'summary_plan8.md'), 'w').write('\n'.join(L) + '\n')
say('summary written')
