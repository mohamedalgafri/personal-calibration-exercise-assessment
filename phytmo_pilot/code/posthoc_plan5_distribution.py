"""POST HOC (16 Nov 2026, after PLAN5 results): per-cell distribution of
ADAPT16 - GEN gains and losses, from the SAVED results_plan5.json.
No model is retrained. Person score = mean over the repetitions (rep) saved
for that person, the same aggregation as run_plan5.py's person-level report.
Tie rule = |diff| <= 0.5 BA points (as in RESULTS_PLAN5.md).

Run:  python3 -P phytmo_pilot/code/posthoc_plan5_distribution.py
"""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'results', 'plan5')
d = json.load(open(os.path.join(RES, 'results_plan5.json')))['results']

TIE = 0.5
rows = []
for cell, recs in d.items():
    per = {}
    for r in recs:
        per.setdefault(r['person'], []).append((r['GEN'], r['ADAPT16']))
    persons = sorted(per)
    gen = np.array([np.mean([g for g, _ in per[p]]) for p in persons])
    ada = np.array([np.mean([a for _, a in per[p]]) for p in persons])
    diff = (ada - gen) * 100
    n = len(diff)
    imp = int((diff > TIE).sum()); wor = int((diff < -TIE).sum()); tie = n - imp - wor
    pos = diff[diff > 0].sum(); neg = diff[diff < 0].sum(); net = diff.sum()
    top5 = np.sort(diff)[::-1][:5].sum()
    order = np.argsort(gen)
    low, high = order[: n // 2], order[n // 2:]
    big_gain = int((diff >= 2).sum()); big_loss = int((diff <= -2).sum())
    ceil = int((gen >= 0.98).sum())
    worst_loss = diff.min(); best_gain = diff.max()
    # where are the losses? GEN of persons who got worse
    gen_worse = gen[diff < -TIE]
    rows.append(dict(cell=cell, n=n, gen_mean=gen.mean(), mean=diff.mean(),
                     median=float(np.median(diff)), imp=imp, wor=wor, tie=tie,
                     big_gain=big_gain, big_loss=big_loss, best=best_gain,
                     worst=worst_loss, pos=pos, neg=neg, net=net,
                     top5_net=100 * top5 / net if net > 0 else float('nan'),
                     top5_pos=100 * top5 / pos if pos > 0 else float('nan'),
                     low=diff[low].mean(), high=diff[high].mean(), ceil=ceil,
                     gen_worse_med=float(np.median(gen_worse)) if len(gen_worse) else float('nan')))

out = []
out.append('# POST HOC: per-cell distribution of ADAPT16 − GEN (from saved results; no retraining)\n')
out.append('Person score = mean over saved repetitions. Differences in balanced-accuracy points. '
           f'Improved/worse = beyond ±{TIE} point.\n')
out.append('| Cell | n | GEN mean | mean Δ | median Δ | improved / worse / tied | Δ ≥ +2 | Δ ≤ −2 | best / worst person | gross gain / gross loss / net (pts·persons) | top-5 share of gross gain | mean Δ lower vs upper half of GEN | GEN ≥ 0.98 | median GEN of the worse |')
out.append('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for r in rows:
    out.append(f"| {r['cell']} | {r['n']} | {r['gen_mean']:.3f} | {r['mean']:+.1f} | {r['median']:+.1f} | "
               f"{r['imp']} / {r['wor']} / {r['tie']} | {r['big_gain']} | {r['big_loss']} | "
               f"{r['best']:+.1f} / {r['worst']:+.1f} | {r['pos']:.0f} / {r['neg']:.0f} / {r['net']:.0f} | "
               f"{r['top5_pos']:.0f}% | {r['low']:+.1f} vs {r['high']:+.1f} | {r['ceil']} | {r['gen_worse_med']:.3f} |")
txt = '\n'.join(out) + '\n'
print(txt)
open(os.path.join(RES, 'posthoc_distribution_B16.md'), 'w').write(txt)
json.dump(rows, open(os.path.join(RES, 'posthoc_distribution_B16.json'), 'w'), indent=1)
