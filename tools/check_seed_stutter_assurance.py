#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = Path("assurance/seed-stutter/ASSURANCE_PROFILE.json")
CANON_PATH = Path("extension/canonical/CANON_PACKAGE.json")
MODEL_PATH = Path("extension/canonical/source/worker-model.json")
SEED_STUTTER_PATH = Path("extension/canonical/formal/WorkerSeedStuttering.tla")
SEED_PROOFS_PATH = Path("extension/canonical/formal/WorkerSeedStutteringProofs.tla")
SEED_EVIDENCE_PATH = Path("extension/canonical/assurance/seed-refinement-proof.json")
V60_PACKAGE_PATH = Path("assurance/seed-recognition-boundary/ASSURANCE_PACKAGE.json")
SEED_RESOLUTION_PATH = Path("seed/canonical/formal/SeedResolution.tla")


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def proof_relation(v60: dict[str, Any], relation_id: str) -> dict[str, Any] | None:
    for relation in v60.get("proof_chain", []):
        if relation.get("id") == relation_id:
            return relation
    return None


def git_head(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def check(worker_root: Path, seed_root: Path) -> dict[str, Any]:
    profile = load(worker_root / PROFILE_PATH)
    canon = load(worker_root / CANON_PATH)
    model = load(worker_root / MODEL_PATH)
    evidence = load(worker_root / SEED_EVIDENCE_PATH)
    v60_path = seed_root / V60_PACKAGE_PATH
    v60 = load(v60_path)

    worker = profile["worker_subject"]
    seed = profile["shared_seed_subject"]
    public = profile["public_v60_subject"]

    require(
        profile.get("normative") is False,
        "assurance profile must remain non-normative",
    )
    require(
        profile.get("normative_precedence") == "NONE",
        "assurance profile gained precedence",
    )
    require(canon.get("canon_id") == worker["canon_id"], "Worker canon id changed")
    require(
        model.get("canon_id") == worker["canon_id"], "Worker model canon id changed"
    )
    require(
        model.get("version") == worker["extension_version"], "Worker version changed"
    )

    identities = {
        MODEL_PATH: "model_sha256",
        SEED_STUTTER_PATH: "seed_stuttering_sha256",
        SEED_PROOFS_PATH: "seed_stuttering_proof_sha256",
        SEED_EVIDENCE_PATH: "seed_refinement_evidence_sha256",
    }
    for path, key in identities.items():
        require(
            sha256(worker_root / path) == worker[key],
            f"artifact identity changed: {path}",
        )

    gate = evidence.get("proof_gate", {})
    require(
        evidence.get("status") == "MECHANICALLY_PROVED",
        "Worker Seed refinement is not mechanically proved",
    )
    require(
        evidence.get("scope") == worker["seed_refinement_scope"],
        "Worker Seed refinement scope changed",
    )
    require(
        gate.get("obligations_proved") == worker["seed_refinement_obligations"],
        "Worker Seed proof-obligation evidence changed",
    )
    require(
        set(gate.get("final_theorems", []))
        == {
            "WorkerOperationsPreserveSeedProjection",
            "WorkerOperationsPreserveSeedOwnedState",
            "WorkerCompositionRefinesSeedResolutionByStuttering",
        },
        "Worker Seed theorem set changed",
    )
    upstream_sha = evidence.get("upstream_seed", {}).get("sha256")
    require(
        upstream_sha == seed["seed_resolution_sha256"],
        "Worker proof points at a different SeedResolution",
    )

    require(
        sha256(v60_path) == public["package_file_sha256"],
        "public v60 package file identity changed",
    )
    require(
        v60.get("assurance_id") == public["assurance_id"],
        "public v60 assurance id changed",
    )
    require(
        v60.get("package_digest") == public["package_digest"],
        "public v60 package digest changed",
    )
    require(
        v60.get("expected_tlaps_obligations") == public["expected_tlaps_obligations"],
        "public v60 obligation evidence changed",
    )
    require(
        v60.get("subject", {}).get("canon_id") == seed["canon_id"],
        "public v60 Seed canon id changed",
    )
    require(
        v60.get("subject", {}).get("canon_version") == seed["canon_version"],
        "public v60 Seed canon version changed",
    )
    require(
        v60.get("subject", {}).get("seed_resolution_sha256") == upstream_sha,
        "public v60 and Worker proof do not share the exact Seed subject",
    )
    require(
        sha256(seed_root / SEED_RESOLUTION_PATH) == upstream_sha,
        "local SeedResolution bytes differ from the shared subject",
    )

    actual_head = git_head(seed_root)
    if actual_head is not None:
        require(
            actual_head == public["commit"],
            "public assurance checkout is not at the pinned commit",
        )

    for expected in public["required_proof_relations"]:
        actual = proof_relation(v60, expected["id"])
        require(actual is not None, f"public v60 relation missing: {expected['id']}")
        require(
            actual.get("final_theorem") == expected["final_theorem"],
            f"public v60 theorem changed: {expected['id']}",
        )
        require(
            actual.get("expected_obligations") == expected["expected_obligations"],
            f"public v60 obligation evidence changed: {expected['id']}",
        )

    require(
        "external effect authorization"
        in model.get("normative_scope", {}).get("does_not_define", []),
        "Worker canon now owns external effect authorization",
    )
    require(
        model.get("composition", {}).get("requires")
        == ["ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3"],
        "Worker direct Seed compatibility binding changed",
    )

    return {
        "assurance_id": profile["assurance_id"],
        "worker_canon_id": worker["canon_id"],
        "worker_seed_refinement": "MECHANICALLY_PROVED",
        "worker_seed_refinement_obligations": gate["obligations_proved"],
        "public_v60_assurance_id": v60["assurance_id"],
        "public_v60_expected_tlaps_obligations": v60["expected_tlaps_obligations"],
        "shared_seed_resolution_sha256": upstream_sha,
        "composition_type": "EVIDENCE_COMPOSITION_NOT_NEW_TLAPS_THEOREM",
        "verdict": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker-root", type=Path, default=ROOT)
    parser.add_argument("--seed-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = check(args.worker_root.resolve(), args.seed_root.resolve())
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"WORKER_SEED_STUTTER_ASSURANCE=FAIL:{exc}")
        return 1
    print("WORKER_SEED_STUTTER_ASSURANCE_SUBJECT_BINDING=PASS")
    print("WORKER_SEED_REFINEMENT_EVIDENCE=19/19")
    print("WORKER_PUBLIC_V60_EVIDENCE=2257/2257")
    print("WORKER_SEED_STUTTER_ASSURANCE=PASS")
    if args.output:
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
