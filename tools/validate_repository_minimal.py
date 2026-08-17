from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ROOT_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    "CITATION.cff",
    "LICENSE",
    "NOTICE",
    "README.md",
    "pyproject.toml",
    "requirements-ci.txt",
}
ALLOWED_ROOT_DIRS = {".github", "history", "runtime", "tests", "tools", "upstream"}
ALLOWED_ACTIVE_PATHS = {
    ".editorconfig",
    ".gitattributes",
    ".github/workflows/verify.yml",
    ".gitignore",
    "CITATION.cff",
    "LICENSE",
    "NOTICE",
    "README.md",
    "history/REFERENCES.aset",
    "pyproject.toml",
    "requirements-ci.txt",
    "runtime/alpha4/RUNTIME.aset",
    "runtime/alpha4/causal/components.petri",
    "runtime/alpha4/formal/OperationalRelationalPairingProofs.tla",
    "runtime/alpha4/formal/RestrictedOperationalSemantics.tla",
    "runtime/alpha4/formal/RuntimeRelations.tla",
    "runtime/alpha4/formal/SeedBoundaryProofs.tla",
    "runtime/alpha4/operational/components.forth",
    "tests/test_alpha4_runtime.py",
    "tests/test_alpha4_runtime_release_architecture.py",
    "tests/test_alpha4_runtime_three_way_assurance.py",
    "tests/test_repository_minimal.py",
    "tools/__init__.py",
    "tools/alpha4_runtime_assurance.py",
    "tools/alpha4_runtime_causal_expression.py",
    "tools/alpha4_runtime_expression_airgap.py",
    "tools/alpha4_runtime_gate.py",
    "tools/alpha4_runtime_manifest.py",
    "tools/alpha4_runtime_paired_expression.py",
    "tools/alpha4_runtime_relational_expression.py",
    "tools/alpha4_runtime_public_release_audit.py",
    "tools/alpha4_runtime_release_admission.py",
    "tools/alpha4_runtime_release_gate.py",
    "tools/alpha4_runtime_release_profiles.py",
    "tools/alpha4_runtime_seed_extension.py",
    "tools/alpha4_runtime_triangulated_expression.py",
    "tools/build_alpha4_runtime_release.py",
    "tools/run_alpha4_runtime_release_tlaps.py",
    "tools/run_alpha4_runtime_tlaps.py",
    "tools/validate_alpha4_runtime.py",
    "tools/validate_repository_minimal.py",
    "upstream/ASET_SEED_ALPHA4_BINDING.aset",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def git_paths(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", *args, "-z"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(result.returncode == 0, f"git surface query failed: {' '.join(args)}")
    return {item.decode("utf-8") for item in result.stdout.split(b"\0") if item}


def repository_paths() -> set[str]:
    paths = git_paths("ls-files", "--cached", "--others", "--exclude-standard")
    deleted = git_paths("diff", "--name-only", "--diff-filter=D")
    deleted |= git_paths("diff", "--cached", "--name-only", "--diff-filter=D")
    return paths - deleted


def relative_files(path: Path) -> set[str]:
    prefix = path.relative_to(ROOT).as_posix().rstrip("/") + "/"
    return {item for item in repository_paths() if item.startswith(prefix)}


def validate_root_surface() -> None:
    paths = repository_paths()
    files = {path for path in paths if "/" not in path}
    dirs = {path.split("/", 1)[0] for path in paths if "/" in path}
    require(
        files == ALLOWED_ROOT_FILES,
        f"root file surface drift: {sorted(files ^ ALLOWED_ROOT_FILES)}",
    )
    require(
        dirs == ALLOWED_ROOT_DIRS,
        f"root directory surface drift: {sorted(dirs ^ ALLOWED_ROOT_DIRS)}",
    )
    require(
        paths == ALLOWED_ACTIVE_PATHS,
        f"active repository surface drift: {sorted(paths ^ ALLOWED_ACTIVE_PATHS)}",
    )


def validate_single_readme() -> None:
    readmes = sorted(
        path for path in repository_paths() if Path(path).name.lower().startswith("readme")
    )
    require(readmes == ["README.md"], f"README surface must be singular: {readmes}")


def validate_active_runtime_line() -> None:
    children = {path.split("/", 2)[1] for path in repository_paths() if path.startswith("runtime/")}
    require(children == {"alpha4"}, "Runtime must contain exactly one active Alpha4 line")
    subject = (ROOT / "runtime/alpha4/RUNTIME.aset").read_text(encoding="utf-8")
    require(
        "PREDECESSOR-COMPATIBILITY NONE" in subject,
        "Runtime predecessor compatibility boundary drift",
    )
    require("SEMANTIC-PRECEDENCE NONE" in subject, "Runtime semantic precedence drift")


def validate_history_surface() -> None:
    history = (ROOT / "history/REFERENCES.aset").read_text(encoding="utf-8")
    require("ASET-HISTORY 1" in history, "history header missing")
    state_lines = [line for line in history.splitlines() if line.startswith("STATE ")]
    require(
        len(state_lines) == 1 and state_lines[0].endswith(" HISTORICAL"),
        "predecessor history reference missing",
    )
    require("ACTIVE-SEMANTICS FALSE" in history, "history active-semantics boundary missing")
    paths = repository_paths()
    for prefix in ("extension/", "assurance/", "docs/", "reference/", "standards/"):
        require(
            not any(path.startswith(prefix) for path in paths),
            f"legacy active surface present: {prefix}",
        )


def validate_upstream_surface() -> None:
    files = relative_files(ROOT / "upstream")
    require(
        files == {"upstream/ASET_SEED_ALPHA4_BINDING.aset"},
        f"upstream surface drift: {sorted(files)}",
    )


def validate_verification_surface() -> None:
    workflows = relative_files(ROOT / ".github/workflows")
    require(
        workflows == {".github/workflows/verify.yml"},
        f"workflow surface drift: {sorted(workflows)}",
    )


def validate_attribution() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    require(readme.startswith("# ASET Runtime\n"), "README Runtime identity drift")
    normalized_readme = " ".join(readme.split())
    require(
        "bounded execution lifecycle extension for ASET Seed 0.4alpha" in normalized_readme,
        "README Runtime role drift",
    )
    require(
        "Execution may produce material. Recognition remains local to Seed." in readme,
        "README recognition boundary drift",
    )

    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    require(notice.startswith("ASET Runtime\n"), "NOTICE Runtime identity drift")
    require("Copyright 2026 Dzmitry Prychyna" in notice, "copyright notice drift")
    require("Attractor Set" in notice, "public author identity missing")
    require(
        "Original author and copyright holder: Dzmitry Prychyna." in notice,
        "original authorship notice missing",
    )
    require(
        "Licensed under the Apache License, Version 2.0." in notice,
        "NOTICE license declaration missing",
    )

    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    for required in (
        'title: "ASET Runtime"',
        'version: "0.1.0-alpha.4"',
        'family-names: "Prychyna"',
        'given-names: "Dzmitry"',
        'alias: "Attractor Set"',
        'repository-code: "https://github.com/attractor-set/aset-runtime"',
        "license: Apache-2.0",
    ):
        require(required in citation, f"citation attribution drift: {required}")

    license_bytes = (ROOT / "LICENSE").read_bytes()
    license_sha256 = hashlib.sha256(license_bytes).hexdigest()
    require(
        license_sha256 == "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
        "Apache-2.0 license byte identity drift",
    )


def main() -> int:
    validate_root_surface()
    validate_single_readme()
    validate_active_runtime_line()
    validate_history_surface()
    validate_upstream_surface()
    validate_verification_surface()
    validate_attribution()
    print("REPOSITORY_ACTIVE_SURFACE=MINIMAL")
    print("REPOSITORY_LEGACY_SEMANTIC_SURFACE=ABSENT")
    print("REPOSITORY_HISTORICAL_EXECUTABLE_SURFACE=ABSENT")
    print("REPOSITORY_HISTORY_REFERENCES=PASS")
    print("REPOSITORY_COPYRIGHT_NOTICE=PASS")
    print("REPOSITORY_SINGLE_README=PASS")
    print("REPOSITORY_SINGLE_ACTIVE_RUNTIME_LINE=ALPHA4")
    print("REPOSITORY_SINGLE_VERIFICATION_WORKFLOW=PASS")
    print("ASET_RUNTIME_REPOSITORY_MINIMAL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
