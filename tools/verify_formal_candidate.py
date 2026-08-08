from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORMAL = ROOT / "extension/canonical/formal"
ASSURANCE = ROOT / "extension/canonical/assurance"
MODEL = ROOT / "extension/canonical/source/worker-model.json"
BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def theorem_present(path: Path, name: str) -> bool:
    text = path.read_text(encoding="utf-8")
    return re.search(rf"^THEOREM {re.escape(name)} ==\s*$", text, re.MULTILINE) is not None


def main() -> int:
    errors: list[str] = []
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/generate_canon_tla_projection.py"), "--check"],
        cwd=ROOT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        errors.append("generated canon projection is stale")

    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    if binding.get("seed_release_commit") != "633c130187b2a2bb42f24cfd66662d475de385d2":
        errors.append("pinned Seed release commit mismatch")

    relations = [
        ASSURANCE / "canon-tla-refinement.json",
        ASSURANCE / "seed-refinement.json",
        ASSURANCE / "lifecycle-proof-candidate.json",
    ]
    for path in relations:
        if not path.is_file():
            errors.append(f"missing relation: {path.relative_to(ROOT)}")

    if not errors:
        canon = json.loads((ASSURANCE / "canon-tla-refinement.json").read_text(encoding="utf-8"))
        seed = json.loads((ASSURANCE / "seed-refinement.json").read_text(encoding="utf-8"))
        life = json.loads((ASSURANCE / "lifecycle-proof-candidate.json").read_text(encoding="utf-8"))

        if canon.get("status") not in {"PROOF_CANDIDATE_MATERIALIZED", "MECHANICALLY_PROVED"}:
            errors.append("canon relation status mismatch")
        if canon.get("status") == "MECHANICALLY_PROVED":
            evidence = canon.get("proof_evidence", {})
            evidence_path = ROOT / evidence.get("path", "")
            if evidence.get("status") != "MECHANICALLY_PROVED" or not evidence_path.is_file():
                errors.append("canon mechanically-proved evidence binding mismatch")
        if canon.get("source_model", {}).get("sha256") != sha(MODEL):
            errors.append("canon relation source digest mismatch")
        for entry, path in [
            (canon.get("generated_projection", {}), FORMAL / "WorkerCanonProjection.tla"),
            (canon.get("target_model", {}), FORMAL / "WorkerLifecycle.tla"),
            (canon.get("proof_candidate", {}), FORMAL / "WorkerCanonRefinementProofs.tla"),
        ]:
            if entry.get("sha256") != sha(path):
                errors.append(f"canon relation digest mismatch: {path.name}")

        if seed.get("status") not in {"PROOF_CANDIDATE_MATERIALIZED", "MECHANICALLY_PROVED"}:
            errors.append("seed relation status mismatch")
        if seed.get("status") == "MECHANICALLY_PROVED":
            evidence = seed.get("proof_evidence", {})
            evidence_path = ROOT / evidence.get("path", "")
            if evidence.get("status") != "MECHANICALLY_PROVED" or not evidence_path.is_file():
                errors.append("seed mechanically-proved evidence binding mismatch")

        if seed.get("upstream_seed", {}).get("sha256") != "sha256:1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926":
            errors.append("SeedResolution digest binding mismatch")
        for entry, path in [
            (seed.get("mapping_candidate", {}), FORMAL / "WorkerSeedStuttering.tla"),
            (seed.get("proof_candidate", {}), FORMAL / "WorkerSeedStutteringProofs.tla"),
        ]:
            if entry.get("sha256") != sha(path):
                errors.append(f"seed relation digest mismatch: {path.name}")

        if life.get("model", {}).get("sha256") != sha(FORMAL / "WorkerLifecycle.tla"):
            errors.append("lifecycle model digest mismatch")
        if life.get("proof", {}).get("sha256") != sha(FORMAL / "WorkerLifecycleProofs.tla"):
            errors.append("lifecycle proof digest mismatch")

        theorem_sets = [
            (FORMAL / "WorkerLifecycleProofs.tla", life.get("proof", {}).get("final_theorems", [])),
            (FORMAL / "WorkerCanonRefinementProofs.tla", canon.get("proof_candidate", {}).get("final_theorems", [])),
            (FORMAL / "WorkerSeedStutteringProofs.tla", seed.get("proof_candidate", {}).get("final_theorems", [])),
        ]
        for path, names in theorem_sets:
            for name in names:
                if not theorem_present(path, name):
                    errors.append(f"missing theorem {name} in {path.name}")

    if errors:
        print("WORKER_FORMAL_CANDIDATE_VERIFY=FAIL")
        for error in errors:
            print(f"WORKER_FORMAL_CANDIDATE_ERROR={error}")
        return 1
    print("WORKER_FORMAL_CANDIDATE_IDENTITY=PASS")
    print("WORKER_CANON_TO_TLA_CANDIDATE=READY")
    print("WORKER_TLAPS_SAFETY_CANDIDATE=READY")
    print("WORKER_SEED_REFINEMENT_CANDIDATE=READY")
    print("WORKER_FORMAL_CANDIDATE_VERIFY=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
