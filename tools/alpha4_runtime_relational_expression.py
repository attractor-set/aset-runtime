from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.alpha4_runtime_manifest import parse_runtime_manifest

ROOT = Path(__file__).resolve().parents[1]


class RelationalExpressionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RelationalExpressionError(message)


def strip_tla_comments(text: str) -> str:
    without_blocks = re.sub(r"\(\*.*?\*\)", "", text, flags=re.DOTALL)
    return re.sub(r"(?m)\\\*.*$", "", without_blocks)


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def extract_operator(text: str, operator: str) -> tuple[tuple[str, ...], str]:
    pattern = re.compile(
        rf"(?ms)^{re.escape(operator)}\((?P<args>[^)]*)\)\s*==\s*(?P<body>.*?)"
        rf"(?=^[A-Z][A-Za-z0-9_]*\([^)]*\)\s*==|^[A-Z][A-Za-z0-9_]*\s*==|^=+)"
    )
    match = pattern.search(text)
    if match is None:
        raise RelationalExpressionError(f"formal operator missing: {operator}")
    args = tuple(item.strip() for item in match.group("args").split(",") if item.strip())
    return args, compact(match.group("body"))


def extract_value(text: str, operator: str) -> str:
    pattern = re.compile(
        rf"(?ms)^{re.escape(operator)}\s*==\s*(?P<body>.*?)"
        rf"(?=^[A-Z][A-Za-z0-9_]*\([^)]*\)\s*==|^[A-Z][A-Za-z0-9_]*\s*==|^=+)"
    )
    match = pattern.search(text)
    if match is None:
        raise RelationalExpressionError(f"formal value missing: {operator}")
    return compact(match.group("body"))


def _record_fields(body: str) -> tuple[str, ...]:
    fields = tuple(re.findall(r"([a-z_]+):(?:SUBSET)?[A-Za-z][A-Za-z0-9_]*", body))
    require(fields, f"record fields missing: {body}")
    return fields


def _quoted_set(body: str) -> frozenset[str]:
    return frozenset(re.findall(r'"([A-Z0-9_]+)"', body))


@dataclass(frozen=True)
class RuntimeRule:
    component_id: str
    operator: str
    classifier: str
    effect: str
    result_code: str
    terminal_kind: str | None = None


@dataclass(frozen=True)
class RuntimeContract:
    start_fields: tuple[str, ...]
    terminal_fields: tuple[str, ...]
    terminal_kinds: frozenset[str]
    start_identifier_field: str
    terminal_identifier_field: str
    start_replay_mode: str
    terminal_replay_mode: str
    matching_fields: tuple[str, ...]
    accepted_results: frozenset[str]
    seed_action: str
    rules: tuple[RuntimeRule, ...]


def derive_runtime_contract(root: Path = ROOT) -> RuntimeContract:
    plan = parse_runtime_manifest(root)
    text = strip_tla_comments((root / plan.relational).read_text(encoding="utf-8"))
    start_fields = _record_fields(extract_value(text, "StartUniverse"))
    terminal_fields = _record_fields(extract_value(text, "TerminalUniverse"))
    terminal_kinds = _quoted_set(extract_value(text, "TerminalKinds"))

    _, same_start = extract_operator(text, "SameStartIdentifier")
    start_id_match = re.fullmatch(r"a\.([a-z_]+)=b\.([a-z_]+)", same_start)
    require(
        start_id_match is not None and start_id_match.group(1) == start_id_match.group(2),
        "SameStartIdentifier semantics drift",
    )
    start_identifier_field = start_id_match.group(1)

    _, same_terminal = extract_operator(text, "SameTerminalIdentifier")
    terminal_id_match = re.fullmatch(r"a\.([a-z_]+)=b\.([a-z_]+)", same_terminal)
    require(
        terminal_id_match is not None and terminal_id_match.group(1) == terminal_id_match.group(2),
        "SameTerminalIdentifier semantics drift",
    )
    terminal_identifier_field = terminal_id_match.group(1)

    _, start_replay = extract_operator(text, "ExactStartReplay")
    if start_replay == "start\\ins.starts":
        start_replay_mode = "EXACT_RECORD"
    elif start_replay == "StartIdentifierExists(s,start)":
        start_replay_mode = "IDENTIFIER_ONLY"
    else:
        raise RelationalExpressionError("ExactStartReplay semantics unsupported")
    _, terminal_replay = extract_operator(text, "ExactTerminalReplay")
    if terminal_replay == "terminal\\ins.terminals":
        terminal_replay_mode = "EXACT_RECORD"
    elif terminal_replay == "TerminalIdentifierExists(s,terminal)":
        terminal_replay_mode = "IDENTIFIER_ONLY"
    else:
        raise RelationalExpressionError("ExactTerminalReplay semantics unsupported")

    _, start_conflict = extract_operator(text, "StartConflict")
    require(
        "StartIdentifierExists(s,start)" in start_conflict
        and "~ExactStartReplay(s,start)" in start_conflict,
        "StartConflict semantics drift",
    )
    _, terminal_conflict = extract_operator(text, "TerminalConflict")
    require(
        "TerminalIdentifierExists(s,terminal)" in terminal_conflict
        and "~ExactTerminalReplay(s,terminal)" in terminal_conflict,
        "TerminalConflict semantics drift",
    )

    _, matching = extract_operator(text, "MatchingStart")
    matching_pairs = re.findall(r"start\.([a-z_]+)=terminal\.([a-z_]+)", matching)
    require(
        matching_pairs and all(left == right for left, right in matching_pairs),
        "MatchingStart field relation drift",
    )
    matching_fields = tuple(left for left, _ in matching_pairs)

    accepted_body = extract_operator(text, "AcceptedResult")[1]
    marker = "result\\in"
    require(marker in accepted_body, "AcceptedResult membership relation missing")
    accepted_results = _quoted_set(accepted_body.split(marker, 1)[1])
    _, seed_action_body = extract_operator(text, "SeedProjectionAction")
    seed_action_match = re.fullmatch(r'"([A-Z0-9_]+)"', seed_action_body)
    require(seed_action_match is not None, "SeedProjectionAction literal missing")
    _, seed_effect = extract_operator(text, "SeedProjectionEffectPermitted")
    require(seed_effect == "FALSE", "SeedProjectionEffectPermitted must remain FALSE")

    rules: list[RuntimeRule] = []
    for pair in plan.pairs:
        _, body = extract_operator(text, pair.formal_operator)
        require(
            "RuntimeInvariant(s)" in body,
            f"{pair.formal_operator}: RuntimeInvariant precondition missing",
        )
        universe = (
            "start\\inStartUniverse"
            if pair.transition == "START-ATTEMPT"
            else "terminal\\inTerminalUniverse"
        )
        require(universe in body, f"{pair.formal_operator}: record universe precondition missing")
        classifier: str
        terminal_kind: str | None = None
        if pair.formal_operator == "StartFresh":
            require("FreshStartIdentifier(s,start)" in body, "StartFresh guard drift")
            classifier, effect = "START_FRESH", "ADD_START"
        elif pair.formal_operator == "StartReplay":
            require("ExactStartReplay(s,start)" in body, "StartReplay guard drift")
            classifier, effect = "START_REPLAY", "PRESERVE"
        elif pair.formal_operator == "RejectStartConflict":
            require("StartConflict(s,start)" in body, "RejectStartConflict guard drift")
            classifier, effect = "START_CONFLICT", "PRESERVE"
        elif pair.formal_operator in {"EndResult", "EndNoResult"}:
            require(
                "ExactRunning(s,terminal)" in body,
                f"{pair.formal_operator}: ExactRunning guard drift",
            )
            kind_match = re.search(r'terminal\.terminal_kind="(RESULT|NO_RESULT)"', body)
            require(kind_match is not None, f"{pair.formal_operator}: terminal kind guard missing")
            terminal_kind = kind_match.group(1)
            classifier, effect = "END_RUNNING", "ADD_TERMINAL"
        elif pair.formal_operator == "EndReplay":
            require("ExactTerminalReplay(s,terminal)" in body, "EndReplay guard drift")
            classifier, effect = "END_REPLAY", "PRESERVE"
        elif pair.formal_operator == "RejectEndConflict":
            require("TerminalConflict(s,terminal)" in body, "RejectEndConflict guard drift")
            classifier, effect = "END_CONFLICT", "PRESERVE"
        elif pair.formal_operator == "RejectEndNotRunning":
            require(
                "FreshTerminalIdentifier(s,terminal)" in body
                and "~MatchingStart(s,terminal)" in body,
                "RejectEndNotRunning guard drift",
            )
            classifier, effect = "END_NOT_RUNNING", "PRESERVE"
        else:
            raise RelationalExpressionError(f"unsupported Runtime operator: {pair.formal_operator}")
        if effect == "ADD_START":
            require(
                "!.starts=@\\cup{start}" in body, f"{pair.formal_operator}: add-start effect drift"
            )
        elif effect == "ADD_TERMINAL":
            require(
                "!.terminals=@\\cup{terminal}" in body,
                f"{pair.formal_operator}: add-terminal effect drift",
            )
        else:
            require("t=s" in body, f"{pair.formal_operator}: preserve-state effect drift")
        result_match = re.search(r'result="([A-Z0-9_]+)"', body)
        require(result_match is not None, f"{pair.formal_operator}: result code missing")
        rules.append(
            RuntimeRule(
                pair.component_id,
                pair.formal_operator,
                classifier,
                effect,
                result_match.group(1),
                terminal_kind,
            )
        )

    return RuntimeContract(
        start_fields=start_fields,
        terminal_fields=terminal_fields,
        terminal_kinds=terminal_kinds,
        start_identifier_field=start_identifier_field,
        terminal_identifier_field=terminal_identifier_field,
        start_replay_mode=start_replay_mode,
        terminal_replay_mode=terminal_replay_mode,
        matching_fields=matching_fields,
        accepted_results=accepted_results,
        seed_action=seed_action_match.group(1),
        rules=tuple(rules),
    )


def _copy_state(state: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {"starts": deepcopy(state["starts"]), "terminals": deepcopy(state["terminals"])}


def _result(contract: RuntimeContract, rule: RuntimeRule) -> dict[str, Any]:
    return {
        "accepted": rule.result_code in contract.accepted_results,
        "code": rule.result_code,
        "state_changed": rule.effect in {"ADD_START", "ADD_TERMINAL"},
        "seed_projection": {"action": contract.seed_action, "effect_permitted": False},
    }


def _exact_start(contract: RuntimeContract, value: dict[str, Any]) -> bool:
    fields = set(contract.start_fields)
    return set(value) == fields and all(
        isinstance(value[field], str) and value[field] for field in fields
    )


def _exact_terminal(contract: RuntimeContract, value: dict[str, Any]) -> bool:
    fields = set(contract.terminal_fields)
    if set(value) != fields or value.get("terminal_kind") not in contract.terminal_kinds:
        return False
    for field in fields - {"terminal_kind", "evidence_bindings"}:
        if not isinstance(value[field], str) or not value[field]:
            return False
    evidence = value.get("evidence_bindings")
    return (
        isinstance(evidence, list)
        and all(isinstance(item, str) and item for item in evidence)
        and len(evidence) == len(set(evidence))
    )


def relational_exact_start_from_source(value: dict[str, Any], root: Path = ROOT) -> bool:
    return _exact_start(derive_runtime_contract(root), value)


def relational_exact_terminal_from_source(value: dict[str, Any], root: Path = ROOT) -> bool:
    return _exact_terminal(derive_runtime_contract(root), value)


def _terminal_equal(contract: RuntimeContract, left: dict[str, Any], right: dict[str, Any]) -> bool:
    if not _exact_terminal(contract, left) or not _exact_terminal(contract, right):
        return False
    scalar_fields = set(contract.terminal_fields) - {"evidence_bindings"}
    return all(left[field] == right[field] for field in scalar_fields) and set(
        left["evidence_bindings"]
    ) == set(right["evidence_bindings"])


def _identifier_exists(records: list[dict[str, Any]], value: dict[str, Any], field: str) -> bool:
    return any(item[field] == value[field] for item in records)


def _matching_start(
    contract: RuntimeContract, state: dict[str, Any], terminal: dict[str, Any]
) -> bool:
    return any(
        all(start[field] == terminal[field] for field in contract.matching_fields)
        for start in state["starts"]
    )


def relational_start_from_source(
    state: dict[str, list[dict[str, Any]]], start: dict[str, Any], root: Path = ROOT
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    contract = derive_runtime_contract(root)
    if not _exact_start(contract, start):
        raise ValueError("exact start record required")
    current = _copy_state(state)
    identifier_exists = _identifier_exists(
        current["starts"], start, contract.start_identifier_field
    )
    exact_replay = (
        start in current["starts"]
        if contract.start_replay_mode == "EXACT_RECORD"
        else identifier_exists
    )
    classifier = (
        "START_REPLAY" if exact_replay else "START_CONFLICT" if identifier_exists else "START_FRESH"
    )
    rules = [rule for rule in contract.rules if rule.classifier == classifier]
    require(len(rules) == 1, f"Runtime start classification not singular: {classifier}")
    rule = rules[0]
    if rule.effect == "ADD_START":
        current["starts"].append(deepcopy(start))
    return current, _result(contract, rule)


def relational_end_from_source(
    state: dict[str, list[dict[str, Any]]], terminal: dict[str, Any], root: Path = ROOT
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    contract = derive_runtime_contract(root)
    if not _exact_terminal(contract, terminal):
        raise ValueError("exact terminal record required")
    current = _copy_state(state)
    identifier_exists = _identifier_exists(
        current["terminals"], terminal, contract.terminal_identifier_field
    )
    exact_replay = (
        any(_terminal_equal(contract, item, terminal) for item in current["terminals"])
        if contract.terminal_replay_mode == "EXACT_RECORD"
        else identifier_exists
    )
    matching = _matching_start(contract, current, terminal)
    if exact_replay:
        classifier = "END_REPLAY"
    elif identifier_exists:
        classifier = "END_CONFLICT"
    elif matching:
        classifier = "END_RUNNING"
    else:
        classifier = "END_NOT_RUNNING"
    rules = [rule for rule in contract.rules if rule.classifier == classifier]
    if classifier == "END_RUNNING":
        rules = [rule for rule in rules if rule.terminal_kind == terminal["terminal_kind"]]
    require(len(rules) == 1, f"Runtime end classification not singular: {classifier}")
    rule = rules[0]
    if rule.effect == "ADD_TERMINAL":
        current["terminals"].append(deepcopy(terminal))
    return current, _result(contract, rule)


def validate_runtime_relational_source(root: Path = ROOT) -> int:
    contract = derive_runtime_contract(root)
    return len(contract.rules)


def main() -> int:
    try:
        count = validate_runtime_relational_source(ROOT)
        print(f"ALPHA4_RUNTIME_RELATIONAL_SOURCE_DERIVATIONS={count}/{count} PASS")
        print("ALPHA4_RUNTIME_RELATIONAL_EXPRESSION=PASS")
        return 0
    except (RelationalExpressionError, OSError, UnicodeError, ValueError, KeyError) as error:
        print(f"ALPHA4_RUNTIME_RELATIONAL_EXPRESSION_ERROR={error}")
        print("ALPHA4_RUNTIME_RELATIONAL_EXPRESSION=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
