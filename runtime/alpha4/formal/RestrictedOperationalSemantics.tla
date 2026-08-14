-------------------- MODULE RestrictedOperationalSemantics --------------------
EXTENDS RuntimeRelations

OperationalStartFresh(s, t, start, result) ==
  /\ RuntimeInvariant(s)
  /\ start \in StartUniverse
  /\ FreshStartIdentifier(s, start)
  /\ t = [s EXCEPT !.starts = @ \cup {start}]
  /\ result = "ATTEMPT_STARTED"

OperationalStartReplay(s, t, start, result) ==
  /\ RuntimeInvariant(s)
  /\ start \in StartUniverse
  /\ ExactStartReplay(s, start)
  /\ t = s
  /\ result = "IDEMPOTENT_REPLAY"

OperationalRejectStartConflict(s, t, start, result) ==
  /\ RuntimeInvariant(s)
  /\ start \in StartUniverse
  /\ StartConflict(s, start)
  /\ t = s
  /\ result = "ATTEMPT_IDENTITY_CONFLICT"

OperationalEndResult(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ terminal.terminal_kind = "RESULT"
  /\ ExactRunning(s, terminal)
  /\ t = [s EXCEPT !.terminals = @ \cup {terminal}]
  /\ result = "ATTEMPT_ENDED_WITH_RESULT"

OperationalEndNoResult(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ terminal.terminal_kind = "NO_RESULT"
  /\ ExactRunning(s, terminal)
  /\ t = [s EXCEPT !.terminals = @ \cup {terminal}]
  /\ result = "ATTEMPT_ENDED_WITH_NO_RESULT"

OperationalEndReplay(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ ExactTerminalReplay(s, terminal)
  /\ t = s
  /\ result = "IDEMPOTENT_REPLAY"

OperationalRejectEndConflict(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ TerminalConflict(s, terminal)
  /\ t = s
  /\ result = "TERMINAL_ATTEMPT_IMMUTABLE"

OperationalRejectEndNotRunning(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ FreshTerminalIdentifier(s, terminal)
  /\ ~MatchingStart(s, terminal)
  /\ t = s
  /\ result = "ATTEMPT_NOT_RUNNING"

=============================================================================
