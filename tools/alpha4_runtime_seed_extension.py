from __future__ import annotations

import argparse
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset"
RUNTIME = ROOT / "runtime/alpha4/RUNTIME.aset"


class SeedExtensionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SeedExtensionError(message)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            digest.update(relative.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


@dataclass(frozen=True)
class SeedBinding:
    release_tag: str
    release_tree: str
    release_archive: str
    profile_tree: str
    profile_archive: str
    sources: dict[str, str]
    assurance_bases: dict[str, tuple[str, tuple[str, ...]]]
    companions: dict[str, tuple[str, str]]


def _lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_seed_binding(path: Path = BINDING) -> SeedBinding:
    lines = _lines(path)
    require(
        lines[0] == "ASET-SEED-BINDING 1 ASET-SEED-0.4-ALPHA CONTENT-ADDRESSED",
        "Seed binding header mismatch",
    )
    scalar: dict[str, str] = {}
    sources: dict[str, str] = {}
    bases: dict[str, tuple[str, tuple[str, ...]]] = {}
    companions: dict[str, tuple[str, str]] = {}
    for line in lines[1:]:
        parts = line.split()
        if not parts:
            continue
        if parts[0] in {
            "RELEASE-TAG",
            "RELEASE-TREE",
            "RELEASE-ARCHIVE",
            "PROFILE-TREE",
            "PROFILE-ARCHIVE",
        }:
            require(len(parts) == 2, f"bad binding scalar: {line}")
            scalar[parts[0]] = parts[1]
        elif parts[0] == "SOURCE":
            require(len(parts) == 3, f"bad bound source: {line}")
            sources[parts[1]] = parts[2]
        elif parts[0] == "ASSURANCE-BASE":
            require(len(parts) == 4, f"bad assurance base: {line}")
            bases[parts[1]] = (parts[2], tuple(parts[3].split(",")))
        elif parts[0] == "COMPANION":
            require(len(parts) == 4, f"bad companion binding: {line}")
            companions[parts[1]] = (parts[2], parts[3])
    for key in (
        "RELEASE-TAG",
        "RELEASE-TREE",
        "RELEASE-ARCHIVE",
        "PROFILE-TREE",
        "PROFILE-ARCHIVE",
    ):
        require(key in scalar, f"Seed binding scalar missing: {key}")
    require(
        set(bases) == {"OPERATIONAL", "RELATIONAL", "CAUSAL"},
        "Seed assurance base surface mismatch",
    )
    require(set(companions) == {"ENGLISH", "PYTHON"}, "Seed companion surface mismatch")
    return SeedBinding(
        release_tag=scalar["RELEASE-TAG"],
        release_tree=scalar["RELEASE-TREE"],
        release_archive=scalar["RELEASE-ARCHIVE"],
        profile_tree=scalar["PROFILE-TREE"],
        profile_archive=scalar["PROFILE-ARCHIVE"],
        sources=sources,
        assurance_bases=bases,
        companions=companions,
    )


def _transition_block(text: str, name: str) -> str:
    match = re.search(rf"(?ms)^TRANSITION {re.escape(name)}\b.*?^END$", text)
    require(match is not None, f"causal transition missing: {name}")
    return match.group(0)


def check_seed_extension(seed_root: Path) -> dict[str, object]:
    binding = parse_seed_binding()
    seed_root = seed_root.resolve()
    for relative, expected in binding.sources.items():
        path = seed_root / relative
        require(path.is_file(), f"bound Seed source missing: {relative}")
        require(sha256(path) == expected, f"bound Seed source digest mismatch: {relative}")

    operational_path, operational_words = binding.assurance_bases["OPERATIONAL"]
    relational_path, relational_operators = binding.assurance_bases["RELATIONAL"]
    causal_path, causal_transitions = binding.assurance_bases["CAUSAL"]

    seed_forth = (seed_root / operational_path).read_text(encoding="utf-8")
    for word in operational_words:
        require(
            re.search(rf"(?m)^:\s+{re.escape(word)}\b.*?NOP\s*;\s*$", seed_forth) is not None,
            f"exact Seed operational preservation boundary unavailable: {word}",
        )

    seed_relational = (seed_root / relational_path).read_text(encoding="utf-8")
    for operator in relational_operators:
        require(
            re.search(rf"(?m)^{re.escape(operator)}\(s, t, e\)\s*==", seed_relational) is not None,
            f"exact Seed relational preservation operator unavailable: {operator}",
        )

    seed_causal = (seed_root / causal_path).read_text(encoding="utf-8")
    expected_places = {
        "PRESERVE-UNKNOWN": ("U", "U"),
        "PRESERVE-ALLOW": ("A", "A"),
        "PRESERVE-BLOCK": ("B", "B"),
    }
    for transition in causal_transitions:
        block = _transition_block(seed_causal, transition)
        before, after = expected_places[transition]
        require(
            f"FROM {before}" in block and f"TO {after}" in block,
            f"{transition}: Seed causal preservation drift",
        )
        require(
            "EFFECT PRESERVE_STATE" in block,
            f"{transition}: Seed causal preserve effect missing",
        )

    runtime_forth = (ROOT / "runtime/alpha4/operational/components.forth").read_text(
        encoding="utf-8"
    )
    require(
        "LOCAL-ALLOW!" not in runtime_forth and "LOCAL-BLOCK!" not in runtime_forth,
        "Runtime acquired Seed recognition operation",
    )
    runtime_relational = (ROOT / "runtime/alpha4/formal/RuntimeRelations.tla").read_text(
        encoding="utf-8"
    )
    require(
        'SeedProjectionAction(result) == "STUTTER"' in runtime_relational,
        "Runtime Seed stutter projection drift",
    )
    require(
        "SeedProjectionEffectPermitted(result) == FALSE" in runtime_relational,
        "Runtime Seed effect boundary drift",
    )

    manifest = set(_lines(RUNTIME))
    required = {
        (
            "SEED-EXTENSION-BIND OPERATIONAL "
            "PRESERVE-UNKNOWN,PRESERVE-ALLOW,PRESERVE-BLOCK ALL-RUNTIME-TRANSITIONS"
        ),
        (
            "SEED-EXTENSION-BIND RELATIONAL "
            "PreserveUnknown,PreserveAllow,PreserveBlock ALL-RUNTIME-TRANSITIONS"
        ),
        (
            "SEED-EXTENSION-BIND CAUSAL "
            "PRESERVE-UNKNOWN,PRESERVE-ALLOW,PRESERVE-BLOCK ALL-RUNTIME-TRANSITIONS"
        ),
        "SEED-PROJECTION ALL-RUNTIME-TRANSITIONS PRESERVE-SEED-STATE",
        "SEED-RECOGNITION-OWNER SEED-ONLY",
        "EFFECT-PERMITTED-BY-RUNTIME NEVER",
    }
    require(required <= manifest, "Runtime exact Seed extension bindings missing")
    return {
        "document_type": "aset-runtime-seed-extension-assurance",
        "seed_release_tag": binding.release_tag,
        "semantic_precedence": "NONE",
        "bindings": {"operational": "PASS", "relational": "PASS", "causal": "PASS"},
        "seed_projection": "STUTTER",
        "seed_redefinition": "ABSENT",
        "status": "PASS",
    }


def check_seed_companion_bases(seed_profiles_root: Path) -> dict[str, object]:
    binding = parse_seed_binding()
    seed_profiles_root = seed_profiles_root.resolve()
    require(seed_profiles_root.is_dir(), "Seed profile tree missing")
    actual_tree = tree_digest(seed_profiles_root)
    require(actual_tree == binding.profile_tree, "Seed profile tree digest mismatch")
    result: dict[str, object] = {"profile_tree_digest": actual_tree}
    for kind, (relative, expected) in binding.companions.items():
        path = seed_profiles_root / relative
        require(path.is_file(), f"Seed {kind.lower()} companion missing")
        require(sha256(path) == expected, f"Seed {kind.lower()} companion byte identity mismatch")
        result[kind.lower()] = {"path": relative, "sha256": expected}
    result["status"] = "PASS"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-root", type=Path, required=True)
    parser.add_argument("--seed-profiles-root", type=Path)
    args = parser.parse_args()
    try:
        evidence = check_seed_extension(args.seed_root)
        print("ALPHA4_RUNTIME_SEED_OPERATIONAL_EXTENSION=PASS")
        print("ALPHA4_RUNTIME_SEED_RELATIONAL_EXTENSION=PASS")
        print("ALPHA4_RUNTIME_SEED_CAUSAL_EXTENSION=PASS")
        print("ALPHA4_RUNTIME_SEED_EXTENSION_BINDINGS=3/3 PASS")
        print(f"ALPHA4_RUNTIME_SEED_REDEFINITION={evidence['seed_redefinition']}")
        print("ALPHA4_RUNTIME_SEED_PROJECTION=STUTTER")
        if args.seed_profiles_root is not None:
            check_seed_companion_bases(args.seed_profiles_root)
            print("ALPHA4_RUNTIME_SEED_ENGLISH_COMPANION_BASE=EXACT")
            print("ALPHA4_RUNTIME_SEED_PYTHON_COMPANION_BASE=EXACT")
        print("ALPHA4_RUNTIME_SEED_EXTENSION_ASSURANCE=PASS")
        return 0
    except (OSError, UnicodeError, ValueError, SeedExtensionError) as error:
        print(f"ALPHA4_RUNTIME_SEED_EXTENSION_ERROR={error}")
        print("ALPHA4_RUNTIME_SEED_EXTENSION_ASSURANCE=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
