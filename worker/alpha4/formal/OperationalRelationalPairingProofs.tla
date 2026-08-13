-------------- MODULE OperationalRelationalPairingProofs --------------
EXTENDS RestrictedOperationalSemantics, TLAPS

THEOREM StartMissingPairing ==
  \A s, t, p, result : OperationalStartMissing(s, t, p, result) <=> StartMissing(s, t, p, result)
PROOF BY DEF OperationalStartMissing

THEOREM StartFreshPairing ==
  \A s, t, p, result : OperationalStartFresh(s, t, p, result) <=> StartFresh(s, t, p, result)
PROOF BY DEF OperationalStartFresh

THEOREM StartReplayPairing ==
  \A s, t, p, result : OperationalStartReplay(s, t, p, result) <=> StartReplay(s, t, p, result)
PROOF BY DEF OperationalStartReplay

THEOREM StartConflictPairing ==
  \A s, t, p, result : OperationalStartConflict(s, t, p, result) <=> StartConflict(s, t, p, result)
PROOF BY DEF OperationalStartConflict

THEOREM EndNotStartedPairing ==
  \A s, t, p, result : OperationalEndNotStarted(s, t, p, result) <=> EndNotStarted(s, t, p, result)
PROOF BY DEF OperationalEndNotStarted

THEOREM EndBindingMismatchPairing ==
  \A s, t, p, result : OperationalEndBindingMismatch(s, t, p, result) <=> EndBindingMismatch(s, t, p, result)
PROOF BY DEF OperationalEndBindingMismatch

THEOREM EndKindRequiredPairing ==
  \A s, t, p, result : OperationalEndKindRequired(s, t, p, result) <=> EndKindRequired(s, t, p, result)
PROOF BY DEF OperationalEndKindRequired

THEOREM EndBindingRequiredPairing ==
  \A s, t, p, result : OperationalEndBindingRequired(s, t, p, result) <=> EndBindingRequired(s, t, p, result)
PROOF BY DEF OperationalEndBindingRequired

THEOREM EndResultPairing ==
  \A s, t, p, result : OperationalEndResult(s, t, p, result) <=> EndResult(s, t, p, result)
PROOF BY DEF OperationalEndResult

THEOREM EndNoResultPairing ==
  \A s, t, p, result : OperationalEndNoResult(s, t, p, result) <=> EndNoResult(s, t, p, result)
PROOF BY DEF OperationalEndNoResult

THEOREM EndReplayPairing ==
  \A s, t, p, result : OperationalEndReplay(s, t, p, result) <=> EndReplay(s, t, p, result)
PROOF BY DEF OperationalEndReplay

THEOREM EndConflictPairing ==
  \A s, t, p, result : OperationalEndConflict(s, t, p, result) <=> EndConflict(s, t, p, result)
PROOF BY DEF OperationalEndConflict

THEOREM OperationalRelationalPairing ==
  /\ StartMissingPairing
  /\ StartFreshPairing
  /\ StartReplayPairing
  /\ StartConflictPairing
  /\ EndNotStartedPairing
  /\ EndBindingMismatchPairing
  /\ EndKindRequiredPairing
  /\ EndBindingRequiredPairing
  /\ EndResultPairing
  /\ EndNoResultPairing
  /\ EndReplayPairing
  /\ EndConflictPairing
PROOF
  BY StartMissingPairing, StartFreshPairing, StartReplayPairing, StartConflictPairing,
     EndNotStartedPairing, EndBindingMismatchPairing, EndKindRequiredPairing,
     EndBindingRequiredPairing, EndResultPairing, EndNoResultPairing,
     EndReplayPairing, EndConflictPairing

=============================================================================
