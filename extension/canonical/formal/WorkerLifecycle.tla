----------------------------- MODULE WorkerLifecycle -----------------------------
EXTENDS FiniteSets

CONSTANT WorkIds

VARIABLES accepted, started, resultWorks, noResultWorks

vars == <<accepted, started, resultWorks, noResultWorks>>

Init ==
    /\ accepted = {}
    /\ started = {}
    /\ resultWorks = {}
    /\ noResultWorks = {}

Terminal == resultWorks \cup noResultWorks

AcceptWork(w) ==
    /\ w \in WorkIds
    /\ w \notin accepted
    /\ accepted' = accepted \cup {w}
    /\ UNCHANGED <<started, resultWorks, noResultWorks>>

StartWork(w) ==
    /\ w \in accepted
    /\ w \notin started
    /\ w \notin Terminal
    /\ started' = started \cup {w}
    /\ UNCHANGED <<accepted, resultWorks, noResultWorks>>

CompleteWithResult(w) ==
    /\ w \in started
    /\ w \notin Terminal
    /\ resultWorks' = resultWorks \cup {w}
    /\ UNCHANGED <<accepted, started, noResultWorks>>

CompleteWithNoResult(w) ==
    /\ w \in started
    /\ w \notin Terminal
    /\ noResultWorks' = noResultWorks \cup {w}
    /\ UNCHANGED <<accepted, started, resultWorks>>

RecognizedWorkerTransition ==
    \/ \E w \in WorkIds : AcceptWork(w)
    \/ \E w \in WorkIds : StartWork(w)
    \/ \E w \in WorkIds : CompleteWithResult(w)
    \/ \E w \in WorkIds : CompleteWithNoResult(w)

Next == RecognizedWorkerTransition

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ accepted \subseteq WorkIds
    /\ started \subseteq WorkIds
    /\ resultWorks \subseteq WorkIds
    /\ noResultWorks \subseteq WorkIds

StartedImpliesAccepted == started \subseteq accepted
ResultImpliesStarted == resultWorks \subseteq started
NoResultImpliesStarted == noResultWorks \subseteq started
ResultXorNoResult == resultWorks \cap noResultWorks = {}

WorkerSafety ==
    /\ TypeOK
    /\ StartedImpliesAccepted
    /\ ResultImpliesStarted
    /\ NoResultImpliesStarted
    /\ ResultXorNoResult

AcceptedAppendOnlyStep == accepted \subseteq accepted'
AcceptedAppendOnly == [][AcceptedAppendOnlyStep]_vars

StartedAppendOnlyStep == started \subseteq started'
StartedAppendOnly == [][StartedAppendOnlyStep]_vars

TerminalAppendOnlyStep ==
    /\ resultWorks \subseteq resultWorks'
    /\ noResultWorks \subseteq noResultWorks'
TerminalAppendOnly == [][TerminalAppendOnlyStep]_vars

WorkerStateChangesOnlyByRecognizedTransitionStep ==
    vars' # vars => RecognizedWorkerTransition

WorkerStateChangesOnlyByRecognizedTransition ==
    [][WorkerStateChangesOnlyByRecognizedTransitionStep]_vars

=============================================================================
