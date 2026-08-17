from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path("runtime/alpha4/RUNTIME.aset")


class ManifestError(RuntimeError):
    pass


@dataclass(frozen=True)
class PairBinding:
    component_id: str
    transition: str
    formal_operator: str
    operational_operator: str
    pairing_theorem: str


@dataclass(frozen=True)
class CausalBinding:
    component_id: str
    causal_transition: str


@dataclass(frozen=True)
class ProofBinding:
    proof_id: str
    module: str
    final_theorem: str
    expected_obligations: int


@dataclass(frozen=True)
class RuntimeBindingPlan:
    operational: str
    relational: str
    formal_reflection: str
    causal_model: str
    pairs: tuple[PairBinding, ...]
    causal_bindings: tuple[CausalBinding, ...]
    proofs: tuple[ProofBinding, ...]
    derivers: tuple[tuple[str, str], ...]
    relations: tuple[tuple[str, str], ...]

    def relation_map(self) -> dict[str, str]:
        return dict(self.relations)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


EXPECTED_HEADER = ("ASET-RUNTIME", "1", "ASET-RUNTIME-ALPHA4", "0.1.0-alpha.4")
EXPECTED_FIXED = (
    "SEMANTIC-PRECEDENCE NONE",
    "PREDECESSOR-COMPATIBILITY NONE",
    "UPSTREAM-SUBJECT ASET-SEED-0.4-ALPHA",
    "UPSTREAM-BINDING upstream/ASET_SEED_ALPHA4_BINDING.aset",
    (
        "SEED-EXTENSION-BIND OPERATIONAL "
        "PRESERVE-UNKNOWN,PRESERVE-ALLOW,PRESERVE-BLOCK "
        "ALL-RUNTIME-TRANSITIONS"
    ),
    (
        "SEED-EXTENSION-BIND RELATIONAL "
        "PreserveUnknown,PreserveAllow,PreserveBlock "
        "ALL-RUNTIME-TRANSITIONS"
    ),
    (
        "SEED-EXTENSION-BIND CAUSAL "
        "PRESERVE-UNKNOWN,PRESERVE-ALLOW,PRESERVE-BLOCK "
        "ALL-RUNTIME-TRANSITIONS"
    ),
    "STATE STARTS,TERMINALS EXACT-APPEND-ONLY-ATTEMPT-RECORDS",
    "TRANSITION START-ATTEMPT",
    "TRANSITION END-ATTEMPT",
    "SEED-PROJECTION ALL-RUNTIME-TRANSITIONS PRESERVE-SEED-STATE",
    "SEED-RECOGNITION-OWNER SEED-ONLY",
    "EFFECT-PERMITTED-BY-RUNTIME NEVER",
    "CHECK BINDING tools/validate_alpha4_runtime.py",
    "CHECK OPERATIONAL_RELATIONAL tools/alpha4_runtime_paired_expression.py",
    "CHECK ASSURANCE tools/alpha4_runtime_assurance.py",
    "CHECK TRIANGULATED_EXPRESSION tools/alpha4_runtime_triangulated_expression.py",
    "GATE tools/alpha4_runtime_gate.py",
)
EXPECTED_SOURCES = {
    "OPERATIONAL": "runtime/alpha4/operational/components.forth",
    "RELATIONAL": "runtime/alpha4/formal/RuntimeRelations.tla",
    "FORMAL-REFLECTION": "runtime/alpha4/formal/RestrictedOperationalSemantics.tla",
    "CAUSAL-MODEL": "runtime/alpha4/causal/components.petri",
}
EXPECTED_PAIRS = (
    PairBinding(
        "ASET-RUNTIME-COMPONENT-START-FRESH",
        "START-ATTEMPT",
        "StartFresh",
        "OperationalStartFresh",
        "StartFreshPairing",
    ),
    PairBinding(
        "ASET-RUNTIME-COMPONENT-START-REPLAY",
        "START-ATTEMPT",
        "StartReplay",
        "OperationalStartReplay",
        "StartReplayPairing",
    ),
    PairBinding(
        "ASET-RUNTIME-COMPONENT-REJECT-START-CONFLICT",
        "START-ATTEMPT",
        "RejectStartConflict",
        "OperationalRejectStartConflict",
        "RejectStartConflictPairing",
    ),
    PairBinding(
        "ASET-RUNTIME-COMPONENT-END-RESULT",
        "END-ATTEMPT",
        "EndResult",
        "OperationalEndResult",
        "EndResultPairing",
    ),
    PairBinding(
        "ASET-RUNTIME-COMPONENT-END-NO-RESULT",
        "END-ATTEMPT",
        "EndNoResult",
        "OperationalEndNoResult",
        "EndNoResultPairing",
    ),
    PairBinding(
        "ASET-RUNTIME-COMPONENT-END-REPLAY",
        "END-ATTEMPT",
        "EndReplay",
        "OperationalEndReplay",
        "EndReplayPairing",
    ),
    PairBinding(
        "ASET-RUNTIME-COMPONENT-REJECT-END-CONFLICT",
        "END-ATTEMPT",
        "RejectEndConflict",
        "OperationalRejectEndConflict",
        "RejectEndConflictPairing",
    ),
    PairBinding(
        "ASET-RUNTIME-COMPONENT-REJECT-END-NOT-RUNNING",
        "END-ATTEMPT",
        "RejectEndNotRunning",
        "OperationalRejectEndNotRunning",
        "RejectEndNotRunningPairing",
    ),
)
EXPECTED_CAUSAL = tuple(
    CausalBinding(item.component_id, transition)
    for item, transition in zip(
        EXPECTED_PAIRS,
        (
            "START-FRESH",
            "START-REPLAY",
            "REJECT-START-CONFLICT",
            "END-RESULT",
            "END-NO-RESULT",
            "END-REPLAY",
            "REJECT-END-CONFLICT",
            "REJECT-END-NOT-RUNNING",
        ),
        strict=True,
    )
)
EXPECTED_PROOFS = (
    ProofBinding(
        "OPERATIONAL_RELATIONAL_PAIRING",
        "runtime/alpha4/formal/OperationalRelationalPairingProofs.tla",
        "OperationalRelationalPairing",
        17,
    ),
    ProofBinding(
        "SEED_BOUNDARY",
        "runtime/alpha4/formal/SeedBoundaryProofs.tla",
        "RuntimePreservesSeedBoundary",
        5,
    ),
)
EXPECTED_DERIVERS = (
    ("OPERATIONAL", "tools/alpha4_runtime_paired_expression.py"),
    ("RELATIONAL", "tools/alpha4_runtime_relational_expression.py"),
    ("CAUSAL", "tools/alpha4_runtime_causal_expression.py"),
)
EXPECTED_RELATIONS = (
    ("OPERATIONAL_RELATIONAL", "BOUNDED_OPERATIONAL_RELATIONAL_CONGRUENCE"),
    ("OPERATIONAL_CAUSAL", "BOUNDED_OPERATIONAL_CAUSAL_CONGRUENCE"),
    ("OPERATIONAL_INTERFACE", "EXACT_STACK_EFFECT_CONTRACT"),
    ("CAUSAL_CONTRACT", "CLOSED_WORLD_REQUIREMENT_EFFECT_OUTPUT_CONTRACT"),
    ("OPERATIONAL_CAUSAL_RESULT", "OBSERVABLE_RESULT_CODE_CONGRUENCE"),
    ("RELATIONAL_CAUSAL", "BOUNDED_RELATIONAL_CAUSAL_CONGRUENCE"),
    ("TRIANGULATED", "THREE_WAY_BOUNDED_OBSERVATIONAL_CONGRUENCE"),
    ("RELATIONAL_SOURCE", "BOUND_TLA_OPERATOR_DERIVATION"),
)


def _strip_tla_comments(source: str) -> str:
    out: list[str] = []
    index = 0
    block_depth = 0
    in_string = False
    while index < len(source):
        if block_depth:
            if source.startswith("(*", index):
                block_depth += 1
                index += 2
            elif source.startswith("*)", index):
                block_depth -= 1
                index += 2
            elif source[index] == "\n":
                out.append("\n")
                index += 1
            else:
                index += 1
            continue

        if in_string:
            char = source[index]
            out.append(char)
            if char == "\\" and index + 1 < len(source):
                out.append(source[index + 1])
                index += 2
            else:
                if char == '"':
                    in_string = False
                index += 1
            continue

        if source.startswith("(*", index):
            block_depth = 1
            index += 2
            continue
        if source.startswith("\\*", index):
            while index < len(source) and source[index] != "\n":
                index += 1
            continue
        char = source[index]
        out.append(char)
        if char == '"':
            in_string = True
        index += 1

    if block_depth:
        raise ManifestError("unterminated TLA block comment in canonical scope")
    if in_string:
        raise ManifestError("unterminated TLA string in canonical scope")
    return "".join(out)


def _canonical_tla_scope_sha256(path: Path) -> str:
    source = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    uncommented = _strip_tla_comments(source)
    canonical = "\n".join(line.strip() for line in uncommented.splitlines() if line.strip())
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


EXPECTED_RELATIONAL_SCOPE_SHA256 = (
    "sha256:9908a323393ce02d08e8c4fc5d398611d23df07aba5497e53ff153aad3c7216d"
)
EXPECTED_FORMAL_REFLECTION_SCOPE_SHA256 = (
    "sha256:635c0aaf93cd792d5caad314b434dd3ba76673f6f19b2133a8ca67e4300e6125"
)
EXPECTED_PROOF_SCOPE_SHA256 = {
    "OPERATIONAL_RELATIONAL_PAIRING": (
        "sha256:b7ff1f0337c949f242c110cd6b0191860d4fabdb81174e4a89653609e83f1f36"
    ),
    "SEED_BOUNDARY": ("sha256:ded37c5612ee835f8e8661519453ec5ef4d90a24b8926de6e3a9242cf451c928"),
}


def _theorem_present(path: Path, theorem: str) -> bool:
    text = path.read_text(encoding="utf-8")
    return f"THEOREM {theorem}" in text or f"{theorem} ==" in text


def parse_runtime_manifest(root: Path = ROOT) -> RuntimeBindingPlan:
    path = root / MANIFEST
    lines = [
        line.strip().split()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    require(lines and tuple(lines[0]) == EXPECTED_HEADER, "Runtime manifest header drift")
    fixed: list[str] = []
    sources: dict[str, str] = {}
    pairs: list[PairBinding] = []
    causal: list[CausalBinding] = []
    proofs: list[ProofBinding] = []
    derivers: list[tuple[str, str]] = []
    relations: list[tuple[str, str]] = []
    for tokens in lines[1:]:
        kind = tokens[0]
        if kind in EXPECTED_SOURCES:
            require(len(tokens) == 2 and kind not in sources, f"duplicate/invalid {kind}")
            sources[kind] = tokens[1]
        elif kind == "PAIR":
            require(len(tokens) == 6, "invalid PAIR binding")
            pairs.append(PairBinding(*tokens[1:]))
        elif kind == "CAUSAL-BIND":
            require(len(tokens) == 3, "invalid CAUSAL-BIND")
            causal.append(CausalBinding(tokens[1], tokens[2]))
        elif kind == "PROOF":
            require(len(tokens) == 5, "proof binding must pin obligation count")
            proofs.append(ProofBinding(tokens[1], tokens[2], tokens[3], int(tokens[4])))
        elif kind == "DERIVER":
            require(len(tokens) == 3, "invalid DERIVER")
            derivers.append((tokens[1], tokens[2]))
        elif kind == "RELATION":
            require(len(tokens) == 3, "invalid RELATION")
            relations.append((tokens[1], tokens[2]))
        else:
            fixed.append(" ".join(tokens))
    require(Counter(fixed) == Counter(EXPECTED_FIXED), "Runtime closed-world declaration drift")
    require(sources == EXPECTED_SOURCES, "Runtime representation source binding drift")
    require(tuple(pairs) == EXPECTED_PAIRS, "Runtime PAIR binding drift")
    require(tuple(causal) == EXPECTED_CAUSAL, "Runtime CAUSAL-BIND drift")
    require(tuple(proofs) == EXPECTED_PROOFS, "Runtime proof binding/scope drift")
    require(tuple(derivers) == EXPECTED_DERIVERS, "Runtime deriver binding drift")
    require(tuple(relations) == EXPECTED_RELATIONS, "Runtime assurance relation binding drift")
    require(len({x.component_id for x in pairs}) == 8, "duplicate Runtime pair component")
    require(len({x.formal_operator for x in pairs}) == 8, "duplicate Runtime formal operator")
    require(len({x.pairing_theorem for x in pairs}) == 8, "duplicate Runtime pairing theorem")
    for relative in (*sources.values(), *(p.module for p in proofs), *(p for _, p in derivers)):
        require((root / relative).is_file(), f"Runtime bound file missing: {relative}")
    require(
        _canonical_tla_scope_sha256(root / sources["RELATIONAL"])
        == EXPECTED_RELATIONAL_SCOPE_SHA256,
        "Runtime relational canonical scope drift",
    )
    require(
        _canonical_tla_scope_sha256(root / sources["FORMAL-REFLECTION"])
        == EXPECTED_FORMAL_REFLECTION_SCOPE_SHA256,
        "Runtime formal reflection canonical scope drift",
    )
    for proof in proofs:
        require(
            _canonical_tla_scope_sha256(root / proof.module)
            == EXPECTED_PROOF_SCOPE_SHA256[proof.proof_id],
            f"Runtime proof canonical scope drift: {proof.proof_id}",
        )
    relational_text = (root / sources["RELATIONAL"]).read_text(encoding="utf-8")
    reflection_text = (root / sources["FORMAL-REFLECTION"]).read_text(encoding="utf-8")
    proof_text = "\n".join((root / proof.module).read_text(encoding="utf-8") for proof in proofs)
    for pair in pairs:
        require(
            f"{pair.formal_operator}(" in relational_text,
            f"formal operator missing: {pair.formal_operator}",
        )
        require(
            f"{pair.operational_operator}(" in reflection_text,
            f"operational reflection missing: {pair.operational_operator}",
        )
        require(
            pair.pairing_theorem in proof_text, f"pairing theorem missing: {pair.pairing_theorem}"
        )
    for proof in proofs:
        require(
            _theorem_present(root / proof.module, proof.final_theorem),
            f"final theorem missing: {proof.final_theorem}",
        )
    return RuntimeBindingPlan(
        operational=sources["OPERATIONAL"],
        relational=sources["RELATIONAL"],
        formal_reflection=sources["FORMAL-REFLECTION"],
        causal_model=sources["CAUSAL-MODEL"],
        pairs=tuple(pairs),
        causal_bindings=tuple(causal),
        proofs=tuple(proofs),
        derivers=tuple(derivers),
        relations=tuple(relations),
    )


def main() -> int:
    try:
        plan = parse_runtime_manifest(ROOT)
        total = sum(item.expected_obligations for item in plan.proofs)
        print(f"ALPHA4_RUNTIME_MANIFEST_PAIRS={len(plan.pairs)}/{len(plan.pairs)} PASS")
        print(f"ALPHA4_RUNTIME_MANIFEST_PROOFS={len(plan.proofs)}/{len(plan.proofs)} PASS")
        print("ALPHA4_RUNTIME_RELATIONAL_CANONICAL_SCOPE=1/1 PASS")
        print("ALPHA4_RUNTIME_FORMAL_REFLECTION_CANONICAL_SCOPE=1/1 PASS")
        print(
            "ALPHA4_RUNTIME_PROOF_CANONICAL_SCOPES="
            f"{len(EXPECTED_PROOF_SCOPE_SHA256)}/{len(EXPECTED_PROOF_SCOPE_SHA256)} PASS"
        )
        print(f"ALPHA4_RUNTIME_MANIFEST_EXPECTED_TLAPS_OBLIGATIONS={total}")
        print("ALPHA4_RUNTIME_BINDING_PLAN=PASS")
        return 0
    except (ManifestError, OSError, UnicodeError, ValueError) as error:
        print(f"ALPHA4_RUNTIME_MANIFEST_ERROR={error}")
        print("ALPHA4_RUNTIME_BINDING_PLAN=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
