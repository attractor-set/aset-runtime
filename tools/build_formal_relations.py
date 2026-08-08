from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "extension/canonical"
FORMAL = CANON / "formal"
ASSURANCE = CANON / "assurance"
MODEL = CANON / "source/worker-model.json"
BINDING = ROOT / "upstream/ASET_SEED_BINDING.json"


def sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_proof_evidence(name: str) -> dict | None:
    path = ASSURANCE / name
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("status") != "MECHANICALLY_PROVED":
        return None
    return payload


def main() -> int:
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    canon_relation = {
        "document_type": "aset-worker-canon-tla-relation",
        "schema_version": 1,
        "status": "PROOF_CANDIDATE_MATERIALIZED",
        "normative_precedence": "MACHINE_READABLE_CANON",
        "relation_type": "STANDALONE_GENERATED_PROJECTION_WITH_BEHAVIORAL_EQUIVALENCE_PROOF_CANDIDATE",
        "profile": "ASET-WORKER-CANON-TLA-PROJECTION-V1",
        "source_model": {
            "path": "extension/canonical/source/worker-model.json",
            "sha256": sha(MODEL),
        },
        "generated_projection": {
            "module": "WorkerCanonProjection",
            "path": "extension/canonical/formal/WorkerCanonProjection.tla",
            "sha256": sha(FORMAL / "WorkerCanonProjection.tla"),
            "generator": "tools/generate_canon_tla_projection.py",
            "generator_sha256": sha(ROOT / "tools/generate_canon_tla_projection.py"),
        },
        "target_model": {
            "module": "WorkerLifecycle",
            "path": "extension/canonical/formal/WorkerLifecycle.tla",
            "sha256": sha(FORMAL / "WorkerLifecycle.tla"),
        },
        "proof_candidate": {
            "module": "WorkerCanonRefinementProofs",
            "path": "extension/canonical/formal/WorkerCanonRefinementProofs.tla",
            "sha256": sha(FORMAL / "WorkerCanonRefinementProofs.tla"),
            "final_theorems": [
                "WorkerSafetyEquivalentToCanonProjection",
                "WorkerLifecycleBehaviorallyEquivalentToCanonProjection",
            ],
        },
        "scope": "DECLARED_LIFECYCLE_SAFETY_PROJECTION",
        "excluded_claims": [
            "wire-schema equivalence",
            "digest construction correctness",
            "exact metadata-payload equivalence",
            "runtime execution correctness",
            "liveness",
            "result correctness",
            "implementation refinement",
        ],
    }
    seed_relation = {
        "document_type": "aset-worker-seed-refinement-relation",
        "schema_version": 1,
        "status": "PROOF_CANDIDATE_MATERIALIZED",
        "relation_type": "WORKER_ONLY_OPERATIONS_AS_SEED_STUTTER_PROOF_CANDIDATE",
        "upstream_seed": {
            "compatibility_standard": binding["compatibility_standard"],
            "release_tag": binding["seed_release_tag"],
            "release_commit": binding["seed_release_commit"],
            "canon_id": binding["canon_id"],
            "canon_version": binding["canon_version"],
            "canon_package_digest": binding["canon_package_digest"],
            "module": "SeedResolution",
            "path": "seed/canonical/formal/SeedResolution.tla",
            "sha256": "sha256:1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926",
            "materialization": "EXTERNAL_PINNED_SEED_SOURCE_NOT_VENDORED",
        },
        "mapping_candidate": {
            "module": "WorkerSeedStuttering",
            "path": "extension/canonical/formal/WorkerSeedStuttering.tla",
            "sha256": sha(FORMAL / "WorkerSeedStuttering.tla"),
            "worker_operations": "SEED_STUTTER",
        },
        "proof_candidate": {
            "module": "WorkerSeedStutteringProofs",
            "path": "extension/canonical/formal/WorkerSeedStutteringProofs.tla",
            "sha256": sha(FORMAL / "WorkerSeedStutteringProofs.tla"),
            "final_theorems": [
                "WorkerOperationsPreserveSeedProjection",
                "WorkerOperationsPreserveSeedOwnedState",
                "WorkerCompositionRefinesSeedResolutionByStuttering",
            ],
        },
        "claim_boundary": "Worker lifecycle operations alter only Worker extension state and are stuttering steps with respect to the exact pinned Seed projection.",
        "excluded_claims": [
            "Worker output is a Seed request",
            "Worker output is a Seed resolution",
            "Worker evidence creates Authority",
            "Worker execution grants effect permission",
            "implementation refinement",
            "liveness",
        ],
    }
    lifecycle_proof = {
        "document_type": "aset-worker-lifecycle-proof-candidate",
        "schema_version": 1,
        "status": "PROOF_CANDIDATE_MATERIALIZED",
        "model": {
            "module": "WorkerLifecycle",
            "path": "extension/canonical/formal/WorkerLifecycle.tla",
            "sha256": sha(FORMAL / "WorkerLifecycle.tla"),
        },
        "proof": {
            "module": "WorkerLifecycleProofs",
            "path": "extension/canonical/formal/WorkerLifecycleProofs.tla",
            "sha256": sha(FORMAL / "WorkerLifecycleProofs.tla"),
            "final_theorems": [
                "SpecImpliesAlwaysWorkerSafety",
                "SpecImpliesAcceptedAppendOnly",
                "SpecImpliesStartedAppendOnly",
                "SpecImpliesTerminalAppendOnly",
                "SpecImpliesWorkerStateChangesOnlyByRecognizedTransition",
            ],
        },
        "excluded_claims": [
            "wire metadata correctness",
            "digest correctness",
            "liveness",
            "result correctness",
            "implementation refinement",
        ],
    }
    canon_evidence = load_proof_evidence("canon-refinement-proof.json")
    if canon_evidence is not None:
        canon_relation["status"] = "MECHANICALLY_PROVED"
        canon_relation["relation_type"] = "STANDALONE_GENERATED_PROJECTION_WITH_BEHAVIORAL_EQUIVALENCE_PROOF"
        canon_relation["proof_evidence"] = {
            "path": "extension/canonical/assurance/canon-refinement-proof.json",
            "status": "MECHANICALLY_PROVED",
            "obligations_proved": canon_evidence["proof_gate"]["obligations_proved"],
        }

    seed_evidence = load_proof_evidence("seed-refinement-proof.json")
    if seed_evidence is not None:
        seed_relation["status"] = "MECHANICALLY_PROVED"
        seed_relation["relation_type"] = "WORKER_ONLY_OPERATIONS_AS_SEED_STUTTER_PROOF"
        seed_relation["proof_evidence"] = {
            "path": "extension/canonical/assurance/seed-refinement-proof.json",
            "status": "MECHANICALLY_PROVED",
            "obligations_proved": seed_evidence["proof_gate"]["obligations_proved"],
        }

    write(ASSURANCE / "canon-tla-refinement.json", canon_relation)
    write(ASSURANCE / "seed-refinement.json", seed_relation)
    write(ASSURANCE / "lifecycle-proof-candidate.json", lifecycle_proof)
    print("WORKER_FORMAL_RELATIONS_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
