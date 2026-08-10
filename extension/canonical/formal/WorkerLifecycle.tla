----------------------------- MODULE WorkerLifecycle -----------------------------
EXTENDS FiniteSets

CONSTANT WorkIds

VARIABLES started, resultWorks, noResultWorks

vars == <<started, resultWorks, noResultWorks>>

Init ==
    /\ started = {}
    /\ resultWorks = {}
    /\ noResultWorks = {}

Terminal == resultWorks \cup noResultWorks

StartWork(w) ==
    /\ w \in WorkIds
    /\ w \notin started
    /\ started' = started \cup {w}
    /\ UNCHANGED <<resultWorks, noResultWorks>>

EndWorkWithResult(w) ==
    /\ w \in started
    /\ w \notin Terminal
    /\ resultWorks' = resultWorks \cup {w}
    /\ UNCHANGED <<started, noResultWorks>>

EndWorkWithNoResult(w) ==
    /\ w \in started
    /\ w \notin Terminal
    /\ noResultWorks' = noResultWorks \cup {w}
    /\ UNCHANGED <<started, resultWorks>>

EndWork(w, terminalKind) ==
    \/ /\ terminalKind = "RESULT"
       /\ EndWorkWithResult(w)
    \/ /\ terminalKind = "NO_RESULT"
       /\ EndWorkWithNoResult(w)

RecognizedWorkerTransition ==
    \/ \E w \in WorkIds : StartWork(w)
    \/ \E w \in WorkIds, terminalKind \in {"RESULT", "NO_RESULT"} : EndWork(w, terminalKind)

Next == RecognizedWorkerTransition

Spec == Init /\ [][Next]_vars

TypeOK ==
    /\ started \subseteq WorkIds
    /\ resultWorks \subseteq WorkIds
    /\ noResultWorks \subseteq WorkIds

ResultImpliesStarted == resultWorks \subseteq started
NoResultImpliesStarted == noResultWorks \subseteq started
ResultXorNoResult == resultWorks \cap noResultWorks = {}

WorkerSafety ==
    /\ TypeOK
    /\ ResultImpliesStarted
    /\ NoResultImpliesStarted
    /\ ResultXorNoResult

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
