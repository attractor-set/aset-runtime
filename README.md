# ASET Worker Extension

`aset-worker-extension` is the minimal productive-attempt boundary of ASET.

The normative bootstrap surface recognizes one work identity through only two operations:

```text
UNREGISTERED
    |
    | START_WORK
    v
  RUNNING
   /   \
  /     \
END      END
 |        |
RESULT  NO_RESULT
   \      /
    \_XOR/
```

The canonical state is append-only: a work identity first gains one exact immutable started-work binding and may later gain one exact immutable terminal record. `RUNNING`, `RESULT`, and `NO_RESULT` are projections of those facts.

`NO_RESULT` is a first-class terminal assertion. It is **not** the absence of a record and it is not equivalent to `RUNNING` without a terminal record.

`RESULT` does not mean success, and `NO_RESULT` does not mean failure. Worker standardizes only whether one exact productive attempt terminally produced result material.

Assignment, acceptance, queueing, scheduling, retry provenance, descriptor internals, verification policy and result quality are deliberately outside the Worker canon. Profiles may define them without changing the base lifecycle.

Worker output, evidence and execution do not create ASET Seed Authority, do not create a Seed Resolution, and do not grant external effect permission by implication.

## Bootstrap status

This semantic revision is `0.1.0-alpha.1` / `ASET-WORKER-CANON-0.1-ALPHA2` and is not release-ready. Because the lifecycle was minimized after the previous proof materialization, formal assurance is intentionally reset to `OPEN`; the new generated projection, lifecycle safety proof candidate and Seed-stuttering proof candidate must be mechanically closed again before release.

## Local gate

```bash
python tools/run_local_gate.py
```

Optional pytest suite:

```bash
python -m pytest -q
```

The local gate uses only the Python standard library.

## Public v60 Seed-stutter assurance

`ASET-WORKER-SEED-STUTTER-ASSURANCE-V1` is a separate non-normative assurance
perimeter. When the materialized Worker-to-Seed stuttering evidence is
`MECHANICALLY_PROVED` (as in the current proof artifact), the checker composes
that evidence with the public ASET v60 recognition-boundary assurance only when
both bind the exact same frozen `SeedResolution.tla` subject.

This does not create a new composed TLAPS theorem and does not change Worker
semantics: productive work remains non-authoritative and grants no Seed
recognition or external effect permission by implication.
