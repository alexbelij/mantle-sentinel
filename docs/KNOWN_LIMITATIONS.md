# Known Limitations

Design-scope boundaries documented during the algorithmic review (ALGO_REVIEW.md).

## 1. Warmup poisoning (W-SEC-1)
If the monitored contract is already under attack when monitoring starts, the 40%
warmup period will learn attack patterns as baseline "normal" behavior. Median/MAD
normalization partially mitigates sparse outliers but not systematic contamination.
**Mitigation (Phase 3):** Operator-guided safe period labeling.

## 2. Out-of-scope DeFi vectors (W-SEC-2)
Sentinel monitors single-contract behavioral drift. It does NOT detect:
- Flash loan attacks (single-tx atomic, no multi-tx drift)
- Sandwich / MEV (tx ordering, mempool-level)
- Oracle manipulation (cross-contract state dependency)
- Governance attacks (parameter semantics, not behavioral patterns)
These require cross-contract and mempool-level analysis — separate systems.

## 3. Frozen entropy baseline (W-SEC-3)
The entropy filter baseline is computed once during warmup and never updated.
New selectors introduced via proxy upgrades post-warmup are invisible to the
entropy tier. HDC Tier-2 and drift Tier-3 still cover behavioral changes.
**Mitigation (Phase 2):** Streaming entropy baseline with exponential decay.

## 4. Sustained high-drift suppression (W-SEC-5)
The static detector fires ONE alert per episode during sustained high-drift.
Subsequent windows above θ do not generate new alerts until drift drops and
re-triggers. By design: reduces alert noise. Individual alert timestamps and
drift values are preserved in window_stats.

## 5. Episode merging on Mantle (W-SEC-4)
EPISODE_COLLAPSE_S=600 (10 minutes ≈ 300 Mantle blocks). Multi-phase attacks
within 10 minutes merge into a single episode. Alert-level timestamps are
preserved. Configurable per-deployment via future operator settings.
