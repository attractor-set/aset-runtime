---------------------- MODULE WorkerSeedStuttering ----------------------
EXTENDS WorkerLifecycle

(***************************************************************************
Refinement bridge from Worker-only lifecycle transitions to the exact pinned
ASET SeedResolution model.

SeedResolution.tla is intentionally NOT vendored here. The proof runner loads
it from a separately supplied Seed checkout and verifies its SHA-256 against
the pinned upstream binding before invoking TLAPS.

The bridge proves the narrow extension claim: every Worker lifecycle operation
is a stuttering step with respect to the entire Seed projection. It does not
claim that Worker output is a Seed request, a Seed resolution, Authority, or an
external effect permission.
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
  <<accepted, started, resultWorks, noResultWorks,
    requestMeta, terminalMeta, conflicts>>

WorkerAcceptWork(w) ==
  /\ AcceptWork(w)
  /\ UNCHANGED projectedSeedVars

WorkerStartWork(w) ==
  /\ StartWork(w)
  /\ UNCHANGED projectedSeedVars

WorkerCompleteWithResult(w) ==
  /\ CompleteWithResult(w)
  /\ UNCHANGED projectedSeedVars

WorkerCompleteWithNoResult(w) ==
  /\ CompleteWithNoResult(w)
  /\ UNCHANGED projectedSeedVars

WorkerOnlyAction ==
  \/ \E w \in WorkIds : WorkerAcceptWork(w)
  \/ \E w \in WorkIds : WorkerStartWork(w)
  \/ \E w \in WorkIds : WorkerCompleteWithResult(w)
  \/ \E w \in WorkIds : WorkerCompleteWithNoResult(w)

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
