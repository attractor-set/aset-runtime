#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "extension/canonical"
FORMAL = CANON / "formal"
ASSURANCE = CANON / "assurance"
DIST = ROOT / "dist/formal-candidate"
BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"
COMPATIBILITY_PROFILE = ROOT / "standards/worker-compatibility/compatibility-standard-profile-v1.json"

EXPECTED_TLAPM_COMMIT = "4600b24c6d95a25ff081ad37b63b2a01c29d43a5"
EXPECTED_TLAPM_VERSION = "4600b24"
EXPECTED_SEED_RELEASE_COMMIT = "633c130187b2a2bb42f24cfd66662d475de385d2"
EXPECTED_SEED_RESOLUTION_SHA256 = "sha256:1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926"

PROOFS = {
    "WORKER_TLAPS_SAFETY": {
        "report": DIST / "worker_tlaps_safety.json",
        "proof": FORMAL / "WorkerLifecycleProofs.tla",
        "final_theorems": [
            "SpecImpliesAlwaysWorkerSafety",
            "SpecImpliesAcceptedAppendOnly",
            "SpecImpliesStartedAppendOnly",
            "SpecImpliesTerminalAppendOnly",
            "SpecImpliesWorkerStateChangesOnlyByRecognizedTransition",
        ],
    },
    "WORKER_CANON_TO_TLA": {
        "report": DIST / "worker_canon_to_tla.json",
        "proof": FORMAL / "WorkerCanonRefinementProofs.tla",
        "final_theorems": [
            "WorkerSafetyEquivalentToCanonProjection",
            "WorkerLifecycleBehaviorallyEquivalentToCanonProjection",
        ],
    },
    "WORKER_SEED_REFINEMENT": {
        "report": DIST / "worker_seed_refinement.json",
        "proof": FORMAL / "WorkerSeedStutteringProofs.tla",
        "final_theorems": [
            "WorkerOperationsPreserveSeedProjection",
            "WorkerOperationsPreserveSeedOwnedState",
            "WorkerCompositionRefinesSeedResolutionByStuttering",
        ],
    },
}


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_report(proof_id: str, spec: dict) -> tuple[dict, list[str]]:
    errors: list[str] = []
    report_path: Path = spec["report"]
    proof_path: Path = spec["proof"]
    if not report_path.is_file():
        return {}, [f"missing proof report: {report_path.relative_to(ROOT)}"]
    report = read_json(report_path)
    expected_sha = sha(proof_path)
    checks = {
        "proof_id": proof_id,
        "verdict": "PASS",
        "proof_sha256": expected_sha,
        "tlapm_commit": EXPECTED_TLAPM_COMMIT,
        "tlapm_version": EXPECTED_TLAPM_VERSION,
    }
    for field, expected in checks.items():
        if report.get(field) != expected:
            errors.append(
                f"{proof_id} {field} mismatch: expected {expected!r}, got {report.get(field)!r}"
            )
    if report.get("final_theorems") != spec["final_theorems"]:
        errors.append(f"{proof_id} final theorem set mismatch")
    obligations = report.get("obligations_proved")
    if not isinstance(obligations, int) or obligations <= 0:
        errors.append(f"{proof_id} obligations_proved is not a positive integer")
    if report.get("returncode") != 0:
        errors.append(f"{proof_id} report returncode is not zero")
    if report.get("timed_out") is not False:
        errors.append(f"{proof_id} report timed_out is not false")
    if report.get("errors") != []:
        errors.append(f"{proof_id} report contains errors")
    return report, errors


def load_verified_runs() -> tuple[dict[str, dict], dict, list[str]]:
    errors: list[str] = []
    gate_path = DIST / "formal-candidate-gate.json"
    if not gate_path.is_file():
        return {}, {}, [f"missing gate report: {gate_path.relative_to(ROOT)}"]
    gate = read_json(gate_path)
    if gate.get("verdict") != "PASS":
        errors.append("formal candidate gate report is not PASS")
    if gate.get("tlapm_commit") != EXPECTED_TLAPM_COMMIT:
        errors.append("formal candidate gate TLAPM commit mismatch")
    if gate.get("tlapm_version") != EXPECTED_TLAPM_VERSION:
        errors.append("formal candidate gate TLAPM version mismatch")
    if gate.get("seed_release_commit") != EXPECTED_SEED_RELEASE_COMMIT:
        errors.append("formal candidate gate Seed release commit mismatch")
    if gate.get("seed_resolution_sha256") != EXPECTED_SEED_RESOLUTION_SHA256:
        errors.append("formal candidate gate SeedResolution digest mismatch")

    reports: dict[str, dict] = {}
    for proof_id, spec in PROOFS.items():
        report, report_errors = validate_report(proof_id, spec)
        reports[proof_id] = report
        errors.extend(report_errors)

    gate_proofs = {p.get("proof_id"): p for p in gate.get("proofs", []) if isinstance(p, dict)}
    for proof_id, report in reports.items():
        gp = gate_proofs.get(proof_id)
        if gp is None:
            errors.append(f"formal candidate gate report is missing {proof_id}")
            continue
        for field in ("verdict", "obligations_proved", "proof_sha256"):
            if gp.get(field) != report.get(field):
                errors.append(f"formal candidate gate {proof_id} {field} mismatch")
    return reports, gate, errors


def build_evidence(reports: dict[str, dict]) -> dict[str, dict]:
    binding = read_json(BINDING)
    safety = reports["WORKER_TLAPS_SAFETY"]
    canon = reports["WORKER_CANON_TO_TLA"]
    seed = reports["WORKER_SEED_REFINEMENT"]

    lifecycle = {
        "document_type": "aset-worker-lifecycle-proof-evidence",
        "schema_version": 1,
        "status": "MECHANICALLY_PROVED",
        "scope": "UNBOUNDED_TLAPS_WORKER_LIFECYCLE_SAFETY",
        "normative_precedence": "MACHINE_READABLE_CANON",
        "artifacts": {
            "model": {
                "module": "WorkerLifecycle",
                "path": "extension/canonical/formal/WorkerLifecycle.tla",
                "sha256": sha(FORMAL / "WorkerLifecycle.tla"),
            },
            "proof": {
                "module": "WorkerLifecycleProofs",
                "path": "extension/canonical/formal/WorkerLifecycleProofs.tla",
                "sha256": sha(FORMAL / "WorkerLifecycleProofs.tla"),
            },
        },
        "proof_gate": {
            "runner": "tools/run_formal_candidate_gate.py",
            "final_theorems": PROOFS["WORKER_TLAPS_SAFETY"]["final_theorems"],
            "obligation_count_semantics": "RECORDED_EVIDENCE_NOT_FIXED_SEMANTIC_CONTRACT",
            "obligations_proved": safety["obligations_proved"],
            "verdict": "PASS",
        },
        "tlapm": {"commit": EXPECTED_TLAPM_COMMIT, "version": EXPECTED_TLAPM_VERSION},
        "claim_boundary": [
            "The proof establishes the declared safety properties of the exact WorkerLifecycle.tla and WorkerLifecycleProofs.tla artifacts recorded here.",
            "It does not establish liveness, result correctness, wire metadata correctness, digest correctness, or implementation refinement.",
        ],
    }

    canon_evidence = {
        "document_type": "aset-worker-canon-refinement-proof-evidence",
        "schema_version": 1,
        "status": "MECHANICALLY_PROVED",
        "scope": "EXACT_CANON_PROJECTION_TO_HANDWRITTEN_LIFECYCLE_EQUIVALENCE",
        "normative_precedence": "MACHINE_READABLE_CANON",
        "profile": "ASET-WORKER-CANON-TLA-PROJECTION-V1",
        "artifacts": {
            "source_model": {
                "path": "extension/canonical/source/worker-model.json",
                "sha256": sha(CANON / "source/worker-model.json"),
            },
            "generated_projection": {
                "module": "WorkerCanonProjection",
                "path": "extension/canonical/formal/WorkerCanonProjection.tla",
                "sha256": sha(FORMAL / "WorkerCanonProjection.tla"),
            },
            "target_model": {
                "module": "WorkerLifecycle",
                "path": "extension/canonical/formal/WorkerLifecycle.tla",
                "sha256": sha(FORMAL / "WorkerLifecycle.tla"),
            },
            "proof": {
                "module": "WorkerCanonRefinementProofs",
                "path": "extension/canonical/formal/WorkerCanonRefinementProofs.tla",
                "sha256": sha(FORMAL / "WorkerCanonRefinementProofs.tla"),
            },
        },
        "proof_gate": {
            "runner": "tools/run_formal_candidate_gate.py",
            "final_theorems": PROOFS["WORKER_CANON_TO_TLA"]["final_theorems"],
            "obligation_count_semantics": "RECORDED_EVIDENCE_NOT_FIXED_SEMANTIC_CONTRACT",
            "obligations_proved": canon["obligations_proved"],
            "verdict": "PASS",
        },
        "tlapm": {"commit": EXPECTED_TLAPM_COMMIT, "version": EXPECTED_TLAPM_VERSION},
        "claim_boundary": [
            "The proof establishes behavioral equivalence only for the declared standalone generated lifecycle-safety projection and the exact handwritten WorkerLifecycle.tla artifact recorded here.",
            "It does not establish correctness of the projection generator, natural-language or wire-schema equivalence, digest construction correctness, runtime execution correctness, liveness, result correctness, or implementation refinement.",
        ],
    }

    seed_evidence = {
        "document_type": "aset-worker-seed-refinement-proof-evidence",
        "schema_version": 1,
        "status": "MECHANICALLY_PROVED",
        "scope": "WORKER_ONLY_OPERATIONS_AS_PINNED_SEED_STUTTER",
        "normative_precedence": "MACHINE_READABLE_CANON",
        "artifacts": {
            "mapping": {
                "module": "WorkerSeedStuttering",
                "path": "extension/canonical/formal/WorkerSeedStuttering.tla",
                "sha256": sha(FORMAL / "WorkerSeedStuttering.tla"),
            },
            "proof": {
                "module": "WorkerSeedStutteringProofs",
                "path": "extension/canonical/formal/WorkerSeedStutteringProofs.tla",
                "sha256": sha(FORMAL / "WorkerSeedStutteringProofs.tla"),
            },
        },
        "upstream_seed": {
            "compatibility_standard": binding["compatibility_standard"],
            "release_tag": binding["seed_release_tag"],
            "release_commit": binding["seed_release_commit"],
            "module": "SeedResolution",
            "path": "seed/canonical/formal/SeedResolution.tla",
            "sha256": EXPECTED_SEED_RESOLUTION_SHA256,
            "materialization": "EXTERNAL_PINNED_SEED_SOURCE_NOT_VENDORED",
        },
        "proof_gate": {
            "runner": "tools/run_formal_candidate_gate.py",
            "final_theorems": PROOFS["WORKER_SEED_REFINEMENT"]["final_theorems"],
            "obligation_count_semantics": "RECORDED_EVIDENCE_NOT_FIXED_SEMANTIC_CONTRACT",
            "obligations_proved": seed["obligations_proved"],
            "verdict": "PASS",
        },
        "tlapm": {"commit": EXPECTED_TLAPM_COMMIT, "version": EXPECTED_TLAPM_VERSION},
        "claim_boundary": [
            "The proof applies to the declared Worker-to-Seed stuttering mapping and the exact pinned SeedResolution.tla artifact recorded here.",
            "It proves Worker-only lifecycle operations preserve the Seed projection and does not make Worker output a Seed request, Resolution, Authority, effect permission, or implementation refinement proof.",
        ],
    }

    registry = {
        "document_type": "aset-worker-formal-verification-registry",
        "schema_version": 1,
        "status": "MECHANICALLY_PROVED",
        "normative_precedence": "MACHINE_READABLE_CANON",
        "toolchain": {"tlapm_commit": EXPECTED_TLAPM_COMMIT, "tlapm_version": EXPECTED_TLAPM_VERSION},
        "proofs": [
            {
                "id": "WORKER_TLAPS_SAFETY",
                "evidence": "extension/canonical/assurance/lifecycle-proof.json",
                "status": "MECHANICALLY_PROVED",
                "obligations_proved": safety["obligations_proved"],
            },
            {
                "id": "WORKER_CANON_TO_TLA",
                "evidence": "extension/canonical/assurance/canon-refinement-proof.json",
                "status": "MECHANICALLY_PROVED",
                "obligations_proved": canon["obligations_proved"],
            },
            {
                "id": "WORKER_SEED_REFINEMENT",
                "evidence": "extension/canonical/assurance/seed-refinement-proof.json",
                "status": "MECHANICALLY_PROVED",
                "obligations_proved": seed["obligations_proved"],
            },
        ],
        "claim_boundary": "Mechanical proof evidence covers the abstract formal surfaces listed above. It does not establish arbitrary Worker runtime implementation refinement, liveness, result correctness, cryptographic correctness, or external-effect safety.",
    }
    return {
        "lifecycle-proof.json": lifecycle,
        "canon-refinement-proof.json": canon_evidence,
        "seed-refinement-proof.json": seed_evidence,
        "verification-registry.json": registry,
    }


def update_relation_metadata(evidence: dict[str, dict]) -> None:
    canon_relation = read_json(ASSURANCE / "canon-tla-refinement.json")
    canon_relation["status"] = "MECHANICALLY_PROVED"
    canon_relation["relation_type"] = "STANDALONE_GENERATED_PROJECTION_WITH_BEHAVIORAL_EQUIVALENCE_PROOF"
    canon_relation["proof_evidence"] = {
        "path": "extension/canonical/assurance/canon-refinement-proof.json",
        "status": "MECHANICALLY_PROVED",
        "obligations_proved": evidence["canon-refinement-proof.json"]["proof_gate"]["obligations_proved"],
    }
    (ASSURANCE / "canon-tla-refinement.json").write_bytes(canonical_bytes(canon_relation))

    seed_relation = read_json(ASSURANCE / "seed-refinement.json")
    seed_relation["status"] = "MECHANICALLY_PROVED"
    seed_relation["relation_type"] = "WORKER_ONLY_OPERATIONS_AS_SEED_STUTTER_PROOF"
    seed_relation["proof_evidence"] = {
        "path": "extension/canonical/assurance/seed-refinement-proof.json",
        "status": "MECHANICALLY_PROVED",
        "obligations_proved": evidence["seed-refinement-proof.json"]["proof_gate"]["obligations_proved"],
    }
    (ASSURANCE / "seed-refinement.json").write_bytes(canonical_bytes(seed_relation))


def expected_relation_metadata(evidence: dict[str, dict]) -> dict[str, dict]:
    # Build expected closed relations in memory without mutating the tree.
    canon_relation = read_json(ASSURANCE / "canon-tla-refinement.json")
    canon_relation["status"] = "MECHANICALLY_PROVED"
    canon_relation["relation_type"] = "STANDALONE_GENERATED_PROJECTION_WITH_BEHAVIORAL_EQUIVALENCE_PROOF"
    canon_relation["proof_evidence"] = {
        "path": "extension/canonical/assurance/canon-refinement-proof.json",
        "status": "MECHANICALLY_PROVED",
        "obligations_proved": evidence["canon-refinement-proof.json"]["proof_gate"]["obligations_proved"],
    }
    seed_relation = read_json(ASSURANCE / "seed-refinement.json")
    seed_relation["status"] = "MECHANICALLY_PROVED"
    seed_relation["relation_type"] = "WORKER_ONLY_OPERATIONS_AS_SEED_STUTTER_PROOF"
    seed_relation["proof_evidence"] = {
        "path": "extension/canonical/assurance/seed-refinement-proof.json",
        "status": "MECHANICALLY_PROVED",
        "obligations_proved": evidence["seed-refinement-proof.json"]["proof_gate"]["obligations_proved"],
    }
    return {
        "canon-tla-refinement.json": canon_relation,
        "seed-refinement.json": seed_relation,
    }


def build_repository_status_metadata() -> dict[str, dict]:
   IBILITY_PROFILE)
    profile["formal_release_gate"] = "REQUIRES_REPRODUCIBLE_FORMAL_RELEASE_GATE"
    profile["status"] = "FORMAL_ASSURANCE_MATERIALIZED_NOT_RELEASED"
    return {
        "standards/worker-compatibility/compatibility-standard-profile-v1.json": profile,
    }


def run_builder(script: str) -> None:
    result = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"builder failed: {script} -> {result.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    reports, _gate, errors = load_verified_runs()
    if errors:
        print("WORKER_FORMAL_EVIDENCE_INPUT=FAIL")
        for error in errors:
            print(f"WORKER_FORMAL_EVIDENCE_ERROR={error}")
        return 1

    evidence = build_evidence(reports)
    if args.check:
        mismatches: list[str] = []
        for name, payload in evidence.items():
            path = ASSURANCE / name
            if not path.is_file() or path.read_bytes() != canonical_bytes(payload):
                mismatches.append(f"stale or missing assurance evidence: {path.relative_to(ROOT)}")
        expected_relations = expected_relation_metadata(evidence)
        for name, payload in expected_relations.items():
            path = ASSURANCE / name
            if path.read_bytes() != canonical_bytes(payload):
                mismatches.append(f"stale assurance relation: {path.relative_to(ROOT)}")
        for rel, payload in build_repository_status_metadata().items():
            path = ROOT / rel
            if not path.is_file() or path.read_bytes() != canonical_bytes(payload):
                mismatches.append(f"stale repository status metadata: {rel}")
        if mismatches:
            print("WORKER_FORMAL_EVIDENCE_CHECK=FAIL")
            for mismatch in mismatches:
                print(f"WORKER_FORMAL_EVIDENCE_ERROR={mismatch}")
            return 1
        print("WORKER_FORMAL_EVIDENCE_CHECK=PASS")
        for proof_id, report in reports.items():
            print(f"{proof_id}_MATERIALIZED_OBLIGATIONS={report['obligations_proved']}")
        return 0

    for name, payload in evidence.items():
        (ASSURANCE / name).write_bytes(canonical_bytes(payload))
    update_relation_metadata(evidence)
    for rel, payload in build_repository_status_metadata().items():
        (ROOT / rel).write_bytes(canonical_bytes(payload))
    run_builder("tools/build_formal_relations.py")
    run_builder("tools/build_canon_package.py")
    print("WORKER_FORMAL_EVIDENCE_MATERIALIZATION=PASS")
    for proof_id, report in reports.items():
        print(f"{proof_id}_MATERIALIZED_OBLIGATIONS={report['obligations_proved']}")
    print("NEXT=python tools/run_formal_release_gate.py --tlapm <path> --seed-root <path>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
