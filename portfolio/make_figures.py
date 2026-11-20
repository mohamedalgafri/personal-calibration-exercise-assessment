"""Builds the portfolio figures as standalone SVG files from the SAVED results only (no model is re-run).
Usage (from UNESP_DHT): python3 -P portfolio/make_figures.py  -> portfolio/figures/*.svg + figures_data.json"""
import os, json, collections, re
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = os.path.join(ROOT, 'portfolio', 'figures'); os.makedirs(OUT, exist_ok=True)
J = lambda p: json.load(open(os.path.join(ROOT, p)))
INK, MUTED, GRID, A, B, C, NEG = '#1f2937', '#6b7280', '#e5e7eb', '#2563eb', '#f59e0b', '#10b981', '#dc2626'
FONT = 'font-family="Inter, Helvetica, Arial, sans-serif"'
DATA = {}


def svg(w, h, body, title):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" {FONT}>'
            f'<title>{title}</title><rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>')


def text(x, y, s, size=12, anchor='start', color=INK, weight='normal'):
    s = str(s).replace('&', '&amp;').replace('<', '&lt;')
    return f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{color}" font-weight="{weight}">{s}</text>'


def save(name, s):
    open(os.path.join(OUT, name), 'w').write(s)


def person_means(rows, key):
    d = collections.defaultdict(list)
    for r in rows:
        d[r['person']].append(r[key])
    return {p: float(np.mean(v)) for p, v in d.items()}


# ---------- F2: PHYTMO per-person gain (ADAPT16 - GEN), 8 cells ----------
R5 = J('phytmo_pilot/results/plan5/results_plan5.json')['results']
cells = list(R5.keys())
W, H, L, T, PW = 820, 380, 70, 50, 85
ymin, ymax = -20, 50
yy = lambda v: T + (ymax - v) / (ymax - ymin) * 260
b = [text(W / 2, 24, 'Study 1 (PHYTMO): gain from 16 of the person\'s own labelled windows, per person', 15, 'middle', weight='bold')]
for v in range(ymin, ymax + 1, 10):
    b.append(f'<line x1="{L}" x2="{W-20}" y1="{yy(v):.1f}" y2="{yy(v):.1f}" stroke="{GRID if v else INK}" stroke-width="{1 if v else 1.2}"/>')
    b.append(text(L - 8, yy(v) + 4, f'{v:+d}' if v else '0', 11, 'end', MUTED))
b.append(text(18, T + 130, 'adapted − general (points)', 11, 'middle', MUTED).replace('<text', '<text transform="rotate(-90 18 180)"'))
f2 = {}
for i, c in enumerate(cells):
    g, a = person_means(R5[c], 'GEN'), person_means(R5[c], 'ADAPT16')
    d = np.array([(a[p] - g[p]) * 100 for p in g])
    f2[c] = dict(n=len(d), mean=float(d.mean()), better=int((d > .5).sum()), worse=int((d < -.5).sum()))
    cx = L + 30 + i * PW
    rng = np.random.default_rng(i)
    for v in d:
        col = A if v > .5 else (NEG if v < -.5 else MUTED)
        b.append(f'<circle cx="{cx + rng.uniform(-14, 14):.1f}" cy="{yy(np.clip(v, ymin, ymax)):.1f}" r="3.2" fill="{col}" fill-opacity="0.75"/>')
    b.append(f'<line x1="{cx-20}" x2="{cx+20}" y1="{yy(d.mean()):.1f}" y2="{yy(d.mean()):.1f}" stroke="{INK}" stroke-width="2.5"/>')
    b.append(text(cx, T + 285, c, 11, 'middle'))
    b.append(text(cx, T + 300, f'{f2[c]["better"]}↑ {f2[c]["worse"]}↓', 11, 'middle', MUTED))
b.append(text(W / 2, H - 8, 'Each dot = one person (mean over 2 repeats). Bar = mean. Blue = better, red = worse (> 0.5 points). Same-session, healthy adults.', 10.5, 'middle', MUTED))
save('F2_phytmo_per_person.svg', svg(W, H, ''.join(b), 'PHYTMO per-person gain'))
DATA['F2'] = f2

# ---------- F3: gain vs general-model accuracy (PHYTMO + GAITEX, logistic regression) ----------
R6 = [r for r in J('gaitex_plan6/results/results_plan6.json')['results'] if r['task'] == '4class']
pts = []
for c in cells:
    g, a = person_means(R5[c], 'GEN'), person_means(R5[c], 'ADAPT16')
    pts += [('PHYTMO', g[p] * 100, (a[p] - g[p]) * 100) for p in g]
for ex in ('RD', 'RGS'):
    rr = [r for r in R6 if r['ex'] == ex.lower()]
    g, a = person_means(rr, 'GEN'), person_means(rr, 'ADAPT16')
    pts += [('GAITEX', g[p] * 100, (a[p] - g[p]) * 100) for p in g]
x = np.array([p[1] for p in pts]); y = np.array([p[2] for p in pts])
def avg_rank(v):
    o = np.argsort(v, kind='mergesort'); r = np.empty(len(v)); r[o] = np.arange(len(v)); vs = v[o]; i = 0
    while i < len(v):
        j = i
        while j + 1 < len(v) and vs[j + 1] == vs[i]: j += 1
        r[o[i:j + 1]] = (i + j) / 2; i = j + 1
    return r
rho = float(np.corrcoef(avg_rank(x), avg_rank(y))[0, 1])
W, H, L, T = 620, 400, 70, 50
xmin, xmax, ymin, ymax = 40, 100, -20, 50
px = lambda v: L + (v - xmin) / (xmax - xmin) * (W - L - 30)
py = lambda v: T + (ymax - v) / (ymax - ymin) * 290
b = [text(W / 2, 24, 'Where the general model is weaker, adaptation gains more', 15, 'middle', weight='bold')]
for v in range(-20, 51, 10):
    b.append(f'<line x1="{L}" x2="{W-30}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID if v else INK}"/>' + text(L - 8, py(v) + 4, f'{v:+d}' if v else '0', 11, 'end', MUTED))
for v in range(40, 101, 10):
    b.append(text(px(v), T + 310, f'{v}%', 11, 'middle', MUTED))
b.append(text(W / 2, T + 330, 'general model accuracy for the person (balanced accuracy)', 11.5, 'middle', MUTED))
b.append(text(18, 0, 'adapted − general (points)', 11, 'middle', MUTED).replace('<text', '<text transform="translate(0,200) rotate(-90 18 0)"'))
for dset, xv, yv in pts:
    b.append(f'<circle cx="{px(np.clip(xv, xmin, xmax)):.1f}" cy="{py(np.clip(yv, ymin, ymax)):.1f}" r="3.2" fill="{A if dset == "PHYTMO" else B}" fill-opacity="0.65"/>')
b.append(f'<circle cx="{W-200}" cy="{T+10}" r="4" fill="{A}"/>' + text(W - 190, T + 14, 'PHYTMO (8 cells)', 11))
b.append(f'<circle cx="{W-200}" cy="{T+28}" r="4" fill="{B}"/>' + text(W - 190, T + 32, 'GAITEX (2 exercises)', 11))
b.append(text(W / 2, H - 8, f'{len(pts)} person × cell points; Spearman ρ = {rho:.2f}. Descriptive: partly expected, since there is less room to gain near 100%.', 10.5, 'middle', MUTED))
save('F3_gain_vs_general.svg', svg(W, H, ''.join(b), 'Gain vs general model accuracy'))
DATA['F3'] = dict(n=len(pts), spearman=rho)

# ---------- F4: GAITEX means: GEN, another person's examples, own examples ----------
W, H, L, T = 560, 330, 60, 50
b = [text(W / 2, 24, 'Study 2 (GAITEX, another laboratory): own examples vs another person\'s', 14, 'middle', weight='bold')]
py = lambda v: T + (100 - v) / 40 * 220
for v in range(60, 101, 10):
    b.append(f'<line x1="{L}" x2="{W-20}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID}"/>' + text(L - 8, py(v) + 4, f'{v}%', 11, 'end', MUTED))
f4 = {}
for i, ex in enumerate(('RD', 'RGS')):
    rr = [r for r in R6 if r['ex'] == ex.lower()]
    vals = [('general', np.mean(list(person_means(rr, 'GEN').values())) * 100, MUTED),
            ("another person's 16", np.mean(list(person_means(rr, 'CTRLNEW16').values())) * 100, B),
            ("own 16", np.mean(list(person_means(rr, 'ADAPT16').values())) * 100, A)]
    f4[ex] = {k: float(v) for k, v, _ in vals}
    for j, (lab, v, col) in enumerate(vals):
        x0 = L + 30 + i * 240 + j * 62
        b.append(f'<rect x="{x0}" y="{py(v):.1f}" width="50" height="{py(60) - py(v):.1f}" fill="{col}" rx="3"/>')
        b.append(text(x0 + 25, py(v) - 6, f'{v:.1f}', 11, 'middle'))
        b.append(text(x0 + 25, py(60) + 16, lab.split(' ')[0] if j != 1 else 'other', 10.5, 'middle', MUTED))
    b.append(text(L + 30 + i * 240 + 87, py(60) + 34, {'RD': 'Resisted dorsiflexion (n = 19)', 'RGS': 'Gait-related exercise (n = 15)'}[ex], 11.5, 'middle'))
b.append(text(W / 2, H - 8, 'Mean balanced accuracy, 4 classes (correct + 3 named deviations). Axis starts at 60%.', 10.5, 'middle', MUTED))
save('F4_gaitex_means.svg', svg(W, H, ''.join(b), 'GAITEX means'))
DATA['F4'] = f4

# ---------- F5: camera view: share of repetitions with a joint missing > 20% of frames ----------
missing = {'front': {'far elbow': 0, 'far wrist': 0, 'other 10 joints': 0}, 'half-profile': {'far elbow': 54, 'far wrist': 38, 'other 10 joints': 0}}
W, H, L, T = 560, 300, 60, 50
b = [text(W / 2, 24, 'Camera extension: why the side view failed', 15, 'middle', weight='bold')]
py = lambda v: T + (60 - v) / 60 * 180
for v in range(0, 61, 20):
    b.append(f'<line x1="{L}" x2="{W-20}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID if v else INK}"/>' + text(L - 8, py(v) + 4, f'{v}%', 11, 'end', MUTED))
for i, view in enumerate(('front', 'half-profile')):
    for j, (joint, v) in enumerate(missing[view].items()):
        x0 = L + 30 + i * 240 + j * 62
        b.append(f'<rect x="{x0}" y="{py(v):.1f}" width="50" height="{max(py(0) - py(v), 1.5):.1f}" fill="{NEG if v else C}" rx="3"/>')
        b.append(text(x0 + 25, py(v) - 6, f'{v}%', 11, 'middle'))
        b.append(text(x0 + 25, py(0) + 16, joint.split(' ')[1] if j < 2 else 'others', 10.5, 'middle', MUTED))
    b.append(text(L + 30 + i * 240 + 87, py(0) + 34, f'{view} view ({197 if view == "front" else 189} repetitions)', 11.5, 'middle'))
b.append(text(W / 2, H - 8, 'Share of repetitions where the joint was not detected in > 20% of frames (MediaPipe lite, REHAB24-6 camera 17).', 10.5, 'middle', MUTED))
save('F5_camera_view.svg', svg(W, H, ''.join(b), 'Camera view'))

# ---------- F6: PSO identity check ----------
W, H, L, T = 560, 300, 60, 50
b = [text(W / 2, 24, 'In this test, PSO picked up person identity when its fitness ignored persons', 14, 'middle', weight='bold')]
py = lambda v: T + (80 - v) / 80 * 180
for v in range(0, 81, 20):
    b.append(f'<line x1="{L}" x2="{W-20}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID if v else INK}"/>' + text(L - 8, py(v) + 4, f'{v}%', 11, 'end', MUTED))
for i, (lab, pso, rnd) in enumerate((('record-wise fitness', 76.1, 24.1), ('person-grouped fitness', 26.1, 25.5))):
    for j, (v, col, k) in enumerate(((pso, NEG if i == 0 else A, 'PSO'), (rnd, MUTED, 'random lists'))):
        x0 = L + 40 + i * 240 + j * 75
        b.append(f'<rect x="{x0}" y="{py(v):.1f}" width="60" height="{py(0) - py(v):.1f}" fill="{col}" rx="3"/>')
        b.append(text(x0 + 30, py(v) - 6, f'{v:.0f}%', 11, 'middle'))
        b.append(text(x0 + 30, py(0) + 16, k, 10.5, 'middle', MUTED))
    b.append(text(L + 40 + i * 240 + 67, py(0) + 34, lab, 11.5, 'middle'))
b.append(text(W / 2, H - 8, 'Share of selected features that were synthetic person codes (voice data, 42 persons; pre-planned check).', 10.5, 'middle', MUTED))
save('F6_pso_identity.svg', svg(W, H, ''.join(b), 'PSO identity check'))

# ---------- F7: quantification with personal calibration (natural recordings) ----------
txt = open(os.path.join(ROOT, 'quantification_pilot/results/summary_calibration.md')).read().split('## shifted')[0]
rows = re.findall(r'\| (\d+) \(≈(\d+) s\) \| [\d.]+ \(([\d.]+) min.*?\| [^|]+\| [^|]+\| [^|]+\| [\d.]+ \(([\d.]+) min', txt)
W, H, L, T = 560, 300, 60, 50
b = [text(W / 2, 24, 'Quantification: a few labelled seconds per activity from the new person', 14, 'middle', weight='bold')]
py = lambda v: T + 12 + (12 - v) / 12 * 168
for v in range(0, 13, 4):
    b.append(f'<line x1="{L}" x2="{W-20}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID if v else INK}"/>' + text(L - 8, py(v) + 4, f'{v}', 11, 'end', MUTED))
b.append(text(16, 0, 'minutes misallocated per activity / 8 h', 10.5, 'middle', MUTED).replace('<text', '<text transform="translate(0,140) rotate(-90 16 0)"'))
f7 = []
for i, (k, sec, cc, ft) in enumerate(rows):
    cc, ft = float(cc), float(ft); f7.append(dict(k=int(k), sec=int(sec), CC=cc, FT_CC=ft))
    for j, (v, col) in enumerate(((cc, MUTED), (ft, A))):
        x0 = L + 25 + i * 115 + j * 42
        b.append(f'<rect x="{x0}" y="{py(v):.1f}" width="36" height="{py(0) - py(v):.1f}" fill="{col}" rx="3"/>')
        b.append(text(x0 + 18, py(v) - 6, f'{v:.1f}', 10.5, 'middle'))
    b.append(text(L + 25 + i * 115 + 39, py(0) + 16, f'≈{sec} s', 11, 'middle'))
b.append(f'<rect x="{L+10}" y="{T-8}" width="10" height="10" fill="{MUTED}"/>' + text(L + 25, T + 1, 'classify and count', 11))
b.append(f'<rect x="{L+160}" y="{T-8}" width="10" height="10" fill="{A}"/>' + text(L + 175, T + 1, 'after personal fine-tuning', 11))
b.append(text(W / 2, H - 8, 'UCI HAR, 30 persons, natural recordings; follow-up planned after the first pilot. Not exercise data.', 10.5, 'middle', MUTED))
save('F7_quantification_calibration.svg', svg(W, H, ''.join(b), 'Quantification calibration'))
DATA['F7'] = f7

# ---------- F8: 24-month plan ----------
phases = [('Courses, Portuguese, re-running the preparatory analyses', 1, 6, MUTED), ('Literature map; qualification plan for the stronger model', 1, 6, A),
          ('Open evaluation package; stability audit; dashboard skeleton', 6, 12, A), ('Frozen protocol; search for multi-session data', 9, 12, B),
          ('Qualifying exam; confirmatory analysis on an unopened dataset', 12, 15, NEG), ('Person-level analysis; manuscript; dashboard', 15, 20, A),
          ('Extensions if agreed (video, adapt-or-not, quantification)', 15, 20, C), ('Dissertation, defence, public release', 20, 24, INK)]
W, H, L, T = 820, 330, 360, 50
px = lambda m: L + (m - 1) / 24 * (W - L - 20)
b = [text(W / 2, 24, 'Illustrative 24-month plan (to be agreed with the advisor)', 15, 'middle', weight='bold')]
for m in (1, 6, 12, 18, 24):
    b.append(f'<line x1="{px(m):.1f}" x2="{px(m):.1f}" y1="{T}" y2="{T + 8 * 30}" stroke="{GRID}"/>' + text(px(m), T + 8 * 30 + 16, f'month {m}', 10.5, 'middle', MUTED))
for i, (lab, s, e, col) in enumerate(phases):
    y0 = T + i * 30
    b.append(text(L - 10, y0 + 17, lab, 11.5, 'end'))
    b.append(f'<rect x="{px(s):.1f}" y="{y0 + 5}" width="{px(e + 1) - px(s):.1f}" height="18" rx="4" fill="{col}" fill-opacity="0.85"/>')
save('F8_timeline.svg', svg(W, H, ''.join(b), '24-month plan'))

json.dump(DATA, open(os.path.join(ROOT, 'portfolio', 'figures_data.json'), 'w'), indent=1)
print(json.dumps(DATA, indent=1)[:1500])

if os.path.exists(os.path.join(ROOT, 'camera_plan7/results/PM_013_jpg1.json')) and os.path.exists(os.path.join(ROOT, 'camera_plan7/data/raw/PM_013-c17-30fps.npy')):
    # ---------- F9: camera proof - wrist height, markerless video vs motion capture (PM_013) ----------
    P13 = J('camera_plan7/results/PM_013_jpg1.json')
    M13 = np.load(os.path.join(ROOT, 'camera_plan7/data/raw/PM_013-c17-30fps.npy'))
    mp = np.array([np.mean([f[15][1], f[16][1]]) if f else np.nan for f in P13['frames']], float)
    mc = M13[:, [9, 14], 1].astype(float).mean(1)
    n = min(len(mp), len(mc)); mp, mc = mp[:n], mc[:n]
    starts = list(range(0, n - 30 * 40, 30)); s0 = max(starts, key=lambda k: np.nanstd(np.diff(mc[k:k + 30 * 40]))); s1 = s0 + 30 * 40
    a_, b_ = mp[s0:s1], mc[s0:s1]
    z = lambda v: (v - np.nanmean(v)) / np.nanstd(v)
    a_, b_ = -z(a_), -z(b_)          # image y grows downwards: flip so that up = up
    ok = ~np.isnan(a_) & ~np.isnan(b_); r9 = float(np.corrcoef(a_[ok], b_[ok])[0, 1])
    W, H, L, T = 820, 300, 60, 50
    px = lambda i: L + i / (s1 - s0) * (W - L - 20)
    py = lambda v: T + (3 - v) / 6 * 190
    b = [text(W / 2, 24, 'Markerless keypoints track motion capture (one REHAB24-6 video, 40 s)', 15, 'middle', weight='bold')]
    for v in (-3, 0, 3):
        b.append(f'<line x1="{L}" x2="{W-20}" y1="{py(v):.1f}" y2="{py(v):.1f}" stroke="{GRID}"/>')
    for sec in range(0, 41, 10):
        b.append(text(px(sec * 30), T + 210, f'{sec} s', 10.5, 'middle', MUTED))
    for arr, col, wdt in ((b_, INK, 2.2), (a_, A, 1.4)):
        pts_ = ' '.join(f'{px(i):.1f},{py(np.clip(v, -3, 3)):.1f}' for i, v in enumerate(arr) if not np.isnan(v))
        b.append(f'<polyline points="{pts_}" fill="none" stroke="{col}" stroke-width="{wdt}" stroke-opacity="0.9"/>')
    b.append(f'<line x1="{L+10}" x2="{L+34}" y1="{T-6}" y2="{T-6}" stroke="{INK}" stroke-width="2.2"/>' + text(L + 40, T - 2, 'motion capture (projected to the camera)', 11))
    b.append(f'<line x1="{L+330}" x2="{L+354}" y1="{T-6}" y2="{T-6}" stroke="{A}" stroke-width="2"/>' + text(L + 360, T - 2, 'MediaPipe in the browser (every frame)', 11))
    b.append(text(W / 2, H - 8, f'Mean wrist height, standardised; correlation over this window r = {r9:.4f} (whole-video check: lag 0 frames, r = 0.999).', 10.5, 'middle', MUTED))
    save('F9_camera_proof.svg', svg(W, H, ''.join(b), 'Camera proof'))
    DATA['F9'] = dict(r_window=r9)
else:
    print('F9 omitted: optional source keypoints/reference were not acquired locally.')

# ---------- F1: pipeline / study design diagram ----------
W, H = 820, 345
b = [text(W / 2, 24, 'How one new person is evaluated (every strategy sees the same evaluation data)', 15, 'middle', weight='bold')]
def box(x, y, w, h, t1, t2='', col=GRID, fill='#f9fafb'):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{col}" stroke-width="1.5"/>'
            + text(x + w / 2, y + (h / 2 if not t2 else h / 2 - 5), t1, 12, 'middle', weight='bold') + (text(x + w / 2, y + h / 2 + 12, t2, 10.5, 'middle', MUTED) if t2 else ''))
def arrow(x1, y1, x2, y2):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{MUTED}" stroke-width="1.5" marker-end="url(#ar)"/>'
b.insert(0, f'<defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker></defs>')
b.append(box(20, 60, 170, 60, 'Other persons', 'train the general model'))
b.append(box(20, 200, 170, 60, 'The new person', 'never seen in training'))
b.append(box(240, 200, 150, 28, 'calibration examples', '', A, '#eff6ff'))
b.append(box(240, 236, 150, 28, 'evaluation examples', '', INK, '#ffffff'))
b.append(arrow(190, 230, 238, 214)); b.append(arrow(190, 230, 238, 250))
strat = [('General model', 'no personal data', MUTED), ('Label-free adjustment', 'calibration data, no labels', C), ('Adapted (own labels)', 'calibration data + labels', A),
         ("Another person's examples", 'same number, unseen donor', B), ('Replay control', 'same number, already seen', B), ('Personal-only model', 'own labels only', MUTED)]
for i, (t1, t2, col) in enumerate(strat):
    y = 50 + i * 42
    b.append(box(450, y, 190, 36, t1, t2, col))
    b.append(arrow(190, 90, 448, y + 18) if i in (0, 3, 4) else arrow(390, 214, 448, y + 18))
b.append(f'<rect x="680" y="110" width="130" height="130" rx="8" fill="#ffffff" stroke="{INK}" stroke-width="1.5"/>' + text(745, 130, 'Per person', 12, 'middle', weight='bold'))
for i, s in enumerate(['balanced accuracy', 'missed deviations', 'false alarms', 'better or worse?', 'stable over splits?']):
    b.append(text(745, 152 + i * 17, s, 10.5, 'middle', MUTED))
for i in range(6):
    b.append(arrow(640, 68 + i * 42, 678, 118 + i * 22))
b.append(f'<path d="M390,250 L420,250 L420,300 L745,300 L745,242" fill="none" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#ar)"/>' + text(560, 295, 'same held-out evaluation examples for every strategy', 10, 'middle', MUTED))
b.append(text(W / 2, H - 8, 'Planned master\'s design; a qualified stronger general model and bias-only recalibration are added to the comparison.', 10.5, 'middle', MUTED))
save('F1_design.svg', svg(W, H, ''.join(b), 'Study design'))
json.dump(DATA, open(os.path.join(ROOT, 'portfolio', 'figures_data.json'), 'w'), indent=1)
if 'F9' in DATA:
    print('F9 r_window', DATA['F9'])
