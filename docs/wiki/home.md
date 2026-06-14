# Mantle Sentinel

**Behavioral DNA agent for DeFi security on Mantle Network.**  
Detects contract behavioral drift using Hyperdimensional Computing — no training data, no labeled exploits.

## What it does

Mantle Sentinel monitors smart contract transactions in real time and detects when a contract starts *behaving differently* — even before traditional signatures or rules could catch it.

| Metric | Result |
|--------|--------|
| Separation ratio (clean p99 / injected p50) | **4.3×** |
| False positives on clean stream (8000 windows) | **0 real FP** (rate ≈ 0.2%) |
| Detection delay | **≤ 2 windows** (S1–S5 scenarios) |
| Test suite | **109 tests**, deterministic |

## Navigation

- [Architecture](architecture) — 5-tier pipeline, HDC math, Dream Mode, BOCPD
- [Quick Start](quickstart) — clone, configure, replay
- [Benchmark](benchmark) — separation ratio, S1–S6 scenarios, Dream A/B
- [Self-Attack Demo](self-attack-demo) — live on-chain proof (Mantle mainnet + Sepolia)
- [Configuration](configuration) — all env vars, seeds, thresholds
- [Contracts](contracts) — deployed addresses, ABI, explorer links

## Tech stack

Mantle Network · Hyperdimensional Computing · BOCPD · Dream Mode · Z.ai · Telegram

> Hackathon: Mantle AI Hackathon — Turing Test Phase II · Track 02 AI Alpha & Data
