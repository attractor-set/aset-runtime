from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

from tools.validate_repository_minimal import repository_paths

ROOT = Path(__file__).resolve().parents[1]
WORKER = ROOT / "worker/alpha4/WORKER.aset"
BINDING = ROOT / "upstream/ASET_SEED_ALPHA4_BINDING.aset"
HISTORY = ROOT / "history/REFERENCES.aset"
CITATION = ROOT / "CITATION.cff"

EXPECTED_SEED_COMMIT = "08bc0c4dfb5c158fe4641c93a87c7c5914cb2d2c"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_binding() -> dict[str, str]:
    value = lines(BINDING)
    require(
        value[0] == "ASET-SEED-BINDING 1 ASET-SEED-0.4-ALPHA CONTENT-ADDRESSED",
        "Seed Alpha4 binding header mismatch",
    )
    require(f"COMMIT {EXPECTED_SEED_COMMIT}" in value, "Seed Alpha4 commit pin mismatch")
    sources: dict[str, str] = {}
    for line in value:
        if line.startswith("SOURCE "):
            _, path, digest = line.split()
            require(path not in sources, f"duplicate Seed source: {path}")
            require(re.fullmatch(r"sha256:[0-9a-f]{64}", digest) is not None, "bad digest")
            sources[path] = digest
    require(len(sources) == 10, "Seed Alpha4 binding must cover exactly 10 active sources")
    required = (
        "REQUIRED-SEED-STATE seed/alpha4/formal/ComponentRelations.tla StateType",
        "REQUIRED-SEED-EFFECT seed/alpha4/formal/ComponentRelations.tla EffectPermitted",
        "WORKER-INHERITANCE START-WORK SEED-STATE-STUTTER",
        "WORKER-INHERITANCE END-WORK SEED-STATE-STUTTER",
    )
    for declaration in required:
        require(declaration in value, f"Seed inheritance declaration missing: {declaration}")
    return sources


def validate_seed_root(seed_root: Path, sources: dict[str, str]) -> None:
    for relative, expected in sources.items():
        path = seed_root / relative
        require(path.is_file(), f"bound Seed source missing: {relative}")
        require(sha256(path) == expected, f"bound Seed source digest mismatch: {relative}")
    subject = (seed_root / "seed/alpha4/SEED.aset").read_text(encoding="utf-8")
    require(
        subject.startswith("ASET-SEED 1 ASET-SEED-0.4-ALPHA 0.4alpha\n"),
        "Seed subject mismatch",
    )


def validate_active_selection() -> None:
    children = {p.split("/", 2)[1] for p in repository_paths() if p.startswith("worker/")}
    require(children == {"alpha4"}, f"Worker active-line surface drift: {sorted(children)}")


def validate_worker_surface() -> None:
    worker = lines(WORKER)
    required = (
        "ASET-WORKER 1 ASET-WORKER-ALPHA4 alpha4",
        "SEMANTIC-PRECEDENCE NONE",
        "ALPHA2-COMPATIBILITY NONE",
        "UPSTREAM-SUBJECT ASET-SEED-0.4-ALPHA",
        "STATE STARTED SET-OF-EXACT-STARTED-WORK-BINDINGS",
        "STATE TERMINALS SET-OF-EXACT-TERMINAL-WORK-BINDINGS",
        "TRANSITION START-WORK",
        "TRANSITION END-WORK",
        "SEED-PROJECTION START-WORK STUTTER",
        "SEED-PROJECTION END-WORK STUTTER",
        "AUTHORITY-CREATED-BY-WORKER NEVER",
        "EFFECT-PERMITTED-BY-WORKER NEVER",
        "TERMINAL-RELATION RESULT-XOR-NO_RESULT",
    )
    for declaration in required:
        require(declaration in worker, f"Worker Alpha4 declaration missing: {declaration}")
    forth = (ROOT / "worker/alpha4/operational/components.forth").read_text(encoding="utf-8")
    require(forth.count(";") == 12, "Worker Alpha4 operational expression must have 12 words")
    require(
        "LOCAL-ALLOW!" not in forth and "LOCAL-BLOCK!" not in forth,
        "Seed recognition leaked into Worker",
    )


def validate_history() -> None:
    history = HISTORY.read_text(encoding="utf-8")
    required = (
        "STATE WORKER-0.1.0-ALPHA.1",
        "IDENTITY WORKER-0.1.0-ALPHA.1 CANON-ID ASET-WORKER-CANON-0.1-ALPHA2",
        "PROOF WORKER-0.1.0-ALPHA.1 SEED-STUTTER 19 MECHANICALLY_PROVED",
        "PROOF WORKER-0.1.0-ALPHA.1 LIFECYCLE-SAFETY 52 MECHANICALLY_PROVED",
        "RELATION ASET-WORKER-ALPHA4 HISTORICAL_PREDECESSOR WORKER-0.1.0-ALPHA.1",
        "COMPATIBILITY ASET-WORKER-ALPHA4 WORKER-0.1.0-ALPHA.1 NONE",
    )
    for marker in required:
        require(marker in history, f"history marker missing: {marker}")


def validate_identity() -> None:
    citation = CITATION.read_text(encoding="utf-8")
    require('version: "0.1.0-alpha.4"' in citation, "Worker citation version mismatch")
    require('family-names: "Prychyna"' in citation, "Worker citation author mismatch")


def validate_all(seed_root: Path | None = None) -> None:
    validate_active_selection()
    validate_worker_surface()
    validate_history()
    validate_identity()
    sources = parse_binding()
    print("ASET_WORKER_CURRENT_REPRESENTATION=ASET-WORKER-ALPHA4")
    print("ASET_WORKER_CURRENT_PROJECT_VERSION=0.1.0-alpha.4")
    print("ASET_WORKER_CURRENT_SELECTION=UNIQUE_ACTIVE_WORKER_LINE")
    print("ASET_WORKER_ALPHA2_PREDECESSOR=HISTORICAL_REFERENCE")
    print("ASET_WORKER_ALPHA2_COMPATIBILITY_INHERITED=false")
    if seed_root is not None:
        validate_seed_root(seed_root.resolve(), sources)
        print("ALPHA4_WORKER_SEED_CONTENT_BINDING=PASS")
    else:
        print("ALPHA4_WORKER_SEED_CONTENT_BINDING=DECLARED")
    print("ALPHA4_WORKER_STATE_FIELDS=2")
    print("ALPHA4_WORKER_TRANSITIONS=START-WORK,END-WORK")
    print("ALPHA4_WORKER_SEED_PROJECTION=STUTTER")
    print("ALPHA4_WORKER_VALIDATION=PASS")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-root", type=Path)
    args = parser.parse_args()
    validate_all(args.seed_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
