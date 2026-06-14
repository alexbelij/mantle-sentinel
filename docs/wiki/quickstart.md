# Quick Start

## Prerequisites

- Python 3.11+
- `uv` (fast Python package manager)
- Mantle RPC endpoint (e.g. `https://rpc.mantle.xyz`)
- Optional: Z.ai API key, Telegram bot token

## 1. Clone and install

```bash
git clone https://github.com/alexbelij/mantle-sentinel.git
cd mantle-sentinel
cp .env.example .env
# Edit .env with your RPC URL and keys
uv sync
```

## 2. Run tests

```bash
make check
# Expected: 109 passed, make lint green
```

## 3. Replay with injection

```bash
# Inject S1 (hi-entropy attack) and detect drift
uv run python -m sentinel replay \
  --snapshot data/snapshots/usdc_e_snapshot.json \
  --inject S1 \
  --warmup 200

# With Dream Mode enabled
uv run python -m sentinel replay \
  --snapshot data/snapshots/usdc_e_snapshot.json \
  --inject S1 \
  --warmup 200 \
  --dream-mode

# With BOCPD detector
SENTINEL_DETECTOR=bocpd uv run python -m sentinel replay \
  --snapshot data/snapshots/usdc_e_snapshot.json \
  --inject S1
```

## 4. Self-attack demo (dry run)

```bash
uv run python bench/self_attack.py --warmup 50 --dry-run
```

## Environment Variables

See [Configuration](configuration) for all options.

## Project Structure

```
sentinel/           # Core pipeline (encoder, drift, detector, dream, interpreter)
bench/              # Injectors, scorer, benchmark harness, REPORT.md
contracts/          # SentinelAlertRegistry (Solidity), deployments.json
dashboard/          # Live HTML dashboard
docs/               # Specs, decisions, status logs
tests/              # 109 deterministic tests
```
