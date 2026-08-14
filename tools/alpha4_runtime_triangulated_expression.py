from __future__ import annotations

from pathlib import Path

from tools.alpha4_runtime_causal_expression import (
    causal_end,
    causal_start,
    check_causal_bindings,
)
from tools.alpha4_runtime_paired_expression import (
    bounded_domain,
    operational_end,
    operational_start,
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


def check_triangulated_assurance() -> dict[str, object]:
    sources = check_representation_source_independence()
    net = check_causal_bindings()
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
    print("ALPHA4_RUNTIME_ASSURANCE_REPRESENTATIONS=OPERATIONAL,RELATIONAL,CAUSAL")
    print("ALPHA4_RUNTIME_ASSURANCE_SEMANTIC_PRECEDENCE=NONE")
    print(f"ALPHA4_RUNTIME_OPERATIONAL_RELATIONAL_CONGRUENCE={total}/{total} PASS")
    print(f"ALPHA4_RUNTIME_OPERATIONAL_CAUSAL_CONGRUENCE={total}/{total} PASS")
    print(f"ALPHA4_RUNTIME_RELATIONAL_CAUSAL_CONGRUENCE={total}/{total} PASS")
    print(f"ALPHA4_RUNTIME_TRIANGULATED_START={start}/{start} PASS")
    print(f"ALPHA4_RUNTIME_TRIANGULATED_END={end}/{end} PASS")
    print(f"ALPHA4_RUNTIME_TRIANGULATED_TOTAL={total}/{total} PASS")
    print("ALPHA4_RUNTIME_REPRESENTATION_SOURCE_INDEPENDENCE=PASS")
    print("ALPHA4_RUNTIME_TRIANGULATED_SEED_ACTION=STUTTER")
    print("ALPHA4_RUNTIME_TRIANGULATED_EXPRESSION=PASS")


def main() -> int:
    evidence = check_triangulated_assurance()
    print_evidence(evidence)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
