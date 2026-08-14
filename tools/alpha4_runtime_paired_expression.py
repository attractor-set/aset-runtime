from __future__ import annotations

import itertools
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FORTH = ROOT / "runtime/alpha4/operational/components.forth"

EXPECTED_WORDS = {
    "START-FRESH": ("EXACT-START?", "FRESH-ID?", "ADD-START", "ATTEMPT-STARTED"),
    "START-REPLAY": (
        "EXACT-START?",
        "EXACT-START-REPLAY?",
        "KEEP-STATE",
        "IDEMPOTENT-REPLAY",
    ),
    "REJECT-START-CONFLICT": (
        "EXACT-START?",
        "START-CONFLICT?",
        "KEEP-STATE",
        "ATTEMPT-IDENTITY-CONFLICT",
    ),
    "END-RESULT": (
        "EXACT-TERMINAL?",
        "EXACT-RUNNING?",
        "FRESH-TERMINAL?",
        "KIND-RESULT?",
        "ADD-TERMINAL",
        "ATTEMPT-ENDED-WITH-RESULT",
    ),
    "END-NO-RESULT": (
        "EXACT-TERMINAL?",
        "EXACT-RUNNING?",
        "FRESH-TERMINAL?",
        "KIND-NO-RESULT?",
        "ADD-TERMINAL",
        "ATTEMPT-ENDED-WITH-NO-RESULT",
    ),
    "END-REPLAY": (
        "EXACT-TERMINAL?",
        "EXACT-TERMINAL-REPLAY?",
        "KEEP-STATE",
        "IDEMPOTENT-REPLAY",
    ),
    "REJECT-END-CONFLICT": (
        "EXACT-TERMINAL?",
        "TERMINAL-CONFLICT?",
        "KEEP-STATE",
        "TERMINAL-ATTEMPT-IMMUTABLE",
    ),
    "REJECT-END-NOT-RUNNING": (
        "EXACT-TERMINAL?",
        "NO-TERMINAL-FOR-ID?",
        "NOT-EXACT-RUNNING?",
        "KEEP-STATE",
        "ATTEMPT-NOT-RUNNING",
    ),
}

START_FIELDS = {"attempt_id", "attempt_digest", "runtime_binding", "descriptor_binding"}
TERMINAL_FIELDS = {
    "attempt_id",
    "attempt_digest",
    "terminal_kind",
    "terminal_digest",
    "terminal_binding",
    "evidence_bindings",
}
TERMINAL_KINDS = {"RESULT", "NO_RESULT"}


def parse_operational_words() -> dict[str, tuple[str, ...]]:
    text = FORTH.read_text(encoding="utf-8")
    pattern = re.compile(r":\s+(?P<word>[A-Z0-9-]+)\s+\([^)]*--[^)]*\)\s+(?P<body>.*?)\s*;")
    words = {
        match.group("word"): tuple(match.group("body").split()) for match in pattern.finditer(text)
    }
    if words != EXPECTED_WORDS:
        raise RuntimeError(f"restricted operational vocabulary mismatch: {words!r}")
    return words


def exact_start(value: dict[str, Any]) -> bool:
    return set(value) == START_FIELDS and all(
        isinstance(value[field], str) and value[field] for field in START_FIELDS
    )


def exact_terminal(value: dict[str, Any]) -> bool:
    if set(value) != TERMINAL_FIELDS:
        return False
    if value["terminal_kind"] not in TERMINAL_KINDS:
        return False
    for field in TERMINAL_FIELDS - {"terminal_kind", "evidence_bindings"}:
        if not isinstance(value[field], str) or not value[field]:
            return False
    evidence = value["evidence_bindings"]
    return isinstance(evidence, list) and all(isinstance(item, str) and item for item in evidence)


def _result(accepted: bool, code: str, changed: bool) -> dict[str, Any]:
    return {
        "accepted": accepted,
        "code": code,
        "state_changed": changed,
        "seed_projection": {"action": "STUTTER", "effect_permitted": False},
    }


def _copy_state(state: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {"starts": deepcopy(state["starts"]), "terminals": deepcopy(state["terminals"])}


def _matching_start(state: dict[str, Any], terminal: dict[str, Any]) -> bool:
    return any(
        item["attempt_id"] == terminal["attempt_id"]
        and item["attempt_digest"] == terminal["attempt_digest"]
        for item in state["starts"]
    )


def operational_start(
    state: dict[str, list[dict[str, Any]]], start: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    parse_operational_words()
    if not exact_start(start):
        raise ValueError("exact start record required")
    current = _copy_state(state)
    same_id = [item for item in current["starts"] if item["attempt_id"] == start["attempt_id"]]
    if not same_id:
        current["starts"].append(deepcopy(start))
        return current, _result(True, "ATTEMPT_STARTED", True)
    if start in same_id:
        return current, _result(True, "IDEMPOTENT_REPLAY", False)
    return current, _result(False, "ATTEMPT_IDENTITY_CONFLICT", False)


def relational_start(
    state: dict[str, list[dict[str, Any]]], start: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    if not exact_start(start):
        raise ValueError("exact start record required")
    current = _copy_state(state)
    identical = start in current["starts"]
    identifier_exists = any(item["attempt_id"] == start["attempt_id"] for item in current["starts"])
    if identical:
        return current, _result(True, "IDEMPOTENT_REPLAY", False)
    if identifier_exists:
        return current, _result(False, "ATTEMPT_IDENTITY_CONFLICT", False)
    current["starts"].append(deepcopy(start))
    return current, _result(True, "ATTEMPT_STARTED", True)


def operational_end(
    state: dict[str, list[dict[str, Any]]], terminal: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    parse_operational_words()
    if not exact_terminal(terminal):
        raise ValueError("exact terminal record required")
    current = _copy_state(state)
    same_terminal_id = [
        item for item in current["terminals"] if item["attempt_id"] == terminal["attempt_id"]
    ]
    if terminal in same_terminal_id:
        return current, _result(True, "IDEMPOTENT_REPLAY", False)
    if same_terminal_id:
        return current, _result(False, "TERMINAL_ATTEMPT_IMMUTABLE", False)
    if not _matching_start(current, terminal):
        return current, _result(False, "ATTEMPT_NOT_RUNNING", False)
    current["terminals"].append(deepcopy(terminal))
    if terminal["terminal_kind"] == "RESULT":
        return current, _result(True, "ATTEMPT_ENDED_WITH_RESULT", True)
    return current, _result(True, "ATTEMPT_ENDED_WITH_NO_RESULT", True)


def relational_end(
    state: dict[str, list[dict[str, Any]]], terminal: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    if not exact_terminal(terminal):
        raise ValueError("exact terminal record required")
    current = _copy_state(state)
    identical = terminal in current["terminals"]
    identifier_exists = any(
        item["attempt_id"] == terminal["attempt_id"] for item in current["terminals"]
    )
    if identical:
        return current, _result(True, "IDEMPOTENT_REPLAY", False)
    if identifier_exists:
        return current, _result(False, "TERMINAL_ATTEMPT_IMMUTABLE", False)
    matching = _matching_start(current, terminal)
    if not matching:
        return current, _result(False, "ATTEMPT_NOT_RUNNING", False)
    current["terminals"].append(deepcopy(terminal))
    code = (
        "ATTEMPT_ENDED_WITH_RESULT"
        if terminal["terminal_kind"] == "RESULT"
        else "ATTEMPT_ENDED_WITH_NO_RESULT"
    )
    return current, _result(True, code, True)


def bounded_domain() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, list[dict[str, Any]]]],
]:
    starts = [
        {
            "attempt_id": attempt_id,
            "attempt_digest": attempt_digest,
            "runtime_binding": "runtime:0",
            "descriptor_binding": "descriptor:0",
        }
        for attempt_id, attempt_digest in itertools.product(("a0", "a1"), ("d0", "d1"))
    ]
    terminals = [
        {
            "attempt_id": attempt_id,
            "attempt_digest": attempt_digest,
            "terminal_kind": terminal_kind,
            "terminal_digest": terminal_digest,
            "terminal_binding": "terminal-binding:0",
            "evidence_bindings": ["e0"],
        }
        for attempt_id, attempt_digest, terminal_kind, terminal_digest in itertools.product(
            ("a0", "a1"), ("d0", "d1"), ("RESULT", "NO_RESULT"), ("t0", "t1")
        )
    ]
    starts_by_id = {
        attempt_id: [item for item in starts if item["attempt_id"] == attempt_id]
        for attempt_id in ("a0", "a1")
    }
    states: list[dict[str, list[dict[str, Any]]]] = []
    start_choices = [[None, *starts_by_id[attempt_id]] for attempt_id in ("a0", "a1")]
    for selected in itertools.product(*start_choices):
        selected_starts = [deepcopy(item) for item in selected if item is not None]
        if not selected_starts:
            states.append({"starts": [], "terminals": []})
            continue
        terminal_choices: list[list[dict[str, Any] | None]] = []
        for start in selected_starts:
            matching = [
                item
                for item in terminals
                if item["attempt_id"] == start["attempt_id"]
                and item["attempt_digest"] == start["attempt_digest"]
            ]
            terminal_choices.append([None, *matching])
        for chosen_terminals in itertools.product(*terminal_choices):
            states.append(
                {
                    "starts": deepcopy(selected_starts),
                    "terminals": [deepcopy(item) for item in chosen_terminals if item is not None],
                }
            )
    return starts, terminals, states


def bounded_pairing_check() -> dict[str, int]:
    starts, terminals, states = bounded_domain()
    start_checks = 0
    end_checks = 0
    for state in states:
        for start in starts:
            op_state, op_result = operational_start(state, start)
            rel_state, rel_result = relational_start(state, start)
            if op_state != rel_state or op_result != rel_result:
                raise RuntimeError(f"start pairing mismatch: state={state!r} start={start!r}")
            start_checks += 1
        for terminal in terminals:
            op_state, op_result = operational_end(state, terminal)
            rel_state, rel_result = relational_end(state, terminal)
            if op_state != rel_state or op_result != rel_result:
                raise RuntimeError(f"end pairing mismatch: state={state!r} terminal={terminal!r}")
            end_checks += 1
    return {"start": start_checks, "end": end_checks, "total": start_checks + end_checks}


def runtime_invariant(state: dict[str, list[dict[str, Any]]]) -> bool:
    starts = state.get("starts")
    terminals = state.get("terminals")
    if not isinstance(starts, list) or not isinstance(terminals, list):
        return False
    if not all(exact_start(item) for item in starts):
        return False
    if not all(exact_terminal(item) for item in terminals):
        return False
    start_ids = [item["attempt_id"] for item in starts]
    terminal_ids = [item["attempt_id"] for item in terminals]
    if len(start_ids) != len(set(start_ids)):
        return False
    if len(terminal_ids) != len(set(terminal_ids)):
        return False
    return all(_matching_start(state, terminal) for terminal in terminals)


def _append_only(before: list[dict[str, Any]], after: list[dict[str, Any]]) -> bool:
    return all(item in after for item in before)


def bounded_safety_check() -> dict[str, int]:
    starts, terminals, states = bounded_domain()
    start_checks = 0
    end_checks = 0
    for state in states:
        if not runtime_invariant(state):
            raise RuntimeError(f"bounded source state violates Runtime invariant: {state!r}")
        for start in starts:
            next_state, _ = relational_start(state, start)
            if not runtime_invariant(next_state):
                raise RuntimeError(
                    f"start transition violates Runtime invariant: state={state!r} start={start!r}"
                )
            if not _append_only(state["starts"], next_state["starts"]):
                raise RuntimeError("start transition violated starts append-only boundary")
            if not _append_only(state["terminals"], next_state["terminals"]):
                raise RuntimeError("start transition violated terminals append-only boundary")
            start_checks += 1
        for terminal in terminals:
            next_state, _ = relational_end(state, terminal)
            if not runtime_invariant(next_state):
                raise RuntimeError(
                    "end transition violates Runtime invariant: "
                    f"state={state!r} terminal={terminal!r}"
                )
            if not _append_only(state["starts"], next_state["starts"]):
                raise RuntimeError("end transition violated starts append-only boundary")
            if not _append_only(state["terminals"], next_state["terminals"]):
                raise RuntimeError("end transition violated terminals append-only boundary")
            end_checks += 1
    return {"start": start_checks, "end": end_checks, "total": start_checks + end_checks}


def main() -> int:
    parse_operational_words()
    counts = bounded_pairing_check()
    safety = bounded_safety_check()
    print("ALPHA4_RUNTIME_OPERATIONAL_WORDS=8/8 PASS")
    print(f"ALPHA4_RUNTIME_START_PAIRED_CASES={counts['start']}/{counts['start']} PASS")
    print(f"ALPHA4_RUNTIME_END_PAIRED_CASES={counts['end']}/{counts['end']} PASS")
    print(f"ALPHA4_RUNTIME_PAIRED_CASES={counts['total']}/{counts['total']} PASS")
    print(f"ALPHA4_RUNTIME_BOUNDED_SAFETY={safety['total']}/{safety['total']} PASS")
    print("ALPHA4_RUNTIME_APPEND_ONLY_BOUNDARY=PASS")
    print("ALPHA4_RUNTIME_PAIRED_EXPRESSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
