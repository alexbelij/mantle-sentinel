# Mantle Sentinel — Q&A Cards

## Q1: Why HDC instead of ML/neural nets?

> HDC gives us three things ML can't here: zero training, deterministic output, and algebraic feature attribution. We can tell you exactly which behavioral feature caused the alert — not a black-box confidence score.

## Q2: What about flash loans / MEV?

> Honest answer: Sentinel monitors multi-window behavioral drift. Single-transaction atomic attacks like flash loans and mempool-level MEV are out of scope by design. Those need separate, complementary systems. We document this in KNOWN_LIMITATIONS.md.

## Q3: How does this compare to Forta?

> Forta relies on community-written detection bots — each one is a signature for a known pattern. Sentinel detects behavioral deviation without any signatures. We catch the unknown unknowns. Complementary, not competing.

## Q4: Can this scale to hundreds of contracts?

> The HDC encoder is O(features × D) per window. D=10,000 is fixed. On a single core, we process a window in <50ms. Multi-contract is a scheduling problem, not a compute problem. Phase 1 roadmap.

## Q5: What if the contract is already compromised when you start monitoring?

> Known limitation #1 — warmup poisoning. If attack patterns are in the warmup window, they become "normal." Phase 3 adds operator-guided safe period labeling. For now, we recommend starting monitoring during known-good periods.
