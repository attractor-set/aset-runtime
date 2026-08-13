from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from tools.validate_alpha4_worker import parse_binding, validate_seed_root

ROOT = Path(__file__).resolve().parents[1]
WORKER_FORMAL = ROOT / "worker/alpha4/formal"
LIFECYCLE_FORMAL = ROOT / "theory/worker-lifecycle/formal"

PROOF_MODULES = (
    "OperationalRelationalPairingProofs.tla",
    "WorkerSafetyProofs.tla",
    "SeedInheritanceProofs.tla",
    "WorkerLifecycleProofs.tla",
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def tlapm_version(tlapm: Path) -> str:
    result = subprocess.run([str(tlapm), "--version"], check=True, capture_output=True, text=True)
    return result.stdout.strip() or result.stderr.strip()


def stage_sources(stage: Path, seed_root: Path) -> None:
    for source in WORKER_FORMAL.glob("*.tla"):
        shutil.copy2(source, stage / source.name)
    for source in LIFECYCLE_FORMAL.glob("*.tla"):
        shutil.copy2(source, stage / source.name)
    seed_sources = (
        "seed/alpha4/formal/ComponentRelations.tla",
        "theory/local-recognition/formal/LocalRecognitionAlgebra.tla",
        "theory/local-recognition/formal/RecognitionCardinality.tla",
    )
    for relative in seed_sources:
        source = seed_root / relative
        require(source.is_file(), f"Seed proof dependency missing: {relative}")
        shutil.copy2(source, stage / source.name)


def count_obligations(output: str) -> int:
    match = re.search(r"All\s+(\d+)\s+obligations\s+proved", output)
    if match is None:
        return 0
    return int(match.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tlapm", type=Path)
    parser.add_argument("--seed-root", type=Path, required=True)
    args = parser.parse_args()

    tlapm = args.tlapm or (Path(os.environ["TLAPM_BIN"]) if "TLAPM_BIN" in os.environ else None)
    require(tlapm is not None and tlapm.is_file(), "TLAPM binary is required")
    seed_root = args.seed_root.resolve()
    validate_seed_root(seed_root, parse_binding())

    total = 0
    with tempfile.TemporaryDirectory(prefix="aset-worker-alpha4-tlaps-") as temp:
        stage = Path(temp)
        stage_sources(stage, seed_root)
        for module in PROOF_MODULES:
            result = subprocess.run(
                [str(tlapm), module],
                cwd=stage,
                check=False,
                capture_output=True,
                text=True,
            )
            output = result.stdout + result.stderr
            print(output, end="")
            require(result.returncode == 0, f"TLAPS failed: {module}")
            obligations = count_obligations(output)
            require(obligations > 0, f"TLAPS obligation count unavailable: {module}")
            total += obligations
            print(f"ALPHA4_WORKER_TLAPS_MODULE={module} OBLIGATIONS={obligations} PASS")

    print(f"ALPHA4_WORKER_TLAPM_VERSION={tlapm_version(tlapm)}")
    print(f"ALPHA4_WORKER_TLAPS_OBLIGATIONS={total}")
    print("ALPHA4_WORKER_TLAPS=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
