------------------- MODULE WorkerSeedStutteringProofs -------------------
EXTENDS WorkerSeedStuttering, TLAPS

(***************************************************************************
Mechanical proof candidate for the Worker -> Seed stuttering relation.

The exact pinned SeedResolution.tla is loaded externally by the runner. This
proof covers only Worker lifecycle actions and their Seed projection. It does
not prove implementation refinement, wire-level digest correctness, liveness,
result quality, effect execution, or Authority establishment mechanisms.
***************************************************************************)

THEOREM ProjectionTupleMatchesSeedVars ==
  projectedSeedVars = Seed!vars
PROOF
  BY DEF projectedSeedVars, Seed!vars

THEOREM ProjectionOwnedTupleMatchesSeedOwnedVars ==
  projectedSeedOwnedVars = Seed!seedVars
PROOF
  BY DEF projectedSeedOwnedVars, Seed!seedVars

THEOREM WorkerAcceptWorkPreservesSeedProjection ==
  \A w \in WorkIds :
    WorkerAcceptWork(w) => UNCHANGED projectedSeedVars
PROOF
  BY DEF WorkerAcceptWork

THEOREM WorkerStartWorkPreservesSeedProjection ==
  \A w \in WorkIds :
    WorkerStartWork(w) => UNCHANGED projectedSeedVars
PROOF
  BY DEF WorkerStartWork

THEOREM WorkerCompleteWithResultPreservesSeedProjection ==
  \A w \in WorkIds :
    WorkerCompleteWithResult(w) => UNCHANGED projectedSeedVars
PROOF
  BY DEF WorkerCompleteWithResult

THEOREM WorkerCompleteWithNoResultPreservesSeedProjection ==
  \A w \in WorkIds :
    WorkerCompleteWithNoResult(w) => UNCHANGED projectedSeedVars
PROOF
  BY DEF WorkerCompleteWithNoResult

THEOREM WorkerOperationsPreserveSeedProjection ==
  WorkerOnlyAction => UNCHANGED projectedSeedVars
PROOF
  BY WorkerAcceptWorkPreservesSeedProjection,
     WorkerStartWorkPreservesSeedProjection,
     WorkerCompleteWithResultPreservesSeedProjection,
     WorkerCompleteWithNoResultPreservesSeedProjection
     DEF WorkerOnlyAction

THEOREM WorkerOperationsPreserveSeedOwnedState ==
  WorkerOnlyAction => UNCHANGED projectedSeedOwnedVars
PROOF
  BY WorkerOperationsPreserveSeedProjection
     DEF projectedSeedVars, projectedSeedOwnedVars

THEOREM CompositionStateStutterPreservesSeedProjection ==
  UNCHANGED compositionVars => UNCHANGED projectedSeedVars
PROOF
  BY DEF compositionVars, projectedSeedVars

THEOREM WorkerBoxStepIsProjectedSeedBoxStep ==
  [WorkerOnlyAction]_compositionVars => [Seed!Next]_projectedSeedVars
PROOF
  BY WorkerOperationsPreserveSeedProjection,
     CompositionStateStutterPreservesSeedProjection
     DEF compositionVars, projectedSeedVars

THEOREM WorkerBoxStepIsSeedBoxStep ==
  [WorkerOnlyAction]_compositionVars => [Seed!Next]_Seed!vars
PROOF
  BY WorkerBoxStepIsProjectedSeedBoxStep
     DEF Seed!vars, projectedSeedVars

THEOREM WorkerCompositionRefinesSeedResolutionByStuttering ==
  CompositionSpec => Seed!Spec
PROOF
  BY PTL,
     WorkerBoxStepIsSeedBoxStep,
     ProjectionTupleMatchesSeedVars
     DEF CompositionSpec, CompositionInit, Seed!Spec

=============================================================================
