from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "extension/canonical/source/worker-model.json"
OUTPUT = ROOT / "extension/canonical/formal/WorkerCanonProjection.tla"
PROFILE = "ASET-WORKER-CANON-TLA-PROJECTION-V1"

EXPECTED_TRANSITIONS = [
    ("UNREGISTERED", "ACCEPT_WORK", "ACCEPTED"),
    ("ACCEPTED", "START_WORK", "RUNNING"),
    ("RUNNING", "COMPLETE_WITH_RESULT", "RESULT"),
    ("RUNNING", "COMPLETE_WITH_NO_RESULT", "NO_RESULT"),
]
EXPECTED_OPERATIONS = [
    "ACCEPT_WORK",
    "START_WORK",
    "COMPLETE_WITH_RESULT",
    "COMPLETE_WITH_NO_RESULT",
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate(model: dict) -> None:
    errors: list[str] = []
    if model.get("canon_id") != "ASET-WORKER-CANON-0.1-ALPHA1":
        errors.append("unexpected canon_id")
    if model.get("version") != "0.1.0-alpha.0":
        errors.append("unexpected version")
    if model.get("state_machine", {}).get("terminal_states") != ["RESULT", "NO_RESULT"]:
        errors.append("terminal states mismatch")
    if model.get("state_machine", {}).get("terminal_relation") != "XOR":
        errors.append("terminal relation is not XOR")
    transitions = [
        (x.get("from"), x.get("operation"), x.get("to"))
        for x in model.get("state_machine", {}).get("transitions", [])
    ]
    if transitions != EXPECTED_TRANSITIONS:
        errors.append("state-machine transition set mismatch")
    operations = [x.get("kind") for x in model.get("operations", [])]
    if operations != EXPECTED_OPERATIONS:
        errors.append("operation catalogue mismatch")
    if len(model.get("requirements", [])) != 11:
        errors.append("requirement count mismatch")
    if len(model.get("invariants", [])) != 11:
        errors.append("invariant count mismatch")
    if errors:
        raise ValueError("; ".join(errors))


def render(model: dict) -> str:
    source_sha = sha256_bytes(MODEL.read_bytes())
    return f'''---------------------- MODULE WorkerCanonProjection ----------------------
EXTENDS FiniteSets

(***************************************************************************
GENERATED FILE. DO NOT EDIT.
Source: extension/canonical/source/worker-model.json
Source SHA-256: {source_sha}
Projection profile: {PROFILE}

This is a standalone safety projection generated from the exact machine-
readable Worker canon. It does not EXTEND or instantiate WorkerLifecycle.
WorkerCanonRefinementProofs.tla explicitly instantiates this generated module
onto the handwritten assurance state.

Wire-level digest construction, exact metadata payloads, runtime execution,
liveness, result correctness and implementation refinement remain outside this
projection. The deterministic generator is part of the assurance trusted
computing base.
***************************************************************************)

CONSTANT WorkIds

VARIABLES accepted, started, resultWorks, noResultWorks

CanonVars == <<accepted, started, resultWorks, noResultWorks>>

CanonInit ==
    /\\ accepted = {{}}
    /\\ started = {{}}
    /\\ resultWorks = {{}}
    /\\ noResultWorks = {{}}

CanonTerminal == resultWorks \\cup noResultWorks

CanonAcceptWork(w) ==
    /\\ w \\in WorkIds
    /\\ w \\notin accepted
    /\\ accepted' = accepted \\cup {{w}}
    /\\ UNCHANGED <<started, resultWorks, noResultWorks>>

CanonStartWork(w) ==
    /\\ w \\in accepted
    /\\ w \\notin started
    /\\ w \\notin CanonTerminal
    /\\ started' = started \\cup {{w}}
    /\\ UNCHANGED <<accepted, resultWorks, noResultWorks>>

CanonCompleteWithResult(w) ==
    /\\ w \\in started
    /\\ w \\notin CanonTerminal
    /\\ resultWorks' = resultWorks \\cup {{w}}
    /\\ UNCHANGED <<accepted, started, noResultWorks>>

CanonCompleteWithNoResult(w) ==
    /\\ w \\in started
    /\\ w \\notin CanonTerminal
    /\\ noResultWorks' = noResultWorks \\cup {{w}}
    /\\ UNCHANGED <<accepted, started, resultWorks>>

CanonRecognizedWorkerTransition ==
    \\/ \\E w \\in WorkIds : CanonAcceptWork(w)
    \\/ \\E w \\in WorkIds : CanonStartWork(w)
    \\/ \\E w \\in WorkIds : CanonCompleteWithResult(w)
    \\/ \\E w \\in WorkIds : CanonCompleteWithNoResult(w)

CanonNext == CanonRecognizedWorkerTransition
CanonSpec == CanonInit /\\ [][CanonNext]_CanonVars

CanonTypeOK ==
    /\\ accepted \\subseteq WorkIds
    /\\ started \\subseteq WorkIds
    /\\ resultWorks \\subseteq WorkIds
    /\\ noResultWorks \\subseteq WorkIds

CanonStartedImpliesAccepted == started \\subseteq accepted
CanonResultImpliesStarted == resultWorks \\subseteq started
CanonNoResultImpliesStarted == noResultWorks \\subseteq started
CanonResultXorNoResult == resultWorks \\cap noResultWorks = {{}}

CanonWorkerSafety ==
    /\\ CanonTypeOK
    /\\ CanonStartedImpliesAccepted
    /\\ CanonResultImpliesStarted
    /\\ CanonNoResultImpliesStarted
    /\\ CanonResultXorNoResult

=============================================================================
'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    model = json.loads(MODEL.read_text(encoding="utf-8"))
    validate(model)
    rendered = render(model).encode("utf-8")
    if args.check:
        if not OUTPUT.is_file():
            print("WORKER_CANON_PROJECTION_CHECK=FAIL")
            print(f"WORKER_CANON_PROJECTION_ERROR=missing {OUTPUT.relative_to(ROOT)}")
            return 1
        actual = OUTPUT.read_bytes()
        if actual != rendered:
            print("WORKER_CANON_PROJECTION_CHECK=FAIL")
            print("WORKER_CANON_PROJECTION_ERROR=committed projection is stale")
            print(f"WORKER_CANON_PROJECTION_EXPECTED_SHA256={sha256_bytes(rendered)}")
            print(f"WORKER_CANON_PROJECTION_ACTUAL_SHA256={sha256_bytes(actual)}")
            return 1
        print(f"WORKER_CANON_PROJECTION={OUTPUT.relative_to(ROOT)}")
        print(f"WORKER_CANON_PROJECTION_SHA256=sha256:{sha256_bytes(actual)}")
        print("WORKER_CANON_PROJECTION_CHECK=PASS")
        return 0
    OUTPUT.write_bytes(rendered)
    print(f"WORKER_CANON_PROJECTION={OUTPUT.relative_to(ROOT)}")
    print(f"WORKER_CANON_PROJECTION_SHA256=sha256:{sha256_bytes(rendered)}")
    print("WORKER_CANON_PROJECTION_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
