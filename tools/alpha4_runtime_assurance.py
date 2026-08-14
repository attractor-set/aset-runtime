from __future__ import annotations

from tools.alpha4_runtime_causal_expression import check_causal_bindings
from tools.alpha4_runtime_triangulated_expression import (
    check_triangulated_assurance,
    print_evidence,
)


def main() -> int:
    check_causal_bindings()
    evidence = check_triangulated_assurance()
    print_evidence(evidence)
    print("ALPHA4_RUNTIME_ASSURANCE_SEMANTIC_DELTA=NONE")
    print("ALPHA4_RUNTIME_ASSURANCE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
