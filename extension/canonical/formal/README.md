# Worker formal assurance

The minimized lifecycle projected here is:

```text
UNREGISTERED -> RUNNING -> (RESULT XOR NO_RESULT)
```

with the two normative operations `START_WORK` and `END_WORK`. The TLA+ state is intentionally smaller than the wire/profile surface: it tracks only append-only started and terminal-kind facts.

The machine-readable canon remains normative. `WorkerCanonProjection.tla` is deterministically generated from it; `WorkerLifecycle.tla` is the handwritten assurance model; `WorkerCanonRefinementProofs.tla` is the behavioral-equivalence proof candidate.

`WorkerSeedStuttering.tla` composes the Worker-only lifecycle with the exact externally pinned Seed model and treats every Worker operation as a Seed stutter.

Formal assurance for this semantic revision is OPEN until the exact new proof artifacts are run and materialized. Previous proof evidence for the pre-minimization `ACCEPTED` lifecycle must not be reused.
