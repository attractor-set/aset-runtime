from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT = "ASET Runtime"
REPRESENTATION_ID = "0.1.0-alpha.4"
SUBJECT_ID = "ASET-RUNTIME-ALPHA4"
REPOSITORY = "https://github.com/attractor-set/aset-runtime"
FINAL_THEOREM = "AssembledRuntimePreservesExactSeedBoundary"
LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"


class PublicReleaseAuditError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PublicReleaseAuditError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def check_public_root(root: Path = ROOT) -> dict[str, str]:
    readme = (root / "README.md").read_text(encoding="utf-8")
    notice = (root / "NOTICE").read_text(encoding="utf-8")
    citation = (root / "CITATION.cff").read_text(encoding="utf-8")
    license_bytes = (root / "LICENSE").read_bytes()

    require(readme.startswith("# ASET Runtime\n"), "README project identity mismatch")
    normalized_readme = " ".join(readme.split())
    require(
        "bounded execution lifecycle extension for ASET Seed 0.4alpha" in normalized_readme,
        "README Runtime role mismatch",
    )
    require(
        "Execution may produce material. Recognition remains local to Seed." in readme,
        "README recognition boundary missing",
    )
    require(
        "operational, relational, and causal" in readme,
        "README assurance representation set missing",
    )
    require("semantic precedence `NONE`" in readme, "README semantic precedence missing")

    require(notice.startswith("ASET Runtime\n"), "NOTICE project identity mismatch")
    require("Copyright 2026 Dzmitry Prychyna" in notice, "NOTICE copyright holder missing")
    require("publicly known as Attractor Set" in notice, "NOTICE public author identity missing")
    require(
        "Original author and copyright holder: Dzmitry Prychyna." in notice,
        "NOTICE original authorship missing",
    )
    require(
        "Licensed under the Apache License, Version 2.0." in notice,
        "NOTICE license declaration missing",
    )

    for expected in (
        'title: "ASET Runtime"',
        'version: "0.1.0-alpha.4"',
        'family-names: "Prychyna"',
        'given-names: "Dzmitry"',
        'alias: "Attractor Set"',
        f'repository-code: "{REPOSITORY}"',
        "license: Apache-2.0",
    ):
        require(expected in citation, f"CITATION identity drift: {expected}")
    require(
        hashlib.sha256(license_bytes).hexdigest() == LICENSE_SHA256,
        "Apache-2.0 LICENSE byte identity drift",
    )

    return {
        "project": PROJECT,
        "representation_id": REPRESENTATION_ID,
        "subject_id": SUBJECT_ID,
        "repository": REPOSITORY,
    }


def check_public_release(
    root: Path,
    release_root: Path,
    profiles_root: Path,
    certificate_path: Path,
) -> dict[str, object]:
    check_public_root(root)

    require(
        (release_root / "NOTICE").read_bytes() == (root / "NOTICE").read_bytes(),
        "release NOTICE is not exact repository NOTICE",
    )
    require(
        (release_root / "LICENSE").read_bytes() == (root / "LICENSE").read_bytes(),
        "release LICENSE is not exact repository LICENSE",
    )

    release = load_json(release_root / "RELEASE_MANIFEST.json")
    profiles = load_json(profiles_root / "RELEASE_PROFILE_MANIFEST.json")
    certificate = load_json(certificate_path)

    require(release.get("subject_id") == SUBJECT_ID, "release subject identity mismatch")
    require(release.get("version") == REPRESENTATION_ID, "release version mismatch")
    require(release.get("semantic_precedence") == "NONE", "release semantic precedence drift")
    architecture = release.get("architecture")
    require(isinstance(architecture, dict), "release architecture missing")
    require(
        architecture.get("representations") == ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
        "release assurance representation set mismatch",
    )
    seed_base = release.get("seed_base")
    require(isinstance(seed_base, dict), "release Seed base metadata missing")
    require(seed_base.get("semantic_redefinition") == "ABSENT", "release redefines Seed")
    require(seed_base.get("projection") == "PRESERVE-SEED-STATE", "release Seed projection drift")
    triangulated = release.get("triangulated_assurance")
    require(isinstance(triangulated, dict), "release triangulated assurance missing")
    require(triangulated.get("status") == "PASS", "release triangulated assurance not PASS")
    require(triangulated.get("semantic_delta") == "NONE", "release assurance semantic delta drift")

    require(profiles.get("subject_id") == SUBJECT_ID, "profile subject identity mismatch")
    require(profiles.get("version") == REPRESENTATION_ID, "profile version mismatch")
    require(profiles.get("semantic_precedence") == "NONE", "profile semantic precedence drift")
    require(
        profiles.get("seed_extension") == "PRESERVE-SEED-STATE",
        "profile Seed extension boundary drift",
    )
    companions = profiles.get("companions")
    require(isinstance(companions, dict), "profile companion set missing")
    require(
        companions.get("controlled_english") == "en/Runtime.md"
        and companions.get("python") == "python/aset_runtime_alpha4.py",
        "profile companion identity mismatch",
    )

    require(certificate.get("subject_id") == SUBJECT_ID, "certificate subject identity mismatch")
    require(certificate.get("version") == REPRESENTATION_ID, "certificate version mismatch")
    require(certificate.get("status") == "PASS", "release admission is not PASS")
    require(certificate.get("semantic_precedence") == "NONE", "certificate precedence drift")
    require(certificate.get("seed_redefinition") == "ABSENT", "certificate Seed redefinition drift")
    require(certificate.get("seed_projection") == "STUTTER", "certificate Seed projection drift")
    seed_bindings = certificate.get("seed_bindings")
    require(
        isinstance(seed_bindings, dict)
        and seed_bindings == {"operational": "PASS", "relational": "PASS", "causal": "PASS"},
        "certificate Seed binding set mismatch",
    )
    post_build = certificate.get("post_build_tlaps")
    require(isinstance(post_build, dict), "certificate post-build TLAPS missing")
    require(post_build.get("status") == "PASS", "certificate post-build TLAPS not PASS")
    require(post_build.get("final_theorem") == FINAL_THEOREM, "certificate final theorem drift")
    require(
        isinstance(post_build.get("obligations_proved"), int)
        and post_build["obligations_proved"] > 0,
        "certificate post-build obligation count invalid",
    )
    require(certificate.get("english_seed_base") == "EXACT", "English Seed base not exact")
    require(certificate.get("python_seed_base") == "EXACT", "Python Seed base not exact")
    python_airgap = certificate.get("python_airgap")
    require(
        isinstance(python_airgap, dict)
        and python_airgap.get("status") == "PASS"
        and isinstance(python_airgap.get("cases"), int)
        and python_airgap["cases"] > 0,
        "Python air-gap public evidence invalid",
    )
    require(certificate.get("archive_binding") == "EXACT", "archive binding is not exact")

    return {
        "document_type": "aset-runtime-public-release-audit",
        "schema_version": 1,
        "project": PROJECT,
        "representation_id": REPRESENTATION_ID,
        "subject_id": SUBJECT_ID,
        "repository": REPOSITORY,
        "assurance_representations": ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
        "semantic_precedence": "NONE",
        "seed_redefinition": "ABSENT",
        "seed_projection": "STUTTER",
        "post_build_formal_assurance": "PASS",
        "release_admission": "PASS",
        "status": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--release-root",
        type=Path,
        default=ROOT / "dist/ASET-Runtime-0.1.0-alpha.4",
    )
    parser.add_argument(
        "--profiles-root",
        type=Path,
        default=ROOT / "dist/ASET-Runtime-0.1.0-alpha.4-profiles",
    )
    parser.add_argument(
        "--certificate",
        type=Path,
        default=ROOT / "dist/runtime-release-admission-certificate.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/runtime-public-release-audit.json",
    )
    args = parser.parse_args(argv)

    try:
        evidence = check_public_release(
            ROOT, args.release_root, args.profiles_root, args.certificate
        )
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print("ALPHA4_RUNTIME_PUBLIC_IDENTITY=ASET_RUNTIME")
        print("ALPHA4_RUNTIME_PUBLIC_REPRESENTATION=0.1.0-alpha.4")
        print("ALPHA4_RUNTIME_PUBLIC_ASSURANCE_REPRESENTATIONS=OPERATIONAL,RELATIONAL,CAUSAL")
        print("ALPHA4_RUNTIME_PUBLIC_SEED_REDEFINITION=ABSENT")
        print("ALPHA4_RUNTIME_PUBLIC_SEED_PROJECTION=STUTTER")
        print("ALPHA4_RUNTIME_PUBLIC_POST_BUILD_FORMAL_ASSURANCE=PASS")
        print("ALPHA4_RUNTIME_PUBLIC_RELEASE_AUDIT=PASS")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, PublicReleaseAuditError) as error:
        print(f"ALPHA4_RUNTIME_PUBLIC_RELEASE_AUDIT_ERROR={error}")
        print("ALPHA4_RUNTIME_PUBLIC_RELEASE_AUDIT=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
