# Architecture

## Detection Pipeline (per transaction)

```
Mantle RPC — tx stream
        │
[Tier 0] Spam pre-filter     ← MIN_INTERVAL rule (k=20 consecutive fast txs → spam_attack)
        │
[Tier 1] Entropy filter      ← per-selector Shannon baseline; |H − mean| > 4σ → entropy_anomaly
        │ hard-alert fan-out
[Tier 2] HDC Encoder         ← D=10,000 bipolar; role-filler binding; sliding window W=50
        │ window hypervector
[Tier 3] Drift signal        ← Hamming + timing; rolling median/MAD norm; drift = max(hamming, timing)
        │ drift ∈ [0,1]
[Tier 4] Detector            ← Static(θ=0.65, k=3 consecutive) | BOCPD (SENTINEL_DETECTOR=bocpd)
        │ alert episode
[Tier 5] Interpreter         ← feature-ablation attribution → structured Alert JSON
        │
   ┌────┴────┐
 Z.ai    Telegram
(explain) (notify)
   └────┬────┘
  On-chain anchor
(SentinelAlertRegistry)
        │
  Live Dashboard
(dashboard/index.html)
```

**Dream Mode feedback loop** (opt-in `--dream-mode`):
```
safe windows (detector silent AND drift < rolling median W=100)
     │ every N=100 safe windows
     ▼
dream_update(V_old, safe_batch, α=0.5)   [D-04: λ = α·N = 50]
     │
     ▼
P_new = sign(λ·P_old + Σ V_safe)
```
Alert clears the pending buffer — attack windows never fold into the baseline.

## Key Parameters

| Parameter | Default | Source |
|-----------|---------|--------|
| HDC dimension D | 10,000 | D-02 |
| Window size W | 50 | MVP_MATH_SPEC §2 |
| Drift threshold θ | 0.65 | MVP_MATH_SPEC §4 |
| k (consecutive alerts) | 3 | MVP_MATH_SPEC §4 |
| Dream consolidation N | 100 | D-04 |
| Dream alpha α | 0.5 | D-04 |
| Safe-window median window | 100 | D-12 |
| MASTER_SEED | 1337 | MVP_MATH_SPEC |

## Drift Formula

```
drift_h = Hamming(V_window, P_prototype) / D
drift_t = |z_timing|   (median/MAD robust z-score)
drift   = max(drift_h, drift_t)
```

## Decisions Log

Key spec-gap decisions (full log: `docs/DECISIONS.md`):

- **D-02**: D=10,000 (panel consensus over 4,096 draft)
- **D-03**: rolling median/MAD normalization (robust to outliers)
- **D-04**: Dream Mode α=0.5, N=100 safe windows
- **D-12**: safe-window criterion = detector silent AND drift < rolling median (last 100 windows)

## Detector Selection

Set `SENTINEL_DETECTOR=bocpd` to use the Bayesian Online Change Point Detector instead of the default static threshold. Both detectors implement the same `process(drift, ts) → alert` interface.
