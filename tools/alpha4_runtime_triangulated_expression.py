from __future__ import annotations

from pathlib import Path

from tools.alpha4_runtime_causal_expression import (
    EXPECTED_CAUSAL_CONTRACTS,
    CausalNet,
    causal_end,
    causal_exact_start,
    causal_exact_terminal,
    causal_start,
    check_causal_bindings,
)
from tools.alpha4_runtime_manifest import parse_runtime_manifest
from tools.alpha4_runtime_paired_expression import (
    EXPECTED_STACK_EFFECTS,
    bounded_domain,
    exact_start,
    exact_terminal,
    field_sensitivity_check,
    operational_end,
    operational_start,
    parse_operational_words,
    relational_end,
    relational_start,
)
from tools.alpha4_runtime_relational_expression import validate_runtime_relational_source

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "runtime/alpha4/RUNTIME.aset"


def check_representation_source_independence() -> dict[str, str]:
    plan = parse_runtime_manifest(ROOT)
    sources = {
        "OPERATIONAL": plan.operational,
        "RELATIONAL": plan.relational,
        "CAUSAL-MODEL": plan.causal_model,
    }
    if len(set(sources.values())) != 3:
        raise RuntimeError(f"Runtime assurance representations share a source path: {sources!r}")
    if plan.relation_map().get("RELATIONAL_SOURCE") != "BOUND_TLA_OPERATOR_DERIVATION":
        raise RuntimeError("Runtime relational source derivation binding missing")
    for source in sources.values():
        if not (ROOT / source).is_file():
            raise RuntimeError(f"bound Runtime assurance source missing: {source}")
    return sources


def check_interface_validator_independence() -> int:
    valid_start = {
        "attempt_id": "a",
        "attempt_digest": "d",
        "runtime_binding": "r",
        "descriptor_binding": "q",
    }
    valid_terminal = {
        "attempt_id": "a",
        "attempt_digest": "d",
        "terminal_kind": "RESULT",
        "terminal_digest": "t",
        "terminal_binding": "b",
        "evidence_bindings": ["e0", "e1"],
    }
    cases = [
        (exact_start(valid_start), causal_exact_start(valid_start), True),
        (
            exact_start({**valid_start, "extra": "x"}),
            causal_exact_start({**valid_start, "extra": "x"}),
            False,
        ),
        (exact_terminal(valid_terminal), causal_exact_terminal(valid_terminal), True),
        (
            exact_terminal({**valid_terminal, "evidence_bindings": ["e0", "e0"]}),
            causal_exact_terminal({**valid_terminal, "evidence_bindings": ["e0", "e0"]}),
            False,
        ),
    ]
    for operational, causal, expected in cases:
        if operational != expected or causal != expected:
            raise RuntimeError("Runtime independent interface validators disagree with contract")
    return len(cases)


def check_operational_causal_interface(net: CausalNet) -> tuple[int, int, int]:
    words = parse_operational_words()
    transitions = {item.symbol: item for item in net.transitions}
    if set(words) != set(transitions):
        raise RuntimeError("Runtime operational/causal transition surface mismatch")
    result_bindings = 0
    for symbol, body in words.items():
        operational_code = body[-1].replace("-", "_")
        causal_code = transitions[symbol].output_map()["CODE"]
        if operational_code != causal_code:
            raise RuntimeError(f"{symbol}: operational/causal result-code mismatch")
        result_bindings += 1
    return len(EXPECTED_STACK_EFFECTS), len(EXPECTED_CAUSAL_CONTRACTS), result_bindings


def check_triangulated_assurance() -> dict[str, object]:
    sources = check_representation_source_independence()
    relational_derivations = validate_runtime_relational_source(ROOT)
    validator_cases = check_interface_validator_independence()
    net = check_causal_bindings()
    stack_contracts, causal_contracts, result_bindings = check_operational_causal_interface(net)
    sensitivity = field_sensitivity_check()
    starts, terminals, states = bounded_domain()
    start_checks = 0
    end_checks = 0
    for state in states:
        for start in starts:
            operational = operational_start(state, start)
            relational = relational_start(state, start)
            causal = causal_start(state, start, net)
            if operational != relational:
                raise RuntimeError(
                    f"operational/relational start mismatch: state={state!r} start={start!r}"
                )
            if operational != causal:
                raise RuntimeError(
                    f"operational/causal start mismatch: state={state!r} start={start!r}"
                )
            if relational != causal:
                raise RuntimeError(
                    f"relational/causal start mismatch: state={state!r} start={start!r}"
                )
            start_checks += 1
        for terminal in terminals:
            operational = operational_end(state, terminal)
            relational = relational_end(state, terminal)
            causal = causal_end(state, terminal, net)
            if operational != relational:
                raise RuntimeError(
                    f"operational/relational end mismatch: state={state!r} terminal={terminal!r}"
                )
            if operational != causal:
                raise RuntimeError(
                    f"operational/causal end mismatch: state={state!r} terminal={terminal!r}"
                )
            if relational != causal:
                raise RuntimeError(
                    f"relational/causal end mismatch: state={state!r} terminal={terminal!r}"
                )
            end_checks += 1
    total_checks = start_checks + end_checks
    return {
        "document_type": "aset-runtime-three-way-assurance-evidence",
        "schema_version": 1,
        "representations": ("OPERATIONAL", "RELATIONAL", "CAUSAL"),
        "representation_sources": sources,
        "representation_source_independence": "PASS",
        "pairwise_relations": {
            "operational_relational": "PASS",
            "operational_causal": "PASS",
            "relational_causal": "PASS",
        },
        "operational_stack_contracts": stack_contracts,
        "causal_closed_world_contracts": causal_contracts,
        "operational_causal_result_code_bindings": result_bindings,
        "relational_source_derivations": relational_derivations,
        "interface_validator_cases": validator_cases,
        "identity_field_sensitivity": sensitivity["total"],
        "evidence_set_order_invariance": sensitivity["evidence_set"],
        "start_checks": start_checks,
        "end_checks": end_checks,
        "total_checks": total_checks,
        "semantic_delta": "NONE",
        "semantic_precedence": "NONE",
        "seed_action": "STUTTER",
        "status": "PASS",
    }


def print_evidence(evidence: dict[str, object]) -> None:
    start = int(evidence["start_checks"])
    end = int(evidence["end_checks"])
    total = int(evidence["total_checks"])
    stacks = int(evidence["operational_stack_contracts"])
    causal_contracts = int(evidence["causal_closed_world_contracts"])
    result_bindings = int(evidence["operational_causal_result_code_bindings"])
    relational_derivations = int(evidence["relational_source_derivations"])
    validator_cases = int(evidence["interface_validator_cases"])
    sensitivity = int(evidence["identity_field_sensitivity"])
    evidence_set = int(evidence["evidence_set_order_invariance"])
    print("ALPHA4_RUNTIME_ASSURANCE_REPRESENTATIONS=OPERATIONAL,RELATIONAL,CAUSAL")
    print("ALPHA4_RUNTIME_ASSURANCE_SEMANTIC_PRECEDENCE=NONE")
    print(f"ALPHA4_RUNTIME_OPERATIONAL_RELATIONAL_CONGRUENCE={total}/{total} PASS")
    print(f"ALPHA4_RUNTIME_OPERATIONAL_CAUSAL_CONGRUENCE={total}/{total} PASS")
    print(f"ALPHA4_RUNTIME_RELATIONAL_CAUSAL_CONGRUENCE={total}/{total} PASS")
    print(f"ALPHA4_RUNTIME_TRIANGULATED_START={start}/{start} PASS")
    print(f"ALPHA4_RUNTIME_TRIANGULATED_END={end}/{end} PASS")
    print(f"ALPHA4_RUNTIME_TRIANGULATED_TOTAL={total}/{total} PASS")
    print(f"ALPHA4_RUNTIME_OPERATIONAL_STACK_CONTRACTS={stacks}/{stacks} PASS")
    print(
        f"ALPHA4_RUNTIME_CAUSAL_CLOSED_WORLD_CONTRACTS={causal_contracts}/{causal_contracts} PASS"
    )
    print(
        f"ALPHA4_RUNTIME_OPERATIONAL_CAUSAL_RESULT_CODES={result_bindings}/{result_bindings} PASS"
    )
    print(
        "ALPHA4_RUNTIME_RELATIONAL_SOURCE_DERIVATIONS="
        f"{relational_derivations}/{relational_derivations} PASS"
    )
    print(
        f"ALPHA4_RUNTIME_INTERFACE_VALIDATOR_INDEPENDENCE={validator_cases}/{validator_cases} PASS"
    )
    print(f"ALPHA4_RUNTIME_IDENTITY_FIELD_SENSITIVITY={sensitivity}/{sensitivity} PASS")
    print(f"ALPHA4_RUNTIME_EVIDENCE_SET_ORDER_INVARIANCE={evidence_set}/{evidence_set} PASS")
    print("ALPHA4_RUNTIME_REPRESENTATION_SOURCE_INDEPENDENCE=PASS")
    print("ALPHA4_RUNTIME_TRIANGULATED_SEED_ACTION=STUTTER")
    print("ALPHA4_RUNTIME_TRIANGULATED_EXPRESSION=PASS")


def main() -> int:
    evidence = check_triangulated_assurance()
    print_evidence(evidence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
