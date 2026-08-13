from __future__ import annotations

from pathlib import Path

from tools.validate_repository_minimal import (
    repository_paths,
    validate_root_surface,
    validate_single_readme,
    validate_single_worker_line,
    validate_theory_surface,
    validate_workflows,
)

ROOT = Path(__file__).resolve().parents[1]


def test_repository_surface_is_minimal() -> None:
    validate_root_surface()
    validate_single_readme()
    validate_single_worker_line()
    validate_theory_surface()
    validate_workflows()


def test_legacy_canon_surfaces_are_absent() -> None:
    paths = repository_paths()
    for prefix in ("assurance/", "docs/", "extension/", "reference/", "standards/"):
        assert not any(path.startswith(prefix) for path in paths)


def test_theory_has_no_checked_in_json() -> None:
    assert not any(
        path.startswith("theory/") and path.endswith(".json") for path in repository_paths()
    )


def test_worker_has_no_current_pointer() -> None:
    assert "worker/CURRENT.aset" not in repository_paths()


def test_only_one_readme_exists() -> None:
    readmes = sorted(path for path in repository_paths() if Path(path).name.startswith("README"))
    assert readmes == ["README.md"]
