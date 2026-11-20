"""PLAN5: GEN vs CTRL vs ADAPT vs PERS, per person, IMU and OPT (see ../PLAN5.md, hashed before download).
Usage: python3 -P run_plan5.py <raw_dir> <out_dir> [exercises]   env MODALITIES=IMU,OPT (default both)
Reuses LogReg / finetune / bal_acc / IMU feature code from run_phytmo.py unchanged."""
import sys, os, re, glob, json, time, collections
import numpy as np

RAW, OUT = sys.argv[1], sys.argv[2]
EXS = sys.argv[3:] or ["SQT", "HAA", "SQZ", "EAH"]
MODS = os.environ.get("MODALITIES", "IMU,OPT").split(",")
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_phytmo.py")).read()
src = src.split("# ---------------- experiment ----------------")[0]
g = {"__name__": "rp"}
sys.argv = [sys.argv[0], RAW, OUT]
exec(compile(src, "run_phytmo.py", "exec"), g)
LogReg, finetune, bal_acc, C = g["LogReg"], g["finetune"], g["bal_acc"], g["C"]
WIN, STEP = 200, 100
BUDGETS = [4, 8, 16]
UNILATERAL = {"HAA", "KFE"}
t0 = time.time()
os.makedirs(OUT, exist_ok=True)
log = []


def say(s):
    print(s, flush=True); log.append(s)


def windows(X):
    """X (T, channels) already trimmed -> per-window features (same 6 stats as run_phytmo)."""
    rows = []
    for st in range(0, len(X) - WIN + 1, STEP):
        w = X[st:st + WIN]
        rows.append(np.concatenate([w.mean(0), w.std(0), w.min(0), w.max(0), w.max(0) - w.min(0),
                                    np.abs(np.diff(w, axis=0)).mean(0)]))
    return np.array(rows) if rows else np.zeros((0, X.shape[1] * 6))


def trim(n):
    return int(0.25 * n), int(0.95 * n)


# ---------------- IMU ----------------
pat_imu = re.compile(r"([A-E])(\d\d)([A-Z]{3})([LR]?)([01])_(\d)\.csv$")


def load_imu(ex):
    rec, bad = collections.defaultdict(dict), []
    for f in glob.glob(os.path.join(RAW, "inertial", "*", "*", "*", f"*{ex}*.csv")):
        m = pat_imu.search(f)
        if not m or m.group(3) != ex:
            continue
        gg, nn, _, leg, P, S = m.groups()
        seg = f.split(os.sep)[-2]
        if ex in UNILATERAL and seg[0] != leg:
            continue
        A = np.genfromtxt(f, delimiter=",", skip_header=1, usecols=range(1, 7))
        if not np.isfinite(A).all():
            bad.append(f); continue
        rec[(gg + nn, leg, int(P), int(S))][seg[1:] if ex in UNILATERAL else seg] = A
    need = 2 if ex in UNILATERAL else 4
    out = {}
    for k, sens in rec.items():
        if len(sens) < need:
            continue
        names = sorted(sens); n = min(len(sens[s]) for s in names); a, b = trim(n)
        ch = []
        for s in names:
            A = sens[s][a:b]; gy, ac = A[:, :3], A[:, 3:]
            ch += [gy, np.linalg.norm(gy, axis=1, keepdims=True), ac, np.linalg.norm(ac, axis=1, keepdims=True)]
        out[k] = windows(np.hstack(ch))
    return out, bad


# ---------------- OPT ----------------
pat_opt = re.compile(r"([A-E])(\d\d)([A-Z]{3})([LR]?)([01])_(\d)_interp\.csv$")


def parse_opt(f):
    with open(f, errors="ignore") as fh:
        head = [next(fh).rstrip("\n").split(",") for _ in range(7)]
    typ, name, kind, axis = head[2], head[3], head[5], head[6]
    A = np.genfromtxt(f, delimiter=",", skip_header=7)
    bodies = {}
    for j in range(len(name)):
        if j < len(typ) and typ[j].strip() == "Rigid Body":
            b = name[j].strip()
            bodies.setdefault(b, {})[(kind[j].strip(), axis[j].strip())] = j
    out = {}
    for b, cols in bodies.items():
        try:
            q = A[:, [cols[("Rotation", a)] for a in "XYZW"]]
            p = A[:, [cols[("Position", a)] for a in "XYZ"]]
        except KeyError:
            continue
        out[b] = (q, p)
    return out


def opt_channels(q, p):
    q = q * np.where(q[:, 3:4] < 0, -1.0, 1.0)  # sign-normalise (w >= 0)
    pc = p - np.median(p, axis=0)
    v = np.vstack([np.zeros((1, 3)), np.diff(p, axis=0) * 100.0])
    sp = np.linalg.norm(v, axis=1, keepdims=True)
    qn = q / np.linalg.norm(q, axis=1, keepdims=True)
    dot = np.abs(np.sum(qn[1:] * qn[:-1], axis=1)).clip(0, 1)
    ang = np.concatenate([[0.0], 2 * np.arccos(dot) * 100.0])[:, None]
    return np.hstack([pc, v, sp, qn, ang])


def load_opt(ex):
    out, bad = {}, []
    for f in glob.glob(os.path.join(RAW, "optical interp", "rigid_bodies", "*", "*", f"*{ex}*_interp.csv")):
        m = pat_opt.search(f)
        if not m or m.group(3) != ex:
            continue
        gg, nn, _, leg, P, S = m.groups()
        bodies = parse_opt(f)
        if ex in UNILATERAL:
            want = ["shin", "thigh"] if leg == "R" else ["shin2", "thigh2"]
        else:
            want = ["shin", "thigh", "shin2", "thigh2"]
        if not all(w in bodies for w in want):
            bad.append(f + " (missing body)"); continue
        n = min(len(bodies[w][0]) for w in want)
        if any(not np.isfinite(bodies[w][0][:n]).all() or not np.isfinite(bodies[w][1][:n]).all() for w in want):
            bad.append(f); continue
        a, b = trim(n)
        ch = [opt_channels(bodies[w][0][a:b], bodies[w][1][a:b]) for w in want]
        out[(gg + nn, leg, int(P), int(S))] = windows(np.hstack(ch))
    return out, bad


# ---------------- per-exercise analysis ----------------
def series(W, p, S):
    """list of (leg, X, y) recordings of person p, series S, sorted (leg, P)."""
    return [(k[1], F, np.full(len(F), k[2])) for k, F in sorted(W.items()) if k[0] == p and k[3] == S and len(F)]


def stackS(W, p, S):
    r = series(W, p, S)
    return np.vstack([x for _, x, _ in r]), np.concatenate([y for _, _, y in r])


def pick_cal(W, p, B, unilateral):
    """balanced B: B/2 per class, first windows in time; unilateral: half from L, half from R."""
    n = B // 2; Xs, ys = [], []
    for c in (0, 1):
        recs = [(k[1], F) for k, F in sorted(W.items()) if k[0] == p and k[3] == 1 and k[2] == c]
        if unilateral:
            byleg = {leg: F for leg, F in recs}
            nl = n // 2; nr = n - nl
            parts = [byleg.get("L", np.zeros((0, 1)))[:nl], byleg.get("R", np.zeros((0, 1)))[:nr]]
            if sum(len(x) for x in parts) < n:
                return None
            Xc = np.vstack([x for x in parts if len(x)])
        else:
            Xc = np.vstack([F for _, F in recs])[:n]
            if len(Xc) < n:
                return None
        Xs.append(Xc); ys.append(np.full(n, c))
    return np.vstack(Xs), np.concatenate(ys)


def eligible(W, p, unilateral):
    if not all(any(k[0] == p and k[2] == P and k[3] == S for k in W) for P in (0, 1) for S in (1, 2)):
        return False
    if unilateral and not all(any(k[0] == p and k[1] == leg and k[3] == 1 and k[2] == c for k in W) for leg in "LR" for c in (0, 1)):
        return False
    return pick_cal(W, p, 16, unilateral) is not None


def boot_ci(d, rng, n=10000):
    d = np.asarray(d); idx = rng.integers(0, len(d), (n, len(d)))
    m = d[idx].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


results, cells = {}, []
for ex in EXS:
    uni = ex in UNILATERAL
    data = {}
    for mod in MODS:
        W, bad = (load_imu if mod == "IMU" else load_opt)(ex)
        data[mod] = W
        say(f"{ex}/{mod}: recordings={len(W)} excluded={len(bad)} {[os.path.basename(b) for b in bad][:6]} ({time.time()-t0:.0f}s)")
    persons = sorted(set.intersection(*[{k[0] for k in data[m]} for m in MODS]))
    persons = [p for p in persons if all(eligible(data[m], p, uni) for m in MODS)]
    say(f"{ex}: eligible persons (all modalities) = {len(persons)}")
    for mod in MODS:
        W = data[mod]
        rows = []
        for rep in range(2):
            perm = np.random.default_rng(3000 + rep).permutation(persons)
            for fi in range(5):
                test_p = set(perm[fi::5]); train_p = [p for p in persons if p not in test_p]
                tr = [stackS(W, p, S) for p in train_p for S in (1, 2)]
                Xtr = np.vstack([x for x, _ in tr]); ytr = np.concatenate([y for _, y in tr])
                gen = LogReg().fit(Xtr, ytr)
                rng = np.random.default_rng(5000 + 10 * rep + fi)
                sub = rng.choice(len(ytr), min(1500, len(ytr)), replace=False)
                tl = sorted(test_p)
                for ip, p in enumerate(tl):
                    q = tl[(ip + 1) % len(tl)]  # Addendum A: another test person of the same fold (not in GEN training)
                    X2, y2 = stackS(W, p, 2)
                    r = dict(rep=rep, fold=fi, person=p, GEN=bal_acc(gen.pred(X2), y2))
                    for B in BUDGETS:
                        Xc, yc = pick_cal(W, p, B, uni)
                        w = np.concatenate([np.ones(len(sub)), np.full(B, 20.0)])
                        ad = finetune(gen, np.vstack([Xtr[sub], Xc]), np.concatenate([ytr[sub], yc]), w)
                        oc = np.concatenate([rng.choice(np.where(ytr == c)[0], B // 2, replace=False) for c in (0, 1)])
                        ct = finetune(gen, np.vstack([Xtr[sub], Xtr[oc]]), np.concatenate([ytr[sub], ytr[oc]]), w)
                        pe = LogReg(); pe.mu, pe.sd = gen.mu, gen.sd; pe.fit(Xc, yc, keep_scaler=True)
                        Xq, yq = pick_cal(W, q, B, uni)
                        cn = finetune(gen, np.vstack([Xtr[sub], Xq]), np.concatenate([ytr[sub], yq]), w)
                        r[f"CTRLNEW{B}"] = bal_acc(cn.pred(X2), y2)
                        r[f"ADAPT{B}"] = bal_acc(ad.pred(X2), y2); r[f"CTRL{B}"] = bal_acc(ct.pred(X2), y2)
                        r[f"PERS{B}"] = bal_acc(pe.pred(X2), y2)
                    rows.append(r)
                say(f"  {ex}/{mod} rep{rep} fold{fi} {time.time()-t0:.0f}s")
        results[f"{ex}/{mod}"] = rows

json.dump(dict(results=results, log=log), open(f"{OUT}/results_plan5.json", "w"))

# ---------------- summary ----------------
brng = np.random.default_rng(7)
out = [f"# PLAN5 results (plan sha256 034a1ab2…386b). Runtime {time.time()-t0:.0f}s", ""] + log[:0]
out += [l for l in log if "rep" not in l] + [""]
out += ["PERS* = personal classifier with source-derived feature scaling (Addendum A). CTRL-NEW = new windows from another test person of the same fold.", ""]
out += ["Balanced accuracy per person (mean of 2 repeats); differences in BA points with bootstrap 95% CI over persons; tie = |d| < 0.5.", ""]
gen_cell = {}
for key, rows in results.items():
    per = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        for k, v in r.items():
            if k not in ("rep", "fold", "person"):
                per[r["person"]][k].append(v)
    P = sorted(per); M = lambda k: np.array([np.mean(per[p][k]) for p in P])
    gen = M("GEN"); gen_cell[key] = gen.mean()
    out += [f"## {key} (n={len(P)} persons) — GEN BA {gen.mean():.3f}", "",
            "| B | ADAPT | CTRL | CTRL-NEW | PERS* | ADAPT−GEN [CI] | ADAPT−CTRL [CI] | ADAPT−CTRL-NEW [CI] | PERS*−ADAPT [CI] (median; +/−/=) |", "|---|---|---|---|---|---|---|---|---|"]
    for B in BUDGETS:
        a, c, pe, cn = M(f"ADAPT{B}"), M(f"CTRL{B}"), M(f"PERS{B}"), M(f"CTRLNEW{B}")
        def fmt(d):
            lo, hi = boot_ci(100 * d, brng)
            return f"{100*d.mean():+.1f} [{lo:+.1f}, {hi:+.1f}]"
        d3 = pe - a
        cnt = f"{100*np.median(d3):+.1f}; {(100*d3 > .5).sum()}/{(100*d3 < -.5).sum()}/{(abs(100*d3) <= .5).sum()}"
        out.append(f"| {B} | {a.mean():.3f} | {c.mean():.3f} | {cn.mean():.3f} | {pe.mean():.3f} | {fmt(a-gen)} | {fmt(a-c)} | {fmt(a-cn)} | {fmt(d3)} ({cnt}) |")
        if B == 16:
            cells.append((key, gen.mean(), 100 * d3.mean(), boot_ci(100 * (a - gen), brng)[0], boot_ci(100 * (a - c), brng)[0], 100 * (a - gen).mean(), boot_ci(100 * (a - cn), brng)[0]))
    cross = None
    for B in BUDGETS:
        if boot_ci(100 * (M(f"PERS{B}") - M(f"ADAPT{B}")), brng)[0] > 0:
            cross = B; break
    out += ["", f"- First tested budget (4/8/16) with evidence PERS* > ADAPT (CI lower > 0): {cross if cross else 'none'}  [not a general minimum]", ""]

out += ["## Expectations", ""]
for mod in MODS:
    cm = [c for c in cells if c[0].endswith("/" + mod)]
    e1 = sum(1 for c in cm if c[5] >= 2 and c[3] > 0); e2 = sum(1 for c in cm if c[4] > 0)
    e2b = sum(1 for c in cm if c[6] > 0)
    out.append(f"- {mod}: E1 (ADAPT−GEN ≥ 2, CI>0 at B=16) in {e1}/{len(cm)} exercises; E2 (ADAPT−CTRL CI>0) in {e2}/{len(cm)}; E2b (ADAPT−CTRL-NEW CI>0) in {e2b}/{len(cm)}.")
if len(cells) >= 3:
    gx = np.array([c[1] for c in cells]); dy = np.array([c[2] for c in cells])
    rk = lambda v: np.argsort(np.argsort(v)).astype(float)
    rho = np.corrcoef(rk(gx), rk(dy))[0, 1]
    out.append(f"- E3 (descriptive, {len(cells)} cells): Spearman ρ(GEN BA, PERS−ADAPT at B=16) = {rho:+.2f}. Cells: " +
               "; ".join(f"{c[0]} GEN {c[1]:.3f} / PERS−ADAPT {c[2]:+.1f}" for c in cells))
open(f"{OUT}/summary_plan5.md", "w").write("\n".join(out) + "\n")
print("\n".join(out))
