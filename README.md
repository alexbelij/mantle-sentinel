# Mantle Sentinel — Behavioral DNA Agent for DeFi Security

> **Hackathon:** Mantle AI Hackathon — Turing Test Phase II · Track 02 AI Alpha & Data  
> **Live contract:** [`0x593C9a4dd6806510e379e30481eaCd27d2016FbE`](https://explorer.mantle.xyz/address/0x593C9a4dd6806510e379e30481eaCd27d2016FbE) (Mantle mainnet)

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

## Pipeline (5 tiers, no GPU)

```
tx stream
  → Tier 0  Spam pre-filter      (MIN_INTERVAL rule, excludes MEV bursts)
  → Tier 1  Shannon entropy      (per-selector, length-conditioned baseline)
  → Tier 2  HDC encode           (D=10,000 bipolar; role-filler binding; window bundle W=50)
  → Tier 3  Drift signal         (Hamming dist + timing dev → normalize → max → [0,1])
  → Tier 4  Detector             (static θ=0.65 + hysteresis k=3 + episode collapse)
  → Tier 5  DNA explainer        (feature-ablation attribution: names what drifted)
  → Z.ai    LLM explainer        (strict template: restates Tier 5 findings in plain English)
  → Telegram alert + on-chain anchor (SentinelAlertRegistry)
```

**Key property:** Tier 5 attribution is computed algebraically (ablate-and-measure), not by LLM — the explanation is already structured before Z.ai is called.

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
Address:  0x593C9a4dd6806510e379e30481eaCd27d2016FbE
Chain:    Mantle mainnet (chainId 5000)
Explorer: https://explorer.mantle.xyz/address/0x593C9a4dd6806510e379e30481eaCd27d2016FbE
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
| S7 payload mutation | Randomized calldata | ✅ Yes | 4 windows |

---

## Dream Mode (V2 — self-updating behavioral DNA)

```
V_new = sign(λ · V_old + Σ V_safe)
```

After each safe epoch, the prototype updates toward new normal traffic — enabling continuous adaptation to protocol upgrades without retraining. λ is relative to N (frozen per D-11 consensus).

---

## Architecture Decisions

See [`docs/DECISIONS.md`](docs/DECISIONS.md) for all major decisions (D-01 through D-11).  
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
