------------------------- MODULE WorkerLifecycle -------------------------
EXTENDS WorkerRelations

VARIABLE worker

vars == <<worker>>

Init == worker = EmptyWorkerState

StartStep == \E request \in StartRequestUniverse, result \in ResultCodes :
  StartWork(worker, worker', request, result)
EndStep == \E request \in EndRequestUniverse, result \in ResultCodes :
  EndWork(worker, worker', request, result)

Next == StartStep \/ EndStep
Spec == Init /\ [][Next]_vars

LifecycleSafety == worker \in WorkerStateType
StartedAppendOnlyStep == worker.started \subseteq worker'.started
TerminalAppendOnlyStep == worker.terminals \subseteq worker'.terminals

=============================================================================
