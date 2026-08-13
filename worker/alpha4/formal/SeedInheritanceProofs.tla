------------------- MODULE SeedInheritanceProofs -------------------
EXTENDS SeedInheritance, TLAPS

THEOREM StartWorkPreservesExactSeedState ==
  \A wb, wa, request, result, sb, sa :
    InheritedStartWork(wb, wa, request, result, sb, sa) => sa = sb
PROOF BY DEF InheritedStartWork, SeedStutter

THEOREM EndWorkPreservesExactSeedState ==
  \A wb, wa, request, result, sb, sa :
    InheritedEndWork(wb, wa, request, result, sb, sa) => sa = sb
PROOF BY DEF InheritedEndWork, SeedStutter

THEOREM StartWorkPreservesSeedAuthorityRecognitionAndEffect ==
  \A wb, wa, request, result, sb, sa :
    InheritedStartWork(wb, wa, request, result, sb, sa) =>
      /\ sa.subject = sb.subject
      /\ sa.authority = sb.authority
      /\ sa.recognition = sb.recognition
      /\ sa.evidence = sb.evidence
      /\ Seed!EffectPermitted(sa) = Seed!EffectPermitted(sb)
PROOF BY StartWorkPreservesExactSeedState

THEOREM EndWorkPreservesSeedAuthorityRecognitionAndEffect ==
  \A wb, wa, request, result, sb, sa :
    InheritedEndWork(wb, wa, request, result, sb, sa) =>
      /\ sa.subject = sb.subject
      /\ sa.authority = sb.authority
      /\ sa.recognition = sb.recognition
      /\ sa.evidence = sb.evidence
      /\ Seed!EffectPermitted(sa) = Seed!EffectPermitted(sb)
PROOF BY EndWorkPreservesExactSeedState

THEOREM WorkerNeverCreatesAuthority ==
  \A result : WorkerCreatesAuthority(result) = FALSE
PROOF BY DEF WorkerCreatesAuthority

THEOREM WorkerNeverPermitsExternalEffect ==
  \A result : WorkerPermitsExternalEffect(result) = FALSE
PROOF BY DEF WorkerPermitsExternalEffect

THEOREM WorkerNeverCreatesSeedRecognition ==
  \A result : WorkerCreatesSeedRecognition(result) = FALSE
PROOF BY DEF WorkerCreatesSeedRecognition

THEOREM WorkerTransitionsInheritSeedByStuttering ==
  /\ StartWorkPreservesSeedAuthorityRecognitionAndEffect
  /\ EndWorkPreservesSeedAuthorityRecognitionAndEffect
  /\ WorkerNeverCreatesAuthority
  /\ WorkerNeverPermitsExternalEffect
  /\ WorkerNeverCreatesSeedRecognition
PROOF
  BY StartWorkPreservesSeedAuthorityRecognitionAndEffect,
     EndWorkPreservesSeedAuthorityRecognitionAndEffect,
     WorkerNeverCreatesAuthority, WorkerNeverPermitsExternalEffect,
     WorkerNeverCreatesSeedRecognition

=============================================================================
