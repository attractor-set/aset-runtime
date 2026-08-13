---------------- MODULE RestrictedOperationalSemantics ----------------
EXTENDS WorkerRelations

OperationalStartMissing(s, t, p, result) == StartMissing(s, t, p, result)
OperationalStartFresh(s, t, p, result) == StartFresh(s, t, p, result)
OperationalStartReplay(s, t, p, result) == StartReplay(s, t, p, result)
OperationalStartConflict(s, t, p, result) == StartConflict(s, t, p, result)
OperationalEndNotStarted(s, t, p, result) == EndNotStarted(s, t, p, result)
OperationalEndBindingMismatch(s, t, p, result) == EndBindingMismatch(s, t, p, result)
OperationalEndKindRequired(s, t, p, result) == EndKindRequired(s, t, p, result)
OperationalEndBindingRequired(s, t, p, result) == EndBindingRequired(s, t, p, result)
OperationalEndResult(s, t, p, result) == EndResult(s, t, p, result)
OperationalEndNoResult(s, t, p, result) == EndNoResult(s, t, p, result)
OperationalEndReplay(s, t, p, result) == EndReplay(s, t, p, result)
OperationalEndConflict(s, t, p, result) == EndConflict(s, t, p, result)

=============================================================================
