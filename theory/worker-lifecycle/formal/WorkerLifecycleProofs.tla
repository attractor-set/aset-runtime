--------------------- MODULE WorkerLifecycleProofs ---------------------
EXTENDS WorkerLifecycle, WorkerSafetyProofs, TLAPS

THEOREM InitImpliesWorkerSafety == Init => LifecycleSafety
PROOF
  BY SMTT(30), EmptyStateIsSafe
     DEF Init, LifecycleSafety, WorkerSafety

THEOREM NextPreservesWorkerSafety ==
  LifecycleSafety /\ Next => LifecycleSafety'
PROOF
  BY SMTT(30), StartWorkProducesSafeState, EndWorkProducesSafeState
     DEF Next, StartStep, EndStep, LifecycleSafety, WorkerSafety

THEOREM StateStutterPreservesWorkerSafety ==
  LifecycleSafety /\ UNCHANGED vars => LifecycleSafety'
PROOF BY SMTT(30) DEF vars, LifecycleSafety

THEOREM BoxNextPreservesWorkerSafety ==
  LifecycleSafety /\ [Next]_vars => LifecycleSafety'
PROOF BY NextPreservesWorkerSafety, StateStutterPreservesWorkerSafety

THEOREM SpecImpliesAlwaysWorkerSafety == Spec => []LifecycleSafety
PROOF BY PTL, InitImpliesWorkerSafety, BoxNextPreservesWorkerSafety DEF Spec

THEOREM StartStepIsAppendOnly == StartStep => /\ StartedAppendOnlyStep /\ TerminalAppendOnlyStep
PROOF BY StartWorkIsAppendOnly DEF StartStep, StartedAppendOnlyStep, TerminalAppendOnlyStep

THEOREM EndStepIsAppendOnly == EndStep => /\ StartedAppendOnlyStep /\ TerminalAppendOnlyStep
PROOF BY EndWorkIsAppendOnly DEF EndStep, StartedAppendOnlyStep, TerminalAppendOnlyStep

=============================================================================
