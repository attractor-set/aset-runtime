# ASET Worker formal assurance surface

`WorkerLifecycle.tla` is the handwritten abstract safety model for the Worker
lifecycle:

```text
UNREGISTERED -> ACCEPTED -> RUNNING -> (RESULT XOR NO_RESULT)
```

`NO_RESULT` is an explicit terminal state. Missing terminal state while a work
identity is `RUNNING` does not imply `NO_RESULT`.

The formal model deliberately abstracts wire-level digests and metadata. The
normative source remains `extension/canonical/source/worker-model.json` together
with the exact files listed by `CANON_PACKAGE.json`. Formal artifacts are
assurance projections and have no normative implementation precedence.

The formal candidate contains three independent proof surfaces:

1. `WorkerLifecycleProofs.tla` — unbounded TLAPS safety over the handwritten
   lifecycle model;
2. `WorkerCanonProjection.tla` + `WorkerCanonRefinementProofs.tla` — standalone
   deterministic projection from the machine-readable canon plus behavioral
   equivalence to the handwritten lifecycle model;
3. `WorkerSeedStuttering.tla` + `WorkerSeedStutteringProofs.tla` — exact pinned
   Seed bridge proving that Worker-only lifecycle operations stutter with
   respect to the Seed projection.

`SeedResolution.tla` is not copied into this repository. The Seed-refinement
runner loads it from a separately supplied checkout and verifies the exact
pinned SHA-256 before TLAPS is invoked.

Until the candidate proof gate is run successfully with the pinned TLAPM build,
`CANON_TO_TLA`, `TLAPS_SAFETY`, and `SEED_REFINEMENT` remain `OPEN` and the
formal release gate remains blocked.

Excluded claims include implementation refinement, cryptographic digest
correctness, liveness, result correctness, worker eligibility, external effect
execution, and concrete Authority establishment.
