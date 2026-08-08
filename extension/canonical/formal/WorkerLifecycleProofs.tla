------------------------ MODULE WorkerLifecycleProofs ------------------------
EXTENDS WorkerLifecycle, TLAPS

(***************************************************************************
Unbounded safety proof for the Worker lifecycle projection.

The proof covers only the abstract lifecycle state represented by
WorkerLifecycle.tla. Exact wire-level metadata, digest construction, runtime
execution, liveness, result correctness and implementation refinement remain
outside this proof boundary.
***************************************************************************)

THEOREM InitImpliesWorkerSafety ==
  Init => WorkerSafety
PROOF
  BY DEF Init,
         WorkerSafety,
         TypeOK,
         StartedImpliesAccepted,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult

THEOREM AcceptWorkPreservesWorkerSafety ==
  \A w \in WorkIds :
    WorkerSafety /\ AcceptWork(w) => WorkerSafety'
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         StartedImpliesAccepted,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         AcceptWork,
         Terminal

THEOREM StartWorkPreservesWorkerSafety ==
  \A w \in WorkIds :
    WorkerSafety /\ StartWork(w) => WorkerSafety'
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         StartedImpliesAccepted,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         StartWork,
         Terminal

THEOREM CompleteWithResultPreservesWorkerSafety ==
  \A w \in WorkIds :
    WorkerSafety /\ CompleteWithResult(w) => WorkerSafety'
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         StartedImpliesAccepted,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         CompleteWithResult,
         Terminal

THEOREM CompleteWithNoResultPreservesWorkerSafety ==
  \A w \in WorkIds :
    WorkerSafety /\ CompleteWithNoResult(w) => WorkerSafety'
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         StartedImpliesAccepted,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         CompleteWithNoResult,
         Terminal

THEOREM RecognizedWorkerTransitionPreservesWorkerSafety ==
  WorkerSafety /\ RecognizedWorkerTransition => WorkerSafety'
PROOF
  BY AcceptWorkPreservesWorkerSafety,
     StartWorkPreservesWorkerSafety,
     CompleteWithResultPreservesWorkerSafety,
     CompleteWithNoResultPreservesWorkerSafety
     DEF RecognizedWorkerTransition

THEOREM StateStutterPreservesWorkerSafety ==
  WorkerSafety /\ UNCHANGED vars => WorkerSafety'
PROOF
  BY DEF vars,
         WorkerSafety,
         TypeOK,
         StartedImpliesAccepted,
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

THEOREM AcceptWorkSatisfiesAcceptedAppendOnlyStep ==
  \A w \in WorkIds :
    AcceptWork(w) => AcceptedAppendOnlyStep
PROOF
  BY DEF AcceptWork, AcceptedAppendOnlyStep

THEOREM StartWorkSatisfiesAcceptedAppendOnlyStep ==
  \A w \in WorkIds :
    StartWork(w) => AcceptedAppendOnlyStep
PROOF
  BY DEF StartWork, AcceptedAppendOnlyStep

THEOREM CompleteWithResultSatisfiesAcceptedAppendOnlyStep ==
  \A w \in WorkIds :
    CompleteWithResult(w) => AcceptedAppendOnlyStep
PROOF
  BY DEF CompleteWithResult, AcceptedAppendOnlyStep

THEOREM CompleteWithNoResultSatisfiesAcceptedAppendOnlyStep ==
  \A w \in WorkIds :
    CompleteWithNoResult(w) => AcceptedAppendOnlyStep
PROOF
  BY DEF CompleteWithNoResult, AcceptedAppendOnlyStep

THEOREM NextSatisfiesAcceptedAppendOnlyStep ==
  Next => AcceptedAppendOnlyStep
PROOF
  BY AcceptWorkSatisfiesAcceptedAppendOnlyStep,
     StartWorkSatisfiesAcceptedAppendOnlyStep,
     CompleteWithResultSatisfiesAcceptedAppendOnlyStep,
     CompleteWithNoResultSatisfiesAcceptedAppendOnlyStep
     DEF Next, RecognizedWorkerTransition

THEOREM BoxNextSatisfiesBoxAcceptedAppendOnlyStep ==
  [Next]_vars => [AcceptedAppendOnlyStep]_vars
PROOF
  BY NextSatisfiesAcceptedAppendOnlyStep
     DEF vars, AcceptedAppendOnlyStep

THEOREM SpecImpliesAcceptedAppendOnly ==
  Spec => AcceptedAppendOnly
PROOF
  BY PTL,
     BoxNextSatisfiesBoxAcceptedAppendOnlyStep
     DEF Spec, AcceptedAppendOnly

THEOREM AcceptWorkSatisfiesStartedAppendOnlyStep ==
  \A w \in WorkIds :
    AcceptWork(w) => StartedAppendOnlyStep
PROOF
  BY DEF AcceptWork, StartedAppendOnlyStep

THEOREM StartWorkSatisfiesStartedAppendOnlyStep ==
  \A w \in WorkIds :
    StartWork(w) => StartedAppendOnlyStep
PROOF
  BY DEF StartWork, StartedAppendOnlyStep

THEOREM CompleteWithResultSatisfiesStartedAppendOnlyStep ==
  \A w \in WorkIds :
    CompleteWithResult(w) => StartedAppendOnlyStep
PROOF
  BY DEF CompleteWithResult, StartedAppendOnlyStep

THEOREM CompleteWithNoResultSatisfiesStartedAppendOnlyStep ==
  \A w \in WorkIds :
    CompleteWithNoResult(w) => StartedAppendOnlyStep
PROOF
  BY DEF CompleteWithNoResult, StartedAppendOnlyStep

THEOREM NextSatisfiesStartedAppendOnlyStep ==
  Next => StartedAppendOnlyStep
PROOF
  BY AcceptWorkSatisfiesStartedAppendOnlyStep,
     StartWorkSatisfiesStartedAppendOnlyStep,
     CompleteWithResultSatisfiesStartedAppendOnlyStep,
     CompleteWithNoResultSatisfiesStartedAppendOnlyStep
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

THEOREM AcceptWorkSatisfiesTerminalAppendOnlyStep ==
  \A w \in WorkIds :
    AcceptWork(w) => TerminalAppendOnlyStep
PROOF
  BY DEF AcceptWork, TerminalAppendOnlyStep

THEOREM StartWorkSatisfiesTerminalAppendOnlyStep ==
  \A w \in WorkIds :
    StartWork(w) => TerminalAppendOnlyStep
PROOF
  BY DEF StartWork, TerminalAppendOnlyStep

THEOREM CompleteWithResultSatisfiesTerminalAppendOnlyStep ==
  \A w \in WorkIds :
    CompleteWithResult(w) => TerminalAppendOnlyStep
PROOF
  BY DEF CompleteWithResult, TerminalAppendOnlyStep

THEOREM CompleteWithNoResultSatisfiesTerminalAppendOnlyStep ==
  \A w \in WorkIds :
    CompleteWithNoResult(w) => TerminalAppendOnlyStep
PROOF
  BY DEF CompleteWithNoResult, TerminalAppendOnlyStep

THEOREM NextSatisfiesTerminalAppendOnlyStep ==
  Next => TerminalAppendOnlyStep
PROOF
  BY AcceptWorkSatisfiesTerminalAppendOnlyStep,
     StartWorkSatisfiesTerminalAppendOnlyStep,
     CompleteWithResultSatisfiesTerminalAppendOnlyStep,
     CompleteWithNoResultSatisfiesTerminalAppendOnlyStep
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
