from __future__ import annotations

import argparse
from pathlib import Path

from tools.alpha4_worker_paired_expression import main as paired_main
from tools.validate_alpha4_worker import validate_all
from tools.validate_repository_minimal import main as minimal_main


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed-root", type=Path)
    args = parser.parse_args()
    minimal_main()
    validate_all(args.seed_root)
    paired_main()
    print("ALPHA4_WORKER_GATE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
