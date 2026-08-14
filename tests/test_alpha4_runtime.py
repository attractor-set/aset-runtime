from __future__ import annotations

from tools.alpha4_runtime_paired_expression import (
    bounded_pairing_check,
    bounded_safety_check,
    operational_end,
    operational_start,
    parse_operational_words,
)
from tools.validate_alpha4_runtime import main as validate_runtime


def test_runtime_alpha4_validation() -> None:
    assert validate_runtime() == 0


def test_operational_surface_is_exactly_eight_components() -> None:
    assert len(parse_operational_words()) == 8


def test_bounded_operational_relational_pairing() -> None:
    evidence = bounded_pairing_check()
    assert evidence == {"start": 484, "end": 1936, "total": 2420}


def test_bounded_runtime_safety_and_append_only_boundaries() -> None:
    evidence = bounded_safety_check()
    assert evidence == {"start": 484, "end": 1936, "total": 2420}


def test_result_and_no_result_are_distinct_exact_terminals() -> None:
    start = {
        "attempt_id": "a0",
        "attempt_digest": "d0",
        "runtime_binding": "runtime:0",
        "descriptor_binding": "descriptor:0",
    }
    empty = {"starts": [], "terminals": []}
    running, started = operational_start(empty, start)
    assert started["code"] == "ATTEMPT_STARTED"
    result_terminal = {
        "attempt_id": "a0",
        "attempt_digest": "d0",
        "terminal_kind": "RESULT",
        "terminal_digest": "t0",
        "terminal_binding": "tb0",
        "evidence_bindings": ["e0"],
    }
    no_result_terminal = {**result_terminal, "terminal_kind": "NO_RESULT", "terminal_digest": "t1"}
    result_state, result = operational_end(running, result_terminal)
    no_result_state, no_result = operational_end(running, no_result_terminal)
    assert result["code"] == "ATTEMPT_ENDED_WITH_RESULT"
    assert no_result["code"] == "ATTEMPT_ENDED_WITH_NO_RESULT"
    assert result_state != no_result_state
    assert (
        result["seed_projection"]
        == no_result["seed_projection"]
        == {
            "action": "STUTTER",
            "effect_permitted": False,
        }
    )


def test_start_identity_conflict_covers_non_digest_bindings() -> None:
    start = {
        "attempt_id": "a0",
        "attempt_digest": "d0",
        "runtime_binding": "runtime:0",
        "descriptor_binding": "descriptor:0",
    }
    running, _ = operational_start({"starts": [], "terminals": []}, start)
    conflicting = {**start, "runtime_binding": "runtime:1"}
    next_state, result = operational_start(running, conflicting)
    assert next_state == running
    assert result["code"] == "ATTEMPT_IDENTITY_CONFLICT"
    assert result["accepted"] is False


def test_terminal_identity_conflict_covers_terminal_binding() -> None:
    start = {
        "attempt_id": "a0",
        "attempt_digest": "d0",
        "runtime_binding": "runtime:0",
        "descriptor_binding": "descriptor:0",
    }
    running, _ = operational_start({"starts": [], "terminals": []}, start)
    terminal = {
        "attempt_id": "a0",
        "attempt_digest": "d0",
        "terminal_kind": "RESULT",
        "terminal_digest": "t0",
        "terminal_binding": "terminal-binding:0",
        "evidence_bindings": ["e0"],
    }
    ended, _ = operational_end(running, terminal)
    conflicting = {**terminal, "terminal_binding": "terminal-binding:1"}
    next_state, result = operational_end(ended, conflicting)
    assert next_state == ended
    assert result["code"] == "TERMINAL_ATTEMPT_IMMUTABLE"
    assert result["accepted"] is False
