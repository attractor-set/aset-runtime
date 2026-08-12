# Seed stutter assurance

`ASET-WORKER-SEED-STUTTER-ASSURANCE-V1` is a non-normative evidence-composition
perimeter for the Worker Extension.

```text
Worker lifecycle transitions
        |
        | mechanically materialized Worker -> Seed stuttering proof
        v
exact SeedResolution.tla (unchanged projection)
        |
        | public ASET v60 recognition-boundary assurance
        v
canonical recognition boundary
```

The checker requires the materialized Worker Seed-refinement evidence and the
public v60 package to bind the exact same `SeedResolution.tla` SHA-256. It fails
closed on any mismatch.

This is not a new mechanically composed theorem and it does not modify Worker or
Seed normative semantics. Worker productive state remains non-authoritative:
Worker transitions create no Seed Resolution, own no Seed state and grant no
external effect permission by implication.

Run against the pinned public ASET assurance checkout:

```bash
python tools/check_seed_stutter_assurance.py \
  --seed-root ~/ASET-public-assurance-e89d9842 \
  --output dist/worker-seed-stutter-assurance.json
```
