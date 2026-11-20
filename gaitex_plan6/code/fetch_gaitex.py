"""Fetch selected GAITEX members (Zenodo 15729056, CC BY 4.0) by HTTP range requests (PLAN6 §3).
Usage: python3 -P fetch_gaitex.py <zip_index.json> <out_dir>
Resumable: a member whose output file already has the expected size is skipped; partial
downloads continue from their current length. Stored (method 0) and deflated (8) members supported."""
import sys, os, json, struct, subprocess, zlib, concurrent.futures as cf, time

IDX, OUT = sys.argv[1], sys.argv[2]
d = json.load(open(IDX)); URL = d['url']


def wanted(n):
    p = n.split('/')
    if len(p) != 4 or p[2] not in ('rd', 'rgs'):
        return False
    f = p[3]
    return (f.startswith('xsens_imu_data_') and 'segment' not in f) or f.startswith('timestamps_') or f.startswith('metadata_')


def curl(a, b, dst=None):
    args = ['curl', '-sL', '--fail', '--retry', '8', '--retry-delay', '5', '-m', '7200', '-r', f'{a}-{b}', URL]
    if dst:
        with open(dst, 'ab') as fh:
            r = subprocess.run(args, stdout=fh)
        return r.returncode
    for attempt in range(60):  # network drops (curl exit 7) happen on this connection: wait and retry
        r = subprocess.run(args, capture_output=True)
        if r.returncode == 0:
            return r.stdout
        time.sleep(30)
    raise RuntimeError(f'curl failed 60 times for range {a}-{b}')


def fetch(e):
    dst = os.path.join(OUT, *e['name'].split('/')[1:])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst) and os.path.getsize(dst) == e['usize']:
        return e['name'], 'skip'
    h = curl(e['offset'], e['offset'] + 29)
    nl, xl = struct.unpack('<HH', h[26:30])
    s = e['offset'] + 30 + nl + xl
    if e['method'] == 0:
        part = dst
        for attempt in range(200):
            have = os.path.getsize(part) if os.path.exists(part) else 0
            if have >= e['csize']:
                break
            if curl(s + have, s + e['csize'] - 1, part) != 0:
                time.sleep(30)
        ok = os.path.getsize(part) == e['usize']
    else:
        raw = curl(s, s + e['csize'] - 1)
        data = zlib.decompress(raw, -15)
        open(dst, 'wb').write(data); ok = len(data) == e['usize']
    return e['name'], 'ok' if ok else f'SIZE MISMATCH {os.path.getsize(dst)} != {e["usize"]}'


sel = sorted([e for e in d['entries'] if wanted(e['name'])], key=lambda e: e['usize'])
print(f'{len(sel)} members, {sum(e["csize"] for e in sel)/1e9:.3f} GB', flush=True)
t0 = time.time()
with cf.ThreadPoolExecutor(4) as ex:
    for name, st in ex.map(fetch, sel):
        print(f'{time.time()-t0:7.0f}s {st:5s} {name}', flush=True)
print('DONE', flush=True)
