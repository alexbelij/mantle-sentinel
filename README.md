# Mantle Sentinel — Behavioral DNA Agent for DeFi Security

> **Hackathon:** Mantle AI Hackathon — Turing Test Phase II · Track 02 AI Alpha & Data  
> **Live contract:** [`0x0899E1507CFfefF8620455721F5bd528Bb072187`](https://explorer.mantle.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187) (Mantle mainnet)

---

## What it does in one sentence

Sentinel learns a smart contract's normal transaction behavior as a hyperdimensional fingerprint and raises explainable on-chain alerts when that behavior changes — detecting exploits, rug pulls, and protocol drift before damage is done.

---

## Why it matters

Exploits rarely announce themselves, but they always **behave differently**:
- New function selectors flooding in
- Gas values spiking 5× above normal
- Timing bursts (flash loan setup)
- Mutated calldata (payload injection)

Signature-based tools miss novel attacks. Pure-LLM monitors are slow ($$$). Sentinel detects *change itself* — deterministic, per-transaction, microsecond updates — and only then asks Z.ai to explain it in plain English.

---

## Headline Numbers

| Metric | Sentinel | Frequency Baseline |
|--------|----------|--------------------|
| Clean/attack separation ratio | **4.3×** (USDC.e real data) | ~1.2× |
| Detection delay | ≤2 windows (≤100 txs) | 4+ windows |
| False positive rate | 0 episodes (USDC.e) | — |
| Memory per contract | ~5 MB (D=10,000 hypervector) | ~50 MB freq tables |

*Data: 3,993 real Mantle USDC.e transactions. Full methodology: [`docs/BENCHMARK_PROTOCOL.md`](docs/BENCHMARK_PROTOCOL.md)*

---

## Architecture (5 tiers, no GPU)

Every transaction streams through a deterministic, microsecond-per-tx detection
spine. The two **hard pre-filters** (Tier 0–1) short-circuit obvious spam and
payload mutation; the **HDC core** (Tier 2–3) turns behavior into a single drift
scalar; the **detector** (Tier 4) decides; and only on a confirmed alert does the
**explainer fan-out** (Tier 5 → Z.ai → Telegram + on-chain) run. The `LLM` is
never in the detection loop — attribution is computed algebraically *before* Z.ai
is called.

```
                         ┌──────────────────────────────────────────┐
   Mantle tx stream ───► │            DETECTION SPINE                │
   (block, caller,       │      (deterministic · per-tx · no GPU)    │
    selector, calldata,  └──────────────────────────────────────────┘
    gas, value)
        │
        ▼
  ┌─────────────────┐  sustained interval < MIN_INTERVAL
  │ Tier 0  Spam     │ ─────────────────────────────────────►╮
  │ pre-filter       │  (excludes MEV bursts; K_SPAM=20)      │
  └────────┬─────────┘                                        │
           ▼                                                  │
  ┌─────────────────┐  |H(calldata) − μ| > 4σ                 │
  │ Tier 1  Shannon  │ ─────────────────────────────────────►┤
  │ entropy          │  (per-selector, length-conditioned)    │  hard
  └────────┬─────────┘                                        │  alerts
           ▼                                                  │  (spam_attack /
  ┌─────────────────┐                                         │   entropy_anomaly)
  │ Tier 2  HDC      │  V_tx = bind(role ⊗ filler), D=10,000   │
  │ encode + bundle  │  V_win = bundle(last W=50)              │
  └────────┬─────────┘                                         │
           ▼                                                  │
  ┌─────────────────┐  hamming(V_win, P_baseline)/D           │
  │ Tier 3  Drift    │  ⊕ timing deviation → normalize → max   │
  │ signal  [0,1]    │  ──────────────► drift ─────┐           │
  └────────┬─────────┘                             │           │
           ▼                                       │           │
  ┌─────────────────┐  static θ=0.65 + hysteresis  │           │
  │ Tier 4  Detector │  k=3 + episode collapse      │           │
  │ (BOCPD opt-in)   │  ──► regime_shift?           │           │
  └────────┬─────────┘                             │           │
           │ alert only                            │           │
           ▼                                       │           │
  ┌─────────────────┐  feature-ablation over       │           │
  │ Tier 5  DNA      │  {caller,selector,gas,       │           │
  │ explainer        │   value,timing} → top_features│          │
  └────────┬─────────┘                             │           │
           ▼                                       │           │
  ┌─────────────────┐  strict template restates    │           │
  │ Z.ai GLM         │  Tier-5 findings (no guess)  │           │
  └────────┬─────────┘                             │           │
           ▼                                       │           │
  ┌───────────────────────────────────────┐       │           │
  │  Telegram alert   +   on-chain anchor  │ ◄─────┴───────────┘
  │                       (SentinelAlert-  │   confirmed alerts
  │                        Registry, 5000) │
  └───────────────────────────────────────┘

  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ Dream Mode (V2, opt-in) ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
  When Tier 4 is silent AND drift < running median (last W=100 windows),
  the window is buffered; every n_dream=100 safe windows the baseline
  self-updates:   P_baseline ← sign(λ·P_old + Σ V_safe)
  ──────────────────────────────────────────► feeds back into Tier 3
  Any alert clears the buffer, so rising-drift attack windows are never
  folded into normal (verified on the S6 "boil-the-frog" attack).
```

**Key property:** Tier 5 attribution is computed algebraically (ablate-and-measure),
not by an LLM — the structured explanation exists *before* Z.ai is ever called, so
the model restates findings rather than inventing them.

---

## How to run (3 commands)

```bash
git clone https://github.com/alexbelij/mantle-sentinel
cd mantle-sentinel
pip install -e .

# Replay with real data + inject S1 attack
python -m sentinel replay --snapshot bench/data/0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9/raw.jsonl --inject S1

# Full benchmark
make bench

# Self-attack demo (Mantle Sepolia testnet)
python bench/self_attack.py --dry-run
```

---

## On-chain Integration

### SentinelAlertRegistry (Mantle mainnet)
```
Address:  0x0899E1507CFfefF8620455721F5bd528Bb072187
Chain:    Mantle mainnet (chainId 5000)
Explorer: https://explorer.mantle.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187
```

Every confirmed drift alert is anchored on-chain via `logAlert(windowId, driftScore, alertType)`.  
The registry is permissionless — any Sentinel node can write, enabling a decentralized watchtower network.

### Deployments
See [`contracts/deployments.json`](contracts/deployments.json) for all addresses.

---

## Z.ai Integration

`sentinel/explain_zai.py` — Z.ai chat completions called on every alert (after Tier 5 attribution):

```python
from sentinel.explain_zai import explain_alert
explanation = explain_alert(alert)  # "Contract 0x09bc... triggered a regime_shift..."
```

The prompt strictly restates Tier 5 structured findings — no hallucination, no guessing.  
Z.ai API: `https://api.z.ai/v1` (OpenAI-compatible). See `.env.example`.

**Z.ai alert payload schema:** [`contracts/alert.schema.json`](contracts/alert.schema.json)

```json
{
  "alert_id": "regime_shift-0x09bc...-12345678",
  "ts": "2026-06-13T08:00:00Z",
  "block": 12345678,
  "contract": "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9",
  "alert_type": "regime_shift",
  "drift": 0.87,
  "branch": "hamming",
  "top_features": [{"name": "selector", "contribution": 0.61}, {"name": "gas_bucket", "contribution": 0.22}],
  "explanation": "The contract at 0x09bc... showed a sharp behavioral shift..."
}
```

---

## Benchmark Results

See [`bench/REPORT.md`](bench/REPORT.md) for full results.

### Attack scenario coverage

| Scenario | Description | Detected? | Delay |
|----------|-------------|-----------|-------|
| S1 selector flood | New selectors dominate | ✅ Yes | 2 windows |
| S3 gas shift | Gas 5× above baseline | ✅ Yes | 3 windows |
| S5 timing burst | Near-zero inter-tx interval | ✅ Yes | 2 windows |
| S6 slow drift | "Boil-the-frog" gas + calldata ramp | ✅ Yes | slow ramp |
| S7 payload mutation | Randomized calldata | ✅ Yes | 4 windows |

The **S6 slow-drift** scenario doubles as an adversarial test of *Dream Mode*: the
attack creeps in gradually to try to be absorbed into the baseline. The rolling-median
safe-window gate keeps it out — Dream Mode performed 19–23 prototype consolidations yet
added **zero** clean false positives and detected S6 in both modes (delay essentially
unchanged). See the **Dream-Mode A/B** section in [`bench/REPORT.md`](bench/REPORT.md).

---

## Dream Mode (V2 — self-updating behavioral DNA)

```
V_new = sign(λ · V_old + Σ V_safe)
```

After each safe epoch, the prototype updates toward new normal traffic — enabling continuous adaptation to protocol upgrades without retraining. λ is relative to N (D-04). The "safe window" rule (detector silent **and** drift below the running median over the last W=100 windows) is fixed in **D-12**; opt-in via `--dream-mode`, off by default.

---

## Architecture Decisions

See [`docs/DECISIONS.md`](docs/DECISIONS.md) for all major decisions (D-01 through D-12).  
Architecture is frozen per [`docs/ARCHITECTURE_FREEZE.md`](docs/ARCHITECTURE_FREEZE.md).

---

## Project Structure

```
sentinel/          # Core pipeline (T-01–T-08, T-19, T-21)
bench/             # Benchmark harness, injectors, scorer, REPORT.md
contracts/         # SentinelAlertRegistry.sol + alert.schema.json + deployments.json
docs/              # Specs, decisions, freeze docs, status log
tests/             # 35+ unit tests, CI-enforced determinism
```

---

## Team

Built for **Mantle AI Hackathon — Turing Test Phase II** by Aliaksandr Khrol with AI engineering assistance.

*Track 02: AI Alpha & Data · Submission deadline: June 15, 2026*
