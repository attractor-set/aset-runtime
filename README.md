# ASET Runtime

ASET Runtime 0.1.0-alpha.4 is the current public representation of the bounded
execution lifecycle extension for ASET Seed 0.4alpha.

**Execution may produce material. Recognition remains local to Seed.**

Runtime owns exact execution-attempt records and lifecycle transitions only. It
does not own Seed recognition, Authority, or external effect permission. Every
Runtime-only transition preserves the exact bound Seed state.

Terminal statements distinguish `RESULT` from `NO_RESULT`; neither term is a quality
judgment and neither grants recognition.

## Active structure

- `runtime/alpha4/operational/` — independently authored restricted-Forth
  operational representation.
- `runtime/alpha4/formal/` — relational representation, formal reflection, and
  mechanical proof surface.
- `runtime/alpha4/causal/` — independently authored causal representation.
- `runtime/alpha4/RUNTIME.aset` — non-semantic composition and identity
  manifest.
- `upstream/ASET_SEED_ALPHA4_BINDING.aset` — content-addressed binding to the
  exact ASET Seed 0.4alpha subject and release companions.
- `tools/alpha4_runtime_gate.py` — complete source-assurance gate.
- `tools/alpha4_runtime_release_gate.py` — deterministic release, post-build
  proof, companion, admission, and public-audit gate.
- `history/REFERENCES.aset` — immutable reference to the superseded public
  predecessor; history is not active semantics.

The 0.1.0-alpha.4 representation claims no compatibility with the predecessor
bootstrap.

## Assurance boundary

The operational, relational, and causal representations are independently
authored and mechanically cross-checked with semantic precedence `NONE`.
Runtime extends Seed only through the exact Seed preservation boundary and does
not copy, redefine, or replace Seed recognition semantics.

Source TLAPS proves the Runtime operational/relational pairing and the Seed
preservation boundary. The deterministic release builder then materializes
`formal/AssembledRuntime.tla`; a separate post-build TLAPS verifier proves the
assembled Runtime release against the exact bound Seed preservation relations.
Verification runs outside the release tree and checks exact release identities.

English and Python are downstream release companion extensions, not additional
assurance representations. Both are bound to the exact released Seed companion
base. The Python companion is admitted through an independent air-gap verifier
and Runtime-only transitions leave the Seed state observationally unchanged.

Verify the source surface with:

```text
python -m tools.alpha4_runtime_gate
```

The complete release gate requires the exact Seed source, Seed release tree,
Seed companion tree, and TLAPM and is implemented by
`tools.alpha4_runtime_release_gate.py`.

SHA-256 identifies exact release bytes; semantic integrity is established by
declared relations and proof obligations. Generated evidence has semantic
precedence `NONE`.

Copyright and attribution are in `NOTICE`. Licensing terms are in `LICENSE`.
