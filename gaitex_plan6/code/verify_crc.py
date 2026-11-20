"""Verify downloaded GAITEX members against the CRC-32 stored in the zip central directory.
Usage: python3 -P verify_crc.py <zip_index.json> <raw_dir> <out_txt>
Re-reads the central directory (about 1 MB, range request) to get CRC-32 values; reads no member data remotely."""
import sys, json, struct, subprocess, zlib, os, time

IDX, RAW, OUT = sys.argv[1:4]
d = json.load(open(IDX)); URL = d['url']; size = d['size']


def rng(a, b):
    for _ in range(60):
        r = subprocess.run(['curl', '-sL', '--fail', '-m', '1800', '-r', f'{a}-{b}', URL], capture_output=True)
        if r.returncode == 0:
            return r.stdout
        time.sleep(30)
    raise RuntimeError('range failed')


tail = rng(size - 65536, size - 1)
z = tail.rfind(b'PK\x06\x06')
cd_size, cd_off = struct.unpack('<QQ', tail[z + 40:z + 56]) if z >= 0 else struct.unpack('<II', tail[tail.rfind(b'PK\x05\x06') + 12:][:8])
cd = rng(cd_off, cd_off + cd_size - 1)
crc, i = {}, 0
while i < len(cd) and cd[i:i + 4] == b'PK\x01\x02':
    c, = struct.unpack('<I', cd[i + 16:i + 20])
    nl, xl, cl = struct.unpack('<HHH', cd[i + 28:i + 34])
    crc[cd[i + 46:i + 46 + nl].decode('utf-8', 'replace')] = c
    i += 46 + nl + xl + cl
lines, bad = [], 0
for root, _, files in os.walk(RAW):
    for f in sorted(files):
        p = os.path.join(root, f)
        name = 'data/' + os.path.relpath(p, RAW).replace(os.sep, '/')
        v = 0
        with open(p, 'rb') as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b''):
                v = zlib.crc32(chunk, v)
        ok = crc.get(name) == (v & 0xFFFFFFFF)
        bad += not ok
        lines.append(f"{'OK ' if ok else 'BAD'} {name}")
open(OUT, 'w').write('\n'.join(sorted(lines)) + f'\nfiles {len(lines)}, bad {bad}\n')
print(f'files {len(lines)}, bad {bad}')
