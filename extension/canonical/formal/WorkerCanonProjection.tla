---------------------- MODULE WorkerCanonProjection ----------------------
EXTENDS FiniteSets

(***************************************************************************
GENERATED FILE. DO NOT EDIT.
Source: extension/canonical/source/worker-model.json
Source SHA-256: a5d5c842cace0a0a3ad0b43ce913117f55eea403a542d5b8c8faf33fde8d2e77
Projection profile: ASET-WORKER-CANON-TLA-PROJECTION-V1

This is a standalone safety projection generated from the exact machine-
readable Worker canon. It does not EXTEND or instantiate WorkerLifecycle.
WorkerCanonRefinementProofs.tla explicitly instantiates this generated module
onto the handwritten assurance state.

Wire-level digest construction, exact metadata payloads, runtime execution,
liveness, result correctness and implementation refinement remain outside this
projection. The deterministic generator is part of the assurance trusted
computing base.
***************************************************************************)

CONSTANT WorkIds

VARIABLES accepted, started, resultWorks, noResultWorks

CanonVars == <<accepted, started, resultWorks, noResultWorks>>

CanonInit ==
    /\ accepted = {}
    /\ started = {}
    /\ resultWorks = {}
    /\ noResultWorks = {}

CanonTerminal == resultWorks \cup noResultWorks

CanonAcceptWork(w) ==
    /\ w \in WorkIds
    /\ w \notin accepted
    /\ accepted' = accepted \cup {w}
    /\ UNCHANGED <<started, resultWorks, noResultWorks>>

CanonStartWork(w) ==
    /\ w \in accepted
    /\ w \notin started
    /\ w \notin CanonTerminal
    /\ started' = started \cup {w}
    /\ UNCHANGED <<accepted, resultWorks, noResultWorks>>

CanonCompleteWithResult(w) ==
    /\ w \in started
    /\ w \notin CanonTerminal
    /\ resultWorks' = resultWorks \cup {w}
    /\ UNCHANGED <<accepted, started, noResultWorks>>

CanonCompleteWithNoResult(w) ==
    /\ w \in started
    /\ w \notin CanonTerminal
    /\ noResultWorks' = noResultWorks \cup {w}
    /\ UNCHANGED <<accepted, started, resultWorks>>

CanonRecognizedWorkerTransition ==
    \/ \E w \in WorkIds : CanonAcceptWork(w)
    \/ \E w \in WorkIds : CanonStartWork(w)
    \/ \E w \in WorkIds : CanonCompleteWithResult(w)
    \/ \E w \in WorkIds : CanonCompleteWithNoResult(w)

CanonNext == CanonRecognizedWorkerTransition
CanonSpec == CanonInit /\ [][CanonNext]_CanonVars

CanonTypeOK ==
    /\ accepted \subseteq WorkIds
    /\ started \subseteq WorkIds
    /\ resultWorks \subseteq WorkIds
    /\ noResultWorks \subseteq WorkIds

CanonStartedImpliesAccepted == started \subseteq accepted
CanonResultImpliesStarted == resultWorks \subseteq started
CanonNoResultImpliesStarted == noResultWorks \subseteq started
CanonResultXorNoResult == resultWorks \cap noResultWorks = {}

CanonWorkerSafety ==
    /\ CanonTypeOK
    /\ CanonStartedImpliesAccepted
    /\ CanonResultImpliesStarted
    /\ CanonNoResultImpliesStarted
    /\ CanonResultXorNoResult

=============================================================================
