"""Build a self-contained HTML report (inline SVG, no external libs) and an English
markdown summary from results_ex1.json.
Usage: python report.py <results_json> <out_dir>"""
import sys, json, html
import numpy as np

R = json.load(open(sys.argv[1]))
OUT = sys.argv[2]
import os
CS_PATH = os.path.join(os.path.dirname(sys.argv[1]), "consensus_scaling_ex1.json")
CS = json.load(open(CS_PATH)) if os.path.exists(CS_PATH) else None
M = R["methods"]

LABEL = {"mean": "Mean predictor", "all": "All features", "all_krr": "All features (kernel)",
         "relieff": "RReliefF top-k", "spearman": "Spearman top-k",
         "bpso": "Binary PSO (1 run)", "consensus": "PSO consensus"}
LABEL_AR = {"mean": "توقّع المتوسط (مرجع)", "all": "كل الخصائص", "all_krr": "كل الخصائص (kernel)",
            "relieff": "RReliefF", "spearman": "Spearman",
            "bpso": "PSO تشغيلة وحدة", "consensus": "PSO بالإجماع"}
ORDER = ["mean", "all", "all_krr", "relieff", "spearman", "bpso", "consensus"]

FEAT_AR = {"shoulder_elev": "رفع الكتف", "elbow_flex": "ثني الكوع", "trunk_sagittal": "ميل الجذع للأمام/الخلف",
           "trunk_lateral": "ميل الجذع للجنب", "wrist_height": "ارتفاع الرسغ",
           "head_forward": "تقدّم الرأس", "hands_distance": "المسافة بين اليدين", "reps_count": "عدد التكرارات",
           "duration_s": "مدّة التمرين", "rep_duration_s": "مدّة التكرار"}
STAT_AR = {"mean": "المتوسط", "std": "التذبذب", "min": "الحد الأدنى", "max": "الحد الأقصى", "range": "مدى الحركة",
           "vel_mean": "متوسط السرعة", "vel_max": "أقصى سرعة", "jerk": "عدم النعومة (jerk)",
           "absdiff": "فرق يمين/يسار", "range_diff": "فرق المدى يمين/يسار", "corr": "تناسق يمين/يسار"}


def feat_ar(name):
    base, _, stat = name.partition("__")
    side = ""
    if base.endswith("_L"):
        base, side = base[:-2], " (يسار)"
    elif base.endswith("_R"):
        base, side = base[:-2], " (يمين)"
    sym = base.startswith("sym_")
    if sym:
        base = base[4:]
    b = FEAT_AR.get(base, base)
    st = STAT_AR.get(stat, stat)
    return f"{b}{side}: {st}" if stat else b


def fmt(x, n=2):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{n}f}"


# ------------------------------------------------------------------ charts (inline SVG)
def bar_chart(rows, xmax, unit="", width=640, highlight=()):
    """rows: list of (label, value, err). Horizontal bars."""
    h = 34 * len(rows) + 30
    left, right = 190, 70
    sc = (width - left - right) / xmax
    out = [f'<svg viewBox="0 0 {width} {h}" class="chart" role="img">']
    for t in np.linspace(0, xmax, 5):
        x = left + t * sc
        out.append(f'<line x1="{x:.1f}" y1="8" x2="{x:.1f}" y2="{h-22}" class="grid"/>')
        out.append(f'<text x="{x:.1f}" y="{h-6}" class="tick" text-anchor="middle">{t:.0f}{unit}</text>')
    for i, (lab, v, e) in enumerate(rows):
        y = 12 + i * 34
        cls = "bar hl" if lab in highlight else "bar"
        out.append(f'<text x="{left-10}" y="{y+16}" class="lab" text-anchor="end">{html.escape(lab)}</text>')
        out.append(f'<rect x="{left}" y="{y+4}" width="{max(v*sc,1):.1f}" height="18" rx="3" class="{cls}"/>')
        if e:
            out.append(f'<line x1="{left+(v-e)*sc:.1f}" y1="{y+13}" x2="{left+(v+e)*sc:.1f}" y2="{y+13}" class="err"/>')
        out.append(f'<text x="{left+(v+(e or 0))*sc+6:.1f}" y="{y+17}" class="val">{v:.2f}</text>')
    out.append("</svg>")
    return "\n".join(out)


def scatter(points, width=640, height=320):
    """points: (label, size, stability, lo, hi)"""
    left, bottom, top, right = 60, 40, 16, 20
    xs = [p[1] for p in points]
    xmax = max(10, max(xs) * 1.15)
    sx = (width - left - right) / xmax
    sy = (height - top - bottom) / 1.0
    out = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">']
    for t in np.linspace(0, 1, 6):
        y = height - bottom - t * sy
        out.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width-right}" y2="{y:.1f}" class="grid"/>')
        out.append(f'<text x="{left-8}" y="{y+4:.1f}" class="tick" text-anchor="end">{t:.1f}</text>')
    for t in np.linspace(0, xmax, 6):
        x = left + t * sx
        out.append(f'<text x="{x:.1f}" y="{height-bottom+18}" class="tick" text-anchor="middle">{t:.0f}</text>')
    out.append(f'<text x="{(width)/2}" y="{height-4}" class="axis" text-anchor="middle">عدد الخصائص المختارة (متوسط)</text>')
    out.append(f'<text x="14" y="{height/2}" class="axis" text-anchor="middle" transform="rotate(-90 14 {height/2})">الثبات (Nogueira)</text>')
    for lab, s, st, lo, hi in points:
        x = left + s * sx
        y = height - bottom - max(st, 0) * sy
        if np.isfinite(lo):
            out.append(f'<line x1="{x:.1f}" y1="{height-bottom-max(lo,0)*sy:.1f}" x2="{x:.1f}" y2="{height-bottom-min(hi,1)*sy:.1f}" class="err"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" class="dot"/>')
        out.append(f'<text x="{x+10:.1f}" y="{y-8:.1f}" class="lab">{html.escape(lab)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def line_chart(series_list, xs, width=640, height=300, ylab="", xlab="", ref=None):
    """series_list: list of (label, ys, lo, hi). y in [0,1]."""
    left, bottom, top, right = 60, 44, 16, 120
    xmax = max(xs)
    sx = lambda v: left + (v / xmax) * (width - left - right)
    sy = lambda v: height - bottom - max(min(v, 1), 0) * (height - top - bottom)
    out = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img">']
    for t in np.linspace(0, 1, 6):
        out.append(f'<line x1="{left}" y1="{sy(t):.1f}" x2="{width-right}" y2="{sy(t):.1f}" class="grid"/>')
        out.append(f'<text x="{left-8}" y="{sy(t)+4:.1f}" class="tick" text-anchor="end">{t:.1f}</text>')
    for v in xs:
        out.append(f'<text x="{sx(v):.1f}" y="{height-bottom+18}" class="tick" text-anchor="middle">{v}</text>')
    out.append(f'<text x="{(width-right+left)/2}" y="{height-4}" class="axis" text-anchor="middle">{xlab}</text>')
    out.append(f'<text x="14" y="{height/2}" class="axis" text-anchor="middle" transform="rotate(-90 14 {height/2})">{ylab}</text>')
    if ref:
        rv, rl = ref
        out.append(f'<line x1="{left}" y1="{sy(rv):.1f}" x2="{width-right}" y2="{sy(rv):.1f}" class="refl"/>')
        out.append(f'<text x="{width-right+6}" y="{sy(rv)+4:.1f}" class="lab">{html.escape(rl)}</text>')
    cls = ["ln1", "ln2", "ln3"]
    for i, (lab, ys, lo, hi) in enumerate(series_list):
        pts = " ".join(f"{sx(x):.1f},{sy(v):.1f}" for x, v in zip(xs, ys))
        out.append(f'<polyline points="{pts}" class="line {cls[i%3]}"/>')
        for x, v, a, b in zip(xs, ys, lo, hi):
            out.append(f'<line x1="{sx(x):.1f}" y1="{sy(a):.1f}" x2="{sx(x):.1f}" y2="{sy(b):.1f}" class="err {cls[i%3]}"/>')
            out.append(f'<circle cx="{sx(x):.1f}" cy="{sy(v):.1f}" r="4" class="pt {cls[i%3]}"/>')
        out.append(f'<text x="{sx(xs[-1])+10:.1f}" y="{sy(ys[-1])+4:.1f}" class="lab {cls[i%3]}t">{html.escape(lab)}</text>')
    out.append("</svg>")
    return "\n".join(out)


# ------------------------------------------------------------------ content
best_sel = min(["relieff", "spearman", "bpso", "consensus"], key=lambda m: M[m]["mae_mean"])
rows_mae = [(LABEL_AR[m], M[m]["mae_mean"], M[m]["mae_sd"]) for m in ORDER]
xmax = max(v + e for _, v, e in rows_mae) * 1.15
chart_mae = bar_chart(rows_mae, xmax, highlight=(LABEL_AR["consensus"], LABEL_AR["bpso"]))
pts = [(LABEL_AR[m], M[m]["size_mean"], M[m]["stability"], M[m]["stab_lo"], M[m]["stab_hi"])
       for m in ["relieff", "spearman", "bpso", "consensus"]]
chart_stab = scatter(pts)
L = R["leakage_demo"]
chart_leak = bar_chart([("تقسيم عشوائي للعيّنات (تسريب)", L["random"]["mae_mean"], L["random"]["mae_sd"]),
                        ("تقسيم حسب الشخص (صحيح)", L["grouped"]["mae_mean"], L["grouped"]["mae_sd"])],
                       max(L["random"]["mae_mean"] + L["random"]["mae_sd"], L["grouped"]["mae_mean"] + L["grouped"]["mae_sd"]) * 1.2)
names = R["feature_names"]
freq = np.array(M["consensus"]["freq"])
top = np.argsort(-freq)[:10]
chart_feat = bar_chart([(feat_ar(names[i]), float(freq[i]) * 100, 0) for i in top if freq[i] > 0], 100, unit="%")

W = R["wilcoxon_vs_all"]
table = []
for m in ORDER:
    e = M[m]
    st = (f'{fmt(e["stability"])} <span class="ci">[{fmt(e["stab_lo"])}, {fmt(e["stab_hi"])}]</span>'
          if "stability" in e else "—")
    size = f'{e["size_mean"]:.1f} ± {e["size_sd"]:.1f}' if "size_sd" in e else (f'{e["size_mean"]:.0f}' if e["size_mean"] else "0")
    p = ("&lt;0.001" if W[m]["p"] < 0.001 else fmt(W[m]["p"], 3)) if m in W else "—"
    table.append(f'<tr><td>{LABEL_AR[m]}<div class="en">{LABEL[m]}</div></td><td>{e["mae_mean"]:.2f} ± {e["mae_sd"]:.2f}</td>'
                 f'<td>{"—" if m == "mean" else fmt(e["rho_mean"])}</td><td>{size}</td><td>{st}</td><td>{p}</td></tr>')

P = R["protocol"]
S = R["score"]
L_r, L_g = L["random"]["mae_mean"], L["grouped"]["mae_mean"]
leak_pct = 100 * (L_g - L_r) / L_g
top_feats_ar = "، ".join(feat_ar(names[i]) for i in top[:4])

# consensus scaling (H2 follow-up)
cs_html, cs_line, cs_en = "", "", ""
if CS:
    rows = [r for r in CS["rows"]]
    runs = CS["runs"]
    ser = []
    for t, lab in [(0.5, "عتبة 50%"), (0.3, "عتبة 30%"), (0.7, "عتبة 70%")]:
        rr = [next(x for x in rows if x["runs"] == k and x["thr"] == t) for k in runs]
        ser.append((lab, [x["stability"] for x in rr], [x["lo"] for x in rr], [x["hi"] for x in rr]))
    _filt = max(M["relieff"]["stability"], M["spearman"]["stability"])
    chart_cs = line_chart(ser, runs, ylab="الثبات (Nogueira)", xlab="عدد تشغيلات PSO اللي بندمجها",
                          ref=(_filt, f"filter ({_filt:.2f})"))
    r1 = next(x for x in rows if x["runs"] == 1 and x["thr"] == 0.5)
    last = [x for x in rows if x["runs"] == runs[-1]]
    best = max(last, key=lambda x: x["stability"])
    filt = max(M["relieff"]["stability"], M["spearman"]["stability"])
    trows = "".join(f'<tr><td>{x["runs"]}</td><td>{int(x["thr"]*100)}%</td><td>{x["stability"]:.2f} <span class="ci">[{x["lo"]:.2f}, {x["hi"]:.2f}]</span></td><td>{x["size"]:.1f}</td><td>{x["fold_mae"]:.2f}</td></tr>' for x in rows if x["thr"] in (0.3, 0.5))
    cs_html = f"""<h2>4) هل الإجماع بيرفع الثبات؟ (اختبار مباشر لـ H2)</h2>
<div class="card">{chart_cs}</div>
<div class="card tablewrap"><table><tr><th>عدد التشغيلات</th><th>العتبة</th><th>الثبات [95% CI]</th><th>عدد الخصائص</th><th>MAE (متوسط الطيّات)</th></tr>{trows}</table></div>
<p class="sub">{CS['n_repeats']}×5 طيّات، ونفس التقسيمات الخارجية للتجربة الأساسية. العتبة = بكم تشغيلة لازم تنختار الخاصية عشان تدخل بالإجماع. ثبات 30 تشغيلة PSO جوّا نفس الطيّة (نفس البيانات بالضبط): {CS['within_fold_stability_30runs']:.2f}.</p>
<div class="card warn"><b>القراءة الصادقة:</b> الإجماع بيرفع الثبات بشكل واضح ومتصاعد مع عدد التشغيلات (عند عتبة 30%)، <b>بس لسا أقل من طرق الـ filter البسيطة ({filt:.2f})</b>، والخطأ ما تحسّن. يعني الإجماع لحاله مش كافي. هاي بالضبط الفجوة اللي بتشتغل عليها الرسالة: fitness أقل ضجيجاً (inner CV مكرر)، وعقوبة على عدم الثبات، ومقارنة مع FSS.</div>"""
    cs_line = (f"<li><b>الإجماع بيساعد، بس مش كفاية:</b> دمج التشغيلات رفع الثبات من {r1['stability']:.2f} (تشغيلة وحدة) لـ {best['stability']:.2f} "
               f"({runs[-1]} تشغيلة، عتبة {int(best['thr']*100)}%، {best['size']:.0f} خاصية)، يعني تقريباً {best['stability']/max(r1['stability'],1e-6):.0f} أضعاف. "
               f"بس لسا أقل من الـ filter ({filt:.2f})، والخطأ ما تحسّن. <b>هاي الفجوة اللي الرسالة بتشتغل عليها.</b></li>")
    cs_en = (f" Combining many PSO runs (a consensus selection) increased stability from {r1['stability']:.2f} to {best['stability']:.2f} "
             f"({runs[-1]} runs), but it remained below the filter methods and did not improve the error, so consensus alone is not enough; "
             f"this is exactly the gap my project addresses.")

findings = f"""<div class="card find"><ul>
<li><b>البيانات بتكفّي والبروتوكول صارم:</b> {R['n_subjects']} شخص و{R['n_features']} خاصية حركية، والتقييم حسب الشخص مع اختيار متداخل. الكود كله اشتغل على بيانات حقيقية.</li>
<li><b>التوقّع ممكن بس متواضع:</b> أحسن نموذج (kernel ridge، كل الخصائص) وصل لـ MAE {M['all_krr']['mae_mean']:.2f} وρ = {M['all_krr']['rho_mean']:.2f}، مقابل {M['mean']['mae_mean']:.2f} لتوقّع المتوسط. أغلب العلامات قريبة من 50 (سقف)، فالفرق الممكن صغير أصلاً. <b>للمقارنة:</b> الأبحاث المنشورة على نفس التمرين وصلت ρ بين 0.41 و 0.55، وأحسن نموذج عميق مع augmentation وصل 0.76 (Abedi et al., 2024). يعني نتيجتنا معقولة (مع إنه التقسيمات مش متطابقة).</li>
<li><b>PSO العادي غير ثابت (دليل على H2):</b> ثبات تشغيلة وحدة = {M['bpso']['stability']:.2f}، يعني شبه عشوائي، مقابل {M['relieff']['stability']:.2f}–{M['spearman']['stability']:.2f} لطرق الـ filter. حتى على نفس البيانات بالضبط، تشغيلات PSO بتختار خصائص مختلفة (ثبات {R['bpso_within_fold_stability_mean']:.2f}).</li>
{cs_line}
<li><b>الخصائص المختارة إلها معنى سريري:</b> {top_feats_ar}. التمرين بيطلب رفع الذراعين ممدودتين لأعلى وبشكل متماثل. النموذج لقى لحاله إنه ثني الكوع، ورفع الكتف لمدى أقل، وعدم التماثل بين اليمين واليسار، مرتبطين بعلامة أقل.</li>
<li><b>التسريب مقاس:</b> لو قسّمنا النوافذ عشوائياً بدل ما نقسّم حسب الشخص، الخطأ بيطلع أقل بـ {leak_pct:.0f}% بشكل وهمي ({L_r:.2f} مقابل {L_g:.2f}).</li>
</ul></div>"""

english = (f"To check feasibility, I ran a small preliminary experiment on one KIMORE exercise (lifting of the arms; "
           f"{R['n_subjects']} people, {R['n_features']} kinematic features, person-level repeated cross-validation with nested feature selection). "
           f"The best model predicted the clinical score with a mean absolute error of {M['all_krr']['mae_mean']:.1f} points and a Spearman correlation of {M['all_krr']['rho_mean']:.2f}, "
           f"which is in the range of earlier published results for this exercise (0.41 to 0.55), but below the best deep-learning model with data augmentation "
           f"(0.76, Abedi et al., 2024); the evaluation splits are not identical, so this comparison is only indicative. "
           f"Most importantly for my research question, the features selected by a single binary-PSO run were almost random across data samples "
           f"(stability index {M['bpso']['stability']:.2f}, compared with {M['spearman']['stability']:.2f} for a simple filter)."
           + cs_en +
           f" The most frequently selected features were clinically meaningful (elbow flexion, the range of shoulder elevation and left/right asymmetry). "
           f"I also found that splitting the data by recording window instead of by person underestimates the error by about {leak_pct:.0f}%. "
           f"These results are preliminary, but they show that the pipeline works and that stability is a real, measurable problem worth studying.")

css = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a65;--line:#e4e1d9;--card:#ffffff;--acc:#2f6f5e;--acc2:#c47a2c;--bar:#9db8ae}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#151614;--fg:#ecebe6;--muted:#a3a29b;--line:#2c2d2a;--card:#1d1e1b;--acc:#79c2a9;--acc2:#e3a25e;--bar:#3f6157}}
:root[data-theme=dark]{--bg:#151614;--fg:#ecebe6;--muted:#a3a29b;--line:#2c2d2a;--card:#1d1e1b;--acc:#79c2a9;--acc2:#e3a25e;--bar:#3f6157}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.7 "Noto Naskh Arabic","Segoe UI",Tahoma,sans-serif}
main{max-width:920px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:1.7rem;margin:0 0 4px}h2{font-size:1.2rem;margin:40px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
.sub{color:var(--muted);margin:0 0 20px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:18px 0}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
.kpi b{display:block;font-size:1.5rem;color:var(--acc)}.kpi span{color:var(--muted);font-size:.9rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:12px 0}
table{width:100%;border-collapse:collapse;font-size:.92rem}th,td{padding:8px 6px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}
th{color:var(--muted);font-weight:600}.en{color:var(--muted);font-size:.8rem;direction:ltr;text-align:right}
.ci{color:var(--muted);font-size:.8rem}.tablewrap{overflow-x:auto}
.chart{width:100%;height:auto;direction:ltr}.chart .grid{stroke:var(--line)}.chart .tick,.chart .axis{fill:var(--muted);font-size:11px}
.chart .lab{fill:var(--fg);font-size:13px}.chart .val{fill:var(--muted);font-size:11px}.chart .bar{fill:var(--bar)}.chart .bar.hl{fill:var(--acc)}
.chart .err{stroke:var(--fg);stroke-width:1.5}.chart .dot{fill:var(--acc)}
.chart .line{fill:none;stroke-width:2.5}.chart .ln1{stroke:var(--acc);fill:var(--acc)}.chart .ln2{stroke:var(--acc2);fill:var(--acc2)}.chart .ln3{stroke:var(--muted);fill:var(--muted)}
.chart polyline.line{fill:none}.chart .ln1t{fill:var(--acc)}.chart .ln2t{fill:var(--acc2)}.chart .ln3t{fill:var(--muted)}
.find li{margin-bottom:8px}.chart .refl{stroke:var(--fg);stroke-dasharray:5 4;stroke-width:1.2}
.ltr{direction:ltr;text-align:left;font-family:Georgia,"Times New Roman",serif;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.warn{border-right:4px solid var(--acc2)}ul{padding-right:20px}code{direction:ltr;unicode-bidi:embed}
"""

cons, bp, al = M["consensus"], M["bpso"], M["all"]
html_out = f"""<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>تجربة KIMORE الأولية</title><style>{css}</style></head>
<body><main>
<h1>التجربة الأولية: KIMORE، تمرين 1 (رفع الذراعين)</h1>
<p class="sub">بيانات حقيقية من KIMORE (مرآة Zenodo، CC-BY 4.0) · تقييم على مستوى الشخص · {P['outer']} مع اختيار متداخل (nested) · {P['bpso_runs']} تشغيلات PSO لكل طيّة</p>

<div class="kpis">
<div class="kpi"><b>{R['n_subjects']}</b><span>شخص (بعد تجميع العيّنات حسب الشخص)</span></div>
<div class="kpi"><b>{R['n_features']}</b><span>خاصية حركية محسوبة</span></div>
<div class="kpi"><b>{fmt(bp['stability'])}</b><span>ثبات PSO (تشغيلة وحدة)</span></div>
<div class="kpi"><b>{fmt(cons['stability'])}</b><span>ثبات PSO بالإجماع</span></div>
</div>

<h2>الخلاصة</h2>
{findings}

<h2>1) النتائج الأساسية</h2>
<div class="card tablewrap"><table>
<tr><th>الطريقة</th><th>الخطأ MAE (نقاط)</th><th>Spearman ρ</th><th>عدد الخصائص</th><th>الثبات [95% CI]</th><th>p (مقابل كل الخصائص)</th></tr>
{''.join(table)}
</table></div>
<p class="sub">العلامة السريرية بهالتمرين: من {S['min']:.1f} لـ {S['max']:.1f} (المتوسط {S['mean']:.1f}، الانحراف {S['sd']:.1f}). MAE = متوسط الخطأ المطلق على العلامة. الأقل أحسن. p من اختبار Wilcoxon على أخطاء الطيّات.</p>

<h2>2) الخطأ حسب الطريقة</h2>
<div class="card">{chart_mae}</div>

<h2>3) الحجم مقابل الثبات (قلب H2)</h2>
<div class="card">{chart_stab}</div>
<p class="sub">الثبات = هل الطريقة بتختار نفس الخصائص لما تتغيّر بيانات التدريب. 1 = نفس الاختيار دائماً، 0 = كأنه عشوائي. الخطوط = فترة ثقة 95%.
متوسط ثبات PSO بين التشغيلات <b>جوّا نفس الطيّة</b> (نفس البيانات، بذرة عشوائية مختلفة): {fmt(R['bpso_within_fold_stability_mean'])}.</p>

{cs_html}

<h2>5) الخصائص الأكثر اختياراً (PSO بالإجماع)</h2>
<div class="card">{chart_feat}</div>
<p class="sub">النسبة = بكم طيّة (من {len(M['consensus']['fold_mae'])}) انختارت الخاصية.</p>

<h2>6) ليش التقييم حسب الشخص مهم (تسريب البيانات)</h2>
<div class="card">{chart_leak}</div>
<p class="sub">نفس النموذج (كل الخصائص) على {L['n_windows']} عيّنة (نوافذ 100 إطار). لما نقسّم النوافذ عشوائياً، نوافذ نفس الشخص بتظهر بالتدريب والاختبار، والخطأ بيطلع أقل بشكل وهمي.</p>

<h2>7) حدود هالتجربة (بصراحة)</h2>
<div class="card warn"><ul>
<li>تجربة <b>أولية</b>: تمرين واحد، {R['n_subjects']} شخص، نموذج خطّي (Ridge). مش نتيجة نهائية.</li>
<li>المرآة ما فيها رقم الشخص ولا مجموعته (سليم أو مريض). استرجعت حدود الأشخاص من: تغيّر العلامة، أو قفزة بالمكان <b>مع</b> تغيّر "بصمة الجسم" (أطوال العظام). القفزة بدون تغيّر البصمة اعتبرتها نفس الشخص، وهاد الخيار المحافظ ضد التسريب. طلع {R['n_subjects']} شخص، والورقة الأصلية فيها 78 بكل الأقسام. ما قدرت أعمل التحليل جوّا مجموعة المرضى.</li>
<li>تنظيف: انحذفت {R['leakage_demo']['n_windows'] - sum(R['windows_per_subject'])} نافذة من {R['leakage_demo']['n_windows']}، وهي نوافذ الشخص ماشي فيها باتجاه الكاميرا، أو الجزء العلوي فيها متتبَّع بشكل ضعيف.</li>
<li>بعض المشاركين عملوا التمرين <b>قاعدين</b> (الركبة بمستوى الورك)، فاستخدمت خصائص الجزء العلوي بس، والأطوال نسبة لطول الجذع. هيك ما انحذف حدا بشكل متحيّز.</li>
<li>الخصائص محسوبة من نوافذ مُعاد معالجتها بالمرآة، مش من التسجيل الخام.</li>
<li>قيم p (Wilcoxon على طيّات CV المكرر) <b>تقريبية</b>، لأن الطيّات مش مستقلة تماماً. بالرسالة بنستخدم اختبارات مصحّحة.</li>
<li>إعدادات PSO ما انضبطت بشكل منهجي (λ={P['pso']['lam']}، {P['pso']['n_particles']} جسيم، {P['pso']['n_iter']} تكرار، تحويل V-shaped).</li>
</ul></div>

<h2>8) فقرة جاهزة للإيميل (English)</h2>
<div class="ltr">{html.escape(english)}</div>

<h2>9) البروتوكول</h2>
<div class="card"><ul>
<li>التقسيم الخارجي: {P['outer']}. التقسيم الداخلي: {P['inner']}. كل اختيار للخصائص وكل ضبط للمعاملات صار <b>جوّا بيانات التدريب بس</b>.</li>
<li>النموذج: Ridge على خصائص معيارية. α من {P['alphas']} باختيار داخلي. Filters: top-k مع k من {P['ks']} باختيار داخلي.</li>
<li>Binary PSO: fitness = MAE داخلي ÷ MAE(المتوسط) + λ·(k/d). الإجماع = الخصائص اللي انختارت بـ ≥50% من التشغيلات.</li>
<li>الثبات: Nogueira, Sechidis &amp; Brown (2018)، مع فترة الثقة التقريبية من نفس الورقة.</li>
<li>الكود: <code>preliminary_experiment/code/</code> (numpy بس). وقت التشغيل: {R['runtime_s']/60:.1f} دقيقة.</li>
</ul></div>
</main></body></html>"""
open(f"{OUT}/report_ex1.html", "w").write(html_out)

# English summary for the email / working file
md = f"""# Preliminary experiment — KIMORE Exercise 1 (lifting of the arms)

Data: KIMORE (Zenodo mirror, CC-BY 4.0). {R['n_subjects']} people after grouping windows by person; {R['n_features']} kinematic features.
Protocol: {P['outer']} cross-validation, nested feature selection, Ridge regression, {P['bpso_runs']} PSO runs per fold.

| Method | MAE | Spearman | # features | Stability [95% CI] | p vs all |
|---|---|---|---|---|---|
""" + "\n".join(
    f"| {LABEL[m]} | {M[m]['mae_mean']:.2f} ± {M[m]['mae_sd']:.2f} | {'—' if m == 'mean' else fmt(M[m]['rho_mean'])} | "
    + (f"{M[m]['size_mean']:.1f}" if M[m].get('size_mean') else "0") + " | "
    + (f"{fmt(M[m]['stability'])} [{fmt(M[m]['stab_lo'])}, {fmt(M[m]['stab_hi'])}]" if 'stability' in M[m] else "—") + " | "
    + (("<0.001" if W[m]['p'] < 0.001 else fmt(W[m]['p'], 3)) if m in W else "—") + " |" for m in ORDER) + f"""

Leakage demo (window-level samples, all features): random split MAE {L['random']['mae_mean']:.2f} vs person-grouped split MAE {L['grouped']['mae_mean']:.2f}.
Mean PSO stability across runs on the same training data: {fmt(R['bpso_within_fold_stability_mean'])}.
"""
md += "\n## Paragraph for the email\n\n" + english + "\n"
open(f"{OUT}/summary_ex1.md", "w").write(md)
print("report written")
