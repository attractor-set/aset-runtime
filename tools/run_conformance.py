from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from reference.oracle import run_case


def main():
    cases = sorted((ROOT / 'extension/canonical/conformance/cases').rglob('*.json'))
    passed = 0
    for path in cases:
        case = json.loads(path.read_text())
        actual = run_case(case)
        assert actual == case['expected'], f"{case['case_id']}: expected {case['expected']}, got {actual}"
        passed += 1
        print(f"CASE={case['case_id']} PASS")
    print(f"CONFORMANCE={passed}/{len(cases)} PASS")

if __name__ == '__main__':
    main()
