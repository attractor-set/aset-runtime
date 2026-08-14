-------------- MODULE OperationalRelationalPairingProofs --------------
EXTENDS RestrictedOperationalSemantics, TLAPS

THEOREM StartFreshPairing ==
  \A s, t, start, result :
    OperationalStartFresh(s, t, start, result) <=> StartFresh(s, t, start, result)
PROOF
  BY DEF OperationalStartFresh, StartFresh

THEOREM StartReplayPairing ==
  \A s, t, start, result :
    OperationalStartReplay(s, t, start, result) <=> StartReplay(s, t, start, result)
PROOF
  BY DEF OperationalStartReplay, StartReplay

THEOREM RejectStartConflictPairing ==
  \A s, t, start, result :
    OperationalRejectStartConflict(s, t, start, result) <=> RejectStartConflict(s, t, start, result)
PROOF
  BY DEF OperationalRejectStartConflict, RejectStartConflict

THEOREM EndResultPairing ==
  \A s, t, terminal, result :
    OperationalEndResult(s, t, terminal, result) <=> EndResult(s, t, terminal, result)
PROOF
  BY DEF OperationalEndResult, EndResult

THEOREM EndNoResultPairing ==
  \A s, t, terminal, result :
    OperationalEndNoResult(s, t, terminal, result) <=> EndNoResult(s, t, terminal, result)
PROOF
  BY DEF OperationalEndNoResult, EndNoResult

THEOREM EndReplayPairing ==
  \A s, t, terminal, result :
    OperationalEndReplay(s, t, terminal, result) <=> EndReplay(s, t, terminal, result)
PROOF
  BY DEF OperationalEndReplay, EndReplay

THEOREM RejectEndConflictPairing ==
  \A s, t, terminal, result :
    OperationalRejectEndConflict(s, t, terminal, result) <=> RejectEndConflict(s, t, terminal, result)
PROOF
  BY DEF OperationalRejectEndConflict, RejectEndConflict

THEOREM RejectEndNotRunningPairing ==
  \A s, t, terminal, result :
    OperationalRejectEndNotRunning(s, t, terminal, result)
      <=> RejectEndNotRunning(s, t, terminal, result)
PROOF
  BY DEF OperationalRejectEndNotRunning, RejectEndNotRunning

THEOREM OperationalRelationalPairing ==
  /\ StartFreshPairing
  /\ StartReplayPairing
  /\ RejectStartConflictPairing
  /\ EndResultPairing
  /\ EndNoResultPairing
  /\ EndReplayPairing
  /\ RejectEndConflictPairing
  /\ RejectEndNotRunningPairing
PROOF
  BY StartFreshPairing,
     StartReplayPairing,
     RejectStartConflictPairing,
     EndResultPairing,
     EndNoResultPairing,
     EndReplayPairing,
     RejectEndConflictPairing,
     RejectEndNotRunningPairing

=============================================================================
