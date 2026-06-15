# Telegram Bot Setup

Interactive monitoring via [@MantleSentinelBot](https://t.me/MantleSentinelBot).

## Architecture

```
GitHub Actions cron (every 4 hours)
  → python scripts/scan_to_supabase.py
  → POST scan results → Supabase (scan_history table)

Telegram user sends /health
  → Telegram → POST /api/telegram (Vercel serverless)
  → GET Supabase REST API → format response → reply
```

## Environment Variables

| Variable | Where | Description |
|----------|-------|-------------|
| `SUPABASE_URL` | Vercel + GitHub Secrets | Supabase project URL |
| `SUPABASE_ANON_KEY` | Dashboard JS (public) | Read-only key for frontend chart |
| `SUPABASE_SERVICE_KEY` | Vercel + GitHub Secrets | Full-access key for writes |
| `TELEGRAM_BOT_TOKEN` | Vercel | Bot token from @BotFather |

## Webhook Setup

Run once after deploying to Vercel:

```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=https://mntsentinel.xyz/api/telegram"
```

Verify:
```bash
curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getWebhookInfo"
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Welcome message + command list |
| `/health` | Latest health scores for all 5 contracts |
| `/scan <addr>` | Latest scan result for a specific address |
| `/status` | Last scan time, total records, uptime |
| `/help` | Command list |

## Adding a New Command

1. Edit `docs/landing/api/telegram.py`
2. Add handler function `_handle_mycommand(chat_id)`
3. Add to the command dispatch in `handler.do_POST()`
4. Push to main → Vercel auto-deploys

## Data Pipeline

`scripts/scan_to_supabase.py` runs via GitHub Actions every 4 hours:

1. Scans 5 hardcoded Mantle contracts via `sentinel.scan.scan_contract()`
2. POSTs results to Supabase `scan_history` table
3. Can also be triggered manually via `workflow_dispatch`

Contracts monitored:
- USDC.e (`0x09bc...`)
- WMNT (`0x78c1...`)
- USDT (`0x201e...`)
- mETH (`0xcda8...`)
- Lendle (`0xcfa5...`)
