from __future__ import annotations

from pathlib import Path

from tools.alpha4_runtime_causal_expression import check_causal_bindings
from tools.alpha4_runtime_paired_expression import EXPECTED_WORDS, parse_operational_words

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "runtime/alpha4/RUNTIME.aset"


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    values = lines(MANIFEST)
    require(
        values[0] == "ASET-RUNTIME 1 ASET-RUNTIME-ALPHA4 0.1.0-alpha.4",
        "Runtime subject header drift",
    )
    require("SEMANTIC-PRECEDENCE NONE" in values, "Runtime semantic precedence drift")
    require(
        "PREDECESSOR-COMPATIBILITY NONE" in values,
        "Runtime predecessor compatibility boundary drift",
    )
    require(
        "UPSTREAM-SUBJECT ASET-SEED-0.4-ALPHA" in values,
        "Runtime Seed subject binding missing",
    )
    require(
        "UPSTREAM-BINDING upstream/ASET_SEED_ALPHA4_BINDING.aset" in values,
        "Runtime Seed binding path drift",
    )
    pairs = [line for line in values if line.startswith("PAIR ")]
    causal = [line for line in values if line.startswith("CAUSAL-BIND ")]
    require(len(pairs) == 8, f"Runtime pair surface must be 8, got {len(pairs)}")
    require(len(causal) == 8, f"Runtime causal binding surface must be 8, got {len(causal)}")
    component_ids = {line.split()[1] for line in pairs}
    require(
        component_ids == {line.split()[1] for line in causal},
        "Runtime pair/causal component identity drift",
    )
    for relative in (
        "runtime/alpha4/operational/components.forth",
        "runtime/alpha4/formal/RuntimeRelations.tla",
        "runtime/alpha4/formal/RestrictedOperationalSemantics.tla",
        "runtime/alpha4/formal/OperationalRelationalPairingProofs.tla",
        "runtime/alpha4/formal/SeedBoundaryProofs.tla",
        "runtime/alpha4/causal/components.petri",
        "upstream/ASET_SEED_ALPHA4_BINDING.aset",
    ):
        require((ROOT / relative).is_file(), f"Runtime active source missing: {relative}")
    require(
        set(parse_operational_words()) == set(EXPECTED_WORDS),
        "Runtime operational surface drift",
    )
    check_causal_bindings()
    relational = (ROOT / "runtime/alpha4/formal/RuntimeRelations.tla").read_text(encoding="utf-8")
    for marker in (
        "RuntimeInvariant(s) ==",
        "StartAttempt(s, t, start, result) ==",
        "EndAttempt(s, t, terminal, result) ==",
        'SeedProjectionAction(result) == "STUTTER"',
        "SeedProjectionEffectPermitted(result) == FALSE",
    ):
        require(marker in relational, f"Runtime relational marker missing: {marker}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    require(
        "RESULT" in readme and "NO_RESULT" in readme,
        "Runtime terminal semantics documentation drift",
    )
    require(
        "Recognition remains local to Seed" in readme,
        "Runtime Seed authority boundary documentation missing",
    )
    print("ALPHA4_RUNTIME_SUBJECT=PASS")
    print("ALPHA4_RUNTIME_COMPONENT_PAIRS=8/8 PASS")
    print("ALPHA4_RUNTIME_CAUSAL_BINDINGS=8/8 PASS")
    print("ALPHA4_RUNTIME_SEMANTIC_PRECEDENCE=NONE")
    print("ALPHA4_RUNTIME_PREDECESSOR_COMPATIBILITY=NONE")
    print("ALPHA4_RUNTIME_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
