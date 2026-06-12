# MVP_MATH_SPEC.md — Frozen Defaults for All Math-Bearing Modules

Purpose: zero-deliberation defaults. Implement exactly this; deviations require a `D-NN` entry in `docs/DECISIONS.md`. All randomness derives from `MASTER_SEED = 1337`.

## 0. Timing pre-filter (Tier 0) — frozen form

- `MIN_INTERVAL` = 0.001-quantile of inter-tx intervals `Δt` on the warm-up split (per contract); floor 0.
- **Spam alert** iff the last `k_spam = 20` consecutive intervals are all `< MIN_INTERVAL`; alert type `spam_attack`; 10-min episode collapsing.
- Spam-flagged transactions are **excluded** from window bundles, prototype building, and rolling history (baseline-poisoning protection). They still count for Tier 1 entropy baselines? **No — excluded everywhere.**

## 1. Hypervector space (Tier 2)

- Dimension `D = 10000` (panel consensus, D-02), bipolar `{−1,+1}`, stored as int8 numpy arrays.
- **Item memory:** each categorical value (selector, caller-property value) gets a random bipolar vector via `seed = hash(MASTER_SEED, feature_name, value)`.
- **Ordinal features (gas, value, timing buckets):** `B = 16` buckets each, **level encoding** — bucket 0 is a random vector; each next bucket flips a fixed random `D/(2(B−1))` coordinates of the previous one. Adjacent buckets ⇒ high similarity, far buckets ⇒ near orthogonal.
- **Bucket edges:** quantiles (equal-frequency) computed on the warm-up split per contract; frozen after warm-up.
- **Caller feature:** encode *properties*, not identity: `{novel_in_history: 0/1, frequency_tier: 4 levels (quantile), is_contract: 0/1}`, each property a role-filler pair.
- **Transaction vector:** `V_tx = sign(Σ_f R_f ⊙ F_f)` — role vector `R_f` (random, per feature name) bound (element-wise multiply) to filler `F_f`, bundled by majority sign (ties broken by +1).
- **Window bundle:** `V_win(t) = sign(Σ over last W=50 tx of V_tx)`.
- **Prototype (Behavioral DNA):** `P = sign(Σ over warm-up tx of V_tx)`, frozen after warm-up for MVP (Dream Mode is deferred).

## 2. Drift signal (Tier 3) — frozen form

```
hamming(t)  = HammingDistance(V_win(t), P) / D            # in [0,1]
timing(t)   = |log(Δt_t) − median_w(log Δt)|              # Δt = inter-tx interval, w = 500-tx rolling window
norm(x)     = squash( (x − median_hist(x)) / (1.4826·MAD_hist(x) + ε) )
squash(z)   = clip(z / 6, 0, 1)                           # z=6 sigma ⇒ 1.0
drift(t)    = max( norm(hamming(t)), norm(timing(t)) )
```

- `median_hist/MAD_hist`: rolling over the last 2,000 windows of the contract's own history, initialized on warm-up, **never shrunk by recent quiet periods faster than the window allows** (no min-max!).
- `ε = 1e-9`. Evaluate per transaction; windows slide by 1 tx.

## 3. Entropy filter (Tier 1)

- Per (selector, calldata-length-bucket) baseline: mean & std of byte-level Shannon entropy over warm-up, length buckets `{0–4, 5–36, 37–100, 101–516, >516}` bytes.
- Alert iff `|H(tx) − mean| > 4·std` **and** ≥ 20 samples exist in that baseline cell; otherwise abstain (never alert from an unpopulated cell).
- Bypasses Tier 4 (per freeze); emits its own alert type `entropy_anomaly`.

## 4. Static threshold detector (Tier 4, MVP)

- Alert iff `drift(t) > θ` for `k = 3` consecutive evaluations (hysteresis). Default `θ = 0.65`; tuned on the calibration split to the FP budget (≤ 2 episodes/contract-day) per BENCHMARK_PROTOCOL §4.3.
- **Episode collapsing:** alerts within 10 min merge into one episode.

## 5. Interpreter (Tier 5)

- Frozen attribution rule (simpler and more robust than unbinding): recompute window bundles **with feature f ablated** (`V_win^{−f}`), and attribute drift to the feature whose ablation most reduces `hamming`:
  `contribution_f = hamming(V_win, P) − hamming(V_win^{−f}, P^{−f})` (ablated prototypes precomputed once, 5 extra prototypes).
- Report top-2 features with contributions > 0; timing alerts attributed directly when `norm(timing)` is the max branch.
- Output JSON: `{alert_id, ts, block, contract, drift, branch: hamming|timing|entropy, top_features: [{name, contribution}], window_stats}`.

### Tier numbering note

Panel numbering (ARCHITECTURE_FREEZE): Tier 0 timing pre-filter · Tier 1 entropy · Tier 2 HDC encode + drift · Tier 3 BOCPD/static detector · Tier 4 explainer · Tier 5 Z.ai. Repo modules keep the section names of this file; tasks reference T-NN IDs. No renumbering churn — map via ARCHITECTURE_FREEZE table.

## 6. Deferred-module parameters (P2; do not implement early)

- **BOCPD:** observation model = Gaussian on the pre-squash z-score (not on drift), hazard `1/1000`; alert when P(run length < 5) > 0.8.
- **Dream Mode:** `V_new = sign(λ·V_old + Σ V_safe)` with `λ = α·N`, `α = 0.5`, `N` = count of safe vectors that night; **safe** = no alert episode and `drift < median` within ±50 blocks. Required unit test: after consolidation with N ∈ {50, 500, 5000}: `V_new ≠ V_old` and `cos(V_new, V_old) > 0.7`.

## 7. Determinism contract

Same snapshot + same config + same seed ⇒ byte-identical alert output. CI asserts this with a golden-file test on a 500-tx fixture.
