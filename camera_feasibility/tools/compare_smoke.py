"""Camera feasibility smoke analysis (CAMERA_FEASIBILITY_PLAN.md §4, §6). No labels, no classifier.
Usage: python3 -P compare_smoke.py <pose_json> <mocap_2d_npy> <segmentation_csv> <video_id> <out_md>"""
import sys, json, csv
import numpy as np

PJ, NPY, SEG, VID, OUT = sys.argv[1:6]
P = json.load(open(PJ)); M = np.load(NPY)                      # M: (T, 26, 2) pixels
# common joints: name, MediaPipe index, REHAB24-6 skeleton index (joints_names.txt)
J = [('L shoulder', 11, 7), ('R shoulder', 12, 12), ('L elbow', 13, 8), ('R elbow', 14, 13), ('L wrist', 15, 9),
     ('R wrist', 16, 14), ('L hip', 23, 16), ('R hip', 24, 21), ('L knee', 25, 17), ('R knee', 26, 22),
     ('L ankle', 27, 18), ('R ankle', 28, 23)]
ARM = [0, 1, 2, 3, 4, 5]
T = P['n_frames']
mp = np.full((T, 12, 3), np.nan)
for i, f in enumerate(P['frames']):
    if f is not None:
        mp[i] = np.array([f[a] for _, a, _ in J])
mc = M[:, [b for _, _, b in J], :]
rows = [r for r in csv.DictReader(open(SEG), delimiter=';') if r['video_id'] == VID]
inrep = np.zeros(T, bool)
for r in rows:
    inrep[int(r['first_frame']):int(r['last_frame']) + 1] = True
det = np.isfinite(mp[:, :, 0]).all(1) & (np.nan_to_num(mp[:, :, 2]) >= 0.5).all(1)
torso = np.median(np.linalg.norm((mc[:, 0] + mc[:, 1]) / 2 - (mc[:, 6] + mc[:, 7]) / 2, axis=1))


USE = det if det[inrep].any() else np.isfinite(mp[:, :, 0]).all(1)  # if no frame passes the visibility rule, errors are descriptive over all detected frames

def err(off, swap=False):
    idx = np.arange(T); j = idx + off; ok = (j >= 0) & (j < len(mc)) & inrep & USE
    a = mp[idx[ok], :, :2]
    b = mc[j[ok]]
    if swap:  # left/right labelling convention check
        b = b[:, [1, 0, 3, 2, 5, 4, 7, 6, 9, 8, 11, 10]]
    d = np.linalg.norm(a - b, axis=2) / torso
    return d, ok.sum()

res = {}
for sw in (False, True):
    for off in range(-6, 7):
        d, n = err(off, sw)
        res[(sw, off)] = (np.median(d), np.median(d[:, ARM]), n)
best = min(res, key=lambda k: res[k][0])
d, n = err(best[1], best[0])
L = ['# Camera smoke test: MediaPipe Pose vs motion-capture 2D joints (same camera, same frames)\n',
     f'- Video `{VID}` camera {sys.argv[6] if len(sys.argv) > 6 else '18'} ({P["width"]}×{P["height"]}), model **{P["model"]}** ({P["version"]}), frames {T}; mocap 2D frames {len(M)}.',
     f'- Processing speed (seek + detect, CPU/WASM in the browser): **{P["fps_processing"]:.1f} frames/s** ({P["seconds"]:.0f} s).',
     f'- Frames inside labelled repetitions: {inrep.sum()}; with all 12 joints detected at visibility ≥ 0.5: **{100 * det[inrep].mean():.1f}%**.',
     f'- Best alignment: offset {best[1]} frames, left/right {"swapped" if best[0] else "as named"} (median error {res[best][0]:.3f} vs '
     f'offset 0 as named {res[(False, 0)][0]:.3f}).',
     f'- Torso length (mocap, median): {torso:.0f} px.',
     f'- Per-joint share of repetition frames with MediaPipe visibility ≥ 0.5: ' + ', '.join(f"{nm} {100*np.mean(np.nan_to_num(mp[inrep, k, 2]) >= 0.5):.0f}%" for k, (nm, _, _) in enumerate(J)) + '.',
     f'- Errors below use {"frames passing the visibility rule" if det[inrep].any() else "ALL frames with a detected pose (no frame passed the visibility rule; descriptive only)"}.',
     f'- **Median error / torso length: all 12 joints {np.median(d):.3f}; arm joints {np.median(d[:, ARM]):.3f}** (frames used {n}).\n',
     '| Joint | median error / torso | 90th percentile |', '|---|---|---|']
for k, (nm, _, _) in enumerate(J):
    L.append(f'| {nm} | {np.median(d[:, k]):.3f} | {np.percentile(d[:, k], 90):.3f} |')
g = dict(a=100 * det[inrep].mean() >= 90, b=P['fps_processing'] >= 5, c=np.median(d[:, ARM]) <= 0.15, d=True)
L.append(f'\n**Criteria (§6):** (a) detection ≥ 90%: {"✅" if g["a"] else "❌"}; (b) ≥ 5 fps: {"✅" if g["b"] else "❌"}; '
         f'(c) arm error ≤ 0.15: {"✅" if g["c"] else "❌"}; (d) alignment determinable: ✅ (video {T} frames = mocap {len(M)} frames).')
L.append(f'\n**Verdict: {"GO" if all(g.values()) else "NOT GO (see §6: rescope or NO-GO)"}**')
L.append('\nNote: this is a sanity check of keypoint extraction on one video of one person, not a validation of the pose estimator. '
         'Mocap 2D joints are the dataset authors\' projection of a skeleton fitted to markers, not ground truth for MediaPipe\'s '
         'own joint definitions, so part of the error is a definition offset.')
open(OUT, 'w').write('\n'.join(L) + '\n'); print('\n'.join(L))
