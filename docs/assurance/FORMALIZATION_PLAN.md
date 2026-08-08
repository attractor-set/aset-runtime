# Formalization plan

The Worker semantic bootstrap now separates four assurance stages:

1. executable/conformance checking of the machine-readable canon;
2. a handwritten Worker lifecycle model and unbounded TLAPS safety proof;
3. a standalone deterministic canon projection with TLAPS behavioral-equivalence proof;
4. a separate stuttering refinement proof against the exact pinned Seed formal model.

The machine-readable canon remains normative. Formal artifacts and proof evidence are assurance surfaces and do not gain normative implementation precedence.

## Candidate proof run

Run the proof candidate with the pinned TLAPM build and exact Seed checkout:

```text
python tools/run_formal_candidate_gate.py \
  --tlapm "$HOME/ASET/.tooling/tlapm/bin/tlapm" \
  --seed-root "$HOME/ASET"
```

A passing candidate gate writes machine-readable run reports under `dist/formal-candidate/`. Those reports are local evidence and are not part of the canon package.

## Evidence materialization

After a reviewed passing proof run, materialize immutable assurance evidence:

```text
python tools/materialize_formal_evidence.py
```

The materializer accepts only a `PASS` candidate-gate report whose exact proof artifacts, TLAPM identity, Seed release commit and pinned `SeedResolution.tla` digest match the current repository. It records the observed obligation counts as reproducibility evidence, not as semantic constants.

Materialized assurance files are:

- `extension/canonical/assurance/lifecycle-proof.json`;
- `extension/canonical/assurance/canon-refinement-proof.json`;
- `extension/canonical/assurance/seed-refinement-proof.json`;
- `extension/canonical/assurance/verification-registry.json`.

The relation metadata is then rebuilt with `MECHANICALLY_PROVED` status and the canon package is rebuilt to bind the exact assurance evidence.

## Reproducible formal release gate

The release gate reruns the proofs before accepting the committed evidence:

```text
python tools/run_formal_release_gate.py \
  --tlapm "$HOME/ASET/.tooling/tlapm/bin/tlapm" \
  --seed-root "$HOME/ASET"
```

It requires projection freshness, the normal local semantic gate, a fresh successful formal-candidate run, exact agreement between that fresh run and the materialized assurance evidence, canon-package integrity, and the Python tests. Only then may it emit `FORMAL_RELEASE_GATE=PASS`.

## Claim boundary

Mechanical proof closure is limited to the declared abstract formal surfaces. It does not establish arbitrary Worker runtime implementation refinement, liveness, result correctness, cryptographic correctness, worker eligibility, external-effect safety, or concrete Authority establishment.
