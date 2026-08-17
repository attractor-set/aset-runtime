from __future__ import annotations

import hashlib
from pathlib import Path

from tools.alpha4_runtime_public_release_audit import check_public_root
from tools.alpha4_runtime_release_profiles import (
    manifest_records,
    parse_english,
    write_english,
    write_python,
)
from tools.build_alpha4_runtime_release import write_assembled_runtime
from tools.run_alpha4_runtime_release_tlaps import FINAL_THEOREM, verifier_source


def test_generated_english_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "Runtime.md"
    records = manifest_records()
    write_english(target, "sha256:" + "0" * 64, records)
    assert parse_english(target) == records


def test_generated_python_uses_exact_seed_base_and_stutters_seed(tmp_path: Path) -> None:
    profiles = tmp_path / "profiles"
    base = profiles / "base/seed/python/aset_seed_alpha4.py"
    runtime = profiles / "python/aset_runtime_alpha4.py"
    base.parent.mkdir(parents=True)
    runtime.parent.mkdir(parents=True)
    base.write_text(
        "def state(subject, authority, recognition='UNKNOWN', evidence=()):\n"
        "    return {'subject': subject, 'authority': authority, "
        "'recognition': recognition, 'evidence': tuple(evidence)}\n\n"
        "def apply_component(current, component_id, **kwargs):\n"
        "    return dict(current)\n",
        encoding="utf-8",
    )
    digest = "sha256:" + hashlib.sha256(base.read_bytes()).hexdigest()
    write_python(runtime, digest, manifest_records())
    namespace = {"__file__": str(runtime), "__name__": "runtime_test_subject"}
    exec(compile(runtime.read_text(encoding="utf-8"), str(runtime), "exec"), namespace)
    current = namespace["state"]()
    seed = {"subject": "s", "authority": "a", "recognition": "ALLOW", "evidence": ("e",)}
    start = {
        "attempt_id": "x",
        "attempt_digest": "d",
        "runtime_binding": "r",
        "descriptor_binding": "q",
    }
    next_runtime, next_seed, result = namespace["start_attempt"](current, start, seed)
    assert next_runtime["starts"] == [start]
    assert next_seed == seed
    assert result["seed_projection"] == {"action": "STUTTER", "effect_permitted": False}


def test_assembled_runtime_is_a_nonsemantic_composition_alias(tmp_path: Path) -> None:
    target = tmp_path / "AssembledRuntime.tla"
    write_assembled_runtime(target)
    text = target.read_text(encoding="utf-8")
    assert "EXTENDS RuntimeRelations" in text
    assert "AssembledStep(s, t, result) ==" in text
    assert "AssembledNext(s, t) == Next(s, t)" in text


def test_post_build_verifier_binds_all_exact_seed_preservation_operators() -> None:
    source = verifier_source()
    assert FINAL_THEOREM == "AssembledRuntimePreservesExactSeedBoundary"
    assert "Seed!PreserveUnknown" in source
    assert "Seed!PreserveAllow" in source
    assert "Seed!PreserveBlock" in source
    assert "AssembledStep(rs, rt, result)" in source
    assert 'SeedProjectionAction(result) = "STUTTER"' in source
    assert "SeedProjectionEffectPermitted(result) = FALSE" in source
    assert "ExactSeedPreservation(s, t, e)" in source
    assert "t = s" in source
    assert "t.recognition = s.recognition" in source


def test_public_root_matches_runtime_identity() -> None:
    identity = check_public_root()
    assert identity["project"] == "ASET Runtime"
    assert identity["representation_id"] == "0.1.0-alpha.4"
    assert identity["subject_id"] == "ASET-RUNTIME-ALPHA4"
    assert identity["repository"] == "https://github.com/attractor-set/aset-runtime"


def test_generated_python_preserves_formal_evidence_set_identity(tmp_path: Path) -> None:
    profiles = tmp_path / "profiles"
    base = profiles / "base/seed/python/aset_seed_alpha4.py"
    runtime = profiles / "python/aset_runtime_alpha4.py"
    base.parent.mkdir(parents=True)
    runtime.parent.mkdir(parents=True)
    base.write_text(
        "def state(subject, authority, recognition='UNKNOWN', evidence=()):\n"
        "    return {'subject': subject, 'authority': authority, "
        "'recognition': recognition, 'evidence': tuple(evidence)}\n\n"
        "def apply_component(current, component_id, **kwargs):\n"
        "    return dict(current)\n",
        encoding="utf-8",
    )
    digest = "sha256:" + hashlib.sha256(base.read_bytes()).hexdigest()
    write_python(runtime, digest, manifest_records())
    namespace = {"__file__": str(runtime), "__name__": "runtime_test_subject_set"}
    exec(compile(runtime.read_text(encoding="utf-8"), str(runtime), "exec"), namespace)
    start = {
        "attempt_id": "a",
        "attempt_digest": "d",
        "runtime_binding": "r",
        "descriptor_binding": "q",
    }
    terminal = {
        "attempt_id": "a",
        "attempt_digest": "d",
        "terminal_kind": "RESULT",
        "terminal_digest": "t",
        "terminal_binding": "b",
        "evidence_bindings": ["e0", "e1"],
    }
    current = namespace["state"]([start], [terminal])
    seed = {"subject": "s", "authority": "a", "recognition": "ALLOW", "evidence": ("e",)}
    reordered = {**terminal, "evidence_bindings": ["e1", "e0"]}
    next_runtime, next_seed, result = namespace["end_attempt"](current, reordered, seed)
    assert next_runtime == current
    assert next_seed == seed
    assert result["code"] == "IDEMPOTENT_REPLAY"


def test_runtime_airgap_executes_generated_companion_under_restricted_runtime(
    tmp_path: Path, monkeypatch
) -> None:
    from tools import alpha4_runtime_expression_airgap as airgap

    profiles = tmp_path / "profiles"
    base = profiles / "base/seed/python/aset_seed_alpha4.py"
    runtime = profiles / "python/aset_runtime_alpha4.py"
    base.parent.mkdir(parents=True)
    runtime.parent.mkdir(parents=True)
    base.write_text(
        "def state(subject, authority, recognition='UNKNOWN', evidence=()):\n"
        "    return {'subject': subject, 'authority': authority, "
        "'recognition': recognition, 'evidence': tuple(evidence)}\n\n"
        "def apply_component(current, component_id, **kwargs):\n"
        "    return dict(current)\n",
        encoding="utf-8",
    )
    digest = "sha256:" + hashlib.sha256(base.read_bytes()).hexdigest()
    write_python(runtime, digest, manifest_records())

    class Binding:
        companions = {"PYTHON": ("base/seed/python/aset_seed_alpha4.py", digest)}

    monkeypatch.setattr(airgap, "parse_seed_binding", Binding)
    evidence = airgap.check_expression_airgap(profiles)
    assert evidence["cases"]["start"] == 1452
    assert evidence["cases"]["end"] == 5808
    assert evidence["cases"]["total"] == 7260
    assert evidence["cases"]["identity_sensitivity"] == 5
    assert evidence["cases"]["grand_total"] == 7265
    assert evidence["companion_import_surface"] == "RESTRICTED"
    assert evidence["companion_file_access"] == "MATERIALIZED_PROFILE_TREE_READ_ONLY"
    assert evidence["companion_dynamic_builtins"] == "DENIED"
    assert evidence["companion_filesystem_method_aliasing"] == "DENIED"
    assert evidence["companion_seed_loader_exec"] == "EXACT_SEED_BASE_BYTES_ONLY"
    assert evidence["runtime_capability_isolation"] == "PASS"
    assert evidence["process_isolation"] == "NOT_CLAIMED"
    assert evidence["status"] == "PASS"


def test_runtime_airgap_rejects_bound_filesystem_capability_alias() -> None:
    import pytest

    from tools.alpha4_runtime_expression_airgap import (
        AirgapError,
        _validate_companion_ast,
    )

    source = "from pathlib import Path\nprobe = Path('.').iterdir\n"
    with pytest.raises(
        AirgapError,
        match="filesystem inspection forbidden",
    ):
        _validate_companion_ast(
            source,
            allowed_imports=frozenset({"pathlib"}),
            allow_seed_loader=False,
        )


def test_runtime_airgap_denies_aliased_dynamic_builtin_at_runtime(
    tmp_path,
) -> None:
    import pytest

    from tools.alpha4_runtime_expression_airgap import (
        AirgapError,
        _load_expression,
    )

    subject = tmp_path / "runtime-subject.py"
    subject.write_text(
        "capability = getattr\ncapability((), 'missing')\n",
        encoding="utf-8",
    )

    with pytest.raises(
        AirgapError,
        match="forbidden runtime capability",
    ):
        _load_expression(
            subject,
            tmp_path,
            allowed_imports=frozenset(),
            allow_seed_loader=False,
        )


def test_runtime_airgap_denies_arbitrary_compile_exec_alias(
    tmp_path,
) -> None:
    import pytest

    from tools.alpha4_runtime_expression_airgap import (
        AirgapError,
        _load_expression,
    )

    subject = tmp_path / "runtime-compile-subject.py"
    subject.write_text(
        "compiler = compile\n"
        "executor = exec\n"
        "code = compiler('VALUE = 1\\n', 'not-seed.py', 'exec')\n"
        "executor(code)\n",
        encoding="utf-8",
    )

    with pytest.raises(
        AirgapError,
        match="compile path is not exact Seed base",
    ):
        _load_expression(
            subject,
            tmp_path,
            allowed_imports=frozenset(),
            allow_seed_loader=True,
        )
