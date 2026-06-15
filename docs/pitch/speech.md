# Mantle Sentinel — Demo Day Speech

> ~450 words · 3 minutes · 10 slides

---

**[Slide 1 — Title, 20 sec]**

Hi everyone. I'm Aleksandr, and this is Mantle Sentinel — a training-free behavioral anomaly detector for smart contracts on Mantle.

**[Slide 2 — Problem, 30 sec]**

Three point four billion dollars stolen in 2025 alone. The problem? Current security tools are reactive — they catch known patterns, not new ones. Signature databases miss novel exploits. LLM-based monitors are slow, expensive, and non-deterministic. And the newest protocols — the ones most at risk — have zero historical data to train on.

**[Slide 3 — Solution, 30 sec]**

Sentinel takes a different approach. Every smart contract has a behavioral fingerprint — a pattern of who calls it, which functions, how much gas, what value, at what time. We encode this into a ten-thousand-dimensional hypervector using HDC — Hyperdimensional Computing. When the fingerprint drifts, we catch it. No training data. No GPU. No signatures. Works on any EVM contract from block one.

**[Slide 4 — How It Works, 40 sec]**

Here's the pipeline. Transactions flow through a Shannon entropy pre-filter, then into our HDC encoder which produces a behavioral DNA hypervector every window. We measure drift using Hamming distance and timing deviation. A Bayesian changepoint detector — or a static threshold fallback — fires the alert. Then we attribute which feature caused the shift, and Z.ai translates that into plain English. Critically, the LLM is never in the detection loop. Detection is deterministic and reproducible, byte for byte.

**[Slide 5 — Z.ai Integration, 30 sec]**

Z.ai powers the explanation layer. Every confirmed alert gets a structured finding — which features drifted, by how much, what changed. Z.ai's GLM model translates that into a plain-English brief operators can act on. The prompt is strict: no hallucinated severity, no invented causes. And if the API is unavailable, detection continues with a deterministic canned brief. CI never touches the live API.

**[Slide 6 — Live Demo Results, 30 sec]**

We scanned the top five Mantle contracts by TVL. USDC.e scores eighty-three, Lendle eighty-one — healthy. WMNT, USDT, and mETH show moderate behavioral variance. Our injection benchmark — seven synthetic attack scenarios — produced a four-point-three-x separation ratio between normal and attack drift. Zero false positives across one hundred twenty-nine tests.

**[Slide 7 — On-Chain Proof, 25 sec]**

Every alert is anchored on-chain to our SentinelAlertRegistry on Mantle mainnet. This isn't a database entry — it's an immutable, verifiable record. Anyone can audit alert history directly on Mantlescan. Contract address: zero-eight-nine-nine on Mantle five-thousand.

**[Slide 8 — Developer Experience, 25 sec]**

For developers: one command gives you a full behavioral profile. Sentinel integrates into GitHub Actions as a health gate — your CI fails if a monitored contract's health drops below threshold. Pre-commit hooks block risky pushes. And operators get real-time Telegram alerts through our bot.

**[Slide 9 — Roadmap, 25 sec]**

Where we're going: multi-contract monitoring with a Python SDK, probabilistic confidence scores instead of binary alerts, and tiered severity. Longer term: EVM multi-chain expansion, a SaaS dashboard, and insurance oracle integration — using drift scores for dynamic premium pricing.

**[Slide 10 — CTA, 20 sec]**

Mantle Sentinel: training-free behavioral anomaly detection, on-chain alert anchoring, Z.ai-powered explanations. Try it now — scan any Mantle contract in one command. Links are on screen. Thank you.
