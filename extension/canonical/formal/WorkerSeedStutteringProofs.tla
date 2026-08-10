------------------- MODULE WorkerSeedStutteringProofs -------------------
EXTENDS WorkerSeedStuttering, TLAPS

(***************************************************************************
Mechanical proof candidate for the minimized Worker -> Seed stuttering
relation. The exact pinned SeedResolution.tla is loaded externally by the
runner.
***************************************************************************)

THEOREM ProjectionTupleMatchesSeedVars ==
  projectedSeedVars = Seed!vars
PROOF
  BY DEF projectedSeedVars, Seed!vars

THEOREM ProjectionOwnedTupleMatchesSeedOwnedVars ==
  projectedSeedOwnedVars = Seed!seedVars
PROOF
  BY DEF projectedSeedOwnedVars, Seed!seedVars

THEOREM WorkerStartWorkPreservesSeedProjection ==
  \A w \in WorkIds :
    WorkerStartWork(w) => UNCHANGED projectedSeedVars
PROOF
  BY DEF WorkerStartWork

THEOREM WorkerEndWorkPreservesSeedProjection ==
  \A w \in WorkIds, terminalKind \in {"RESULT", "NO_RESULT"} :
    WorkerEndWork(w, terminalKind) => UNCHANGED projectedSeedVars
PROOF
  BY DEF WorkerEndWork

THEOREM WorkerOperationsPreserveSeedProjection ==
  WorkerOnlyAction => UNCHANGED projectedSeedVars
PROOF
  BY WorkerStartWorkPreservesSeedProjection,
     WorkerEndWorkPreservesSeedProjection
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
