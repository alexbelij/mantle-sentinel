# Mantle Sentinel — DoraHacks BUIDL submission (draft)

> Track: Mantle Turing Test Hackathon 2026 · Z.ai integration
> Placeholder to fill before publishing: `<DORAHACKS_BUIDL_URL>`. (Live alert tx from run 3a is filled in below.)

## One-liner
Your smart contracts have a behavioral fingerprint. Mantle Sentinel detects the moment it changes — training-free, deterministic, on-chain.

## Problem
Signature-based monitors (Chainalysis-style) only catch *known* exploit patterns and miss novel attacks. Pure-LLM monitors are slow, non-deterministic, and expensive at scale. Neither watches the one thing every exploit has in common: the contract's transaction *behavior* suddenly stops looking like itself.

## Solution
Sentinel builds a 10,000-dimensional hyperdimensional (HDC) "behavioral DNA" signature for a contract from its live transaction stream, then measures drift per window. When drift crosses threshold it (1) attributes the shift to a specific feature algebraically, (2) anchors an immutable alert on Mantle mainnet, and (3) asks Z.ai to translate the structured finding into a plain-English brief. Same algorithm, same thresholds, any EVM contract, zero GPU, zero retraining.

## Key Features

- Training-free 10,000-dim HDC anomaly detection — zero GPU, zero retraining
- On-chain alert anchoring on Mantle mainnet
- **Telegram alerts** — real-time notifications via [@MantleSentinelBot](https://t.me/MantleSentinelBot)
- Z.ai plain-English explanations for every confirmed alert
- Live dashboard at [mntsentinel.xyz/dashboard](https://mntsentinel.xyz/dashboard/)

## How it works (T0–T6 pipeline)
- **T0** Entropy pre-filter over calldata selector distribution
- **T1** HDC encoder → 10,000-dim bipolar hypervector per window
- **T2** Drift = max(Hamming distance, timing deviation)
- **T3** Detector: static threshold or Bayesian online change-point (BOCPD)
- **T4** Feature-ablation attribution (recompute bundle without feature *f*)
- **T5** Z.ai GLM natural-language explanation — restates T4 findings only
- **T6** Telegram notification via [@MantleSentinelBot](https://t.me/MantleSentinelBot)

The LLM is **never** in the detection loop: the structured explanation exists with or without Z.ai, so detection stays deterministic and reproducible byte-for-byte.

## Z.ai integration
Every confirmed alert calls Z.ai (`glm-4.5-flash`, OpenAI-compatible `https://api.z.ai/api/paas/v4`) with a strict template that may only restate the Tier-5 structured findings — no hallucinated severity, no invented cause. Without a key the explainer returns a deterministic canned brief so CI never touches the live API. Prompt + schema: `docs/zai_prompt.md`.

## On-chain proof (Mantle)
- **SentinelAlertRegistry v2 — Mainnet (5000):** `0x0899E1507CFfefF8620455721F5bd528Bb072187`
  https://mantlescan.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187
- **Registry v2 — Testnet (5003):** `0x2543Cc701632b105eE3DB75345140a7357664389`
- **VictimCounter (Mantle Sepolia, self-attack target):** `0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64`
- **Live self-attack alert tx:** `0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c` (warm-up → injected anomaly → on-chain `logAlert`, mainnet block 96,680,154, `getAlertCount() == 1`)
  https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c

## Results
- **4.3×** clean/attack separation on real data (vs ~1.2× signature baseline)
- **0** false-positive episodes across the full benchmark
- **≤2 windows** (≤100 txs) detection delay
- **129** Python tests + **6** Foundry tests, all passing & deterministic
- Benchmarked on **3,993 real Mantle USDC.e transactions** (`0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9`)

## Why us vs incumbents
- **Forta** — rule/ML-based, needs per-threat models & training. Sentinel is training-free.
- **Chainalysis** — signature databases for known patterns. Sentinel detects *change itself*, catching novel attacks.

## Business model
SaaS subscription per monitored contract — flat, no per-alert fees. Target customers: DeFi protocols, bridges, DAO treasuries.

## What's Built
- Live demo: https://mntsentinel.xyz/
- Live dashboard: https://mntsentinel.xyz/dashboard/
- Telegram bot: [@MantleSentinelBot](https://t.me/MantleSentinelBot) — real-time alert notifications
- Code (MIT): https://github.com/alexbelij/mantle-sentinel
- BUIDL: `<DORAHACKS_BUIDL_URL>`
