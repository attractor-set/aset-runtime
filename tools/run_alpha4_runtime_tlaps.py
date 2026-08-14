from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "runtime/alpha4/formal"
MODULES = [
    FORMAL / "OperationalRelationalPairingProofs.tla",
    FORMAL / "SeedBoundaryProofs.tla",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", required=True)
    args = parser.parse_args()
    total = 0
    for module in MODULES:
        result = subprocess.run(
            [args.tlapm, "-I", str(FORMAL), str(module)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        print(result.stdout, end="")
        if result.returncode:
            print(f"ALPHA4_RUNTIME_TLAPS_MODULE={module.name} FAIL")
            return result.returncode
        matches = re.findall(r"All ([0-9]+) obligations? proved\.", result.stdout)
        if not matches:
            print(f"ALPHA4_RUNTIME_TLAPS_MODULE={module.name} SUMMARY_MISSING")
            return 1
        count = int(matches[-1])
        total += count
        print(f"ALPHA4_RUNTIME_TLAPS_MODULE={module.name} OBLIGATIONS={count} PASS")
    print(f"ALPHA4_RUNTIME_TLAPS_OBLIGATIONS={total} PASS")
    print("ALPHA4_RUNTIME_TLAPS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
