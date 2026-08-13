from __future__ import annotations

import argparse
import hashlib
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
ARCHIVE = DIST / "ASET-Worker-Repository-Snapshot.zip"


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return [line for line in result.stdout.splitlines() if line]


def build(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in tracked_files():
            source = ROOT / relative
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 & 0xFFFF) << 16
            archive.writestr(info, source.read_bytes())


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-determinism", action="store_true")
    args = parser.parse_args()
    build(ARCHIVE)
    if args.verify_determinism:
        second = DIST / ".worker-snapshot-rebuild.zip"
        build(second)
        if ARCHIVE.read_bytes() != second.read_bytes():
            raise RuntimeError("Worker repository snapshot is not deterministic")
        second.unlink()
        print("WORKER_REPOSITORY_SNAPSHOT_DETERMINISTIC_REBUILD=PASS")
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    print(f"WORKER_REPOSITORY_SNAPSHOT_SOURCE_COMMIT={source_commit}")
    print(f"WORKER_REPOSITORY_SNAPSHOT_ARCHIVE={ARCHIVE}")
    print(f"WORKER_REPOSITORY_SNAPSHOT_SHA256={digest(ARCHIVE)}")
    print("WORKER_REPOSITORY_SNAPSHOT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
