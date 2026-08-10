------------------------ MODULE WorkerSeedStuttering ------------------------
EXTENDS WorkerLifecycle

(***************************************************************************
Worker -> Seed stuttering bridge.

SeedResolution.tla is supplied externally from the exact pinned Seed release.
Every minimized Worker lifecycle operation is a stuttering step with respect
to the entire Seed projection. Worker output is not a Seed request, a Seed
resolution, Authority, or external effect permission.
***************************************************************************)

CONSTANTS ResolutionIds, Bindings, Authorities, TerminalCommitments,
          RecognizedTerminalCommitments, NoCommitment,
          RecognizedAuthorityBindings

VARIABLES requestMeta, terminalMeta, conflicts

Seed == INSTANCE SeedResolution
  WITH ResolutionIds <- ResolutionIds,
       Bindings <- Bindings,
       Authorities <- Authorities,
       TerminalCommitments <- TerminalCommitments,
       RecognizedTerminalCommitments <- RecognizedTerminalCommitments,
       NoCommitment <- NoCommitment,
       RecognizedAuthorityBindings <- RecognizedAuthorityBindings,
       requestMeta <- requestMeta,
       terminalMeta <- terminalMeta,
       conflicts <- conflicts

projectedSeedVars == <<requestMeta, terminalMeta, conflicts>>
projectedSeedOwnedVars == <<requestMeta, terminalMeta>>
compositionVars ==
  <<started, resultWorks, noResultWorks,
    requestMeta, terminalMeta, conflicts>>

WorkerStartWork(w) ==
  /\ StartWork(w)
  /\ UNCHANGED projectedSeedVars

WorkerEndWork(w, terminalKind) ==
  /\ EndWork(w, terminalKind)
  /\ UNCHANGED projectedSeedVars

WorkerOnlyAction ==
  \/ \E w \in WorkIds : WorkerStartWork(w)
  \/ \E w \in WorkIds, terminalKind \in {"RESULT", "NO_RESULT"} : WorkerEndWork(w, terminalKind)

CompositionInit ==
  /\ Init
  /\ Seed!Init

CompositionSpec ==
  CompositionInit /\ [][WorkerOnlyAction]_compositionVars

WorkerOperationsPreserveSeedProjectionStep ==
  WorkerOnlyAction => UNCHANGED projectedSeedVars

WorkerOperationsPreserveSeedOwnedStateStep ==
  WorkerOnlyAction => UNCHANGED projectedSeedOwnedVars

=============================================================================
