# Mantle Sentinel — HDC Behavioral DNA Agent

Real-time **behavioral drift detection** for Mantle smart contracts. Sentinel learns a contract's
behavioral fingerprint ("DNA") as a hyperdimensional vector and raises explainable alerts when the
live transaction stream stops looking like the contract it learned.

> Первое применение Hyperdimensional Computing для поведенческих отпечатков DeFi-контрактов на
> Mantle: BOCPD заменяет магические пороги на байесовскую детекцию смены режима, а Dream Mode
> обновляет память агента ночью.

## Why

Exploits rarely announce themselves, but they almost always *behave differently*: new selectors,
new caller patterns, shifted gas profiles, timing bursts, mutated calldata. Signature-based tools
miss novel attacks; pure-LLM monitors are slow and expensive. Sentinel detects *change itself* —
cheap, deterministic, per-transaction — and only then asks an LLM to explain it.

## Pipeline

```
tx → Tier 0 timing pre-filter → Tier 1 Shannon entropy → Tier 2 HDC encode (D=10,000)
   → drift = max(norm(hamming), norm(timing)) → Tier 3 detector (static θ / BOCPD)
   → Tier 4 DNA drift explainer → Tier 5 Z.ai GLM → Telegram + on-chain SentinelAlertRegistry
```

Details: [`docs/ARCHITECTURE_FREEZE.md`](docs/ARCHITECTURE_FREEZE.md) ·
math: [`docs/MVP_MATH_SPEC.md`](docs/MVP_MATH_SPEC.md) ·
evaluation: [`docs/BENCHMARK_PROTOCOL.md`](docs/BENCHMARK_PROTOCOL.md)

## What makes it interesting

- **HDC behavioral fingerprints** — a contract's normal behavior compressed into one bipolar
  hypervector; structural deviation = Hamming distance. No training, no GPU, microsecond updates.
- **Explainable by construction** — feature-ablation attribution names *what* drifted
  (caller / selector / gas / value / timing) before any LLM is involved.
- **Deterministic replays** — same snapshot + seed ⇒ byte-identical alerts (CI-enforced).
- **Measured, not vibed** — detection delay (blocks) and false-positive episodes/day against a
  frequency baseline at a matched FP budget; scenarios S1–S8 in the benchmark protocol.

## Repository layout

```
sentinel/    detection pipeline (numpy-only, Python 3.11+)
bench/       snapshots, injectors, scoring, REPORT.md
contracts/   alert.schema.json + SentinelAlertRegistry.sol (Mantle alert anchor)
tests/       unit + golden-file determinism tests
docs/        frozen specs, tasks, decisions, status log
```

## Run

```bash
make check                                   # lint + tests
python -m sentinel replay --snapshot bench/data/<contract>/raw.jsonl
python -m sentinel replay --snapshot ... --inject S1   # injected incident demo
```

## Status

Hackathon MVP (Mantle Turing Test Hackathon 2026, Track 02 — AI Alpha & Data).
Backlog: [`docs/TASKS.md`](docs/TASKS.md) · log: [`docs/status/LOG.md`](docs/status/LOG.md).
Historical GPT design drafts live in `docs/archive/gpt_drafts/` and are **not** source of truth.

## License

MIT
