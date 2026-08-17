from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    [sys.executable, "-m", "tools.validate_repository_minimal"],
    [sys.executable, "-m", "tools.validate_alpha4_runtime"],
    [sys.executable, "-m", "tools.alpha4_runtime_manifest"],
    [sys.executable, "-m", "tools.alpha4_runtime_relational_expression"],
    [sys.executable, "-m", "tools.alpha4_runtime_paired_expression"],
    [sys.executable, "-m", "tools.alpha4_runtime_assurance"],
]


def main() -> int:
    for command in COMMANDS:
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            print("ALPHA4_RUNTIME_GATE=FAIL")
            return result.returncode
    print("ALPHA4_RUNTIME_GATE_SCOPE=LOCAL_SEMANTIC_NO_TLAPS_NO_PYTEST")
    print("ALPHA4_RUNTIME_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
