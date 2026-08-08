# Generative-verification interpretation

This document is explanatory and non-normative.

A useful intuition is a generator evaluated by a mathematical teacher:

```text
Worker
  |
  v
candidate/result material
  |
  v
evidence / verification material
  |
  v
target-local Context machine
```

The analogy is deliberately limited. This is **not GAN semantics**. The pinned Seed semantics are not a learned discriminator and are not co-optimized against the Worker. A Worker may adapt to the constraints of recognized Context evolution; those constraints do not adapt merely because the Worker repeatedly fails to satisfy them.

A closer technical analogy is candidate generation or synthesis under an external verifier. Even that analogy is only explanatory: the Worker extension itself does not define a verifier or a learning algorithm.

Two distinct questions must remain separate:

```text
optimization:  which produced material appears better?
admissibility: which consequential change may be recognized?
```

Worker standardizes the productive side of the boundary, not the normative decision.
