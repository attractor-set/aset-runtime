from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "extension/canonical/formal"
DIST = ROOT / "dist/formal-candidate"
BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"

EXPECTED_TLAPM_VERSION = "4600b24"
EXPECTED_TLAPM_COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
EXPECTED_SEED_RELEASE_COMMIT = "633c130187b2a2bb42f24cfd66662d475de385d2"
EXPECTED_SEED_RESOLUTION_SHA256 = "1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926"

PROOFS = [
    {
        "id": "WORKER_TLAPS_SAFETY",
        "path": FORMAL / "WorkerLifecycleProofs.tla",
        "final_theorems": [
            "SpecImpliesAlwaysWorkerSafety",
            "SpecImpliesStartedAppendOnly",
            "SpecImpliesTerminalAppendOnly",
            "SpecImpliesWorkerStateChangesOnlyByRecognizedTransition",
        ],
        "needs_seed": False,
    },
    {
        "id": "WORKER_CANON_TO_TLA",
        "path": FORMAL / "WorkerCanonRefinementProofs.tla",
        "final_theorems": [
            "WorkerSafetyEquivalentToCanonProjection",
            "WorkerLifecycleBehaviorallyEquivalentToCanonProjection",
        ],
        "needs_seed": False,
    },
    {
        "id": "WORKER_SEED_REFINEMENT",
        "path": FORMAL / "WorkerSeedStutteringProofs.tla",
        "final_theorems": [
            "WorkerOperationsPreserveSeedProjection",
            "WorkerOperationsPreserveSeedOwnedState",
            "WorkerCompositionRefinesSeedResolutionByStuttering",
        ],
        "needs_seed": True,
    },
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def run_checked(command: list[str], cwd: Path, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def write_report(name: str, payload: dict) -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / f"{name}.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def materialize_pinned_seed(seed_root: Path) -> tuple[Path | None, list[str]]:
    errors: list[str] = []
    if not (seed_root / ".git").exists():
        return None, [f"Seed checkout is not a git repository: {seed_root}"]
    commit_check = run_checked(
        ["git", "cat-file", "-e", f"{EXPECTED_SEED_RELEASE_COMMIT}^{{commit}}"],
        seed_root,
    )
    if commit_check.returncode != 0:
        errors.append("pinned Seed release commit is absent from local object database")
        return None, errors
    show = run_checked(
        [
            "git",
            "show",
            f"{EXPECTED_SEED_RELEASE_COMMIT}:seed/canonical/formal/SeedResolution.tla",
        ],
        seed_root,
    )
    if show.returncode != 0:
        errors.append("cannot materialize SeedResolution.tla from pinned Seed commit")
        return None, errors
    data = show.stdout.encode("utf-8")
    actual = sha_bytes(data)
    if actual != EXPECTED_SEED_RESOLUTION_SHA256:
        errors.append(
            "pinned SeedResolution.tla digest mismatch: "
            f"expected {EXPECTED_SEED_RESOLUTION_SHA256}, got {actual}"
        )
        return None, errors
    pinned = DIST / "pinned-seed-formal"
    pinned.mkdir(parents=True, exist_ok=True)
    target = pinned / "SeedResolution.tla"
    target.write_bytes(data)
    return pinned, errors


def theorem_presence(path: Path, names: list[str]) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    for theorem in names:
        if re.search(rf"^THEOREM {re.escape(theorem)} ==\s*$", text, re.MULTILINE) is None:
            errors.append(f"missing final theorem {theorem} in {path.name}")
    return errors


def run_proof(
    proof_id: str,
    path: Path,
    final_theorems: list[str],
    tlapm: Path,
    seed_include: Path | None,
    timeout_seconds: int,
) -> dict:
    errors = theorem_presence(path, final_theorems)
    include_args = ["-I", str(FORMAL)]
    if seed_include is not None:
        include_args += ["-I", str(seed_include)]
    shutil.rmtree(ROOT / ".tlacache", ignore_errors=True)
    command = [str(tlapm), *include_args, str(path)]
    output = ""
    returncode: int | None = None
    timed_out = False
    if not errors:
        try:
            result = run_checked(command, ROOT, timeout_seconds)
            output = result.stdout
            returncode = result.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            captured = exc.stdout or ""
            if isinstance(captured, bytes):
                captured = captured.decode("utf-8", errors="replace")
            output = captured
            errors.append("TLAPS proof timed out")
    if output:
        print(output, end="" if output.endswith("\n") else "\n")
    matches = re.findall(r"All ([0-9]+) obligations? proved\.", output)
    obligations = int(matches[-1]) if matches else None
    forbidden = (
        "obligations failed",
        "unproved obligations",
        "backend errors",
        "Zenon error",
        "Proof.Parser",
        "[ERROR]",
    )
    if returncode != 0:
        errors.append(f"TLAPM returned {returncode}")
    if obligations is None:
        errors.append("TLAPM success summary was not found")
    for marker in forbidden:
        if marker in output:
            errors.append(f"TLAPM output contains {marker!r}")
    verdict = "PASS" if not errors else "FAIL"
    report = {
        "document_type": "aset-worker-formal-candidate-proof-run",
        "schema_version": 1,
        "proof_id": proof_id,
        "proof_path": path.relative_to(ROOT).as_posix(),
        "proof_sha256": "sha256:" + sha_file(path),
        "final_theorems": final_theorems,
        "command": command,
        "tlapm_commit": EXPECTED_TLAPM_COMMIT,
        "tlapm_version": EXPECTED_TLAPM_VERSION,
        "obligations_proved": obligations,
        "returncode": returncode,
        "timed_out": timed_out,
        "errors": errors,
        "verdict": verdict,
    }
    write_report(proof_id.lower(), report)
    if obligations is not None:
        print(f"{proof_id}_OBLIGATIONS={obligations}")
    print(f"{proof_id}_VERDICT={verdict}")
    for error in errors:
        print(f"{proof_id}_ERROR={error}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tlapm",
        type=Path,
        default=Path.home() / "ASET/.tooling/tlapm/bin/tlapm",
    )
    parser.add_argument("--seed-root", type=Path, default=Path.home() / "ASET")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()

    tlapm = args.tlapm.expanduser().resolve()
    seed_root = args.seed_root.expanduser().resolve()
    DIST.mkdir(parents=True, exist_ok=True)

    print("=== ASET WORKER FORMAL CANDIDATE GATE ===")
    errors: list[str] = []

    projection = run_checked(
        [sys.executable, str(ROOT / "tools/generate_canon_tla_projection.py"), "--check"],
        ROOT,
    )
    print(projection.stdout, end="" if projection.stdout.endswith("\n") else "\n")
    if projection.returncode != 0:
        errors.append("canon projection freshness check failed")

    candidate = run_checked(
        [sys.executable, str(ROOT / "tools/verify_formal_candidate.py")], ROOT
    )
    print(candidate.stdout, end="" if candidate.stdout.endswith("\n") else "\n")
    if candidate.returncode != 0:
        errors.append("formal candidate identity check failed")

    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    if binding.get("seed_release_commit") != EXPECTED_SEED_RELEASE_COMMIT:
        errors.append("upstream Seed binding commit mismatch")

    if not tlapm.is_file():
        errors.append(f"missing TLAPM executable: {tlapm}")
    elif not os.access(tlapm, os.X_OK):
        errors.append(f"TLAPM is not executable: {tlapm}")

    version_output = ""
    if tlapm.is_file() and os.access(tlapm, os.X_OK):
        version = run_checked([str(tlapm), "--version"], ROOT)
        version_output = version.stdout.strip()
        if version.returncode != 0:
            errors.append(f"tlapm --version returned {version.returncode}")
        if version_output != EXPECTED_TLAPM_VERSION:
            errors.append(f"unexpected TLAPM version: {version_output!r}")

    seed_include, seed_errors = materialize_pinned_seed(seed_root)
    errors.extend(seed_errors)

    print(f"TLAPM_COMMIT={EXPECTED_TLAPM_COMMIT}")
    print(f"TLAPM_VERSION={version_output}")
    print(f"SEED_RELEASE_COMMIT={EXPECTED_SEED_RELEASE_COMMIT}")
    if seed_include is not None:
        seed_file = seed_include / "SeedResolution.tla"
        print(f"PINNED_SEED_RESOLUTION={seed_file}")
        print(f"PINNED_SEED_RESOLUTION_SHA256=sha256:{sha_file(seed_file)}")

    if errors:
        print("FORMAL_CANDIDATE_GATE=FAIL")
        for error in errors:
            print(f"FORMAL_CANDIDATE_ERROR={error}")
        write_report(
            "formal-candidate-gate",
            {
                "document_type": "aset-worker-formal-candidate-gate",
                "schema_version": 1,
                "verdict": "FAIL",
                "errors": errors,
            },
        )
        return 1

    reports = []
    for spec in PROOFS:
        print(f"{spec['id']}=START")
        for theorem in spec["final_theorems"]:
            print(f"{spec['id']}_FINAL_THEOREM={theorem}")
        reports.append(
            run_proof(
                spec["id"],
                spec["path"],
                spec["final_theorems"],
                tlapm,
                seed_include if spec["needs_seed"] else None,
                args.timeout_seconds,
            )
        )

    verdict = "PASS" if all(r["verdict"] == "PASS" for r in reports) else "FAIL"
    gate_report = {
        "document_type": "aset-worker-formal-candidate-gate",
        "schema_version": 1,
        "tlapm_commit": EXPECTED_TLAPM_COMMIT,
        "tlapm_version": version_output,
        "seed_release_commit": EXPECTED_SEED_RELEASE_COMMIT,
        "seed_resolution_sha256": "sha256:" + EXPECTED_SEED_RESOLUTION_SHA256,
        "proofs": [
            {
                "proof_id": r["proof_id"],
                "verdict": r["verdict"],
                "obligations_proved": r["obligations_proved"],
                "proof_sha256": r["proof_sha256"],
            }
            for r in reports
        ],
        "verdict": verdict,
    }
    write_report("formal-candidate-gate", gate_report)
    print(f"FORMAL_CANDIDATE_GATE={verdict}")
    print("FORMAL_RELEASE_GATE=BLOCKED_PENDING_EVIDENCE_MATERIALIZATION")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
