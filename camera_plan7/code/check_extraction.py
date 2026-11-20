"""PLAN7 §4 checks for one video: frame counts/timestamps (ffprobe), displayed-frame check, detection, wrist lag.
Usage: python3 -P check_extraction.py <id> <exercise 1|2> <attempt> -> prints JSON line, appends to results/extraction_log.jsonl"""
import sys, os, json, csv, subprocess
import numpy as np

ID, EX, ATT = sys.argv[1], sys.argv[2], sys.argv[3]
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
SEG = os.path.join(ROOT, '..', 'feasibility_2026-11-16', 'rehab24', 'Segmentation.csv')


def pts(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'frame=pts_time',
                          '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.split()
    return np.array([float(x.strip(',')) for x in out if x.strip(',')])

src = pts(os.path.join(ROOT, 'data', 'raw', f'{ID}-Camera17-30fps.mp4'))
enc = pts(os.path.join(ROOT, 'data', 'intra', f'{ID}.mp4'))
ts_ok = len(src) == len(enc) and np.allclose(src - src[0], np.arange(len(src)) / 30, atol=0.002) and np.allclose(enc - enc[0], np.arange(len(enc)) / 30, atol=0.002)
P = json.load(open(os.path.join(ROOT, 'results', f'{ID}_attempt{ATT}.json' if ATT.isdigit() else f'{ID}_{ATT}.json')))
M = np.load(os.path.join(ROOT, 'data', 'raw', f'{ID}-c17-30fps.npy'))
T = P['n_frames']
JPG = str(P.get('method', '')).startswith('jpg')   # Addendum C: frame index = image index by construction
pt = (np.arange(P['n_frames']) / 30.0) if JPG else np.array([x if x is not None else -1 for x in P['presented_time']], float)
# fixed 16 Nov (Stage A): browsers report mediaTime rounded to 6 decimals (e.g. 0.133333), so floor(30*t) gave 3 instead of 4;
# the presented frame index is round(30*t). The pass criterion (>= 99%, no duplicates) is unchanged.
idx_shown = np.where(pt >= 0, np.round(pt * 30).astype(int), -1)
match = np.mean(idx_shown == np.arange(T))
used = idx_shown[idx_shown >= 0]
dup = len(used) - len(set(used.tolist()))
rows = [r for r in csv.DictReader(open(SEG), delimiter=';') if r['video_id'] == ID]
inrep = np.zeros(T, bool)
for r in rows:
    inrep[int(r['first_frame']):int(r['last_frame']) + 1] = True
MPI = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
pose = np.array([f is not None for f in P['frames']])
vis = np.array([[f[i][2] for i in MPI] if f else [0] * 12 for f in P['frames']])
det12 = (vis >= 0.5).all(1)
# wrist vertical trajectory: Ex1 right wrist (MP 16 / mocap 14); Ex2 mean of wrists (MP 15,16 / mocap 9,14)
def wrist(f):  # Addendum A.2: correct grouping for missing poses
    if f is None:
        return np.nan
    return f[16][1] if EX == '1' else (f[15][1] + f[16][1]) / 2
mpw = np.array([wrist(f) for f in P['frames']], float)
mcw = M[:, 14, 1] if EX == '1' else M[:, [9, 14], 1].mean(1)
def corr_at(lag):
    i = np.arange(T); j = i + lag; ok = (j >= 0) & (j < len(mcw)) & inrep & np.isfinite(mpw)
    ok[ok] &= np.isfinite(mcw[j[ok]])   # Addendum A.2
    a, b = mpw[i[ok]], mcw[j[ok]]
    return float(np.corrcoef(a - a.mean(), b - b.mean())[0, 1]) if ok.sum() > 30 else np.nan
cs = {lag: corr_at(lag) for lag in range(-15, 16)}
best = max(cs, key=lambda k: -np.inf if np.isnan(cs[k]) else cs[k])
res = dict(id=ID, ex=EX, attempt=ATT, frames=T, mocap_frames=len(M), src_frames=len(src), enc_frames=len(enc), timestamps_ok=bool(ts_ok),
           rvfc=P.get('rvfc'), presented_match=round(float(match), 4), presented_match_raw=float(match), presented_dups=int(dup),
           pose_in_rep=round(float(pose[inrep].mean()), 4), det12_in_rep=round(float(det12[inrep].mean()), 4),
           lag_best=int(best), corr_best=round(cs[best], 4), corr_lag0=round(cs[0], 4), fps=round(P['fps_processing'], 2),
           rerun_trigger=bool(pose[inrep].mean() < 0.5))
if JPG:   # Addendum C: file-count check replaces the presented-frame check
    nfiles = len([x for x in os.listdir(os.path.join(ROOT, 'data', 'frames', ID)) if x.endswith('.jpg')])
    res['frame_files'] = nfiles; res['method'] = 'jpg'
    match = 1.0 if (nfiles == len(src) == T) else 0.0
    res['presented_match'] = match; res['presented_match_raw'] = match
res['pass'] = bool(ts_ok and match >= 0.99 and dup == 0 and abs(best) <= 2 and not res['rerun_trigger'])
print(json.dumps(res))
open(os.path.join(ROOT, 'results', 'extraction_log.jsonl'), 'a').write(json.dumps(res) + '\n')
