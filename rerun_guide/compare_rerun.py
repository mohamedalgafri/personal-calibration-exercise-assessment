"""Compares re-run outputs (rerun_workspace/) with the original saved results, number by number.
Usage (from UNESP_DHT):  python3 -P rerun_guide/compare_rerun.py [rerun_root]
Writes rerun_workspace/RERUN_REPORT.md. Timing fields are ignored; everything else must match within 1e-9."""
import os, sys, json, datetime, math
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
RR = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(ROOT, 'rerun_workspace')
SKIP = {'log', 'runtime', 'elapsed', 'time', 'seconds'}
PAIRS = [  # (study, original, re-run)
    ('Study 1 (PHYTMO, PLAN5)', 'phytmo_pilot/results/plan5/results_plan5.json', 'phytmo_pilot/results/plan5/results_plan5.json'),
    ('Study 1 post hoc distribution', 'phytmo_pilot/results/plan5/posthoc_distribution_B16.json', 'phytmo_pilot/results/plan5/posthoc_distribution_B16.json'),
    ('Pilot 4 (correct-only calibration)', 'phytmo_pilot/results/pilot4/results_pilot4.json', 'phytmo_pilot/results/pilot4/results_pilot4.json'),
    ('Study 2 (GAITEX, PLAN6)', 'gaitex_plan6/results/results_plan6.json', 'gaitex_plan6/results/results_plan6.json'),
    ('Study 2 tuning (PSO / random)', 'gaitex_plan6/results/tuning_plan6.json', 'gaitex_plan6/results/tuning_plan6.json'),
    ('Study 2 post hoc other-leg check', 'gaitex_plan6/results/posthoc_uninvolved_sensors_RD.md', 'gaitex_plan6/results/posthoc_uninvolved_sensors_RD.md'),
    ('Study 3 (MLP, PLAN8)', 'stronger_plan8/results/results_plan8.json', 'stronger_plan8/results/results_plan8.json'),
    ('Camera, primary (PLAN7)', 'camera_plan7/results/results_plan7_primary.json', 'camera_plan7/results/results_plan7.json'),
    ('Camera, front view (PLAN7 Addendum D)', 'camera_plan7/results/results_plan7_front.json', 'camera_plan7/results/results_plan7_front.json'),
]


def flat(x, p=''):
    if isinstance(x, dict):
        for k, v in x.items():
            if str(k).lower() not in SKIP:
                yield from flat(v, f'{p}/{k}')
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from flat(v, f'{p}[{i}]')
    else:
        yield p, x


def compare(a, b):
    if a.endswith('.md'):
        la = [l for l in open(a).read().splitlines() if 'untime' not in l]
        lb = [l for l in open(b).read().splitlines() if 'untime' not in l]
        return la == lb, len(la), 0.0, ('identical text' if la == lb else 'text differs')
    A, B = dict(flat(json.load(open(a)))), dict(flat(json.load(open(b))))
    if A.keys() != B.keys():
        return False, len(A), None, f'different structure ({len(A.keys() ^ B.keys())} fields differ)'
    worst, bad = 0.0, 0
    for k in A:
        x, y = A[k], B[k]
        if isinstance(x, bool) or isinstance(y, bool):
            bad += not (isinstance(x, bool) and isinstance(y, bool) and x == y)
        elif isinstance(x, (int, float)) and isinstance(y, (int, float)):
            if math.isnan(x) or math.isnan(y):
                bad += not (math.isnan(x) and math.isnan(y)); continue
            if math.isinf(x) or math.isinf(y):
                bad += x != y; continue
            d = abs(x - y); worst = max(worst, d); bad += d > 1e-9
        elif x != y:
            bad += 1
    return bad == 0, len(A), worst, f'{bad} values differ'


L = [f'# Re-run report ({datetime.datetime.now():%Y-%m-%d %H:%M})\n', f'Re-run folder: `{RR}`\n',
     '| Study | Values compared | Max difference | Result |', '|---|---|---|---|']
ok_all = True
for name, o, r in PAIRS:
    po, pr = os.path.join(ROOT, o), os.path.join(RR, r)
    if not os.path.exists(pr):
        L.append(f'| {name} | – | – | ⏳ not run yet (`{r}` missing) |'); ok_all = False; continue
    ok, n, worst, msg = compare(po, pr)
    ok_all &= ok
    L.append(f'| {name} | {n} | {"–" if worst is None else f"{worst:.1e}"} | {"✅ identical" if ok else "❌ " + msg} |')
L.append('\n' + ('**All re-runs reproduced the saved results.**' if ok_all else '**Not all studies are complete or identical yet; see the table.**'))
out = '\n'.join(L) + '\n'
print(out)
if os.path.isdir(RR):
    open(os.path.join(RR, 'RERUN_REPORT.md'), 'w').write(out)

# Nonzero status makes missing or mismatching outputs visible to automation.
sys.exit(0 if ok_all else 1)
