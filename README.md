# ASET Worker Extension

ASET Worker Alpha4 is the current representation of the minimal productive-attempt
layer inherited from ASET Seed 0.4alpha.

Worker owns only productive-attempt state. It does not own Seed recognition,
Authority, or effect permission. Every Worker transition is a stuttering step with
respect to the exact bound Seed state.

The lifecycle is intentionally small:

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
```

`RESULT` means result material was produced; it does not imply correctness or
acceptance. `NO_RESULT` is an explicit terminal assertion, not the absence of a
record and not an implicit failure classification.

Active structure:

- `worker/alpha4/WORKER.aset` — machine-readable Worker Alpha4 semantic subject.
- `worker/alpha4/operational/` — restricted-Forth Worker expression.
- `worker/alpha4/formal/` — relational expression, pairing, safety, and Seed-inheritance proofs.
- `theory/worker-lifecycle/` — temporal lifecycle theory over the Alpha4 relations.
- `upstream/ASET_SEED_ALPHA4_BINDING.aset` — exact content binding to ASET Seed 0.4alpha.
- `history/REFERENCES.aset` — immutable references to the superseded Alpha2 canon.
- `tools/alpha4_worker_gate.py` — verification gate.

The Alpha4 representation claims no compatibility with the previous Worker canon.

Verify locally:

```text
python -m tools.alpha4_worker_gate
```

Copyright and attribution are in `NOTICE`. Licensing terms are in `LICENSE`.
