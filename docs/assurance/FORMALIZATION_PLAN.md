# Formalization plan

The minimized Worker semantic bootstrap separates four assurance stages:

1. executable/conformance checking of the machine-readable canon;
2. a handwritten append-only Worker lifecycle model and unbounded TLAPS safety proof;
3. a standalone deterministic canon projection with TLAPS behavioral-equivalence proof;
4. a separate stuttering refinement proof against the exact pinned Seed formal model.

The machine-readable canon remains normative. Formal artifacts and proof evidence are assurance surfaces and do not gain normative implementation precedence.

Because `0.1.0-alpha.1` removes `ACCEPTED/ACCEPT_WORK` and unifies terminal completion under `END_WORK`, proof evidence from the previous semantic revision is intentionally invalidated and removed. New proof evidence must bind the exact current hashes.

## Candidate proof run

```text
python tools/run_formal_candidate_gate.py \
  --tlapm "$HOME/ASET/.tooling/tlapm/bin/tlapm" \
  --seed-root "$HOME/ASET-seed-0.3.0-alpha.3"
```

A passing candidate gate writes machine-readable run reports under `dist/formal-candidate/`. Those reports are local evidence and are not part of the canon package.

## Evidence materialization

After a reviewed passing proof run:

```text
python tools/materialize_formal_evidence.py
```

The materializer accepts only a `PASS` candidate-gate report whose exact proof artifacts, TLAPM identity, Seed release commit and pinned `SeedResolution.tla` digest match the current repository.

## Reproducible formal release gate

```text
python tools/run_formal_release_gate.py \
  --tlapm "$HOME/ASET/.tooling/tlapm/bin/tlapm" \
  --seed-root "$HOME/ASET-seed-0.3.0-alpha.3"
```

## Claim boundary

Mechanical proof closure is limited to the abstract minimized lifecycle and Seed-stuttering relation. It does not establish arbitrary runtime implementation refinement, descriptor correctness, liveness, result correctness, cryptographic correctness, worker eligibility, external-effect safety, or concrete Authority establishment.
