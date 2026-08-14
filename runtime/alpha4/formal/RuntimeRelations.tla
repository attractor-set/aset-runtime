--------------------------- MODULE RuntimeRelations ---------------------------
EXTENDS FiniteSets

CONSTANTS AttemptIds, AttemptDigests, RuntimeBindings, DescriptorBindings,
          TerminalDigests, TerminalBindings, EvidenceBindings

TerminalKinds == {"RESULT", "NO_RESULT"}

StartUniverse ==
  [attempt_id : AttemptIds,
   attempt_digest : AttemptDigests,
   runtime_binding : RuntimeBindings,
   descriptor_binding : DescriptorBindings]

TerminalUniverse ==
  [attempt_id : AttemptIds,
   attempt_digest : AttemptDigests,
   terminal_kind : TerminalKinds,
   terminal_digest : TerminalDigests,
   terminal_binding : TerminalBindings,
   evidence_bindings : SUBSET EvidenceBindings]

StateType == [starts : SUBSET StartUniverse, terminals : SUBSET TerminalUniverse]

SameStartIdentifier(a, b) == a.attempt_id = b.attempt_id
SameTerminalIdentifier(a, b) == a.attempt_id = b.attempt_id

StartIdentifierExists(s, start) ==
  \E current \in s.starts : SameStartIdentifier(current, start)

TerminalIdentifierExists(s, terminal) ==
  \E current \in s.terminals : SameTerminalIdentifier(current, terminal)

FreshStartIdentifier(s, start) == ~StartIdentifierExists(s, start)
ExactStartReplay(s, start) == start \in s.starts
StartConflict(s, start) ==
  /\ StartIdentifierExists(s, start)
  /\ ~ExactStartReplay(s, start)

FreshTerminalIdentifier(s, terminal) == ~TerminalIdentifierExists(s, terminal)
ExactTerminalReplay(s, terminal) == terminal \in s.terminals
TerminalConflict(s, terminal) ==
  /\ TerminalIdentifierExists(s, terminal)
  /\ ~ExactTerminalReplay(s, terminal)

MatchingStart(s, terminal) ==
  \E start \in s.starts :
    /\ start.attempt_id = terminal.attempt_id
    /\ start.attempt_digest = terminal.attempt_digest

ExactRunning(s, terminal) ==
  /\ MatchingStart(s, terminal)
  /\ FreshTerminalIdentifier(s, terminal)

StartIdentifiersUnique(s) ==
  \A a, b \in s.starts : SameStartIdentifier(a, b) => a = b

TerminalIdentifiersUnique(s) ==
  \A a, b \in s.terminals : SameTerminalIdentifier(a, b) => a = b

TerminalsBoundToStarts(s) ==
  \A terminal \in s.terminals : MatchingStart(s, terminal)

RuntimeInvariant(s) ==
  /\ s \in StateType
  /\ StartIdentifiersUnique(s)
  /\ TerminalIdentifiersUnique(s)
  /\ TerminalsBoundToStarts(s)

ResultCodes ==
  {"ATTEMPT_STARTED",
   "IDEMPOTENT_REPLAY",
   "ATTEMPT_IDENTITY_CONFLICT",
   "ATTEMPT_ENDED_WITH_RESULT",
   "ATTEMPT_ENDED_WITH_NO_RESULT",
   "TERMINAL_ATTEMPT_IMMUTABLE",
   "ATTEMPT_NOT_RUNNING"}

AcceptedResult(result) ==
  result \in
    {"ATTEMPT_STARTED",
     "IDEMPOTENT_REPLAY",
     "ATTEMPT_ENDED_WITH_RESULT",
     "ATTEMPT_ENDED_WITH_NO_RESULT"}

SeedProjectionAction(result) == "STUTTER"
SeedProjectionEffectPermitted(result) == FALSE

StartFresh(s, t, start, result) ==
  /\ RuntimeInvariant(s)
  /\ start \in StartUniverse
  /\ FreshStartIdentifier(s, start)
  /\ t = [s EXCEPT !.starts = @ \cup {start}]
  /\ result = "ATTEMPT_STARTED"

StartReplay(s, t, start, result) ==
  /\ RuntimeInvariant(s)
  /\ start \in StartUniverse
  /\ ExactStartReplay(s, start)
  /\ t = s
  /\ result = "IDEMPOTENT_REPLAY"

RejectStartConflict(s, t, start, result) ==
  /\ RuntimeInvariant(s)
  /\ start \in StartUniverse
  /\ StartConflict(s, start)
  /\ t = s
  /\ result = "ATTEMPT_IDENTITY_CONFLICT"

StartAttempt(s, t, start, result) ==
  \/ StartFresh(s, t, start, result)
  \/ StartReplay(s, t, start, result)
  \/ RejectStartConflict(s, t, start, result)

EndResult(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ terminal.terminal_kind = "RESULT"
  /\ ExactRunning(s, terminal)
  /\ t = [s EXCEPT !.terminals = @ \cup {terminal}]
  /\ result = "ATTEMPT_ENDED_WITH_RESULT"

EndNoResult(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ terminal.terminal_kind = "NO_RESULT"
  /\ ExactRunning(s, terminal)
  /\ t = [s EXCEPT !.terminals = @ \cup {terminal}]
  /\ result = "ATTEMPT_ENDED_WITH_NO_RESULT"

EndReplay(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ ExactTerminalReplay(s, terminal)
  /\ t = s
  /\ result = "IDEMPOTENT_REPLAY"

RejectEndConflict(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ TerminalConflict(s, terminal)
  /\ t = s
  /\ result = "TERMINAL_ATTEMPT_IMMUTABLE"

RejectEndNotRunning(s, t, terminal, result) ==
  /\ RuntimeInvariant(s)
  /\ terminal \in TerminalUniverse
  /\ FreshTerminalIdentifier(s, terminal)
  /\ ~MatchingStart(s, terminal)
  /\ t = s
  /\ result = "ATTEMPT_NOT_RUNNING"

EndAttempt(s, t, terminal, result) ==
  \/ EndResult(s, t, terminal, result)
  \/ EndNoResult(s, t, terminal, result)
  \/ EndReplay(s, t, terminal, result)
  \/ RejectEndConflict(s, t, terminal, result)
  \/ RejectEndNotRunning(s, t, terminal, result)

Next(s, t) ==
  \/ \E start \in StartUniverse, result \in ResultCodes : StartAttempt(s, t, start, result)
  \/ \E terminal \in TerminalUniverse, result \in ResultCodes : EndAttempt(s, t, terminal, result)

=============================================================================
