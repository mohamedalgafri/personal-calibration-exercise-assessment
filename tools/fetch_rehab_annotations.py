"""Obtain REHAB24-6 annotations from the original record, separately from the code release."""
from pathlib import Path
import hashlib, urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'feasibility_2026-11-16/rehab24'
EXPECTED = {'joints_names.txt': '3f04a37cce43086b1ea1fa49f1e4514f', 'Segmentation.csv': '90b8fbd7445dd050bf27b17126c78fbe', 'Segmentation.txt': '5f2a5b886c6f794f03e1a8f642738c86'}

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for name, expected in EXPECTED.items():
        target = DEST / name
        if target.exists() and hashlib.md5(target.read_bytes()).hexdigest() == expected:
            print(f'{name}: existing checksum matches'); continue
        url = f'https://zenodo.org/records/13305826/files/{name}?download=1'
        with urllib.request.urlopen(url, timeout=90) as response:
            content = response.read()
        if hashlib.md5(content).hexdigest() != expected:
            raise RuntimeError(f'{name}: source checksum mismatch; no file written')
        temporary = target.with_name(target.name + '.part')
        temporary.write_bytes(content)
        temporary.replace(target)
        print(f'{name}: downloaded and checksum verified')

if __name__ == '__main__':
    main()
