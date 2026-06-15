# Mantle Sentinel — HDC Behavioral DNA Agent

[![Tests](https://github.com/alexbelij/mantle-sentinel/actions/workflows/pytest.yml/badge.svg)](https://github.com/alexbelij/mantle-sentinel/actions/workflows/pytest.yml)

> Your smart contracts have a behavioral fingerprint. Sentinel knows when it changes.

Signature-based tools miss novel attacks. Pure-LLM monitors are slow and
expensive. Sentinel detects **change itself** — deterministic, per-transaction,
microsecond updates — using a 10,000-dimensional hyperdimensional (HDC)
behavioral signature, and only *then* asks Z.ai to explain the confirmed alert
in plain English. The model is **never** in the detection loop.

**Live demo:** https://mntsentinel.xyz/

---

## Pipeline

```
  [Mantle RPC]
      |
  T0  Entropy pre-filter (calldata selector distribution)
      |
  T1  HDC Encoder — 10,000-dim bipolar hypervector per window
      |
  T2  Drift = max(Hamming distance, timing deviation)
      |
  T3  Detector — static threshold or BOCPD regime-change
      |
  T4  Feature attribution (ablation: recompute bundle without feature f)
      |
  T5  Z.ai natural-language explanation (restates Tier-4 findings only)
      |
  [Telegram alert  +  on-chain logAlert()  +  Dashboard]
```

Attribution is computed **algebraically before** Z.ai is ever called — the
structured explanation exists with or without the LLM.

---

## Quick Start

```bash
git clone https://github.com/alexbelij/mantle-sentinel
cd mantle-sentinel
cp .env.example .env            # add keys (ZAI_API_KEY optional — dry-run without it)
pip install -r requirements.txt

# version check
python -m sentinel --version

# replay a real snapshot through the full pipeline (with an injected attack)
python -m sentinel replay \
  --snapshot bench/data/0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9/raw.jsonl \
  --inject S1

# self-attack demo (synthetic, no RPC):
python bench/self_attack.py --dry-run
```

Live on-chain mode (warm up on a victim contract, inject anomalies, anchor the
alert on Mantle mainnet) additionally needs the `live` extras and a funded key:

```bash
pip install web3 eth-account          # or: pip install ".[live]"
export MANTLE_PRIVATE_KEY=0x...        # Sentinel agent wallet (see .env.example)
python bench/self_attack.py --victim 0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64 \
                            --rpc https://rpc.sepolia.mantle.xyz
```

---

## Contract — `SentinelAlertRegistry` v2

Immutable, owner-gated on-chain registry for behavioral-drift alerts. Source:
[`contracts/SentinelAlertRegistry.sol`](contracts/SentinelAlertRegistry.sol).

| Network            | Chain ID | Address                                      |
| ------------------ | -------- | -------------------------------------------- |
| **Mantle Mainnet** | 5000     | `0x0899E1507CFfefF8620455721F5bd528Bb072187` |
| Mantle Testnet     | 5003     | `0x2543Cc701632b105eE3DB75345140a7357664389` |

Explorer: https://mantlescan.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187

`driftScore` is stored x10000 (`0.87` → `8700`). Events carry the storage
`alertIndex` so any off-chain consumer reconstructs the timeline without
array scans. Reads (`getAlertCount`, `getAlert`, `getLatestAlerts`) are O(1)
or bounded-gas.

---

## Results

| Metric                        | Sentinel                     | Signature baseline |
| ----------------------------- | ---------------------------- | ------------------ |
| Clean/attack separation ratio | **4.3×** (USDC.e real data)  | ~1.2×              |
| Detection delay               | ≤2 windows (≤100 txs)        | 4+ windows         |
| False positive rate           | **0** episodes (USDC.e)      | —                  |

*Data: 3,993 real Mantle USDC.e transactions. Full methodology:
[`docs/BENCHMARK_PROTOCOL.md`](docs/BENCHMARK_PROTOCOL.md).*

### Injection scenarios

| Scenario          | Signature                       | Detected | Delay     |
| ----------------- | ------------------------------- | -------- | --------- |
| S1 selector flood | New selectors dominate          | ✅       | 2 windows |
| S3 gas shift      | Gas 5× above baseline           | ✅       | 3 windows |
| S5 timing burst   | Near-zero inter-tx interval     | ✅       | 2 windows |
| S7 payload mutation | Randomized calldata           | ✅       | 4 windows |

### Tests

```
python -m pytest tests/ -q     # 109 passed
forge test                     # 6 passed  (contracts/SentinelAlertRegistry.sol)
```

---

## Z.ai Integration

[`sentinel/explain_zai.py`](sentinel/explain_zai.py) calls Z.ai (OpenAI-compatible
`chat/completions`) on every confirmed alert, **after** Tier-4 attribution.
Z.ai only restates the structured findings — it cannot create or suppress an
alert. Prompt template + schema: [`docs/zai_prompt.md`](docs/zai_prompt.md).

- Endpoint: `https://api.z.ai/api/paas/v4` · model `glm-4.5-flash` (free tier)
- No `ZAI_API_KEY` → deterministic dry-run explanation (CI never hits the API)
- Alert payload schema: [`contracts/alert.schema.json`](contracts/alert.schema.json)

---

## Why Sentinel

Unlike Forta (rule-based, requires model training) or Chainalysis (signature
databases), Sentinel is **training-free**: same algorithm, same thresholds, any
EVM contract, zero GPU. Detection is algebraic; the LLM is only a translator.

**Target customers:** DeFi protocols, bridges, DAO treasuries.
**Business model:** SaaS subscription per monitored contract — no per-alert fees.

---

## CI

GitHub Actions runs the Python suite on every push / PR:
[`.github/workflows/pytest.yml`](.github/workflows/pytest.yml) →
`python -m pytest tests/ -q`. Contract tests run locally via Foundry
(`forge test`).

---

## Repo layout

```
sentinel/          Python package — Tiers T0–T5 pipeline
  prefilter.py     T0  entropy pre-filter
  hdc.py           T1  hyperdimensional encoder
  drift.py         T2  Hamming + timing drift
  detector.py      T3  static / BOCPD detector
  bocpd.py             Bayesian online change-point detector
  interpreter.py   T4  feature-ablation attribution
  explain_zai.py   T5  Z.ai explainer (dry-run safe)
  notify_telegram.py   Telegram fan-out
  replay.py            snapshot replay harness
contracts/         SentinelAlertRegistry.sol (v2) + VictimCounter.sol + ABI/deployments
test/              Foundry tests (forge)
tests/             pytest suite
bench/             self_attack.py demo + real snapshot data
dashboard/         static on-chain alert viewer
docs/landing/      marketing site (Vercel)
```
