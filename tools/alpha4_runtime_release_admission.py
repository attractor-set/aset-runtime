from __future__ import annotations

import argparse
import json
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from tools.alpha4_runtime_release_profiles import manifest_records, parse_english
from tools.alpha4_runtime_seed_extension import (
    check_seed_companion_bases,
    check_seed_extension,
    parse_seed_binding,
    sha256,
    tree_digest,
)

ROOT = Path(__file__).resolve().parents[1]


class AdmissionError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionError(message)


def archive_tree_digest(archive: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="aset-runtime-archive-") as temp_dir:
        root = Path(temp_dir)
        with zipfile.ZipFile(archive) as value:
            value.extractall(root)
        children = [path for path in root.iterdir() if path.is_dir()]
        require(len(children) == 1, f"archive root surface drift: {archive.name}")
        return tree_digest(children[0])


def load_json(path: Path, document_type: str) -> dict[str, Any]:
    require(path.is_file(), f"required evidence missing: {path.name}")
    value = json.loads(path.read_text(encoding="utf-8"))
    require(value.get("document_type") == document_type, f"unexpected evidence type: {path.name}")
    require(value.get("status") == "PASS", f"evidence not PASS: {path.name}")
    return value


def check_release_admission(
    *,
    seed_root: Path,
    seed_release_root: Path,
    seed_profiles_root: Path,
    release_root: Path,
    profiles_root: Path,
    release_archive: Path,
    profiles_archive: Path,
    tlaps_evidence_path: Path,
    airgap_evidence_path: Path,
) -> dict[str, Any]:
    binding = parse_seed_binding()
    extension = check_seed_extension(seed_root)
    companions = check_seed_companion_bases(seed_profiles_root)
    require(extension["status"] == "PASS", "Runtime Seed extension assurance failed")
    require(companions["status"] == "PASS", "Runtime Seed companion base assurance failed")
    require(
        tree_digest(seed_release_root) == binding.release_tree,
        "exact Seed release tree mismatch",
    )

    release_manifest = json.loads(
        (release_root / "RELEASE_MANIFEST.json").read_text(encoding="utf-8")
    )
    profile_manifest = json.loads(
        (profiles_root / "RELEASE_PROFILE_MANIFEST.json").read_text(encoding="utf-8")
    )
    require(
        release_manifest.get("document_type") == "aset-runtime-alpha4-release-materialization",
        "Runtime release manifest drift",
    )
    require(
        profile_manifest.get("document_type")
        == "aset-runtime-alpha4-release-companion-materialization",
        "Runtime profile manifest drift",
    )
    release_tree = tree_digest(release_root)
    profile_tree = tree_digest(profiles_root)

    tlaps = load_json(tlaps_evidence_path, "aset-runtime-release-assembled-tlaps-evidence")
    airgap = load_json(airgap_evidence_path, "aset-runtime-python-airgap-evidence")
    require(
        tlaps["release_binding"]["tree_digest"] == release_tree,
        "post-build TLAPS not bound to exact Runtime release tree",
    )
    require(
        tlaps["seed_binding"]["release_tree_digest"] == binding.release_tree,
        "post-build TLAPS not bound to exact Seed release tree",
    )
    require(
        airgap["profile_tree_digest"] == profile_tree,
        "Python air-gap not bound to exact Runtime profile tree",
    )
    require(airgap["seed_base"]["status"] == "EXACT", "Python air-gap Seed base not exact")
    require(airgap["seed_projection"] == "STUTTER", "Python air-gap Seed projection drift")
    cases = airgap.get("cases")
    require(
        isinstance(cases, dict)
        and cases.get("total") == 7260
        and cases.get("identity_sensitivity") == 5
        and cases.get("grand_total") == 7265,
        "Runtime Python air-gap sensitivity coverage drift",
    )
    require(
        airgap.get("semantic_source_runtime_dependency") == "NONE"
        and airgap.get("generator_runtime_dependency") == "NONE"
        and airgap.get("companion_import_surface") == "RESTRICTED"
        and airgap.get("companion_file_access") == "MATERIALIZED_PROFILE_TREE_READ_ONLY",
        "Runtime Python air-gap independence boundary drift",
    )

    seed_english = profiles_root / "base/seed/en/Seed.md"
    seed_python = profiles_root / "base/seed/python/aset_seed_alpha4.py"
    require(
        sha256(seed_english) == binding.companions["ENGLISH"][1],
        "Runtime English Seed base drift",
    )
    require(
        sha256(seed_python) == binding.companions["PYTHON"][1],
        "Runtime Python Seed base drift",
    )
    require(
        parse_english(profiles_root / "en/Runtime.md") == manifest_records(ROOT),
        "Runtime English companion projection drift",
    )

    require(
        archive_tree_digest(release_archive) == release_tree,
        "Runtime release archive binding mismatch",
    )
    require(
        archive_tree_digest(profiles_archive) == profile_tree,
        "Runtime profile archive binding mismatch",
    )

    return {
        "document_type": "aset-runtime-release-admission-certificate",
        "schema_version": 1,
        "subject_id": "ASET-RUNTIME-ALPHA4",
        "version": "0.1.0-alpha.4",
        "semantic_precedence": "NONE",
        "assurance_representations": ["OPERATIONAL", "RELATIONAL", "CAUSAL"],
        "seed_bindings": {"operational": "PASS", "relational": "PASS", "causal": "PASS"},
        "seed_redefinition": "ABSENT",
        "seed_projection": "STUTTER",
        "post_build_tlaps": {
            "status": "PASS",
            "final_theorem": tlaps["proof"]["final_theorem"],
            "obligations_proved": tlaps["proof"]["obligations_proved"],
        },
        "english_seed_base": "EXACT",
        "python_seed_base": "EXACT",
        "python_airgap": {
            "status": "PASS",
            "structural_cases": airgap["cases"]["total"],
            "identity_sensitivity_cases": airgap["cases"]["identity_sensitivity"],
            "grand_total_cases": airgap["cases"]["grand_total"],
            "runtime_isolation": "PASS",
        },
        "release": {
            "tree_digest": release_tree,
            "archive_sha256": sha256(release_archive),
        },
        "profiles": {
            "tree_digest": profile_tree,
            "archive_sha256": sha256(profiles_archive),
        },
        "archive_binding": "EXACT",
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-root", type=Path, required=True)
    parser.add_argument("--seed-release-root", type=Path, required=True)
    parser.add_argument("--seed-profiles-root", type=Path, required=True)
    parser.add_argument("--release-root", type=Path, required=True)
    parser.add_argument("--profiles-root", type=Path, required=True)
    parser.add_argument("--release-archive", type=Path, required=True)
    parser.add_argument("--profiles-archive", type=Path, required=True)
    parser.add_argument(
        "--tlaps-evidence",
        type=Path,
        default=ROOT / "dist/runtime-release-assembled-tlaps-evidence.json",
    )
    parser.add_argument(
        "--airgap-evidence",
        type=Path,
        default=ROOT / "dist/runtime-python-airgap-evidence.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist/runtime-release-admission-certificate.json",
    )
    args = parser.parse_args()
    try:
        certificate = check_release_admission(
            seed_root=args.seed_root,
            seed_release_root=args.seed_release_root,
            seed_profiles_root=args.seed_profiles_root,
            release_root=args.release_root,
            profiles_root=args.profiles_root,
            release_archive=args.release_archive,
            profiles_archive=args.profiles_archive,
            tlaps_evidence_path=args.tlaps_evidence,
            airgap_evidence_path=args.airgap_evidence,
        )
        output = args.output if args.output.is_absolute() else ROOT / args.output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_SEED_BINDINGS=3/3 PASS")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_SEED_REDEFINITION=ABSENT")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_SEED_PROJECTION=STUTTER")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_POST_BUILD_TLAPS=PASS")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_ENGLISH_SEED_BASE=EXACT")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_PYTHON_SEED_BASE=EXACT")
        cases = certificate["python_airgap"]["structural_cases"]
        print(f"ALPHA4_RUNTIME_RELEASE_ADMISSION_PYTHON_AIRGAP={cases}/{cases} PASS")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_PYTHON_AIRGAP_IDENTITY_SENSITIVITY=5/5 PASS")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_PYTHON_AIRGAP_GRAND_TOTAL=7265/7265 PASS")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_PYTHON_RUNTIME_ISOLATION=PASS")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_ARCHIVE_BINDING=EXACT")
        print("ALPHA4_RUNTIME_PUBLIC_ASSURANCE_REPRESENTATIONS=OPERATIONAL,RELATIONAL,CAUSAL")
        print("ALPHA4_RUNTIME_PUBLIC_POST_BUILD_FORMAL_ASSURANCE=PASS")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_CERTIFICATE=PASS")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile, AdmissionError) as error:
        print(f"ALPHA4_RUNTIME_RELEASE_ADMISSION_ERROR={error}")
        print("ALPHA4_RUNTIME_RELEASE_ADMISSION_CERTIFICATE=FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
