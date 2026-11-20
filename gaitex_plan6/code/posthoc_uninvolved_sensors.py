"""POST HOC diagnostic (16 Nov 2026, after seeing PLAN6 results; NOT in PLAN6).

Why: ADAPT16 reached BA = 1.0 for 16/19 RD and 14/15 RGS persons. Calibration (first 4 reps per variant) and
evaluation (last 5) come from the same set, and the variants were recorded in a fixed order. A within-session
signature (stance, sensor drift) could therefore let a person-specific model separate the variants without
learning the right-foot movement itself.

Diagnostic: repeat the primary RD analysis (4-class, B = 16, fixed settings, same folds/seeds) using ONLY sensors on
the LEFT leg (Foot_Left, LowerLeg_Left), which do not perform RD (right-foot dorsiflexion while standing).
A second subset uses the Sternum only.

Interpretation rule, written before running this script:
- If ADAPT16 or PERS16 on the left-leg subset reaches mean BA >= 0.80 while GEN on that subset stays <= 0.50,
  a within-session signature is a plausible contributor to the near-perfect personal results, and the PLAN6 gains
  must not be attributed to learning the target movement alone.
- If ADAPT16/PERS16 on the left-leg subset stay <= 0.50, this specific confound is not supported by this check
  (it does not rule out other session effects).
- In between: inconclusive, reported as such.
Usage: python3 -P posthoc_uninvolved_sensors.py <raw_dir> <out_md>
"""
import sys, os
import numpy as np

RAWD, OUTMD = sys.argv[1], sys.argv[2]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_plan6.py')).read()
src = src[:src.index('# ---------------- load ----------------')]
sys.argv = ['x', RAWD, os.path.join(os.path.dirname(OUTMD), 'posthoc_tmp')]  # fixed 16 Nov: the head of run_plan6 opens <out>/run_log.txt in 'w' mode; a separate folder keeps the main run log intact
ns = {'__name__': 'posthoc', '__file__': 'run_plan6.py'}
exec(compile(src, 'run_plan6_head', 'exec'), ns)
ns['LOG'] = open(os.devnull, 'w')
import glob
SENS = sorted(['XSens_Sternum', 'XSens_LowerLeg_Right', 'XSens_Foot_Right', 'XSens_Hand_Right', 'XSens_Pelvis',
               'XSens_UpperLeg_Left', 'XSens_LowerLeg_Left', 'XSens_Foot_Left', 'XSens_UpperLeg_Right'])
SUBSETS = {'left leg (Foot_Left + LowerLeg_Left)': ['XSens_Foot_Left', 'XSens_LowerLeg_Left'],
           'sternum only': ['XSens_Sternum'],
           'all 9 sensors (reproduces PLAN6)': SENS}
excl = []
D = {}
for pdir in sorted(glob.glob(os.path.join(RAWD, '*'))):
    if os.path.isdir(os.path.join(pdir, 'rd')):
        r = ns['load_person']('rd', pdir, excl)
        if r is not None:
            D[os.path.basename(pdir)] = r
persons = sorted(D)
LogReg, adapt, pers, bal_acc = ns['LogReg'], ns['adapt'], ns['pers'], ns['bal_acc']
FIX_A, FIX_P, cal, evl, all_reps = ns['FIX_A'], ns['FIX_P'], ns['cal'], ns['evl'], ns['all_reps']
out = ['# POST HOC: uninvolved-sensor diagnostic on RD (4-class, B = 16, fixed settings)\n',
       open(__file__).read().split('"""')[1].strip().replace('\n', '\n> ').join(['> ', '']) + '\n',
       f'Persons: {len(persons)}. Person score = mean over 2 repeats (same folds and seeds as PLAN6).\n',
       '| Feature subset | GEN | ADAPT16 | PERS16 | CTRL-NEW16 | ADAPT16 = 1.0 (persons) |', '|---|---|---|---|---|---|']
for name, keep in SUBSETS.items():
    cols = np.concatenate([np.arange(48) + 48 * SENS.index(s) for s in keep])
    Ds = {p: {c: D[p][c][:, cols] for c in range(4)} for p in persons}
    res = {k: {p: [] for p in persons} for k in ('GEN', 'ADAPT', 'PERS', 'CN')}
    for rep in range(2):
        rng0 = np.random.default_rng(6000 + rep)
        folds = [sorted(f) for f in np.array_split(list(rng0.permutation(persons)), 5)]
        for fi, test_p in enumerate(folds):
            train_p = [p for p in persons if p not in test_p]
            Xs, ys = all_reps(Ds, train_p)
            gen = LogReg(4).fit(Xs, ys)
            for ip, p in enumerate(test_p):
                q = test_p[(ip + 1) % len(test_p)]
                Xe, ye = evl(Ds, p); Xc, yc = cal(Ds, p, 4); Xq, yq = cal(Ds, q, 4)
                res['GEN'][p].append(bal_acc(gen.pred(Xe), ye))
                res['ADAPT'][p].append(bal_acc(adapt(gen, Xs, ys, Xc, yc, FIX_A, 4).pred(Xe), ye))
                res['PERS'][p].append(bal_acc(pers(gen, Xc, yc, FIX_P, 4).pred(Xe), ye))
                res['CN'][p].append(bal_acc(adapt(gen, Xs, ys, Xq, yq, FIX_A, 4).pred(Xe), ye))
    m = {k: np.array([np.mean(v[p]) for p in persons]) for k, v in res.items()}
    out.append(f"| {name} | {m['GEN'].mean():.3f} | {m['ADAPT'].mean():.3f} | {m['PERS'].mean():.3f} | {m['CN'].mean():.3f} | {(m['ADAPT'] >= .999).sum()}/{len(persons)} |")
    print(out[-1], flush=True)
open(OUTMD, 'w').write('\n'.join(out) + '\n\nChance level for 4 balanced classes = 0.25.\n')
