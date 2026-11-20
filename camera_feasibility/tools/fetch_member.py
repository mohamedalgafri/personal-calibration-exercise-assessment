"""Resumable download of one zip member (REHAB24-6) by HTTP range requests, writing to disk as it goes.
Usage: python3 -P fetch_member.py <zip_index.json> <member_name> <out_file>
The compressed bytes go to <out_file>.part (resumes from its size); then inflated and size-checked."""
import sys, json, os, struct, subprocess, zlib, time

IDX, NAME, OUT = sys.argv[1:4]
d = json.load(open(IDX)); URL = d['url']
e = [x for x in d['entries'] if x['name'] == NAME][0]


def head():
    for _ in range(60):
        r = subprocess.run(['curl', '-sL', '--fail', '-m', '120', '-r', f"{e['offset']}-{e['offset'] + 29}", URL], capture_output=True)
        if r.returncode == 0 and len(r.stdout) == 30:
            return r.stdout
        time.sleep(10)
    raise SystemExit('header failed')


h = head(); nl, xl = struct.unpack('<HH', h[26:30]); s = e['offset'] + 30 + nl + xl
part = OUT + '.part'
for attempt in range(500):
    have = os.path.getsize(part) if os.path.exists(part) else 0
    if have > e['csize']:   # corrupted (e.g. two writers): restart from zero
        os.remove(part); have = 0
    if have >= e['csize']:
        break
    with open(part, 'ab') as fh:
        subprocess.run(['curl', '-sL', '--fail', '-m', '600', '-r', f"{s + have}-{s + e['csize'] - 1}", URL], stdout=fh)
    print(f'{time.strftime("%H:%M:%S")} {os.path.getsize(part)}/{e["csize"]} bytes', flush=True)
raw = open(part, 'rb').read()
data = zlib.decompress(raw, -15) if e['method'] == 8 else raw
assert len(data) == e['usize'], (len(data), e['usize'])
open(OUT, 'wb').write(data); os.remove(part)
print('DONE', NAME, len(data), flush=True)
