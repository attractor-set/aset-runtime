from __future__ import annotations

from pathlib import Path

from tools.alpha4_runtime_causal_expression import (
    EXPECTED_CAUSAL_CONTRACTS,
    CausalNet,
    causal_end,
    causal_start,
    check_causal_bindings,
)
from tools.alpha4_runtime_paired_expression import (
    EXPECTED_STACK_EFFECTS,
    bounded_domain,
    operational_end,
    operational_start,
    parse_operational_words,
    relational_end,
    relational_start,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "runtime/alpha4/RUNTIME.aset"


def _manifest_lines() -> list[str]:
    return [
        line.strip() for line in MANIFEST.read_text(encoding="utf-8").splitlines() if line.strip()
    ]


def check_representation_source_independence() -> dict[str, str]:
    lines = _manifest_lines()
    if "SEMANTIC-PRECEDENCE NONE" not in lines:
        raise RuntimeError("Runtime semantic precedence drift")
    for relation in (
        "RELATION OPERATIONAL_INTERFACE EXACT_STACK_EFFECT_CONTRACT",
        "RELATION CAUSAL_CONTRACT CLOSED_WORLD_REQUIREMENT_EFFECT_OUTPUT_CONTRACT",
        "RELATION OPERATIONAL_CAUSAL_RESULT OBSERVABLE_RESULT_CODE_CONGRUENCE",
    ):
        if relation not in lines:
            raise RuntimeError(f"Runtime assurance relation missing: {relation}")
    sources: dict[str, str] = {}
    for line in lines:
        tokens = line.split()
        if tokens[0] in {"OPERATIONAL", "RELATIONAL", "CAUSAL-MODEL"}:
            sources[tokens[0]] = tokens[1]
    expected = {"OPERATIONAL", "RELATIONAL", "CAUSAL-MODEL"}
    if set(sources) != expected:
        raise RuntimeError(f"three-way Runtime source binding incomplete: {sources!r}")
    if len(set(sources.values())) != 3:
        raise RuntimeError(f"Runtime assurance representations share a source path: {sources!r}")
    for source in sources.values():
        if not (ROOT / source).is_file():
            raise RuntimeError(f"bound Runtime assurance source missing: {source}")
    return sources


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
    net = check_causal_bindings()
    stack_contracts, causal_contracts, result_bindings = check_operational_causal_interface(net)
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
    print("ALPHA4_RUNTIME_REPRESENTATION_SOURCE_INDEPENDENCE=PASS")
    print("ALPHA4_RUNTIME_TRIANGULATED_SEED_ACTION=STUTTER")
    print("ALPHA4_RUNTIME_TRIANGULATED_EXPRESSION=PASS")


def main() -> int:
    evidence = check_triangulated_assurance()
    print_evidence(evidence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
