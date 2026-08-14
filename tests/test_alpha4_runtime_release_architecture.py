from __future__ import annotations

import hashlib
from pathlib import Path

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
