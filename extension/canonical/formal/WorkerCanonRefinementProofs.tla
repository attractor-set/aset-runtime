------------------- MODULE WorkerCanonRefinementProofs -------------------
EXTENDS WorkerLifecycle, TLAPS

(***************************************************************************
Behavioral-equivalence proof candidate between the handwritten minimized
WorkerLifecycle model and the standalone deterministic projection generated
from the exact machine-readable Worker canon.
***************************************************************************)

Canon == INSTANCE WorkerCanonProjection
  WITH WorkIds <- WorkIds,
       started <- started,
       resultWorks <- resultWorks,
       noResultWorks <- noResultWorks

THEOREM WorkerSafetyEquivalentToCanonProjection ==
  WorkerSafety <=> Canon!CanonWorkerSafety
PROOF
  BY DEF WorkerSafety,
         TypeOK,
         ResultImpliesStarted,
         NoResultImpliesStarted,
         ResultXorNoResult,
         Canon!CanonWorkerSafety,
         Canon!CanonTypeOK,
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
         StartWork,
         EndWork,
         EndWorkWithResult,
         EndWorkWithNoResult,
         Terminal,
         vars,
         Canon!CanonSpec,
         Canon!CanonInit,
         Canon!CanonNext,
         Canon!CanonRecognizedWorkerTransition,
         Canon!CanonStartWork,
         Canon!CanonEndWork,
         Canon!CanonEndWorkWithResult,
         Canon!CanonEndWorkWithNoResult,
         Canon!CanonTerminal,
         Canon!CanonVars

=============================================================================
