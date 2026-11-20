"""Read the central directory of a remote zip with HTTP range requests (no data download).
Usage: python3 -P zip_index.py <url> <out.json>"""
import sys, json, struct, subprocess

URL, OUT = sys.argv[1], sys.argv[2]

def rng(a, b):
    return subprocess.run(['curl', '-sL', '--retry', '5', '-m', '1800', '-r', f'{a}-{b}', URL],
                          capture_output=True, check=True).stdout

size = int([l for l in subprocess.run(['curl', '-sIL', URL], capture_output=True, text=True).stdout.splitlines()
            if l.lower().startswith('content-length')][-1].split(':')[1])
tail = rng(size - 65536, size - 1)
e = tail.rfind(b'PK\x05\x06')
cd_size, cd_off = struct.unpack('<II', tail[e + 12:e + 20])
z = tail.rfind(b'PK\x06\x06')  # zip64 EOCD
if z >= 0:
    cd_size, cd_off = struct.unpack('<QQ', tail[z + 40:z + 56])
print('archive', size, 'central dir', cd_size, 'bytes at', cd_off, flush=True)
cd = rng(cd_off, cd_off + cd_size - 1)
ents, i = [], 0
while i < len(cd) and cd[i:i + 4] == b'PK\x01\x02':
    meth, = struct.unpack('<H', cd[i + 10:i + 12])
    csz, usz = struct.unpack('<II', cd[i + 20:i + 28])
    nl, xl, cl = struct.unpack('<HHH', cd[i + 28:i + 34])
    off, = struct.unpack('<I', cd[i + 42:i + 46])
    name = cd[i + 46:i + 46 + nl].decode('utf-8', 'replace')
    ex = cd[i + 46 + nl:i + 46 + nl + xl]
    j = 0
    while j < len(ex):  # zip64 extra field
        hid, hl = struct.unpack('<HH', ex[j:j + 4])
        if hid == 1:
            vals, k = [], j + 4
            for cond in (usz == 0xFFFFFFFF, csz == 0xFFFFFFFF, off == 0xFFFFFFFF):
                if cond:
                    vals.append(struct.unpack('<Q', ex[k:k + 8])[0]); k += 8
                else:
                    vals.append(None)
            usz = vals[0] if vals[0] is not None else usz
            csz = vals[1] if vals[1] is not None else csz
            off = vals[2] if vals[2] is not None else off
        j += 4 + hl
    ents.append(dict(name=name, method=meth, csize=csz, usize=usz, offset=off))
    i += 46 + nl + xl + cl
json.dump(dict(url=URL, size=size, entries=ents), open(OUT, 'w'))
print('entries', len(ents), flush=True)
