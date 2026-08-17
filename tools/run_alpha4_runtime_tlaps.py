from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

try:
    from tools.alpha4_runtime_manifest import ProofBinding, parse_runtime_manifest
except ModuleNotFoundError:  # direct ``python tools/...py`` execution
    from alpha4_runtime_manifest import ProofBinding, parse_runtime_manifest

ROOT = Path(__file__).resolve().parents[1]


def _run_proof(tlapm: str, proof: ProofBinding) -> int:
    module = ROOT / proof.module
    formal = module.parent
    print(f"ALPHA4_RUNTIME_TLAPS_PROOF={proof.proof_id}")
    print(f"ALPHA4_RUNTIME_TLAPS_MODULE={proof.module}")
    print(f"ALPHA4_RUNTIME_TLAPS_FINAL_THEOREM={proof.final_theorem}")
    print(f"ALPHA4_RUNTIME_TLAPS_EXPECTED_OBLIGATIONS={proof.expected_obligations}")
    result = subprocess.run(
        [tlapm, "-I", str(formal), str(module)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    print(result.stdout, end="")
    if result.returncode:
        print(f"ALPHA4_RUNTIME_TLAPS_MODULE={module.name} FAIL")
        return -1
    matches = re.findall(r"All ([0-9]+) obligations? proved\.", result.stdout)
    if not matches:
        print(f"ALPHA4_RUNTIME_TLAPS_MODULE={module.name} SUMMARY_MISSING")
        return -1
    count = int(matches[-1])
    if count != proof.expected_obligations:
        print(
            f"ALPHA4_RUNTIME_TLAPS_MODULE={module.name} "
            f"EXPECTED={proof.expected_obligations} ACTUAL={count} SCOPE_DRIFT"
        )
        return -1
    print(f"ALPHA4_RUNTIME_TLAPS_MODULE={module.name} OBLIGATIONS={count} PASS")
    return count


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", required=True)
    args = parser.parse_args()
    plan = parse_runtime_manifest(ROOT)
    total = 0
    expected_total = sum(proof.expected_obligations for proof in plan.proofs)
    for proof in plan.proofs:
        count = _run_proof(args.tlapm, proof)
        if count < 0:
            print("ALPHA4_RUNTIME_TLAPS=FAIL")
            return 1
        total += count
    if total != expected_total:
        print(f"ALPHA4_RUNTIME_TLAPS_OBLIGATIONS={total}/{expected_total} SCOPE_DRIFT")
        print("ALPHA4_RUNTIME_TLAPS=FAIL")
        return 1
    print(f"ALPHA4_RUNTIME_TLAPS_OBLIGATIONS={total}/{expected_total} PASS")
    print("ALPHA4_RUNTIME_TLAPS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
