# Worker role

## Productive boundary

A Worker is an implementation-neutral source of productive work. It may be a human, an AI model, a deterministic program, a solver, a compiler, a tool, a remote service, a physical actuator, or another implementation.

The Worker extension does not standardize how work is assigned, described internally or performed. It standardizes only one exact productive attempt:

```text
exact START_WORK binding
        |
        v
      RUNNING
       /   \
      /     \
  RESULT   NO_RESULT
```

`RESULT` means that exact result material was terminally produced. `NO_RESULT` means that the exact attempt terminally produced no result material. Neither state evaluates quality, correctness, usefulness, policy compliance or acceptability.

## Descriptor opacity

`START_WORK` binds an opaque exact `work_descriptor_binding`. Profiles may put repository coordinates, prompts, skills, MCP tools, models, input artifacts, constraints or other information behind that binding. None of those structures belong to the Worker canon.

## Productive power is not normative power

```text
productive power != normative power
```

Worker execution, terminal result material and evidence do not create Resolution Authority and do not become recognized Context state by implication.

Worker transitions are Seed-stuttering extension transitions: Worker state may change while the pinned Seed projection remains unchanged. Consequential recognition of Worker material, when required, occurs through a separate target-local Context/Seed path.

## Non-goals

The Worker extension does not define task discovery, task decomposition, eligibility, assignment, acceptance, queueing, scheduling, ranking, planning, retry provenance, learning, memory, verification policy, result quality, external effect authorization or Worker implementation technology.
