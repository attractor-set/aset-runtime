#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "dist/formal-release-gate.json"


def write_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_stage(name: str, command: list[str]) -> dict[str, object]:
    print(f"FORMAL_RELEASE_STAGE={name}:START")
    result = subprocess.run(command, cwd=ROOT, check=False)
    verdict = "PASS" if result.returncode == 0 else "FAIL"
    print(f"FORMAL_RELEASE_STAGE={name}:{verdict}")
    return {"name": name, "command": command, "returncode": result.returncode, "verdict": verdict}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", type=Path, required=True)
    parser.add_argument("--seed-root", type=Path, default=Path.home() / "ASET")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    output = args.output.expanduser()
    if not output.is_absolute():
        output = ROOT / output
    tlapm = args.tlapm.expanduser().resolve()
    seed_root = args.seed_root.expanduser().resolve()
    python = sys.executable

    stages = [
        ("CANON_PROJECTION_CHECK", [python, "tools/generate_canon_tla_projection.py", "--check"]),
        ("LOCAL_GATE", [python, "tools/run_local_gate.py"]),
        (
            "FORMAL_CANDIDATE_GATE",
            [
                python,
                "tools/run_formal_candidate_gate.py",
                "--tlapm",
                str(tlapm),
                "--seed-root",
                str(seed_root),
                "--timeout-seconds",
                str(args.timeout_seconds),
            ],
        ),
        ("FORMAL_EVIDENCE_CHECK", [python, "tools/materialize_formal_evidence.py", "--check"]),
        ("CANON_PACKAGE_VERIFY", [python, "tools/verify_canon_package.py"]),
        ("TESTS", [python, "-m", "pytest", "-q"]),
    ]

    results: list[dict[str, object]] = []
    for name, command in stages:
        result = run_stage(name, command)
        results.append(result)
        if result["verdict"] != "PASS":
            write_report(
                output,
                {
                    "document_type": "aset-worker-formal-release-gate-report",
                    "schema_version": 1,
                    "verdict": "FAIL",
                    "failed_stage": name,
                    "stages": results,
                },
            )
            print("FORMAL_RELEASE_GATE=FAIL")
            print(f"FORMAL_RELEASE_GATE_FAILED_STAGE={name}")
            return 1

    registry = json.loads(
        (ROOT / "extension/canonical/assurance/verification-registry.json").read_text(encoding="utf-8")
    )
    package = json.loads(
        (ROOT / "extension/canonical/CANON_PACKAGE.json").read_text(encoding="utf-8")
    )
    report = {
        "document_type": "aset-worker-formal-release-gate-report",
        "schema_version": 1,
        "verdict": "PASS",
        "canon_id": package["canon_id"],
        "canon_version": package["version"],
        "formal_verification_status": registry["status"],
        "proofs": registry["proofs"],
        "tlapm_commit": registry["toolchain"]["tlapm_commit"],
        "tlapm_version": registry["toolchain"]["tlapm_version"],
        "stages": results,
    }
    write_report(output, report)
    for proof in registry["proofs"]:
        print(f"FORMAL_RELEASE_{proof['id']}_STATUS={proof['status']}")
        print(f"FORMAL_RELEASE_{proof['id']}_OBLIGATIONS={proof['obligations_proved']}")
    print("FORMAL_RELEASE_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
