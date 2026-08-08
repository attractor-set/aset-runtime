------------------- MODULE WorkerCanonRefinementProofs -------------------
EXTENDS WorkerLifecycle, TLAPS

(***************************************************************************
Behavioral-equivalence proof candidate between the handwritten WorkerLifecycle
model and the standalone deterministic projection generated from the exact
machine-readable Worker canon.
***************************************************************************)

Canon == INSTANCE WorkerCanonProjection
  WITH WorkIds <- WorkIds,
       accepted <- accepted,
       started <- started,
       resultWorks <- resultWorks,
       noResultWorks <- noResultWorks

THEOREM WorkerSafetyEquivalentToCanonProjection ==
  WorkerSafety <=> Canon!CanonWorkerSafety
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         StartedImpliesAccepted,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         Canon!CanonWorkerSafety,
         Canon!CanonTypeOK,
         Canon!CanonStartedImpliesAccepted,
         Canon!CanonResultImpliesStarted,
         Canon!CanonNoResultImpliesStarted,
         Canon!CanonResultXorNoResult

THEOREM WorkerLifecycleBehaviorallyEquivalentToCanonProjection ==
  Spec <=> Canon!CanonSpec
PROOF
  BY DEF Spec,
         Init,
         Next,
         RecognizedWorkerTransition,
         AcceptWork,
         StartWork,
         CompleteWithResult,
         CompleteWithNoResult,
         Terminal,
         vars,
         Canon!CanonSpec,
         Canon!CanonInit,
         Canon!CanonNext,
         Canon!CanonRecognizedWorkerTransition,
         Canon!CanonAcceptWork,
         Canon!CanonStartWork,
         Canon!CanonCompleteWithResult,
         Canon!CanonCompleteWithNoResult,
         Canon!CanonTerminal,
         Canon!CanonVars

=============================================================================
