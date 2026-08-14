from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RELEASE_NAME = "ASET-Runtime-0.1.0-alpha.4"


def run(command: list[str]) -> int:
    result = subprocess.run(command, cwd=ROOT, check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-root", type=Path, required=True)
    parser.add_argument("--seed-release-root", type=Path, required=True)
    parser.add_argument("--seed-profiles-root", type=Path, required=True)
    parser.add_argument("--tlapm", required=True)
    args = parser.parse_args()
    python = sys.executable

    stages = [
        [python, "-m", "tools.alpha4_runtime_gate"],
        [
            python,
            "-m",
            "tools.alpha4_runtime_seed_extension",
            "--seed-root",
            str(args.seed_root),
            "--seed-profiles-root",
            str(args.seed_profiles_root),
        ],
        [python, "-m", "tools.run_alpha4_runtime_tlaps", "--tlapm", args.tlapm],
        [python, "-m", "pytest", "-q"],
    ]
    ruff = shutil.which("ruff")
    if ruff is not None:
        stages += [[ruff, "format", "--check", "."], [ruff, "check", "."]]
    for command in stages:
        if run(command):
            print("ALPHA4_RUNTIME_RELEASE_GATE=FAIL")
            return 1

    build = [
        python,
        "-m",
        "tools.build_alpha4_runtime_release",
        "--seed-profiles-root",
        str(args.seed_profiles_root),
        "--verify-determinism",
    ]
    if run(build):
        print("ALPHA4_RUNTIME_RELEASE_GATE=FAIL")
        return 1

    release_root = ROOT / "dist" / RELEASE_NAME
    profiles_root = ROOT / "dist" / f"{RELEASE_NAME}-profiles"
    release_archive = ROOT / "dist" / f"{RELEASE_NAME}.zip"
    profiles_archive = ROOT / "dist" / f"{RELEASE_NAME}-profiles.zip"

    post_build = [
        python,
        "-m",
        "tools.run_alpha4_runtime_release_tlaps",
        "--release-root",
        str(release_root),
        "--seed-release-root",
        str(args.seed_release_root),
        "--tlapm",
        args.tlapm,
    ]
    if run(post_build):
        print("ALPHA4_RUNTIME_RELEASE_GATE=FAIL")
        return 1

    airgap = [
        python,
        "-m",
        "tools.alpha4_runtime_expression_airgap",
        "--profiles-root",
        str(profiles_root),
    ]
    if run(airgap):
        print("ALPHA4_RUNTIME_RELEASE_GATE=FAIL")
        return 1

    admission = [
        python,
        "-m",
        "tools.alpha4_runtime_release_admission",
        "--seed-root",
        str(args.seed_root),
        "--seed-release-root",
        str(args.seed_release_root),
        "--seed-profiles-root",
        str(args.seed_profiles_root),
        "--release-root",
        str(release_root),
        "--profiles-root",
        str(profiles_root),
        "--release-archive",
        str(release_archive),
        "--profiles-archive",
        str(profiles_archive),
    ]
    if run(admission):
        print("ALPHA4_RUNTIME_RELEASE_GATE=FAIL")
        return 1

    print("ALPHA4_RUNTIME_RELEASE_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
