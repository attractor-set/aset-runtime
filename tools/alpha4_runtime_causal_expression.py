from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tools.alpha4_runtime_manifest import parse_runtime_manifest

ROOT = Path(__file__).resolve().parents[1]
CAUSAL = ROOT / "runtime/alpha4/causal/components.petri"


class CausalExpressionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CausalExpressionError(message)


@dataclass(frozen=True)
class CausalTransition:
    symbol: str
    component_id: str
    requirements: tuple[str, ...]
    effects: tuple[str, ...]
    outputs: tuple[tuple[str, str], ...]

    def output_map(self) -> dict[str, str]:
        return dict(self.outputs)


@dataclass(frozen=True)
class CausalNet:
    schema_version: int
    subject_id: str
    semantic_precedence: str
    mode: str
    transitions: tuple[CausalTransition, ...]


EXPECTED_CAUSAL_CONTRACTS: dict[str, tuple[str, frozenset[str], frozenset[str], dict[str, str]]] = {
    "START-FRESH": (
        "ASET-RUNTIME-COMPONENT-START-FRESH",
        frozenset({"EXACT_START", "FRESH_ID"}),
        frozenset({"ADD_START"}),
        {
            "ACCEPTED": "TRUE",
            "CODE": "ATTEMPT_STARTED",
            "STATE_CHANGED": "TRUE",
            "SEED_ACTION": "STUTTER",
            "SEED_EFFECT": "FALSE",
        },
    ),
    "START-REPLAY": (
        "ASET-RUNTIME-COMPONENT-START-REPLAY",
        frozenset({"EXACT_START", "EXACT_START_REPLAY"}),
        frozenset({"PRESERVE_STATE"}),
        {
            "ACCEPTED": "TRUE",
            "CODE": "IDEMPOTENT_REPLAY",
            "STATE_CHANGED": "FALSE",
            "SEED_ACTION": "STUTTER",
            "SEED_EFFECT": "FALSE",
        },
    ),
    "REJECT-START-CONFLICT": (
        "ASET-RUNTIME-COMPONENT-REJECT-START-CONFLICT",
        frozenset({"EXACT_START", "START_CONFLICT"}),
        frozenset({"PRESERVE_STATE"}),
        {
            "ACCEPTED": "FALSE",
            "CODE": "ATTEMPT_IDENTITY_CONFLICT",
            "STATE_CHANGED": "FALSE",
            "SEED_ACTION": "STUTTER",
            "SEED_EFFECT": "FALSE",
        },
    ),
    "END-RESULT": (
        "ASET-RUNTIME-COMPONENT-END-RESULT",
        frozenset({"EXACT_TERMINAL", "EXACT_RUNNING", "FRESH_TERMINAL", "KIND_RESULT"}),
        frozenset({"ADD_TERMINAL"}),
        {
            "ACCEPTED": "TRUE",
            "CODE": "ATTEMPT_ENDED_WITH_RESULT",
            "STATE_CHANGED": "TRUE",
            "SEED_ACTION": "STUTTER",
            "SEED_EFFECT": "FALSE",
        },
    ),
    "END-NO-RESULT": (
        "ASET-RUNTIME-COMPONENT-END-NO-RESULT",
        frozenset({"EXACT_TERMINAL", "EXACT_RUNNING", "FRESH_TERMINAL", "KIND_NO_RESULT"}),
        frozenset({"ADD_TERMINAL"}),
        {
            "ACCEPTED": "TRUE",
            "CODE": "ATTEMPT_ENDED_WITH_NO_RESULT",
            "STATE_CHANGED": "TRUE",
            "SEED_ACTION": "STUTTER",
            "SEED_EFFECT": "FALSE",
        },
    ),
    "END-REPLAY": (
        "ASET-RUNTIME-COMPONENT-END-REPLAY",
        frozenset({"EXACT_TERMINAL", "EXACT_TERMINAL_REPLAY"}),
        frozenset({"PRESERVE_STATE"}),
        {
            "ACCEPTED": "TRUE",
            "CODE": "IDEMPOTENT_REPLAY",
            "STATE_CHANGED": "FALSE",
            "SEED_ACTION": "STUTTER",
            "SEED_EFFECT": "FALSE",
        },
    ),
    "REJECT-END-CONFLICT": (
        "ASET-RUNTIME-COMPONENT-REJECT-END-CONFLICT",
        frozenset({"EXACT_TERMINAL", "TERMINAL_CONFLICT"}),
        frozenset({"PRESERVE_STATE"}),
        {
            "ACCEPTED": "FALSE",
            "CODE": "TERMINAL_ATTEMPT_IMMUTABLE",
            "STATE_CHANGED": "FALSE",
            "SEED_ACTION": "STUTTER",
            "SEED_EFFECT": "FALSE",
        },
    ),
    "REJECT-END-NOT-RUNNING": (
        "ASET-RUNTIME-COMPONENT-REJECT-END-NOT-RUNNING",
        frozenset({"EXACT_TERMINAL", "NO_TERMINAL_FOR_ID", "NOT_EXACT_RUNNING"}),
        frozenset({"PRESERVE_STATE"}),
        {
            "ACCEPTED": "FALSE",
            "CODE": "ATTEMPT_NOT_RUNNING",
            "STATE_CHANGED": "FALSE",
            "SEED_ACTION": "STUTTER",
            "SEED_EFFECT": "FALSE",
        },
    ),
}


CAUSAL_START_FIELDS = {"attempt_id", "attempt_digest", "runtime_binding", "descriptor_binding"}
CAUSAL_TERMINAL_FIELDS = {
    "attempt_id",
    "attempt_digest",
    "terminal_kind",
    "terminal_digest",
    "terminal_binding",
    "evidence_bindings",
}
CAUSAL_TERMINAL_KINDS = {"RESULT", "NO_RESULT"}


def causal_exact_start(value: dict[str, Any]) -> bool:
    return set(value) == CAUSAL_START_FIELDS and all(
        isinstance(value[field], str) and value[field] for field in CAUSAL_START_FIELDS
    )


def causal_exact_terminal(value: dict[str, Any]) -> bool:
    if (
        set(value) != CAUSAL_TERMINAL_FIELDS
        or value.get("terminal_kind") not in CAUSAL_TERMINAL_KINDS
    ):
        return False
    for field in CAUSAL_TERMINAL_FIELDS - {"terminal_kind", "evidence_bindings"}:
        if not isinstance(value[field], str) or not value[field]:
            return False
    evidence = value.get("evidence_bindings")
    return (
        isinstance(evidence, list)
        and all(isinstance(item, str) and item for item in evidence)
        and len(evidence) == len(set(evidence))
    )


def causal_terminal_equal(left: dict[str, Any], right: dict[str, Any]) -> bool:
    if not causal_exact_terminal(left) or not causal_exact_terminal(right):
        return False
    scalar_fields = CAUSAL_TERMINAL_FIELDS - {"evidence_bindings"}
    return all(left[field] == right[field] for field in scalar_fields) and set(
        left["evidence_bindings"]
    ) == set(right["evidence_bindings"])


def validate_causal_contract(net: CausalNet) -> int:
    actual = {item.symbol: item for item in net.transitions}
    require(
        set(actual) == set(EXPECTED_CAUSAL_CONTRACTS),
        "Runtime causal transition surface drift",
    )
    for symbol, (component_id, requirements, effects, outputs) in EXPECTED_CAUSAL_CONTRACTS.items():
        transition = actual[symbol]
        require(
            transition.component_id == component_id,
            f"{symbol}: causal component identity drift",
        )
        require(
            frozenset(transition.requirements) == requirements,
            f"{symbol}: causal requirement contract drift",
        )
        require(
            frozenset(transition.effects) == effects,
            f"{symbol}: causal effect contract drift",
        )
        require(
            transition.output_map() == outputs,
            f"{symbol}: causal output contract drift",
        )
    return len(EXPECTED_CAUSAL_CONTRACTS)


def _lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_causal_net(path: Path = CAUSAL) -> CausalNet:
    lines = _lines(path)
    require(lines, "causal source is empty")
    head = lines[0].split()
    require(
        head == ["ASET-CAUSAL-NET", "1", "ASET-RUNTIME-ALPHA4-CAUSAL"],
        "causal header mismatch",
    )
    semantic_precedence = ""
    mode = ""
    transitions: list[CausalTransition] = []
    index = 1
    while index < len(lines):
        tokens = lines[index].split()
        if tokens[0] == "SEMANTIC-PRECEDENCE":
            require(tokens == ["SEMANTIC-PRECEDENCE", "NONE"], "causal precedence drift")
            semantic_precedence = "NONE"
            index += 1
            continue
        if tokens[0] == "MODE":
            require(tokens == ["MODE", "STATE-TRANSITION"], "causal mode drift")
            mode = "STATE-TRANSITION"
            index += 1
            continue
        require(
            tokens[0] == "TRANSITION" and len(tokens) == 3,
            f"invalid causal statement: {lines[index]}",
        )
        symbol, component_id = tokens[1], tokens[2]
        requirements: list[str] = []
        effects: list[str] = []
        outputs: list[tuple[str, str]] = []
        index += 1
        while index < len(lines) and lines[index] != "END":
            body = lines[index].split()
            if body[0] == "REQUIRE":
                require(len(body) == 2, f"{symbol}: invalid REQUIRE")
                requirements.append(body[1])
            elif body[0] == "EFFECT":
                require(len(body) == 2, f"{symbol}: invalid EFFECT")
                effects.append(body[1])
            elif body[0] == "OUTPUT":
                require(len(body) == 3, f"{symbol}: invalid OUTPUT")
                outputs.append((body[1], body[2]))
            else:
                raise CausalExpressionError(f"{symbol}: unsupported statement {body[0]}")
            index += 1
        require(index < len(lines) and lines[index] == "END", f"{symbol}: END missing")
        require(len(set(requirements)) == len(requirements), f"{symbol}: duplicate requirement")
        require(len(set(effects)) == len(effects), f"{symbol}: duplicate effect")
        require(len({key for key, _ in outputs}) == len(outputs), f"{symbol}: duplicate output")
        transitions.append(
            CausalTransition(
                symbol=symbol,
                component_id=component_id,
                requirements=tuple(requirements),
                effects=tuple(effects),
                outputs=tuple(outputs),
            )
        )
        index += 1
    require(semantic_precedence == "NONE", "causal semantic precedence missing")
    require(mode == "STATE-TRANSITION", "causal mode missing")
    require(len(transitions) == 8, "Runtime causal surface must contain exactly eight transitions")
    require(len({item.symbol for item in transitions}) == 8, "duplicate causal transition")
    require(len({item.component_id for item in transitions}) == 8, "duplicate causal component")
    return CausalNet(1, "ASET-RUNTIME-ALPHA4-CAUSAL", semantic_precedence, mode, tuple(transitions))


def manifest_bindings(root: Path = ROOT) -> dict[str, str]:
    plan = parse_runtime_manifest(root)
    return {item.component_id: item.causal_transition for item in plan.causal_bindings}


def check_causal_bindings(root: Path = ROOT) -> CausalNet:
    plan = parse_runtime_manifest(root)
    net = parse_causal_net(root / plan.causal_model)
    actual = {item.component_id: item.symbol for item in net.transitions}
    require(actual == manifest_bindings(root), "causal component binding mismatch")
    validate_causal_contract(net)
    for transition in net.transitions:
        outputs = transition.output_map()
        require(outputs.get("SEED_ACTION") == "STUTTER", f"{transition.symbol}: Seed action drift")
        require(outputs.get("SEED_EFFECT") == "FALSE", f"{transition.symbol}: Seed effect drift")
    return net


def _bool(value: str) -> bool:
    require(value in {"TRUE", "FALSE"}, f"invalid causal boolean: {value}")
    return value == "TRUE"


def _copy_state(state: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    return {"starts": deepcopy(state["starts"]), "terminals": deepcopy(state["terminals"])}


def _result(transition: CausalTransition) -> dict[str, Any]:
    outputs = transition.output_map()
    return {
        "accepted": _bool(outputs["ACCEPTED"]),
        "code": outputs["CODE"],
        "state_changed": _bool(outputs["STATE_CHANGED"]),
        "seed_projection": {
            "action": outputs["SEED_ACTION"],
            "effect_permitted": _bool(outputs["SEED_EFFECT"]),
        },
    }


def causal_start(
    state: dict[str, list[dict[str, Any]]], start: dict[str, Any], net: CausalNet
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    if not causal_exact_start(start):
        raise ValueError("exact start record required")
    current = _copy_state(state)
    same_id = [item for item in current["starts"] if item["attempt_id"] == start["attempt_id"]]
    facts = {"EXACT_START"}
    if not same_id:
        facts.add("FRESH_ID")
    elif start in same_id:
        facts.add("EXACT_START_REPLAY")
    else:
        facts.add("START_CONFLICT")
    candidates = [
        item
        for item in net.transitions
        if item.symbol in {"START-FRESH", "START-REPLAY", "REJECT-START-CONFLICT"}
        and set(item.requirements) <= facts
    ]
    require(len(candidates) == 1, f"start causal classification not singular: {facts!r}")
    transition = candidates[0]
    if "ADD_START" in transition.effects:
        current["starts"].append(deepcopy(start))
    else:
        require("PRESERVE_STATE" in transition.effects, f"{transition.symbol}: unsupported effect")
    return current, _result(transition)


def causal_end(
    state: dict[str, list[dict[str, Any]]], terminal: dict[str, Any], net: CausalNet
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    if not causal_exact_terminal(terminal):
        raise ValueError("exact terminal record required")
    current = _copy_state(state)
    same_terminal_id = [
        item for item in current["terminals"] if item["attempt_id"] == terminal["attempt_id"]
    ]
    matching_start = any(
        item["attempt_id"] == terminal["attempt_id"]
        and item["attempt_digest"] == terminal["attempt_digest"]
        for item in current["starts"]
    )
    facts = {"EXACT_TERMINAL"}
    if any(causal_terminal_equal(item, terminal) for item in same_terminal_id):
        facts.add("EXACT_TERMINAL_REPLAY")
    elif same_terminal_id:
        facts.add("TERMINAL_CONFLICT")
    elif matching_start:
        facts.update({"EXACT_RUNNING", "FRESH_TERMINAL"})
        facts.add("KIND_RESULT" if terminal["terminal_kind"] == "RESULT" else "KIND_NO_RESULT")
    else:
        facts.update({"NO_TERMINAL_FOR_ID", "NOT_EXACT_RUNNING"})
    end_symbols = {
        "END-RESULT",
        "END-NO-RESULT",
        "END-REPLAY",
        "REJECT-END-CONFLICT",
        "REJECT-END-NOT-RUNNING",
    }
    candidates = [
        item
        for item in net.transitions
        if item.symbol in end_symbols and set(item.requirements) <= facts
    ]
    require(len(candidates) == 1, f"end causal classification not singular: {facts!r}")
    transition = candidates[0]
    if "ADD_TERMINAL" in transition.effects:
        current["terminals"].append(deepcopy(terminal))
    else:
        require("PRESERVE_STATE" in transition.effects, f"{transition.symbol}: unsupported effect")
    return current, _result(transition)


def main() -> int:
    check_causal_bindings()
    print("ALPHA4_RUNTIME_CAUSAL_COMPONENTS=8/8 PASS")
    print("ALPHA4_RUNTIME_CAUSAL_SEMANTIC_PRECEDENCE=NONE")
    print("ALPHA4_RUNTIME_CAUSAL_SEED_ACTION=STUTTER")
    print("ALPHA4_RUNTIME_CAUSAL_EXPRESSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
