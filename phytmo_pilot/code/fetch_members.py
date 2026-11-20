"""Fetch selected members of the PHYTMO Zenodo zip (CC BY 4.0, record 5052756) with HTTP range requests.
Usage: python3 -P fetch_members.py <zip_index.json> <out_dir>
Selection: inertial CSVs for SQT (4 IMUs), KFE (shin+thigh of the moving leg), EFE (4 IMUs). Verifies decompressed size (inflate must succeed)."""
import sys, json, re, os, struct, zlib, subprocess, concurrent.futures as cf

URL = "https://zenodo.org/records/5052756/files/PHYTMO.zip?download=1"
idx = json.load(open(sys.argv[1])); OUT = sys.argv[2]
WANT_ALL = set(os.environ.get("WANT_ALL", "SQT,EFE").split(","))
WANT_LEG = set(os.environ.get("WANT_LEG", "KFE").split(","))
pat = re.compile(r"([A-E])(\d\d)([A-Z]{3})([LR]?)([01])_(\d)\.csv$")


OPT_EX = [x for x in os.environ.get("OPT_EX", "").split(",") if x]


def opt_wanted(e):
    n = e["name"]
    if not n.startswith("optical interp/rigid_bodies/") or not n.endswith("_interp.csv"):
        return False
    m = re.search(r"([A-E])(\d\d)([A-Z]{3})([LR]?)([01])_(\d)_interp\.csv$", n)
    return bool(m) and m.group(3) in OPT_EX


def wanted(e):
    if opt_wanted(e):
        return True
    n = e["name"]
    if not n.startswith("inertial/") or not n.endswith(".csv"):
        return False
    m = pat.search(n)
    if not m:
        return False
    ex, leg, seg = m.group(3), m.group(4), n.split("/")[3]
    if ex in WANT_ALL:
        return True
    if ex in WANT_LEG:
        return seg[0] == leg  # sensor on the moving leg
    return False


sel = [e for e in idx if wanted(e)]
ORDER = [x for x in os.environ.get("ORDER", "").split(",") if x]
def prio(e):
    for i, tag in enumerate(ORDER):
        if tag in e["name"]:
            return i
    return len(ORDER)
sel.sort(key=prio)
print("selected", len(sel), "files,", round(sum(e["csize"] for e in sel) / 1e6, 1), "MB compressed", flush=True)


def get(e):
    dst = os.path.join(OUT, e["name"])
    if os.path.exists(dst) and os.path.getsize(dst) == e["usize"]:
        return "skip"
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    a = e["lho"]; b = a + 30 + 512 + e["csize"]
    for _ in range(8):
        r = subprocess.run(["curl", "-sL", "--max-time", "300", "-r", f"{a}-{b}", URL], capture_output=True)
        raw = r.stdout
        if len(raw) < 30 or raw[:4] != b"PK\x03\x04":
            continue
        nl, el = struct.unpack("<HH", raw[26:30])
        data = raw[30 + nl + el: 30 + nl + el + e["csize"]]
        if len(data) < e["csize"]:
            continue
        out = zlib.decompress(data, -15) if e["method"] == 8 else data
        if len(out) != e["usize"]:
            continue
        open(dst, "wb").write(out)
        return "ok"
    return "FAIL " + e["name"]


with cf.ThreadPoolExecutor(10) as ex:
    res = list(ex.map(get, sel))
print({k: res.count(k) for k in set(r if not r.startswith("FAIL") else "FAIL" for r in res)})
for r in res:
    if r.startswith("FAIL"):
        print(r)
