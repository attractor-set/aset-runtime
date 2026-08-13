---------------------- MODULE WorkerSafetyProofs ----------------------
EXTENDS WorkerRelations, TLAPS

WorkerSafety(s) == s \in WorkerStateType

THEOREM EmptyStateIsSafe == WorkerSafety(EmptyWorkerState)
PROOF
  BY SMTT(30)
     DEF WorkerSafety, EmptyWorkerState, WorkerStateType, RawStateType,
         StartIdentityUnique, TerminalIdentityUnique, TerminalReferencesExactStart,
         StartsFor, TerminalsFor, StoredStartUniverse, StoredTerminalUniverse

THEOREM StartMissingPreservesSafety ==
  \A s, t, p, result : StartMissing(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF StartMissing, WorkerSafety

THEOREM StartFreshPreservesSafety ==
  \A s, t, p, result : StartFresh(s, t, p, result) => WorkerSafety(t)
PROOF
  <1>1. SUFFICES ASSUME NEW s, NEW t, NEW p, NEW result,
                         StartFresh(s, t, p, result)
                  PROVE WorkerSafety(t)
    OBVIOUS
  <1>2. s \in WorkerStateType
    BY <1>1 DEF StartFresh
  <1>3. t = [started |-> s.started \cup {p}, terminals |-> s.terminals]
    BY <1>1 DEF StartFresh
  <1>4. /\ t.started = s.started \cup {p}
         /\ t.terminals = s.terminals
    BY <1>3
  <1>5. p \in StoredStartUniverse
    BY SMTT(30), <1>1
       DEF StartFresh, ValidStartRequest, StartRequestUniverse,
           StoredStartUniverse
  <1>6. /\ s.started \subseteq StoredStartUniverse
         /\ s.terminals \subseteq StoredTerminalUniverse
         /\ StartIdentityUnique(s)
         /\ TerminalIdentityUnique(s)
         /\ TerminalReferencesExactStart(s)
    BY SMTT(30), <1>2
       DEF WorkerStateType, RawStateType
  <1>7. \A old \in s.started : old.work_id # p.work_id
    BY SMTT(30), <1>1
       DEF StartFresh, StartsFor
  <1>8. [started |-> s.started \cup {p}, terminals |-> s.terminals]
           \in RawStateType
    BY SMTT(30), <1>5, <1>6
       DEF RawStateType
  <1>9. t \in RawStateType
    BY <1>3, <1>8
  <1>10. StartIdentityUnique(t)
    BY SMTT(30), <1>4, <1>6, <1>7
       DEF StartIdentityUnique
  <1>11. TerminalIdentityUnique(t)
    BY SMTT(30), <1>4, <1>6
       DEF TerminalIdentityUnique
  <1>12. TerminalReferencesExactStart(t)
    BY SMTT(30), <1>4, <1>6
       DEF TerminalReferencesExactStart
  <1>13. QED
    BY <1>9, <1>10, <1>11, <1>12
       DEF WorkerSafety, WorkerStateType

THEOREM StartReplayPreservesSafety ==
  \A s, t, p, result : StartReplay(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF StartReplay, WorkerSafety

THEOREM StartConflictPreservesSafety ==
  \A s, t, p, result : StartConflict(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF StartConflict, WorkerSafety

THEOREM StartWorkProducesSafeState ==
  \A s, t, p, result : StartWork(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30), StartMissingPreservesSafety, StartFreshPreservesSafety,
     StartReplayPreservesSafety, StartConflictPreservesSafety
     DEF StartWork

THEOREM EndNotStartedPreservesSafety ==
  \A s, t, p, result : EndNotStarted(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF EndNotStarted, WorkerSafety

THEOREM EndBindingMismatchPreservesSafety ==
  \A s, t, p, result : EndBindingMismatch(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF EndBindingMismatch, WorkerSafety

THEOREM EndKindRequiredPreservesSafety ==
  \A s, t, p, result : EndKindRequired(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF EndKindRequired, WorkerSafety

THEOREM EndBindingRequiredPreservesSafety ==
  \A s, t, p, result : EndBindingRequired(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF EndBindingRequired, WorkerSafety

THEOREM EndResultPreservesSafety ==
  \A s, t, p, result : EndResult(s, t, p, result) => WorkerSafety(t)
PROOF
  <1>1. SUFFICES ASSUME NEW s, NEW t, NEW p, NEW result,
                         EndResult(s, t, p, result)
                  PROVE WorkerSafety(t)
    OBVIOUS
  <1>2. s \in WorkerStateType
    BY <1>1 DEF EndResult
  <1>3. t = [started |-> s.started, terminals |-> s.terminals \cup {p}]
    BY <1>1 DEF EndResult
  <1>4. /\ t.started = s.started
         /\ t.terminals = s.terminals \cup {p}
    BY <1>3
  <1>5. p \in StoredTerminalUniverse
    BY SMTT(30), <1>1
       DEF EndResult, ValidEndRequest, ValidTerminalKind, ValidTerminalBinding,
           EndRequestUniverse, StoredTerminalUniverse, TerminalKinds
  <1>6. /\ s.started \subseteq StoredStartUniverse
         /\ s.terminals \subseteq StoredTerminalUniverse
         /\ StartIdentityUnique(s)
         /\ TerminalIdentityUnique(s)
         /\ TerminalReferencesExactStart(s)
    BY SMTT(30), <1>2
       DEF WorkerStateType, RawStateType
  <1>7. \A old \in s.terminals : old.work_id # p.work_id
    BY SMTT(30), <1>1
       DEF EndResult, TerminalsFor
  <1>8. \E start \in s.started :
           /\ start.work_id = p.work_id
           /\ start.work_binding_digest = p.work_binding_digest
    BY SMTT(30), <1>1
       DEF EndResult, StartedBindingMatches, StartsFor
  <1>9. [started |-> s.started, terminals |-> s.terminals \cup {p}]
           \in RawStateType
    BY SMTT(30), <1>5, <1>6
       DEF RawStateType
  <1>10. t \in RawStateType
    BY <1>3, <1>9
  <1>11. StartIdentityUnique(t)
    BY SMTT(30), <1>4, <1>6
       DEF StartIdentityUnique
  <1>12. TerminalIdentityUnique(t)
    BY SMTT(30), <1>4, <1>6, <1>7
       DEF TerminalIdentityUnique
  <1>13. TerminalReferencesExactStart(t)
    BY SMTT(30), <1>4, <1>6, <1>8
       DEF TerminalReferencesExactStart
  <1>14. QED
    BY <1>10, <1>11, <1>12, <1>13
       DEF WorkerSafety, WorkerStateType

THEOREM EndNoResultPreservesSafety ==
  \A s, t, p, result : EndNoResult(s, t, p, result) => WorkerSafety(t)
PROOF
  <1>1. SUFFICES ASSUME NEW s, NEW t, NEW p, NEW result,
                         EndNoResult(s, t, p, result)
                  PROVE WorkerSafety(t)
    OBVIOUS
  <1>2. s \in WorkerStateType
    BY <1>1 DEF EndNoResult
  <1>3. t = [started |-> s.started, terminals |-> s.terminals \cup {p}]
    BY <1>1 DEF EndNoResult
  <1>4. /\ t.started = s.started
         /\ t.terminals = s.terminals \cup {p}
    BY <1>3
  <1>5. p \in StoredTerminalUniverse
    BY SMTT(30), <1>1
       DEF EndNoResult, ValidEndRequest, ValidTerminalKind, ValidTerminalBinding,
           EndRequestUniverse, StoredTerminalUniverse, TerminalKinds
  <1>6. /\ s.started \subseteq StoredStartUniverse
         /\ s.terminals \subseteq StoredTerminalUniverse
         /\ StartIdentityUnique(s)
         /\ TerminalIdentityUnique(s)
         /\ TerminalReferencesExactStart(s)
    BY SMTT(30), <1>2
       DEF WorkerStateType, RawStateType
  <1>7. \A old \in s.terminals : old.work_id # p.work_id
    BY SMTT(30), <1>1
       DEF EndNoResult, TerminalsFor
  <1>8. \E start \in s.started :
           /\ start.work_id = p.work_id
           /\ start.work_binding_digest = p.work_binding_digest
    BY SMTT(30), <1>1
       DEF EndNoResult, StartedBindingMatches, StartsFor
  <1>9. [started |-> s.started, terminals |-> s.terminals \cup {p}]
           \in RawStateType
    BY SMTT(30), <1>5, <1>6
       DEF RawStateType
  <1>10. t \in RawStateType
    BY <1>3, <1>9
  <1>11. StartIdentityUnique(t)
    BY SMTT(30), <1>4, <1>6
       DEF StartIdentityUnique
  <1>12. TerminalIdentityUnique(t)
    BY SMTT(30), <1>4, <1>6, <1>7
       DEF TerminalIdentityUnique
  <1>13. TerminalReferencesExactStart(t)
    BY SMTT(30), <1>4, <1>6, <1>8
       DEF TerminalReferencesExactStart
  <1>14. QED
    BY <1>10, <1>11, <1>12, <1>13
       DEF WorkerSafety, WorkerStateType

THEOREM EndReplayPreservesSafety ==
  \A s, t, p, result : EndReplay(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF EndReplay, WorkerSafety

THEOREM EndConflictPreservesSafety ==
  \A s, t, p, result : EndConflict(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30)
     DEF EndConflict, WorkerSafety

THEOREM EndWorkProducesSafeState ==
  \A s, t, p, result : EndWork(s, t, p, result) => WorkerSafety(t)
PROOF
  BY SMTT(30), EndNotStartedPreservesSafety, EndBindingMismatchPreservesSafety,
     EndKindRequiredPreservesSafety, EndBindingRequiredPreservesSafety,
     EndResultPreservesSafety, EndNoResultPreservesSafety,
     EndReplayPreservesSafety, EndConflictPreservesSafety
     DEF EndWork

THEOREM StartWorkIsAppendOnly ==
  \A s, t, p, result : StartWork(s, t, p, result) =>
    /\ s.started \subseteq t.started
    /\ s.terminals \subseteq t.terminals
PROOF
  BY SMTT(30)
     DEF StartWork, StartMissing, StartFresh, StartReplay, StartConflict

THEOREM EndWorkIsAppendOnly ==
  \A s, t, p, result : EndWork(s, t, p, result) =>
    /\ s.started \subseteq t.started
    /\ s.terminals \subseteq t.terminals
PROOF
  BY SMTT(30)
     DEF EndWork, EndNotStarted, EndBindingMismatch, EndKindRequired,
         EndBindingRequired, EndResult, EndNoResult, EndReplay, EndConflict

THEOREM WorkerTransitionsPreserveWorkerSafety ==
  /\ StartWorkProducesSafeState
  /\ EndWorkProducesSafeState
  /\ StartWorkIsAppendOnly
  /\ EndWorkIsAppendOnly
PROOF
  BY StartWorkProducesSafeState, EndWorkProducesSafeState,
     StartWorkIsAppendOnly, EndWorkIsAppendOnly

=============================================================================
