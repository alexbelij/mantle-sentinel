# Mantle Sentinel — Roadmap

> From hackathon prototype to production-grade behavioral security infrastructure.

---

## Phase 1 — Multi-Contract Monitoring

- Parallel monitoring of multiple contracts from a single operator
- Python SDK for seamless integration
- Webhook and multi-channel alert delivery
- Circuit breaker and alert deduplication

## Phase 2 — Explainability & Confidence

- Probabilistic confidence scoring (beyond binary alerts)
- Feature-level heatmaps: which behavioral channel triggered the alert
- Tiered alert severity (Warning → Critical → Emergency)
- Automated weekly baseline health reports

## Phase 3 — Adaptive Baseline Learning

- Production-grade baseline consolidation (self-calibrating, no manual tuning)
- Operator-guided safe period labeling
- Poisoning resistance for slow-drift attacks
- Prototype versioning with automatic rollback

## Phase 4 — Enterprise & SaaS

- Multi-tenant web dashboard with per-client isolation
- Synchronized on-chain + off-chain alert history
- Tiered pricing (Free → Pro → Enterprise)
- On-chain proof-of-protection for monitored protocols

---

## Horizontal Expansion

### EVM Multi-Chain

Target networks: Arbitrum, Base, OP Stack, Polygon zkEVM, zkSync.
Chain-adaptive gas normalization. One registry deployment per network.

### DeFi Protocol Partnerships

Verticals: DEX/AMM, Lending, Bridges.
"Protected by Sentinel" co-marketing. Revenue share with insurance protocols.

### Threat Intelligence Marketplace

Aggregate anonymized alert patterns across all monitored contracts.
Cross-contract attack pattern detection. Known-threat signatures for zero warm-up onboarding.

### Insurance Protocol Integration

Real-time drift score as an oracle for dynamic premium pricing.
Automatic claim triggers on critical behavioral shifts.

### AI Agent Integration

Sentinel as an MCP tool for autonomous on-chain agents.
AVS integration for decentralized alert validation.
Safe Wallet integration: alert → automated pause proposal.

---

## Competitive Position

|  | Rules-based | Signature DB | LLM heuristics | **Sentinel** |
|---|---|---|---|---|
| Training data | required | required | required | **none** |
| GPU | yes | yes | yes | **no** |
| Latency | minutes | minutes–hours | seconds | **< 1 window** |
| Explainability | limited | none | partial | **feature attribution** |
| Novel attacks | miss | miss | partial | **detect by design** |

**Core differentiator:** the only behavioral detector that requires no training data, no GPU, and no attack signatures — making it uniquely suited for new protocols, novel attack vectors, and resource-constrained operators.
