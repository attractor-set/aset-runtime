---------------------- MODULE SeedBoundaryProofs ----------------------
EXTENDS RuntimeRelations, TLAPS

THEOREM RuntimeProjectsOnlyToSeedStutter ==
  \A result \in ResultCodes : SeedProjectionAction(result) = "STUTTER"
PROOF
  BY DEF SeedProjectionAction

THEOREM RuntimeNeverPermitsSeedEffect ==
  \A result \in ResultCodes : SeedProjectionEffectPermitted(result) = FALSE
PROOF
  BY DEF SeedProjectionEffectPermitted

THEOREM RuntimePreservesSeedBoundary ==
  /\ RuntimeProjectsOnlyToSeedStutter
  /\ RuntimeNeverPermitsSeedEffect
PROOF
  BY RuntimeProjectsOnlyToSeedStutter, RuntimeNeverPermitsSeedEffect

=============================================================================
