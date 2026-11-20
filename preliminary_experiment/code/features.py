"""Loading KIMORE (Zenodo mirror, preprocessed) and computing clinically
meaningful kinematic features for Exercise 1 (lifting of the arms).

Data format (verified on the file):
- Train_X.csv: one row per frame, 100 columns = 25 Kinect v2 joints x (x, y, z, tracking_state).
  Samples are 100-frame windows; consecutive windows of the same person are continuous.
- Train_Y.csv: one clinical score per window (same value for all windows of a person).
- Y axis points up, Z is depth (metres).
"""
import io
import zipfile
import numpy as np

# Kinect v2 joint indices
SPINE_BASE, SPINE_MID, NECK, HEAD = 0, 1, 2, 3
SH_L, EL_L, WR_L, HA_L = 4, 5, 6, 7
SH_R, EL_R, WR_R, HA_R = 8, 9, 10, 11
HIP_L, KN_L, AN_L, FO_L = 12, 13, 14, 15
HIP_R, KN_R, AN_R, FO_R = 16, 17, 18, 19
SPINE_SH = 20
FPS = 30.0
WIN = 100


def load_zip(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        fx = [n for n in names if n.endswith("Train_X.csv")][0]
        fy = [n for n in names if n.endswith("Train_Y.csv")][0]
        X = np.loadtxt(io.TextIOWrapper(z.open(fx)), delimiter=",")
        Y = np.loadtxt(io.TextIOWrapper(z.open(fy)), delimiter=",")
    return X, Y


BONES = [(SH_L, EL_L), (EL_L, WR_L), (SH_R, EL_R), (EL_R, WR_R), (HIP_L, KN_L),
         (KN_L, AN_L), (HIP_R, KN_R), (KN_R, AN_R), (SPINE_BASE, SPINE_SH)]


def window_bones(J, w):
    P = J[w * WIN:(w + 1) * WIN, :, :3]
    return np.array([np.median(np.linalg.norm(P[:, a] - P[:, b], axis=1)) for a, b in BONES])


def group_subjects(J, y, jump=0.05, bone_tol=0.02):
    """Recover person boundaries (the mirror has no subject id).
    A new person starts when the clinical score changes (scores are per person), or
    when SpineBase jumps by > `jump` m across a window boundary AND the mean
    bone-length difference ("body fingerprint") exceeds `bone_tol` m. A jump with
    near-identical bone lengths is treated as a recording break of the SAME person,
    which is the conservative choice against train/test leakage."""
    nwin = len(J) // WIN
    BL = np.array([window_bones(J, w) for w in range(nwin)])
    groups, cur = [], [0]
    for w in range(1, nwin):
        a = J[w * WIN - 1, SPINE_BASE, :3]
        b = J[w * WIN, SPINE_BASE, :3]
        moved = np.linalg.norm(a - b) > jump
        body_changed = np.abs(BL[w] - BL[w - 1]).mean() > bone_tol
        new = abs(y[w] - y[w - 1]) > 1e-9 or (moved and body_changed)
        if new:
            groups.append(cur)
            cur = [w]
        else:
            cur.append(w)
    groups.append(cur)
    return groups


def _angle(u, v):
    cu = np.einsum("ij,ij->i", u, v) / (np.linalg.norm(u, axis=1) * np.linalg.norm(v, axis=1) + 1e-12)
    return np.degrees(np.arccos(np.clip(cu, -1, 1)))


def _smooth(x, k=5):
    if len(x) < k:
        return x
    ker = np.ones(k) / k
    xp = np.pad(x, (k // 2, k // 2), mode="edge")
    return np.convolve(xp, ker, mode="valid")


def series(P):
    """P: (T, 25, 3) joint positions. Upper-body series only: Exercise 1 is an
    upper-limb exercise and several participants performed it seated, so lower-body
    joints are unreliable. Lengths are normalised by trunk length (SpineBase-SpineShoulder)."""
    trunk_down = P[:, SPINE_BASE] - P[:, SPINE_SH]
    trunk_up = -trunk_down
    trunk = np.median(np.linalg.norm(trunk_up, axis=1))
    s = {}
    s["shoulder_elev_L"] = _angle(P[:, EL_L] - P[:, SH_L], trunk_down)
    s["shoulder_elev_R"] = _angle(P[:, EL_R] - P[:, SH_R], trunk_down)
    s["elbow_flex_L"] = 180 - _angle(P[:, SH_L] - P[:, EL_L], P[:, WR_L] - P[:, EL_L])
    s["elbow_flex_R"] = 180 - _angle(P[:, SH_R] - P[:, EL_R], P[:, WR_R] - P[:, EL_R])
    # trunk inclination: sagittal (y-z plane) and lateral (x-y plane)
    s["trunk_sagittal"] = np.degrees(np.arctan2(trunk_up[:, 2], trunk_up[:, 1]))
    s["trunk_lateral"] = np.degrees(np.arctan2(trunk_up[:, 0], trunk_up[:, 1]))
    s["wrist_height_L"] = (P[:, WR_L, 1] - P[:, HEAD, 1]) / trunk
    s["wrist_height_R"] = (P[:, WR_R, 1] - P[:, HEAD, 1]) / trunk
    s["head_forward"] = (P[:, HEAD, 2] - P[:, SPINE_SH, 2]) / trunk
    s["hands_distance"] = np.linalg.norm(P[:, WR_L] - P[:, WR_R], axis=1) / trunk
    return {k: _smooth(v) for k, v in s.items()}


def _count_reps(x):
    """Count elevation cycles: crossings of the mid-level with hysteresis."""
    lo, hi = np.percentile(x, 10), np.percentile(x, 90)
    if hi - lo < 10:  # less than 10 degrees of movement
        return 0
    th_hi, th_lo = lo + 0.7 * (hi - lo), lo + 0.3 * (hi - lo)
    state, reps = 0, 0
    for v in x:
        if state == 0 and v > th_hi:
            state, reps = 1, reps + 1
        elif state == 1 and v < th_lo:
            state = 0
    return reps


def features(P):
    s = series(P)
    f = {}
    for name, x in s.items():
        v = np.gradient(x) * FPS
        jerk = np.gradient(np.gradient(v)) * FPS * FPS
        f[f"{name}__mean"] = x.mean()
        f[f"{name}__std"] = x.std()
        f[f"{name}__min"] = np.percentile(x, 2)
        f[f"{name}__max"] = np.percentile(x, 98)
        f[f"{name}__range"] = np.percentile(x, 98) - np.percentile(x, 2)
        f[f"{name}__vel_mean"] = np.abs(v).mean()
        f[f"{name}__vel_max"] = np.percentile(np.abs(v), 98)
        f[f"{name}__jerk"] = np.log1p(np.abs(jerk).mean())
    # symmetry / coordination
    for a, b, nm in [("shoulder_elev_L", "shoulder_elev_R", "shoulder_elev"),
                     ("elbow_flex_L", "elbow_flex_R", "elbow_flex"),
                     ("wrist_height_L", "wrist_height_R", "wrist_height")]:
        f[f"sym_{nm}__absdiff"] = np.abs(s[a] - s[b]).mean()
        f[f"sym_{nm}__range_diff"] = abs(f[f"{a}__range"] - f[f"{b}__range"])
        c = np.corrcoef(s[a], s[b])[0, 1]
        f[f"sym_{nm}__corr"] = 0.0 if not np.isfinite(c) else c
    elev = (s["shoulder_elev_L"] + s["shoulder_elev_R"]) / 2
    reps = _count_reps(elev)
    dur = len(P) / FPS
    f["reps_count"] = reps
    f["duration_s"] = dur
    f["rep_duration_s"] = dur / reps if reps > 0 else dur
    return f


def build_dataset(zip_path):
    X, Y = load_zip(zip_path)
    J = X.reshape(len(X), 25, 4)
    nwin = len(J) // WIN
    assert nwin * WIN == len(J), "rows are not a multiple of 100"
    assert len(Y) == nwin, f"Y has {len(Y)} rows but there are {nwin} windows"
    groups = group_subjects(J, Y)
    groups, dropped = clean_groups(J, groups)
    rows, scores, info = [], [], []
    for g in groups:
        frames = np.concatenate([np.arange(w * WIN, (w + 1) * WIN) for w in g])
        P = J[frames, :, :3]
        inferred = float((J[frames, :, 3] < 2).mean())
        f = features(P)
        rows.append(f)
        scores.append(Y[g[0]])
        info.append({"windows": len(g), "frames": len(frames), "inferred_frac": inferred,
                     "score_const": bool(np.ptp(Y[g]) < 1e-9)})
    names = list(rows[0].keys())
    F = np.array([[r[n] for n in names] for r in rows], float)
    return F, np.array(scores), names, info, {"n_windows": nwin, "n_rows": len(X), "Y_raw": Y,
                                              "dropped_windows": dropped}


UPPER = [SPINE_BASE, SPINE_MID, NECK, HEAD, SH_L, EL_L, WR_L, SH_R, EL_R, WR_R, SPINE_SH]


def window_quality(J, w, max_inferred=0.3, max_travel=0.15):
    """A window is usable if the upper body is tracked (share of 'inferred' upper-body
    joints <= 30%) and the person is not walking (SpineBase horizontal travel <= 0.15 m)."""
    P = J[w * WIN:(w + 1) * WIN]
    inferred = float((P[:, UPPER, 3] < 2).mean())
    base = P[:, SPINE_BASE][:, [0, 2]]
    travel = float(np.linalg.norm(base.max(0) - base.min(0)))
    return inferred <= max_inferred and travel <= max_travel, inferred, travel


def clean_groups(J, groups):
    kept, dropped = [], []
    for g in groups:
        ok = []
        for w in g:
            good, h, tr = window_quality(J, w)
            if good:
                ok.append(w)
            else:
                dropped.append({"window": int(w), "inferred_upper": h, "travel": tr})
        if ok:
            kept.append(ok)
    return kept, dropped
