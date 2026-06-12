# DECISIONS.md — Spec-Gap Decision Log

Format: `D-NN | date | gap | choice | rationale` (one line each). Curator audits this file every review.

D-01 | 2026-06-13 | Tier 5 attribution method unspecified | Feature-ablation contribution (MVP_MATH_SPEC §5) | avoids unbinding complexity; testable per scenario
D-02 | 2026-06-13 | HDC dimension | D=10,000 (was 4,096 in first spec draft) | panel consensus; cost negligible at MVP scale
D-03 | 2026-06-13 | timing/drift normalization estimator | rolling median/MAD robust z (not mean/std) | resists outlier contamination of baseline; architecture unchanged
D-04 | 2026-06-13 | Dream Mode lambda | lambda = alpha*N, alpha=0.5 (was fixed lambda=50) | fixed lambda is a no-op for large N and erases memory for small N; panel allows tuning
D-05 | 2026-06-13 | conflicting GPT docs uploaded 06-12 | archived to docs/archive/gpt_drafts/, canonical docs restored/rewritten | they described different products; repo docs must be a single source of truth
D-06 | 2026-06-13 | alert schema | replaced generic IT-alert schema with drift-detector schema at contracts/alert.schema.json | matches MVP_MATH_SPEC §5 output and T-07
