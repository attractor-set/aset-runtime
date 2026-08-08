# Work lifecycle state machine

For each `work_id`, absence from Worker state is the implicit `UNREGISTERED` condition.

The only recognized Worker lifecycle transitions in this bootstrap are:

```text
UNREGISTERED --ACCEPT_WORK------------> ACCEPTED
ACCEPTED     --START_WORK-------------> RUNNING
RUNNING      --COMPLETE_WITH_RESULT---> RESULT
RUNNING      --COMPLETE_WITH_NO_RESULT-> NO_RESULT
```

`RESULT` and `NO_RESULT` are terminal, immutable and mutually exclusive.

There is no `FAILED`, `SUCCESS`, `TIMEOUT`, `CANCELLED`, `PARTIAL`, or `ABORTED` state in the core lifecycle. Such classifications may exist as evidence or profile-level material but do not alter the minimal Worker state machine.

A retry never reopens terminal work. A retry is fresh work with a fresh `work_id`; if a retry relationship is declared, the new accepted-work record binds the exact predecessor terminal record.

No liveness claim is made. A work item may remain `ACCEPTED` or `RUNNING` indefinitely unless a stricter profile adds independently stated liveness conditions.
