# ARCHITECTURE_FREEZE.md — Mantle Sentinel: HDC Behavioral DNA Agent

Status: **FROZEN** (panel consensus, 2026-06-13). Only the Project Lead can unfreeze.
Math defaults: `docs/MVP_MATH_SPEC.md`. Scope: `docs/MVP_IMPLEMENTATION_FREEZE.md`. Tasks: `docs/TASKS.md`.

## Real-time pipeline (per transaction)

```
Incoming Mantle transaction
        │
        ▼
Tier 0: Timing Pre-filter
        interval < MIN_INTERVAL (sustained) → Alert "spam_attack"
        │
        ▼
Tier 1: Shannon Entropy (hard threshold, per-selector baseline)
        |H(calldata) − mean| > 4σ → Alert "entropy_anomaly"
        │
        ▼
Tier 2: HDC Encode (D = 10,000 bipolar)
        V_tx  = hdc_encode(metadata)
        hamming = distance(V_win, P_baseline) / D
        timing  = robust deviation of log Δt
        drift   = max(norm(hamming), norm(timing))
        │
        ▼
Tier 3: Detector
        MVP: static threshold θ + hysteresis  → Alert "regime_shift"
        Full: BOCPD, P(changepoint|drift) > 0.95 (pluggable module, same interface)
        │
        ▼
Tier 4: DNA Drift Explainer (alert-only)
        feature-ablation contributions: {caller, selector, gas, value, timing}
        │
        ▼
Tier 5: Z.ai GLM (alert-only, strict template) → Telegram + on-chain log (SentinelAlertRegistry)
```

## Nightly cycle (00:00 UTC — full version, deferred)

```python
V_new = sign(lam * V_old + sum(V_safe_txs))   # lam = alpha * N, alpha = 0.5 (D-04)
bocpd_model.update_priors(safe_signals)
```

## Component roles

| Component | Role | Catches | Repo module | Task |
|---|---|---|---|---|
| Timing pre-filter (T0) | Hard pre-filter | Spam / frequency attacks | `sentinel/prefilter.py` | T-05b |
| Shannon entropy (T1) | Hard pre-filter | Payload/calldata mutation | `sentinel/entropy.py` | T-05 |
| HDC encoder (T2) | Memory + encoder | Behavioral fingerprint | `sentinel/hdc.py` | T-03 |
| Hamming + timing drift (T2) | Detector signal | Structural deviation | `sentinel/drift.py` | T-04 |
| Static threshold / BOCPD (T3) | Adaptive threshold | Regime shift | `sentinel/detector.py` | T-06 / T-17 |
| DNA Drift explainer (T4) | Explainer | What exactly changed | `sentinel/interpreter.py` | T-07 |
| Z.ai GLM (T5) | Interpreter | Human-readable alert | `sentinel/explain_zai.py` | T-19 |
| Telegram delivery (T5) | Alert channel | — | `sentinel/notify_telegram.py` | T-21 |
| On-chain log (T5) | Alert anchor | — | `contracts/SentinelAlertRegistry.sol` | T-13 |
| Dream Mode | Lifecycle | Agent memory update | deferred | T-18 |

## Rejected approaches (confirmed on data)

TDA, Transfer Entropy, Tensor Networks, Spectral Role Fingerprinting, Hyperbolic Geometry — did not survive validation on real Mantle data. Do not reintroduce.

## MVP vs full version

- **MVP (days 1–3):** Tier 0 + Shannon + HDC + static threshold + explainer + Z.ai + Telegram + Alert JSON.
- **Full (days 4–5):** + BOCPD + Dream Mode. BOCPD is a swappable module behind the T-06 interface — if time runs out, fallback to the static threshold with no rewrite.

## Innovation statement

"Mantle Sentinel — первое применение Hyperdimensional Computing для поведенческих отпечатков DeFi-контрактов на Mantle, где BOCPD заменяет магические пороги на байесовскую детекцию смены режима, а Dream Mode обновляет память агента ночью."

## Freeze rules

No new subsystems, no algorithm swaps, no framework/storage changes without a `D-NN` entry approved by the Project Lead. Spec gaps: simplest compliant interpretation + `D-NN` note, keep moving.
