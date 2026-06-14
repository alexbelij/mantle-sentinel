# Configuration

All configuration via environment variables. Copy `.env.example` to `.env`.

## Required

| Variable | Description |
|----------|-------------|
| `MANTLE_RPC_URL` | Mantle RPC endpoint (e.g. `https://rpc.mantle.xyz`) |

## Optional — on-chain anchoring

| Variable | Description |
|----------|-------------|
| `MANTLE_PRIVATE_KEY` | Private key for `logAlert()` calls (mainnet) |
| `REGISTRY_ADDRESS` | Override default `0x593C9a4dd6806510e379e30481eaCd27d2016FbE` |

## Optional — notifications

| Variable | Description |
|----------|-------------|
| `ZAI_API_KEY` | Z.ai API key for LLM explanation |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat/group ID for alerts |

## Detector selection

| Variable | Values | Default |
|----------|--------|---------|
| `SENTINEL_DETECTOR` | `static` \| `bocpd` | `static` |

CLI override: `--detector bocpd` (takes precedence over env).

## Pipeline flags (CLI only)

| Flag | Description |
|------|-------------|
| `--dream-mode` | Enable Dream Mode prototype consolidation |
| `--warmup N` | Warm-up window count (default: 200) |
| `--inject SCENARIO` | Inject attack scenario (S1–S6) |
| `--seed N` | Override MASTER_SEED (default: 1337) |

## Math defaults (frozen)

| Parameter | Value | Decision |
|-----------|-------|---------|
| HDC dimension D | 10,000 | D-02 |
| Window W | 50 | MVP_MATH_SPEC |
| Drift threshold θ | 0.65 | MVP_MATH_SPEC |
| k (consecutive) | 3 | MVP_MATH_SPEC |
| Dream N | 100 | D-04 |
| Dream α | 0.5 | D-04 |
| MASTER_SEED | 1337 | MVP_MATH_SPEC |
