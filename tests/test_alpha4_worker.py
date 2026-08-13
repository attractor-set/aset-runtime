from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from tools.alpha4_worker_paired_expression import (
    bounded_pairing_check,
    empty_state,
    operational_end,
    operational_start,
)
from tools.validate_alpha4_worker import parse_binding, validate_worker_surface

ROOT = Path(__file__).resolve().parents[1]


def start_request(**changes: str) -> dict[str, str]:
    value = {
        "work_id": "work:1",
        "work_binding_digest": "sha256:" + "1" * 64,
        "worker_binding": "sha256:" + "2" * 64,
        "work_descriptor_binding": "sha256:" + "3" * 64,
    }
    value.update(changes)
    return value


def end_request(**changes: str | None) -> dict[str, str | None]:
    value: dict[str, str | None] = {
        "work_id": "work:1",
        "work_binding_digest": "sha256:" + "1" * 64,
        "terminal_kind": "RESULT",
        "terminal_record_digest": "sha256:" + "7" * 64,
        "terminal_binding": "sha256:" + "8" * 64,
        "evidence_bindings": ("sha256:" + "9" * 64,),
    }
    value.update(changes)
    return value


def test_worker_alpha4_surface_is_valid() -> None:
    validate_worker_surface()


def test_seed_binding_covers_full_active_seed_subject() -> None:
    sources = parse_binding()
    assert len(sources) == 10
    assert "seed/alpha4/SEED.aset" in sources
    assert "theory/local-recognition/formal/RecognitionCardinality.tla" in sources
    assert "theory/local-recognition/formal/RecognitionCardinalityProofs.tla" in sources


def test_start_fresh_replay_conflict() -> None:
    state = empty_state()
    request = start_request()
    state, result = operational_start(state, request)
    assert result["code"] == "WORK_STARTED"
    assert result["seed_projection"] == "STUTTER"
    replay_state, replay = operational_start(state, request)
    assert replay_state == state
    assert replay["code"] == "IDEMPOTENT_REPLAY"
    conflict_request = start_request(work_descriptor_binding="sha256:" + "4" * 64)
    conflict_state, conflict = operational_start(state, conflict_request)
    assert conflict_state == state
    assert conflict["code"] == "WORK_IDENTITY_CONFLICT"


def test_result_and_no_result_are_explicit_xor_terminal_forms() -> None:
    running, _ = operational_start(empty_state(), start_request())
    result_state, result = operational_end(running, end_request())
    assert result["code"] == "WORK_ENDED_WITH_RESULT"
    assert result_state["terminals"][0]["terminal_kind"] == "RESULT"

    no_result_state, no_result = operational_end(
        running,
        end_request(
            terminal_kind="NO_RESULT",
            terminal_record_digest="sha256:" + "a" * 64,
            terminal_binding="sha256:" + "b" * 64,
        ),
    )
    assert no_result["code"] == "WORK_ENDED_WITH_NO_RESULT"
    assert no_result_state["terminals"][0]["terminal_kind"] == "NO_RESULT"


def test_terminal_is_immutable_and_exact_replay_is_idempotent() -> None:
    running, _ = operational_start(empty_state(), start_request())
    terminal_request = end_request()
    terminal, _ = operational_end(running, terminal_request)
    replay_state, replay = operational_end(terminal, terminal_request)
    assert replay_state == terminal
    assert replay["code"] == "IDEMPOTENT_REPLAY"

    conflicting = deepcopy(terminal_request)
    conflicting["terminal_kind"] = "NO_RESULT"
    conflicting["terminal_record_digest"] = "sha256:" + "a" * 64
    conflicting["terminal_binding"] = "sha256:" + "b" * 64
    conflict_state, conflict = operational_end(terminal, conflicting)
    assert conflict_state == terminal
    assert conflict["code"] == "TERMINAL_WORK_IMMUTABLE"

    evidence_conflict = deepcopy(terminal_request)
    evidence_conflict["evidence_bindings"] = ("sha256:" + "c" * 64,)
    evidence_state, evidence_result = operational_end(terminal, evidence_conflict)
    assert evidence_state == terminal
    assert evidence_result["code"] == "TERMINAL_WORK_IMMUTABLE"


def test_missing_and_mismatched_bindings_fail_closed() -> None:
    missing_start = start_request(work_binding_digest="")
    state, result = operational_start(empty_state(), missing_start)
    assert state == empty_state()
    assert result["code"] == "WORK_BINDING_REQUIRED"

    running, _ = operational_start(empty_state(), start_request())
    mismatch_state, mismatch = operational_end(
        running,
        end_request(work_binding_digest="sha256:" + "f" * 64),
    )
    assert mismatch_state == running
    assert mismatch["code"] == "WORK_BINDING_MISMATCH"


def test_worker_never_claims_seed_authority_or_effect() -> None:
    state, start_result = operational_start(empty_state(), start_request())
    _, end_result = operational_end(state, end_request())
    for result in (start_result, end_result):
        assert result["authority_created"] is False
        assert result["effect_permitted"] is False
        assert result["seed_projection"] == "STUTTER"


def test_operational_relational_pairing_covers_every_branch() -> None:
    checks, branches = bounded_pairing_check()
    assert checks > 0
    assert len(branches) == 12
    assert all(count > 0 for count in branches.values())


def test_worker_uniqueness_is_domain_size_independent() -> None:
    relation = (ROOT / "worker/alpha4/formal/WorkerRelations.tla").read_text()
    assert "Cardinality(" not in relation
    assert "\\A left \\in s.started" in relation
    assert "\\A right \\in s.started" in relation
    assert "\\A left \\in s.terminals" in relation
    assert "\\A right \\in s.terminals" in relation


def test_worker_state_changing_relations_use_explicit_post_state_records() -> None:
    relation = (ROOT / "worker/alpha4/formal/WorkerRelations.tla").read_text()
    assert "[s EXCEPT" not in relation
    assert "t = [started |-> s.started \\cup {p}," in relation
    assert "terminals |-> s.terminals \\cup {p}]" in relation
