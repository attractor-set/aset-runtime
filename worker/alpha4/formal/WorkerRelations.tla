-------------------------- MODULE WorkerRelations --------------------------
EXTENDS FiniteSets

CONSTANTS WorkIds, WorkBindingDigests, WorkerBindings, DescriptorBindings,
          TerminalRecordDigests, TerminalBindings, EvidenceBundles, NoValue

TerminalKinds == {"RESULT", "NO_RESULT"}
ResultCodes == {"WORK_BINDING_REQUIRED", "WORK_STARTED", "IDEMPOTENT_REPLAY",
               "WORK_IDENTITY_CONFLICT", "WORK_NOT_STARTED", "WORK_BINDING_MISMATCH",
               "TERMINAL_KIND_REQUIRED", "TERMINAL_BINDING_REQUIRED",
               "WORK_ENDED_WITH_RESULT", "WORK_ENDED_WITH_NO_RESULT",
               "TERMINAL_WORK_IMMUTABLE"}

ASSUME /\ WorkIds # {}
       /\ WorkBindingDigests # {}
       /\ WorkerBindings # {}
       /\ DescriptorBindings # {}
       /\ TerminalRecordDigests # {}
       /\ TerminalBindings # {}
       /\ EvidenceBundles # {}
       /\ NoValue \notin WorkIds
       /\ NoValue \notin WorkBindingDigests
       /\ NoValue \notin WorkerBindings
       /\ NoValue \notin DescriptorBindings
       /\ NoValue \notin TerminalRecordDigests
       /\ NoValue \notin TerminalBindings
       /\ NoValue \notin EvidenceBundles
       /\ NoValue \notin TerminalKinds

StartRequestUniverse ==
  [work_id : WorkIds \cup {NoValue},
   work_binding_digest : WorkBindingDigests \cup {NoValue},
   worker_binding : WorkerBindings \cup {NoValue},
   work_descriptor_binding : DescriptorBindings \cup {NoValue}]

StoredStartUniverse ==
  [work_id : WorkIds,
   work_binding_digest : WorkBindingDigests,
   worker_binding : WorkerBindings,
   work_descriptor_binding : DescriptorBindings]

EndRequestUniverse ==
  [work_id : WorkIds \cup {NoValue},
   work_binding_digest : WorkBindingDigests \cup {NoValue},
   terminal_kind : TerminalKinds \cup {NoValue},
   terminal_record_digest : TerminalRecordDigests \cup {NoValue},
   terminal_binding : TerminalBindings \cup {NoValue},
   evidence_bindings : EvidenceBundles \cup {NoValue}]

StoredTerminalUniverse ==
  [work_id : WorkIds,
   work_binding_digest : WorkBindingDigests,
   terminal_kind : TerminalKinds,
   terminal_record_digest : TerminalRecordDigests,
   terminal_binding : TerminalBindings,
   evidence_bindings : EvidenceBundles \cup {NoValue}]

RawStateType ==
  [started : SUBSET StoredStartUniverse,
   terminals : SUBSET StoredTerminalUniverse]

StartsFor(s, w) == {x \in s.started : x.work_id = w}
TerminalsFor(s, w) == {x \in s.terminals : x.work_id = w}

StartIdentityUnique(s) ==
  \A left \in s.started :
    \A right \in s.started :
      left.work_id = right.work_id => left = right

TerminalIdentityUnique(s) ==
  \A left \in s.terminals :
    \A right \in s.terminals :
      left.work_id = right.work_id => left = right

TerminalReferencesExactStart(s) ==
  \A terminal \in s.terminals :
    \E start \in s.started :
      /\ terminal.work_id = start.work_id
      /\ terminal.work_binding_digest = start.work_binding_digest

WorkerStateType ==
  {s \in RawStateType :
    /\ StartIdentityUnique(s)
    /\ TerminalIdentityUnique(s)
    /\ TerminalReferencesExactStart(s)}

EmptyWorkerState == [started |-> {}, terminals |-> {}]

ValidStartRequest(p) ==
  /\ p \in StartRequestUniverse
  /\ p.work_id # NoValue
  /\ p.work_binding_digest # NoValue
  /\ p.worker_binding # NoValue
  /\ p.work_descriptor_binding # NoValue

ValidTerminalKind(p) ==
  /\ p \in EndRequestUniverse
  /\ p.terminal_kind \in TerminalKinds

ValidTerminalBinding(p) ==
  /\ p \in EndRequestUniverse
  /\ p.terminal_record_digest # NoValue
  /\ p.terminal_binding # NoValue

ValidEndRequest(p) ==
  /\ p \in EndRequestUniverse
  /\ p.work_id # NoValue
  /\ p.work_binding_digest # NoValue
  /\ ValidTerminalKind(p)
  /\ ValidTerminalBinding(p)

StartedBindingMatches(s, p) ==
  \E start \in StartsFor(s, p.work_id) :
    p.work_binding_digest = start.work_binding_digest

StartMissing(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ p \in StartRequestUniverse
  /\ ~ValidStartRequest(p)
  /\ t = s
  /\ result = "WORK_BINDING_REQUIRED"

StartFresh(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ ValidStartRequest(p)
  /\ StartsFor(s, p.work_id) = {}
  /\ t = [started |-> s.started \cup {p},
           terminals |-> s.terminals]
  /\ result = "WORK_STARTED"

StartReplay(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ ValidStartRequest(p)
  /\ p \in s.started
  /\ t = s
  /\ result = "IDEMPOTENT_REPLAY"

StartConflict(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ ValidStartRequest(p)
  /\ StartsFor(s, p.work_id) # {}
  /\ p \notin s.started
  /\ t = s
  /\ result = "WORK_IDENTITY_CONFLICT"

StartWork(s, t, p, result) ==
  \/ StartMissing(s, t, p, result)
  \/ StartFresh(s, t, p, result)
  \/ StartReplay(s, t, p, result)
  \/ StartConflict(s, t, p, result)

EndNotStarted(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ p \in EndRequestUniverse
  /\ StartsFor(s, p.work_id) = {}
  /\ t = s
  /\ result = "WORK_NOT_STARTED"

EndBindingMismatch(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ p \in EndRequestUniverse
  /\ StartsFor(s, p.work_id) # {}
  /\ ~StartedBindingMatches(s, p)
  /\ t = s
  /\ result = "WORK_BINDING_MISMATCH"

EndKindRequired(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ p \in EndRequestUniverse
  /\ StartsFor(s, p.work_id) # {}
  /\ StartedBindingMatches(s, p)
  /\ p.terminal_kind = NoValue
  /\ t = s
  /\ result = "TERMINAL_KIND_REQUIRED"

EndBindingRequired(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ p \in EndRequestUniverse
  /\ StartsFor(s, p.work_id) # {}
  /\ StartedBindingMatches(s, p)
  /\ ValidTerminalKind(p)
  /\ ~ValidTerminalBinding(p)
  /\ t = s
  /\ result = "TERMINAL_BINDING_REQUIRED"

EndResult(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ ValidEndRequest(p)
  /\ StartedBindingMatches(s, p)
  /\ TerminalsFor(s, p.work_id) = {}
  /\ p.terminal_kind = "RESULT"
  /\ t = [started |-> s.started,
           terminals |-> s.terminals \cup {p}]
  /\ result = "WORK_ENDED_WITH_RESULT"

EndNoResult(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ ValidEndRequest(p)
  /\ StartedBindingMatches(s, p)
  /\ TerminalsFor(s, p.work_id) = {}
  /\ p.terminal_kind = "NO_RESULT"
  /\ t = [started |-> s.started,
           terminals |-> s.terminals \cup {p}]
  /\ result = "WORK_ENDED_WITH_NO_RESULT"

EndReplay(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ ValidEndRequest(p)
  /\ StartedBindingMatches(s, p)
  /\ p \in s.terminals
  /\ t = s
  /\ result = "IDEMPOTENT_REPLAY"

EndConflict(s, t, p, result) ==
  /\ s \in WorkerStateType
  /\ ValidEndRequest(p)
  /\ StartedBindingMatches(s, p)
  /\ TerminalsFor(s, p.work_id) # {}
  /\ p \notin s.terminals
  /\ t = s
  /\ result = "TERMINAL_WORK_IMMUTABLE"

EndWork(s, t, p, result) ==
  \/ EndNotStarted(s, t, p, result)
  \/ EndBindingMismatch(s, t, p, result)
  \/ EndKindRequired(s, t, p, result)
  \/ EndBindingRequired(s, t, p, result)
  \/ EndResult(s, t, p, result)
  \/ EndNoResult(s, t, p, result)
  \/ EndReplay(s, t, p, result)
  \/ EndConflict(s, t, p, result)

RecognizedResult(result) ==
  result \in {"WORK_STARTED", "WORK_ENDED_WITH_RESULT",
              "WORK_ENDED_WITH_NO_RESULT", "IDEMPOTENT_REPLAY"}

WorkerCreatesAuthority(result) == FALSE
WorkerPermitsExternalEffect(result) == FALSE
WorkerCreatesSeedRecognition(result) == FALSE

=============================================================================
