from __future__ import annotations
import hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CANON=ROOT/'extension/canonical'

def main():
    pkg=json.loads((CANON/'CANON_PACKAGE.json').read_text())
    for entry in pkg['files']:
        p=CANON/entry['path']
        assert p.is_file(), entry['path']
        actual='sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
        assert actual==entry['sha256'], (entry['path'], actual, entry['sha256'])
    print(f"CANON_PACKAGE_VERIFY={len(pkg['files'])}/{len(pkg['files'])} PASS")
if __name__=='__main__': main()
