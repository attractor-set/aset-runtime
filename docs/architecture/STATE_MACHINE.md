# Work lifecycle state machine

For each `work_id`, absence from Worker state is the implicit `UNREGISTERED` condition.

The only normative Worker operations are:

```text
UNREGISTERED --START_WORK----------------------> RUNNING
RUNNING      --END_WORK(kind=RESULT)-----------> RESULT
RUNNING      --END_WORK(kind=NO_RESULT)--------> NO_RESULT
```

The implementation may expose `RESULT` and `NO_RESULT` as derived states; canonically they are the mutually exclusive kinds of one immutable terminal record.

`START_WORK` establishes the exact immutable binding of one productive attempt. The work descriptor is opaque to the Worker canon. Its internal structure belongs to a profile or implementation.

`END_WORK` terminates exact running work. `NO_RESULT` is explicit and never inferred from missing output or missing terminal state.

There is no `ACCEPTED`, `FAILED`, `SUCCESS`, `TIMEOUT`, `CANCELLED`, `PARTIAL`, or `ABORTED` state in the base lifecycle. Assignment, acceptance, queueing and such classifications may exist in profiles or orchestration.

Terminal work is never reopened. Any later productive attempt uses a fresh `work_id`. Whether that later attempt is a retry, successor, alternative or unrelated work is provenance outside the Worker lifecycle canon.

No liveness claim is made. A work identity may remain `RUNNING` indefinitely unless a stricter profile adds independently stated liveness conditions.
