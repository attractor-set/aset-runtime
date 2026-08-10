------------------------ MODULE WorkerLifecycleProofs ------------------------
EXTENDS WorkerLifecycle, TLAPS

(***************************************************************************
Unbounded safety proof candidate for the minimized Worker lifecycle projection.

The proof covers only the abstract append-only productive-attempt state in
WorkerLifecycle.tla. Exact wire metadata, digest construction, descriptor
contents, runtime execution, liveness, result correctness and implementation
refinement remain outside this proof boundary.
***************************************************************************)

THEOREM InitImpliesWorkerSafety ==
  Init => WorkerSafety
PROOF
  BY DEF Init,
         WorkerSafety,
         TypeOK,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult

THEOREM StartWorkPreservesWorkerSafety ==
  \A w \in WorkIds :
    WorkerSafety /\ StartWork(w) => WorkerSafety'
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         StartWork,
         Terminal

THEOREM EndWorkWithResultPreservesWorkerSafety ==
  \A w \in WorkIds :
    WorkerSafety /\ EndWorkWithResult(w) => WorkerSafety'
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         EndWorkWithResult,
         Terminal

THEOREM EndWorkWithNoResultPreservesWorkerSafety ==
  \A w \in WorkIds :
    WorkerSafety /\ EndWorkWithNoResult(w) => WorkerSafety'
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         EndWorkWithNoResult,
         Terminal

THEOREM EndWorkPreservesWorkerSafety ==
  \A w \in WorkIds, terminalKind \in {"RESULT", "NO_RESULT"} :
    WorkerSafety /\ EndWork(w, terminalKind) => WorkerSafety'
PROOF
  BY EndWorkWithResultPreservesWorkerSafety,
     EndWorkWithNoResultPreservesWorkerSafety
     DEF EndWork

THEOREM RecognizedWorkerTransitionPreservesWorkerSafety ==
  WorkerSafety /\ RecognizedWorkerTransition => WorkerSafety'
PROOF
  BY StartWorkPreservesWorkerSafety,
     EndWorkPreservesWorkerSafety
     DEF RecognizedWorkerTransition

THEOREM StateStutterPreservesWorkerSafety ==
  WorkerSafety /\ UNCHANGED vars => WorkerSafety'
PROOF
  BY DEF vars,
         WorkerSafety,
         TypeOK,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult

THEOREM BoxNextPreservesWorkerSafety ==
  WorkerSafety /\ [Next]_vars => WorkerSafety'
PROOF
  BY RecognizedWorkerTransitionPreservesWorkerSafety,
     StateStutterPreservesWorkerSafety
     DEF Next

THEOREM SpecImpliesAlwaysWorkerSafety ==
  Spec => []WorkerSafety
PROOF
  BY PTL,
     InitImpliesWorkerSafety,
     BoxNextPreservesWorkerSafety
     DEF Spec

THEOREM StartWorkSatisfiesStartedAppendOnlyStep ==
  \A w \in WorkIds :
    StartWork(w) => StartedAppendOnlyStep
PROOF
  BY DEF StartWork, StartedAppendOnlyStep

THEOREM EndWorkWithResultSatisfiesStartedAppendOnlyStep ==
  \A w \in WorkIds :
    EndWorkWithResult(w) => StartedAppendOnlyStep
PROOF
  BY DEF EndWorkWithResult, StartedAppendOnlyStep

THEOREM EndWorkWithNoResultSatisfiesStartedAppendOnlyStep ==
  \A w \in WorkIds :
    EndWorkWithNoResult(w) => StartedAppendOnlyStep
PROOF
  BY DEF EndWorkWithNoResult, StartedAppendOnlyStep

THEOREM EndWorkSatisfiesStartedAppendOnlyStep ==
  \A w \in WorkIds, terminalKind \in {"RESULT", "NO_RESULT"} :
    EndWork(w, terminalKind) => StartedAppendOnlyStep
PROOF
  BY EndWorkWithResultSatisfiesStartedAppendOnlyStep,
     EndWorkWithNoResultSatisfiesStartedAppendOnlyStep
     DEF EndWork

THEOREM NextSatisfiesStartedAppendOnlyStep ==
  Next => StartedAppendOnlyStep
PROOF
  BY StartWorkSatisfiesStartedAppendOnlyStep,
     EndWorkSatisfiesStartedAppendOnlyStep
     DEF Next, RecognizedWorkerTransition

THEOREM BoxNextSatisfiesBoxStartedAppendOnlyStep ==
  [Next]_vars => [StartedAppendOnlyStep]_vars
PROOF
  BY NextSatisfiesStartedAppendOnlyStep
     DEF vars, StartedAppendOnlyStep

THEOREM SpecImpliesStartedAppendOnly ==
  Spec => StartedAppendOnly
PROOF
  BY PTL,
     BoxNextSatisfiesBoxStartedAppendOnlyStep
     DEF Spec, StartedAppendOnly

THEOREM StartWorkSatisfiesTerminalAppendOnlyStep ==
  \A w \in WorkIds :
    StartWork(w) => TerminalAppendOnlyStep
PROOF
  BY DEF StartWork, TerminalAppendOnlyStep

THEOREM EndWorkWithResultSatisfiesTerminalAppendOnlyStep ==
  \A w \in WorkIds :
    EndWorkWithResult(w) => TerminalAppendOnlyStep
PROOF
  BY DEF EndWorkWithResult, TerminalAppendOnlyStep

THEOREM EndWorkWithNoResultSatisfiesTerminalAppendOnlyStep ==
  \A w \in WorkIds :
    EndWorkWithNoResult(w) => TerminalAppendOnlyStep
PROOF
  BY DEF EndWorkWithNoResult, TerminalAppendOnlyStep

THEOREM EndWorkSatisfiesTerminalAppendOnlyStep ==
  \A w \in WorkIds, terminalKind \in {"RESULT", "NO_RESULT"} :
    EndWork(w, terminalKind) => TerminalAppendOnlyStep
PROOF
  BY EndWorkWithResultSatisfiesTerminalAppendOnlyStep,
     EndWorkWithNoResultSatisfiesTerminalAppendOnlyStep
     DEF EndWork

THEOREM NextSatisfiesTerminalAppendOnlyStep ==
  Next => TerminalAppendOnlyStep
PROOF
  BY StartWorkSatisfiesTerminalAppendOnlyStep,
     EndWorkSatisfiesTerminalAppendOnlyStep
     DEF Next, RecognizedWorkerTransition

THEOREM BoxNextSatisfiesBoxTerminalAppendOnlyStep ==
  [Next]_vars => [TerminalAppendOnlyStep]_vars
PROOF
  BY NextSatisfiesTerminalAppendOnlyStep
     DEF vars, TerminalAppendOnlyStep

THEOREM SpecImpliesTerminalAppendOnly ==
  Spec => TerminalAppendOnly
PROOF
  BY PTL,
     BoxNextSatisfiesBoxTerminalAppendOnlyStep
     DEF Spec, TerminalAppendOnly

THEOREM RecognizedWorkerTransitionSatisfiesStateChangeBoundary ==
  RecognizedWorkerTransition => WorkerStateChangesOnlyByRecognizedTransitionStep
PROOF
  BY DEF WorkerStateChangesOnlyByRecognizedTransitionStep

THEOREM BoxNextSatisfiesBoxStateChangeBoundary ==
  [Next]_vars => [WorkerStateChangesOnlyByRecognizedTransitionStep]_vars
PROOF
  BY RecognizedWorkerTransitionSatisfiesStateChangeBoundary
     DEF Next, vars, WorkerStateChangesOnlyByRecognizedTransitionStep

THEOREM SpecImpliesWorkerStateChangesOnlyByRecognizedTransition ==
  Spec => WorkerStateChangesOnlyByRecognizedTransition
PROOF
  BY PTL,
     BoxNextSatisfiesBoxStateChangeBoundary
     DEF Spec, WorkerStateChangesOnlyByRecognizedTransition

=============================================================================
