from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path

from tools.alpha4_runtime_release_profiles import build_release_profiles
from tools.alpha4_runtime_seed_extension import parse_seed_binding, sha256, tree_digest
from tools.alpha4_runtime_triangulated_expression import check_triangulated_assurance

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
RELEASE_NAME = "ASET-Runtime-0.1.0-alpha.4"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


def write_assembled_runtime(target: Path) -> None:
    target.write_text(
        "\n".join(
            [
                "------------------------- MODULE AssembledRuntime -------------------------",
                "EXTENDS RuntimeRelations",
                "",
                "AssembledStart(s, t, start, result) == StartAttempt(s, t, start, result)",
                "AssembledEnd(s, t, terminal, result) == EndAttempt(s, t, terminal, result)",
                "AssembledStep(s, t, result) ==",
                "  \\/ \\E start \\in StartUniverse : AssembledStart(s, t, start, result)",
                "  \\/ \\E terminal \\in TerminalUniverse : AssembledEnd(s, t, terminal, result)",
                "AssembledNext(s, t) == Next(s, t)",
                "",
                "=============================================================================",
                "",
            ]
        ),
        encoding="utf-8",
    )


def zip_tree(root: Path, output: Path, archive_root_name: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = f"{archive_root_name}/{path.relative_to(root).as_posix()}"
            info = zipfile.ZipInfo(relative, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, path.read_bytes())


def source_digest(paths: list[str]) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update((ROOT / relative).read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def build_tree(output: Path) -> dict[str, object]:
    if output.exists():
        shutil.rmtree(output)
    for relative in ("source", "operational", "causal", "formal", "upstream"):
        (output / relative).mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "LICENSE", output / "LICENSE")
    shutil.copy2(ROOT / "NOTICE", output / "NOTICE")
    shutil.copy2(ROOT / "runtime/alpha4/RUNTIME.aset", output / "source/RUNTIME.aset")
    shutil.copy2(
        ROOT / "runtime/alpha4/operational/components.forth",
        output / "operational/components.forth",
    )
    shutil.copy2(
        ROOT / "runtime/alpha4/causal/components.petri",
        output / "causal/components.petri",
    )
    formal_sources = [
        "runtime/alpha4/formal/RuntimeRelations.tla",
        "runtime/alpha4/formal/RestrictedOperationalSemantics.tla",
        "runtime/alpha4/formal/OperationalRelationalPairingProofs.tla",
        "runtime/alpha4/formal/SeedBoundaryProofs.tla",
    ]
    for relative in formal_sources:
        shutil.copy2(ROOT / relative, output / "formal" / Path(relative).name)
    write_assembled_runtime(output / "formal/AssembledRuntime.tla")
    shutil.copy2(
        ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset",
        output / "upstream/ASET_SEED_ALPHA4_BINDING.aset",
    )
    assurance = check_triangulated_assurance()
    (output / "TRIANGULATED_ASSURANCE.json").write_text(
        json.dumps(assurance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    binding = parse_seed_binding()
    sources = [
        "runtime/alpha4/RUNTIME.aset",
        "runtime/alpha4/operational/components.forth",
        "runtime/alpha4/causal/components.petri",
        *formal_sources,
        "upstream/ASET_SEED_ALPHA4_BINDING.aset",
    ]
    manifest: dict[str, object] = {
        "document_type": "aset-runtime-alpha4-release-materialization",
        "schema_version": 1,
        "subject_id": "ASET-RUNTIME-ALPHA4",
        "version": "0.1.0-alpha.4",
        "semantic_precedence": "NONE",
        "source_byte_identity_digest": source_digest(sources),
        "seed_base": {
            "release_tag": binding.release_tag,
            "tree_digest": binding.release_tree,
            "projection": "PRESERVE-SEED-STATE",
            "semantic_redefinition": "ABSENT",
        },
        "architecture": {
            "operational": "operational/components.forth",
            "relational": "formal/RuntimeRelations.tla",
            "causal": "causal/components.petri",
            "assembled_formal": "formal/AssembledRuntime.tla",
            "representations": ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
        },
        "triangulated_assurance": assurance,
        "post_build_assurance": {
            "required": True,
            "final_theorem": "AssembledRuntimePreservesExactSeedBoundary",
            "seed_relations": ["PreserveUnknown", "PreserveAllow", "PreserveBlock"],
        },
    }
    (output / "RELEASE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-profiles-root", type=Path, required=True)
    parser.add_argument("--verify-determinism", action="store_true")
    args = parser.parse_args(argv)

    DIST.mkdir(parents=True, exist_ok=True)
    release_dir = DIST / RELEASE_NAME
    profiles_dir = DIST / f"{RELEASE_NAME}-profiles"
    build_tree(release_dir)
    release_digest = tree_digest(release_dir)
    build_release_profiles(args.seed_profiles_root, profiles_dir)
    profile_digest = tree_digest(profiles_dir)

    if args.verify_determinism:
        with tempfile.TemporaryDirectory(prefix="aset-runtime-alpha4-") as tmp:
            tmp_root = Path(tmp)
            first = tmp_root / "first"
            second = tmp_root / "second"
            first_profiles = tmp_root / "first-profiles"
            second_profiles = tmp_root / "second-profiles"
            build_tree(first)
            build_tree(second)
            if tree_digest(first) != tree_digest(second):
                print("ALPHA4_RUNTIME_RELEASE_DETERMINISM=FAIL")
                return 1
            build_release_profiles(args.seed_profiles_root, first_profiles)
            build_release_profiles(args.seed_profiles_root, second_profiles)
            if tree_digest(first_profiles) != tree_digest(second_profiles):
                print("ALPHA4_RUNTIME_RELEASE_PROFILE_DETERMINISM=FAIL")
                return 1
        print("ALPHA4_RUNTIME_RELEASE_DETERMINISM=PASS")
        print("ALPHA4_RUNTIME_RELEASE_PROFILE_DETERMINISM=PASS")

    archive = DIST / f"{RELEASE_NAME}.zip"
    profiles_archive = DIST / f"{RELEASE_NAME}-profiles.zip"
    zip_tree(release_dir, archive, RELEASE_NAME)
    zip_tree(profiles_dir, profiles_archive, f"{RELEASE_NAME}-profiles")
    print(f"ALPHA4_RUNTIME_RELEASE_TREE_DIGEST={release_digest}")
    print(f"ALPHA4_RUNTIME_RELEASE_ARCHIVE={archive.relative_to(ROOT)}")
    print(f"ALPHA4_RUNTIME_RELEASE_ARCHIVE_SHA256={sha256(archive)}")
    print(f"ALPHA4_RUNTIME_RELEASE_PROFILE_TREE_DIGEST={profile_digest}")
    print(f"ALPHA4_RUNTIME_RELEASE_PROFILE_ARCHIVE={profiles_archive.relative_to(ROOT)}")
    print(f"ALPHA4_RUNTIME_RELEASE_PROFILE_ARCHIVE_SHA256={sha256(profiles_archive)}")
    print("ALPHA4_RUNTIME_RELEASE_ENGLISH_EXTENSION=PASS")
    print("ALPHA4_RUNTIME_RELEASE_PYTHON_EXTENSION=EXACT_SEED_BASE")
    print("ALPHA4_RUNTIME_RELEASE_BUILD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
