# ASET Runtime

ASET Runtime 0.1.0-alpha.4 is the current public representation of the minimal
productive-attempt lifecycle extension for ASET Seed.

**Execution may produce material. Recognition remains local to Seed.**

The Runtime core owns exact attempt lifecycle state only. One exact attempt is
started once, may be replayed idempotently, and may terminate once as either
`RESULT` or `NO_RESULT`. A terminal attempt never reopens; a subsequent attempt
uses a fresh identifier.

`RESULT` does not mean success. `NO_RESULT` does not mean failure. Both are exact
terminal statements about whether one productive attempt produced result
material.

Runtime does not own ASET Seed recognition, Authority, or external effect
permission. Every Runtime-only transition stutters the exact bound Seed state.

## Active structure

- `runtime/alpha4/` — the single active Runtime semantic line;
- `runtime/alpha4/operational/` — independently authored restricted-Forth representation;
- `runtime/alpha4/formal/` — relational representation and mechanical proof surface;
- `runtime/alpha4/causal/` — independently authored causal representation;
- `runtime/alpha4/RUNTIME.aset` — non-semantic composition and identity manifest;
- `upstream/ASET_SEED_ALPHA4_BINDING.aset` — content-addressed binding to the exact ASET Seed 0.4alpha subject;
- `history/REFERENCES.aset` — immutable predecessor references only; history is not active semantics.

The predecessor bootstrap is not an active compatibility layer. Runtime
0.1.0-alpha.4 claims no semantic compatibility with it.

## Runtime semantics

The bounded core has eight exact outcomes:

- fresh start → `ATTEMPT_STARTED`, state changes;
- exact start replay → `IDEMPOTENT_REPLAY`, state stutters;
- conflicting start identifier → `ATTEMPT_IDENTITY_CONFLICT`, state stutters;
- exact running attempt ending with result → `ATTEMPT_ENDED_WITH_RESULT`, state changes;
- exact running attempt ending with no result → `ATTEMPT_ENDED_WITH_NO_RESULT`, state changes;
- exact terminal replay → `IDEMPOTENT_REPLAY`, state stutters;
- conflicting terminal record → `TERMINAL_ATTEMPT_IMMUTABLE`, state stutters;
- end request without the exact running attempt → `ATTEMPT_NOT_RUNNING`, state stutters.

Wire-format validation, scheduling, assignment, retry policy, result quality,
model/tool choice, planning, memory, and execution technology remain outside the
Runtime semantic core.

## Three-way assurance

Runtime binds independently authored operational, relational, and causal
representations with semantic precedence `NONE`. Bounded triangulation checks
operational↔relational, operational↔causal, and relational↔causal observations over
the complete valid bounded state domain used by the checker. The same bounded pass
checks Runtime invariants and append-only state preservation. TLA/TLAPS remains the
deductive proof machinery for the relational line.

Runtime extends Seed by preservation rather than recognition. For every Runtime
transition, the operational, relational, and causal parent bindings are the
corresponding exact Seed preservation boundaries (`PRESERVE-UNKNOWN`,
`PRESERVE-ALLOW`, `PRESERVE-BLOCK`). Runtime adds no Seed state and does not
redefine Seed recognition behavior.

## Release materialization

English and Python are downstream release companions, not additional assurance
representations. The Runtime English companion extends the exact Seed English
companion. The Runtime Python companion loads and verifies the exact Seed Python
companion bytes and keeps the Seed state observationally unchanged across Runtime-only
transitions.

The release builder materializes `formal/AssembledRuntime.tla`. A separate
post-build TLAPS verifier proves that every assembled Runtime transition can be
composed with exact Seed preservation while retaining the same Seed subject,
authority, evidence, recognition, and effect-permission state. Verification runs
in an isolated temporary directory and checks that neither release tree changes.

```text
source Forth / TLA / Petri
          |
          v
   three-way assurance
          |
          v
      source TLAPS
          |
          v
         build
          |
          v
 AssembledRuntime.tla
          |
          v
 post-build exact-Seed TLAPS
          |
       +--+--+
       |     |
    English Python
       |     |
       |   air-gap
       +--+--+
          |
          v
   release admission
```

Verify the source surface with:

```text
python -m tools.alpha4_runtime_gate
```

The complete release gate is `tools.alpha4_runtime_release_gate.py`; it requires
the exact immutable Seed source, release tree, companion tree, and TLAPM.

SHA-256 identifies exact bytes; semantic integrity is established by declared
relations and proof obligations. Generated evidence has semantic precedence
`NONE`.

Copyright and attribution are in `NOTICE`. Licensing terms are in `LICENSE`.
