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
    assert evidence["relational_source_derivations"] == 8
    assert evidence["interface_validator_cases"] == 28
    assert evidence["identity_field_sensitivity"] == 5
    assert evidence["evidence_set_order_invariance"] == 1
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


def test_relational_source_derivation_and_identity_sensitivity_are_first_class() -> None:
    evidence = check_triangulated_assurance()
    assert evidence["relational_source_derivations"] == 8
    assert evidence["interface_validator_cases"] == 28
    assert evidence["identity_field_sensitivity"] == 5
    assert evidence["evidence_set_order_invariance"] == 1


def test_causal_interface_validators_are_not_imported_from_operational_model() -> None:
    source = Path("tools/alpha4_runtime_causal_expression.py").read_text(encoding="utf-8")
    assert "from tools.alpha4_runtime_paired_expression import exact_start" not in source
    assert "from tools.alpha4_runtime_paired_expression import exact_terminal" not in source
    assert "def causal_exact_start" in source
    assert "def causal_exact_terminal" in source


def _copy_repo(tmp_path: Path) -> Path:
    import shutil
    import subprocess

    source = Path.cwd()
    target = tmp_path / "repo"
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(".git", ".pytest_cache", "__pycache__", ".tlacache", "dist"),
    )
    subprocess.run(["git", "init", "-q"], cwd=target, check=True)
    subprocess.run(["git", "add", "."], cwd=target, check=True)
    return target


def _run_gate(repo: Path) -> tuple[int, str]:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "tools.alpha4_runtime_gate"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.returncode, result.stdout


def test_bound_runtime_tla_replay_mutation_breaks_gate(tmp_path: Path) -> None:
    repo = _copy_repo(tmp_path)
    path = repo / "runtime/alpha4/formal/RuntimeRelations.tla"
    text = path.read_text(encoding="utf-8")
    old = "ExactStartReplay(s, start) == start \\in s.starts"
    assert old in text
    path.write_text(
        text.replace(old, "ExactStartReplay(s, start) == StartIdentifierExists(s, start)", 1),
        encoding="utf-8",
    )
    status, output = _run_gate(repo)
    assert status != 0
    assert "relational canonical scope drift" in output.lower()


def test_runtime_manifest_duplicate_precedence_breaks_gate(tmp_path: Path) -> None:
    repo = _copy_repo(tmp_path)
    path = repo / "runtime/alpha4/RUNTIME.aset"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "SEMANTIC-PRECEDENCE NONE",
            "SEMANTIC-PRECEDENCE OPERATIONAL\nSEMANTIC-PRECEDENCE NONE",
            1,
        ),
        encoding="utf-8",
    )
    status, output = _run_gate(repo)
    assert status != 0
    assert "closed-world declaration drift" in output


def test_runtime_manifest_pair_and_proof_scope_are_canonical(tmp_path: Path) -> None:
    import shutil

    from tools.alpha4_runtime_manifest import ManifestError, parse_runtime_manifest

    repo = _copy_repo(tmp_path)
    manifest = repo / "runtime/alpha4/RUNTIME.aset"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace(
        "StartFresh OperationalStartFresh StartFreshPairing",
        "BogusRelation OperationalStartFresh BogusPairing",
        1,
    )
    manifest.write_text(text, encoding="utf-8")
    with pytest.raises(ManifestError, match="PAIR binding drift"):
        parse_runtime_manifest(repo)

    repo2 = tmp_path / "repo-proof"
    shutil.copytree(repo, repo2)
    manifest2 = repo2 / "runtime/alpha4/RUNTIME.aset"
    text2 = manifest2.read_text(encoding="utf-8").replace(
        "BogusRelation OperationalStartFresh BogusPairing",
        "StartFresh OperationalStartFresh StartFreshPairing",
        1,
    )
    text2 = text2.replace(
        "OperationalRelationalPairing 17",
        "OperationalRelationalPairing 1",
        1,
    )
    manifest2.write_text(text2, encoding="utf-8")
    with pytest.raises(ManifestError, match="proof binding/scope drift"):
        parse_runtime_manifest(repo2)


def test_runtime_tlaps_runner_rejects_reduced_proof_scope(tmp_path: Path) -> None:
    import subprocess
    import sys

    fake = tmp_path / "tlapm"
    fake.write_text("#!/bin/sh\necho 'All 1 obligation proved.'\n", encoding="utf-8")
    fake.chmod(0o755)
    result = subprocess.run(
        [sys.executable, "tools/run_alpha4_runtime_tlaps.py", "--tlapm", str(fake)],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode != 0
    assert "SCOPE_DRIFT" in result.stdout


def test_runtime_relational_and_proof_scopes_are_closed_world(tmp_path: Path) -> None:
    from tools.alpha4_runtime_manifest import ManifestError, parse_runtime_manifest

    repo = _copy_repo(tmp_path / "relational")
    relational = repo / "runtime/alpha4/formal/RuntimeRelations.tla"
    text = relational.read_text(encoding="utf-8")
    marker = "ExactStartReplay(s, start) == start \\in s.starts"
    assert marker in text
    relational.write_text(text.replace(marker, marker + " /\\ FALSE", 1), encoding="utf-8")
    with pytest.raises(ManifestError, match="relational canonical scope drift"):
        parse_runtime_manifest(repo)

    repo = _copy_repo(tmp_path / "proof")
    proof = repo / "runtime/alpha4/formal/OperationalRelationalPairingProofs.tla"
    text = proof.read_text(encoding="utf-8")
    marker = "THEOREM StartFreshPairing =="
    assert marker in text
    proof.write_text(text.replace(marker, marker + "\n  /\\ TRUE", 1), encoding="utf-8")
    with pytest.raises(ManifestError, match="proof canonical scope drift"):
        parse_runtime_manifest(repo)


def test_runtime_airgap_rejects_repository_semantic_import() -> None:
    from tools.alpha4_runtime_expression_airgap import AirgapError, _validate_companion_ast

    source = "from tools.alpha4_runtime_relational_expression import derive_runtime_contract\n"
    with pytest.raises(AirgapError, match="import forbidden"):
        _validate_companion_ast(
            source,
            allowed_imports=frozenset({"hashlib", "copy", "pathlib"}),
            allow_seed_loader=True,
        )


def test_runtime_airgap_rejects_import_smuggling_and_object_traversal() -> None:
    from tools.alpha4_runtime_expression_airgap import AirgapError, _validate_companion_ast

    with pytest.raises(AirgapError, match="import forbidden"):
        _validate_companion_ast(
            "from pathlib import os\n",
            allowed_imports=frozenset({"hashlib", "copy", "pathlib"}),
            allow_seed_loader=True,
        )

    with pytest.raises(AirgapError, match="private attribute forbidden"):
        _validate_companion_ast(
            "value = ().__class__\n",
            allowed_imports=frozenset({"hashlib", "copy", "pathlib"}),
            allow_seed_loader=True,
        )


def test_runtime_release_sensitivity_rejects_ignored_start_binding() -> None:
    from copy import deepcopy

    from tools.alpha4_runtime_expression_airgap import AirgapError, _check_identity_sensitivity

    def buggy_start(current, start, seed_state):
        next_state = deepcopy(current)
        same = [
            item
            for item in next_state["starts"]
            if item["attempt_id"] == start["attempt_id"]
            and item["attempt_digest"] == start["attempt_digest"]
        ]
        if same:
            result = {
                "accepted": True,
                "code": "IDEMPOTENT_REPLAY",
                "state_changed": False,
                "seed_projection": {"action": "STUTTER", "effect_permitted": False},
            }
        else:
            next_state["starts"].append(deepcopy(start))
            result = {
                "accepted": True,
                "code": "ATTEMPT_STARTED",
                "state_changed": True,
                "seed_projection": {"action": "STUTTER", "effect_permitted": False},
            }
        return next_state, deepcopy(seed_state), result

    namespace = {"start_attempt": buggy_start, "end_attempt": lambda *args: args}
    seed_state = {"subject": "s", "authority": "a", "recognition": "UNKNOWN", "evidence": ()}
    with pytest.raises(AirgapError, match="start identity sensitivity"):
        _check_identity_sensitivity(namespace, seed_state)


def test_runtime_formal_reflection_scope_is_closed_world(tmp_path: Path) -> None:
    from tools.alpha4_runtime_manifest import ManifestError, parse_runtime_manifest

    repo = _copy_repo(tmp_path)
    reflection = repo / "runtime/alpha4/formal/RestrictedOperationalSemantics.tla"
    text = reflection.read_text(encoding="utf-8")
    marker = "OperationalStartFresh(s, t, start, result) =="
    assert marker in text
    reflection.write_text(text.replace(marker, marker + "\n  /\\ TRUE", 1), encoding="utf-8")
    with pytest.raises(ManifestError, match="formal reflection canonical scope drift"):
        parse_runtime_manifest(repo)


def test_runtime_tla_scope_preserves_comment_tokens_inside_strings(tmp_path: Path) -> None:
    from tools.alpha4_runtime_manifest import ManifestError, parse_runtime_manifest

    repo = _copy_repo(tmp_path)
    relational = repo / "runtime/alpha4/formal/RuntimeRelations.tla"
    text = relational.read_text(encoding="utf-8")
    marker = 'result = "ATTEMPT_STARTED"'
    assert marker in text
    relational.write_text(
        text.replace(marker, 'result = "ATTEMPT_STARTED(*scope-drift*)"', 1),
        encoding="utf-8",
    )
    with pytest.raises(ManifestError, match="relational canonical scope drift"):
        parse_runtime_manifest(repo)
