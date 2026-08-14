from __future__ import annotations

from tools.alpha4_runtime_causal_expression import check_causal_bindings
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
    assert evidence["pairwise_relations"] == {
        "operational_relational": "PASS",
        "operational_causal": "PASS",
        "relational_causal": "PASS",
    }
    assert evidence["representation_source_independence"] == "PASS"
    assert evidence["seed_action"] == "STUTTER"
    assert evidence["status"] == "PASS"
