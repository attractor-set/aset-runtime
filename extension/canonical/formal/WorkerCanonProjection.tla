---------------------- MODULE WorkerCanonProjection ----------------------
EXTENDS FiniteSets

(***************************************************************************
GENERATED FILE. DO NOT EDIT.
Source: extension/canonical/source/worker-model.json
Source SHA-256: e7769e1ea41fce4ebf05f66adb03f6c048f3040ec215011c8d070b62a32b8ff0
Projection profile: ASET-WORKER-CANON-TLA-PROJECTION-V2

This standalone safety projection captures only the minimized append-only
productive-attempt lifecycle declared by the machine-readable Worker canon.
It does not interpret the opaque work descriptor, terminal payload, wire-level
digests, runtime execution, liveness, result correctness or implementation
refinement.
***************************************************************************)

CONSTANT WorkIds

VARIABLES started, resultWorks, noResultWorks

CanonVars == <<started, resultWorks, noResultWorks>>

CanonInit ==
    /\ started = {}
    /\ resultWorks = {}
    /\ noResultWorks = {}

CanonTerminal == resultWorks \cup noResultWorks

CanonStartWork(w) ==
    /\ w \in WorkIds
    /\ w \notin started
    /\ started' = started \cup {w}
    /\ UNCHANGED <<resultWorks, noResultWorks>>

CanonEndWorkWithResult(w) ==
    /\ w \in started
    /\ w \notin CanonTerminal
    /\ resultWorks' = resultWorks \cup {w}
    /\ UNCHANGED <<started, noResultWorks>>

CanonEndWorkWithNoResult(w) ==
    /\ w \in started
    /\ w \notin CanonTerminal
    /\ noResultWorks' = noResultWorks \cup {w}
    /\ UNCHANGED <<started, resultWorks>>

CanonEndWork(w, terminalKind) ==
    \/ /\ terminalKind = "RESULT"
       /\ CanonEndWorkWithResult(w)
    \/ /\ terminalKind = "NO_RESULT"
       /\ CanonEndWorkWithNoResult(w)

CanonRecognizedWorkerTransition ==
    \/ \E w \in WorkIds : CanonStartWork(w)
    \/ \E w \in WorkIds, terminalKind \in {"RESULT", "NO_RESULT"} : CanonEndWork(w, terminalKind)

CanonNext == CanonRecognizedWorkerTransition
CanonSpec == CanonInit /\ [][CanonNext]_CanonVars

CanonTypeOK ==
    /\ started \subseteq WorkIds
    /\ resultWorks \subseteq WorkIds
    /\ noResultWorks \subseteq WorkIds

CanonResultImpliesStarted == resultWorks \subseteq started
CanonNoResultImpliesStarted == noResultWorks \subseteq started
CanonResultXorNoResult == resultWorks \cap noResultWorks = {}

CanonWorkerSafety ==
    /\ CanonTypeOK
    /\ CanonResultImpliesStarted
    /\ CanonNoResultImpliesStarted
    /\ CanonResultXorNoResult

=============================================================================
