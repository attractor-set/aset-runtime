from __future__ import annotations

from pathlib import Path

import pytest

from tools.alpha4_runtime_causal_expression import (
    CausalExpressionError,
    check_causal_bindings,
    parse_causal_net,
    validate_causal_contract,
)
from tools.alpha4_runtime_paired_expression import parse_operational_words
from tools.alpha4_runtime_triangulated_expression import (
    check_representation_source_independence,
    check_triangulated_assurance,
)


def test_causal_surface_binds_all_runtime_components() -> None:
    net = check_causal_bindings()
    assert len(net.transitions) == 8
    assert all(item.output_map()["SEED_ACTION"] == "STUTTER" for item in net.transitions)
    assert all(item.output_map()["SEED_EFFECT"] == "FALSE" for item in net.transitions)


def test_three_assurance_representations_use_distinct_source_paths() -> None:
    sources = check_representation_source_independence()
    assert set(sources) == {"OPERATIONAL", "RELATIONAL", "CAUSAL-MODEL"}
    assert len(set(sources.values())) == 3


def test_three_way_assurance_covers_complete_bounded_domain() -> None:
    evidence = check_triangulated_assurance()
    assert evidence["start_checks"] == 484
    assert evidence["end_checks"] == 1936
    assert evidence["total_checks"] == 2420
    assert evidence["operational_stack_contracts"] == 8
    assert evidence["causal_closed_world_contracts"] == 8
    assert evidence["operational_causal_result_code_bindings"] == 8
    assert evidence["pairwise_relations"] == {
        "operational_relational": "PASS",
        "operational_causal": "PASS",
        "relational_causal": "PASS",
    }
    assert evidence["representation_source_independence"] == "PASS"
    assert evidence["seed_action"] == "STUTTER"
    assert evidence["status"] == "PASS"


def _mutated_source(tmp_path: Path, source: Path, old: str, new: str) -> Path:
    target = tmp_path / source.name
    text = source.read_text(encoding="utf-8")
    assert old in text
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return target


def test_runtime_operational_stack_contract_rejects_missing_start(tmp_path: Path) -> None:
    source = Path("runtime/alpha4/operational/components.forth")
    mutated = _mutated_source(
        tmp_path, source, "( state start -- state result )", "( state -- state result )"
    )
    with pytest.raises(RuntimeError, match="stack contract mismatch"):
        parse_operational_words(mutated)


def test_runtime_causal_effect_surface_rejects_unbound_extra_effect(tmp_path: Path) -> None:
    source = Path("runtime/alpha4/causal/components.petri")
    mutated = _mutated_source(
        tmp_path, source, "EFFECT ADD_START", "EFFECT ADD_START\nEFFECT DESTROY_STATE"
    )
    net = parse_causal_net(mutated)
    with pytest.raises(CausalExpressionError, match="causal effect contract drift"):
        validate_causal_contract(net)


def test_runtime_causal_output_surface_rejects_wrong_result_code(tmp_path: Path) -> None:
    source = Path("runtime/alpha4/causal/components.petri")
    mutated = _mutated_source(
        tmp_path, source, "OUTPUT CODE ATTEMPT_STARTED", "OUTPUT CODE WRONG_CODE"
    )
    net = parse_causal_net(mutated)
    with pytest.raises(CausalExpressionError, match="causal output contract drift"):
        validate_causal_contract(net)
