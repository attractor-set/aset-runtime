------------------------ MODULE SeedInheritance ------------------------
EXTENDS WorkerRelations

CONSTANTS Subjects, Authorities, EvidenceItems, AuthorityRecognition

Seed == INSTANCE ComponentRelations
  WITH Subjects <- Subjects,
       Authorities <- Authorities,
       EvidenceItems <- EvidenceItems,
       AuthorityRecognition <- AuthorityRecognition

SeedStateType == Seed!StateType

SeedStutter(seedBefore, seedAfter) ==
  /\ seedBefore \in SeedStateType
  /\ seedAfter = seedBefore

InheritedStartWork(workerBefore, workerAfter, request, result, seedBefore, seedAfter) ==
  /\ StartWork(workerBefore, workerAfter, request, result)
  /\ SeedStutter(seedBefore, seedAfter)

InheritedEndWork(workerBefore, workerAfter, request, result, seedBefore, seedAfter) ==
  /\ EndWork(workerBefore, workerAfter, request, result)
  /\ SeedStutter(seedBefore, seedAfter)

=============================================================================
