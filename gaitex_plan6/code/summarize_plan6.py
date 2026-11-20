"""Summary-only re-entry for PLAN6 (same summary code as run_plan6.py, reading the saved raw outputs).\nAdded 16 Nov 2026 after run_plan6.py crashed in its summary step (KeyError in the T3 line, fixed in both files).\nUsage: python3 -P summarize_plan6.py <unused> <results_dir>\n\nOriginal docstring: PLAN6 (../PLAN6.md, sha256 3ead82b1...36e3): personal adaptation on GAITEX RD/RGS (inertial orientation).
Usage: python3 -P run_plan6.py <raw_dir> <out_dir> [--smoke]
numpy only. Model code = run_phytmo.LogReg/finetune generalised to C classes (same optimiser, same defaults)."""
import sys, os, json, glob, time, csv
import numpy as np

RAW, OUT = sys.argv[1], sys.argv[2]
SMOKE = '--smoke' in sys.argv
os.makedirs(OUT, exist_ok=True)
T0 = time.time()
LOG = open(os.path.join(OUT, 'summary_log.txt'), 'w')


def say(s):
    s = f'[{time.time()-T0:6.0f}s] {s}'; print(s, flush=True); LOG.write(s + '\n'); LOG.flush()


VARS = {'rd': ['rd_correct', 'rd_toes', 'rd_supination', 'rd_pronation'],
        'rgs': ['rgs_correct', 'rgs_flexion', 'rgs_abduction', 'rgs_stork']}
BUDGETS = [4, 8, 16]          # = 4k, k in {1,2,4} per variant (PLAN6 §6)
N_EVAL = 5                    # last 5 repetitions per variant
MIN_REPS = 9                  # PLAN6 §4 rule 3
FS = 100.0


VARS = {'rd': None, 'rgs': None}
BUDGETS = [4, 8, 16]
RES = json.load(open(os.path.join(OUT, 'results_plan6.json')))['results']
TUNE = json.load(open(os.path.join(OUT, 'tuning_plan6.json')))['tuning']
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
