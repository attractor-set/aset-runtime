from __future__ import annotations

import argparse
import itertools
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.alpha4_runtime_seed_extension import parse_seed_binding, sha256, tree_digest

ROOT = Path(__file__).resolve().parents[1]


class AirgapError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AirgapError(message)


def _load_expression(path: Path) -> dict[str, Any]:
    namespace: dict[str, Any] = {
        "__file__": str(path),
        "__name__": "aset_runtime_alpha4_airgap_subject",
    }
    source = path.read_text(encoding="utf-8")
    exec(compile(source, str(path), "exec"), namespace)
    return namespace


def _starts() -> list[dict[str, Any]]:
    return [
        {
            "attempt_id": attempt_id,
            "attempt_digest": attempt_digest,
            "runtime_binding": "runtime:0",
            "descriptor_binding": "descriptor:0",
        }
        for attempt_id in ("a0", "a1")
        for attempt_digest in ("d0", "d1")
    ]


def _terminals() -> list[dict[str, Any]]:
    return [
        {
            "attempt_id": attempt_id,
            "attempt_digest": attempt_digest,
            "terminal_kind": terminal_kind,
            "terminal_digest": terminal_digest,
            "terminal_binding": "terminal-binding:0",
            "evidence_bindings": ["e0"],
        }
        for attempt_id in ("a0", "a1")
        for attempt_digest in ("d0", "d1")
        for terminal_kind in ("RESULT", "NO_RESULT")
        for terminal_digest in ("t0", "t1")
    ]


def _states() -> list[dict[str, list[dict[str, Any]]]]:
    starts = _starts()
    terminals = _terminals()
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
    return states


def _result(accepted: bool, code: str, changed: bool) -> dict[str, Any]:
    return {
        "accepted": accepted,
        "code": code,
        "state_changed": changed,
        "seed_projection": {"action": "STUTTER", "effect_permitted": False},
    }


def _terminal_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    scalar_fields = {
        "attempt_id",
        "attempt_digest",
        "terminal_kind",
        "terminal_digest",
        "terminal_binding",
    }
    return all(left[field] == right[field] for field in scalar_fields) and set(
        left["evidence_bindings"]
    ) == set(right["evidence_bindings"])


def _expected_start(
    state: dict[str, list[dict[str, Any]]], start: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    next_state = deepcopy(state)
    same_id = [item for item in next_state["starts"] if item["attempt_id"] == start["attempt_id"]]
    if start in same_id:
        return next_state, _result(True, "IDEMPOTENT_REPLAY", False)
    if same_id:
        return next_state, _result(False, "ATTEMPT_IDENTITY_CONFLICT", False)
    next_state["starts"].append(deepcopy(start))
    return next_state, _result(True, "ATTEMPT_STARTED", True)


def _expected_end(
    state: dict[str, list[dict[str, Any]]], terminal: dict[str, Any]
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    next_state = deepcopy(state)
    same_id = [
        item for item in next_state["terminals"] if item["attempt_id"] == terminal["attempt_id"]
    ]
    if any(_terminal_equal(item, terminal) for item in same_id):
        return next_state, _result(True, "IDEMPOTENT_REPLAY", False)
    if same_id:
        return next_state, _result(False, "TERMINAL_ATTEMPT_IMMUTABLE", False)
    matching = any(
        item["attempt_id"] == terminal["attempt_id"]
        and item["attempt_digest"] == terminal["attempt_digest"]
        for item in next_state["starts"]
    )
    if not matching:
        return next_state, _result(False, "ATTEMPT_NOT_RUNNING", False)
    next_state["terminals"].append(deepcopy(terminal))
    code = (
        "ATTEMPT_ENDED_WITH_RESULT"
        if terminal["terminal_kind"] == "RESULT"
        else "ATTEMPT_ENDED_WITH_NO_RESULT"
    )
    return next_state, _result(True, code, True)


def check_expression_airgap(profiles_root: Path) -> dict[str, Any]:
    profiles_root = profiles_root.resolve()
    binding = parse_seed_binding()
    expression = profiles_root / "python/aset_runtime_alpha4.py"
    seed_base = profiles_root / "base/seed/python/aset_seed_alpha4.py"
    require(expression.is_file(), "Runtime Python companion missing")
    require(seed_base.is_file(), "exact Seed Python base missing")
    require(
        sha256(seed_base) == binding.companions["PYTHON"][1],
        "Seed Python base byte identity mismatch",
    )
    tree_before = tree_digest(profiles_root)
    namespace = _load_expression(expression)
    require(callable(namespace.get("start_attempt")), "generated Runtime start entry point missing")
    require(callable(namespace.get("end_attempt")), "generated Runtime end entry point missing")
    require(
        len(namespace.get("COMPONENT_BINDINGS", [])) == 8,
        "generated Runtime component binding surface drift",
    )
    seed_states = [
        {"subject": "s0", "authority": "a0", "recognition": recognition, "evidence": ("e0",)}
        for recognition in ("UNKNOWN", "ALLOW", "BLOCK")
    ]
    starts = _starts()
    terminals = _terminals()
    states = _states()
    start_checks = 0
    end_checks = 0
    for seed_state in seed_states:
        for state in states:
            for start in starts:
                expected_state, expected_result = _expected_start(state, start)
                actual_state, actual_seed, actual_result = namespace["start_attempt"](
                    deepcopy(state), deepcopy(start), deepcopy(seed_state)
                )
                require(actual_state == expected_state, "generated Runtime start state mismatch")
                require(actual_result == expected_result, "generated Runtime start result mismatch")
                require(actual_seed == seed_state, "Runtime start changed exact Seed state")
                start_checks += 1
            for terminal in terminals:
                expected_state, expected_result = _expected_end(state, terminal)
                actual_state, actual_seed, actual_result = namespace["end_attempt"](
                    deepcopy(state), deepcopy(terminal), deepcopy(seed_state)
                )
                require(actual_state == expected_state, "generated Runtime end state mismatch")
                require(actual_result == expected_result, "generated Runtime end result mismatch")
                require(actual_seed == seed_state, "Runtime end changed exact Seed state")
                end_checks += 1
    set_order_checks = 0
    set_start = {
        "attempt_id": "set-a",
        "attempt_digest": "set-d",
        "runtime_binding": "runtime:set",
        "descriptor_binding": "descriptor:set",
    }
    set_terminal = {
        "attempt_id": "set-a",
        "attempt_digest": "set-d",
        "terminal_kind": "RESULT",
        "terminal_digest": "set-t",
        "terminal_binding": "terminal-binding:set",
        "evidence_bindings": ["e0", "e1"],
    }
    set_state = {"starts": [deepcopy(set_start)], "terminals": [deepcopy(set_terminal)]}
    reordered = {**set_terminal, "evidence_bindings": ["e1", "e0"]}
    expected_state, expected_result = _expected_end(set_state, reordered)
    actual_state, actual_seed, actual_result = namespace["end_attempt"](
        deepcopy(set_state), deepcopy(reordered), deepcopy(seed_states[0])
    )
    require(actual_state == expected_state, "Runtime evidence-set replay state mismatch")
    require(actual_result == expected_result, "Runtime evidence-set replay result mismatch")
    require(actual_seed == seed_states[0], "Runtime evidence-set replay changed exact Seed state")
    require(
        actual_result["code"] == "IDEMPOTENT_REPLAY", "Runtime evidence-set order changed identity"
    )
    set_order_checks += 1
    require(
        tree_digest(profiles_root) == tree_before,
        "Runtime profile tree changed during air-gap verification",
    )
    return {
        "document_type": "aset-runtime-python-airgap-evidence",
        "schema_version": 1,
        "semantic_precedence": "NONE",
        "semantic_source_runtime_dependency": "NONE",
        "generator_runtime_dependency": "NONE",
        "seed_base": {"sha256": sha256(seed_base), "status": "EXACT"},
        "profile_tree_digest": tree_before,
        "cases": {
            "start": start_checks,
            "end": end_checks,
            "total": start_checks + end_checks,
        },
        "seed_states_checked": ["UNKNOWN", "ALLOW", "BLOCK"],
        "evidence_set_order_checks": set_order_checks,
        "seed_projection": "STUTTER",
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles-root", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/runtime-python-airgap-evidence.json",
    )
    args = parser.parse_args()
    try:
        evidence = check_expression_airgap(args.profiles_root)
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        cases = evidence["cases"]
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_START={cases['start']}/{cases['start']} PASS")
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_END={cases['end']}/{cases['end']} PASS")
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_TOTAL={cases['total']}/{cases['total']} PASS")
        print(
            "ALPHA4_RUNTIME_PYTHON_EVIDENCE_SET_ORDER="
            f"{evidence['evidence_set_order_checks']}/{evidence['evidence_set_order_checks']} PASS"
        )
        print("ALPHA4_RUNTIME_PYTHON_SEED_BASE=EXACT")
        print("ALPHA4_RUNTIME_PYTHON_SEED_PROJECTION=STUTTER")
        print("ALPHA4_RUNTIME_PYTHON_SEMANTIC_SOURCE_DEPENDENCY=NONE")
        print("ALPHA4_RUNTIME_PYTHON_GENERATOR_DEPENDENCY=NONE")
        print("ALPHA4_RUNTIME_PYTHON_PROFILE_TREE_UNCHANGED=PASS")
        print("ALPHA4_RUNTIME_PYTHON_AIRGAP=PASS")
        return 0
    except (OSError, ValueError, AirgapError) as error:
        print(f"ALPHA4_RUNTIME_PYTHON_AIRGAP_ERROR={error}")
        print("ALPHA4_RUNTIME_PYTHON_AIRGAP=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
