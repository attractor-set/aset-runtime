from __future__ import annotations

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
ALLOWED_ROOT_DIRS = {
    ".github",
    "history",
    "tests",
    "theory",
    "tools",
    "upstream",
    "worker",
}
FORBIDDEN_ROOT_DIRS = {"assurance", "docs", "extension", "reference", "standards"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def repository_paths() -> set[str]:
    proc = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = {p for p in proc.stdout.decode().split("\0") if p}
    deleted = subprocess.run(
        ["git", "ls-files", "--deleted", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths.difference_update(p for p in deleted.stdout.decode().split("\0") if p)
    return paths


def validate_root_surface() -> None:
    paths = repository_paths()
    root_files = {p for p in paths if "/" not in p}
    root_dirs = {p.split("/", 1)[0] for p in paths if "/" in p}
    file_drift = sorted(root_files ^ ALLOWED_ROOT_FILES)
    require(root_files == ALLOWED_ROOT_FILES, f"root file surface drift: {file_drift}")
    dir_drift = sorted(root_dirs ^ ALLOWED_ROOT_DIRS)
    require(root_dirs == ALLOWED_ROOT_DIRS, f"root directory surface drift: {dir_drift}")
    require(not (root_dirs & FORBIDDEN_ROOT_DIRS), "legacy root surface returned")


def validate_single_readme() -> None:
    readmes = sorted(p for p in repository_paths() if Path(p).name.startswith("README"))
    require(readmes == ["README.md"], f"README surface drift: {readmes}")


def validate_single_worker_line() -> None:
    children = {p.split("/", 2)[1] for p in repository_paths() if p.startswith("worker/")}
    require(children == {"alpha4"}, f"Worker active-line surface drift: {sorted(children)}")
    require("worker/alpha4/WORKER.aset" in repository_paths(), "Worker Alpha4 subject missing")


def validate_theory_surface() -> None:
    theory = sorted(p for p in repository_paths() if p.startswith("theory/"))
    expected = [
        "theory/worker-lifecycle/formal/WorkerLifecycle.tla",
        "theory/worker-lifecycle/formal/WorkerLifecycleProofs.tla",
    ]
    require(theory == expected, f"Worker theory surface drift: {theory}")
    require(not any(p.endswith(".json") for p in theory), "checked-in JSON leaked into theory")


def validate_workflows() -> None:
    workflows = sorted(p for p in repository_paths() if p.startswith(".github/workflows/"))
    require(workflows == [".github/workflows/verify.yml"], f"workflow surface drift: {workflows}")


def main() -> int:
    validate_root_surface()
    validate_single_readme()
    validate_single_worker_line()
    validate_theory_surface()
    validate_workflows()
    print("WORKER_REPOSITORY_ACTIVE_SURFACE=MINIMAL")
    print("WORKER_REPOSITORY_LEGACY_CANON_SURFACE=ABSENT")
    print("WORKER_REPOSITORY_SINGLE_README=PASS")
    print("WORKER_REPOSITORY_SINGLE_ACTIVE_LINE=ALPHA4")
    print("WORKER_REPOSITORY_SINGLE_VERIFICATION_WORKFLOW=PASS")
    print("ASET_WORKER_REPOSITORY_MINIMAL=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
