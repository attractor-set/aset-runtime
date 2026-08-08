# ASET Worker Extension

`aset-worker-extension` is a semantic bootstrap for the productive-work boundary of ASET.

The normative bootstrap surface models one work identity through the lifecycle:

```text
UNREGISTERED
    |
    | ACCEPT_WORK
    v
 ACCEPTED
    |
    | START_WORK
    v
  RUNNING
   /   \
  /     \
RESULT  NO_RESULT
   \     /
    \_XOR/
```

`NO_RESULT` is a first-class terminal record. It is **not** the absence of a record and it is not equivalent to `RUNNING` without a result.

`RESULT` does not mean success, and `NO_RESULT` does not mean failure. The extension standardizes whether exact result material was produced for the exact work invocation, not whether that material is good, accepted, useful, or authorized.

Worker output, evidence and execution do not create ASET Seed Authority, do not create a Seed Resolution, and do not grant external effect permission by implication.

## Bootstrap status

This repository is intentionally `0.1.0-alpha.0` and not release-ready. The machine-readable canon, protocol schemas, executable oracle, conformance corpus, finite-state checker and a draft TLA+ safety projection are present. Canon-to-TLA equivalence and mechanically proved Seed refinement are explicitly open gates.

## Local gate

```bash
python tools/run_local_gate.py
```

Optional pytest suite:

```bash
python -m pytest -q
```

The local gate uses only the Python standard library.
