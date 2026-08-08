# Worker role

## Productive boundary

A Worker is an implementation-neutral source of productive work. It may be a human, an AI model, a deterministic program, a solver, a compiler, a tool, a remote service, a physical actuator, or another implementation.

The Worker extension does not standardize how work is performed. It standardizes the exact lifecycle and provenance boundary around one accepted work identity.

```text
exact work acceptance
        |
        v
     ACCEPTED
        |
        v
      RUNNING
       /   \
      /     \
  RESULT   NO_RESULT
      \     /
       \_XOR/
```

`RESULT` means that exact result material was terminally produced. `NO_RESULT` means that the exact work attempt terminally produced no result material. Neither state evaluates quality, correctness, usefulness, policy compliance or acceptability.

## Productive power is not normative power

The central architectural boundary is:

```text
productive power != normative power
```

Worker capability, work acceptance, work execution, terminal result material and work evidence do not create Resolution Authority and do not become recognized Context state by implication.

Worker transitions are intended to be Seed-stuttering extension transitions: Worker state may change while the pinned Seed projection remains unchanged. Consequential recognition of Worker material, when required, occurs through a separate target-local Context/Seed path.

## Non-goals

The Worker extension does not define task discovery, task decomposition, scheduling, eligibility, ranking, planning, learning, memory, verification policy, result quality, external effect authorization or Worker implementation technology.
