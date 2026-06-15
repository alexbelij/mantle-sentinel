# TZ_INTERACTIVE — Telegram-бот + Drift Chart (Demo Day)

> Для Dev Viktor. 2 фичи: интерактивный Telegram-бот и drift timeline chart в дашборде.
> Архитектура: Supabase (free tier) как data layer, Vercel API routes, GitHub Actions cron.

---

## АРХИТЕКТУРА

```
┌──────────────────────────────────────────────────────────────┐
│  GitHub Actions cron (каждые 4 часа)                         │
│  python -m sentinel scan <5 контрактов> --json               │
│       │                                                      │
│       ▼                                                      │
│  POST → Supabase REST API → таблица scan_history             │
└──────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────┐    ┌──────────────────────────────┐
│ Telegram Bot         │    │ Dashboard drift chart         │
│ Vercel: /api/telegram│    │ JS → Supabase anon read      │
│ webhook handler      │    │ Canvas/SVG timeline           │
└─────────────────────┘    └──────────────────────────────┘
```

---

## ПРЕДВАРИТЕЛЬНЫЙ ШАГ (РУЧНОЙ — Aleksandr)

Создать Supabase проект (бесплатный):
1. https://supabase.com → New Project
2. Region: EU West
3. Записать: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`
4. SQL Editor → выполнить:

```sql
create table scan_history (
  id bigint generated always as identity primary key,
  contract text not null,
  contract_name text,
  health_score int not null,
  drift_median float,
  drift_p99 float,
  alert_count int default 0,
  tx_analyzed int default 0,
  scanned_at timestamptz default now()
);

create index idx_scan_contract_time on scan_history(contract, scanned_at desc);

-- RLS: анонимный read-only для дашборда
alter table scan_history enable row level security;
create policy "anon_read" on scan_history for select using (true);
```

5. Добавить в Vercel Environment Variables:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (для dashboard JS — публичный)
   - `SUPABASE_SERVICE_KEY` (для API routes и GH Actions — секретный)
   - `TELEGRAM_BOT_TOKEN` (уже есть)
   - `ZAI_API_KEY` (уже есть)

6. Добавить в GitHub Secrets:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_KEY`

---

## ITER 1 — Data Pipeline (GitHub Actions → Supabase)

### Файлы

**`scripts/scan_to_supabase.py`** — скрипт, который:
1. Запускает `sentinel.scan.analyze_records()` для 5 контрактов
2. POST результаты в Supabase REST API (`/rest/v1/scan_history`)
3. Использует `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` из env

Контракты (hardcoded список):
```python
CONTRACTS = {
    "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9": "USDC.e",
    "0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8": "WMNT",
    "0x201eba5cc46d216ce6dc03f6a759e8e766e956ae": "USDT",
    "0xcda86a272531e8640cd7f1a92c01839911b90bb0": "mETH",
    "0xcfa5ae7c2ce8fadc6426c1ff872ca45378fb7cf3": "Lendle",
}
```

**`.github/workflows/scan-cron.yml`** — обновить:
```yaml
name: Sentinel Health Scan
on:
  schedule:
    - cron: '0 */4 * * *'     # каждые 4 часа
  workflow_dispatch:
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - name: Scan and push to Supabase
        run: python scripts/scan_to_supabase.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
```

### Проверка ITER 1
- `workflow_dispatch` → запустить вручную
- Supabase Table Editor → 5 строк появились
- Повторный запуск → ещё 5 строк (history растёт)

---

## ITER 2 — Telegram Bot (Vercel API Route)

### Структура

Перенести Vercel проект из `docs/landing/` в корень репо (или добавить `api/` в `docs/landing/`).

Проще: добавить `api/` в `docs/landing/` и обновить `vercel.json`:

**`docs/landing/api/telegram.py`** — Vercel Python serverless function:

```
POST /api/telegram ← Telegram webhook
```

Команды:
| Команда | Действие |
|---------|----------|
| `/start` | Приветствие + список команд |
| `/health` | Последний health score всех 5 контрактов (из Supabase) |
| `/scan <addr>` | Последний скан конкретного адреса (из Supabase) |
| `/status` | Uptime: когда был последний скан, сколько записей в БД |
| `/help` | Список команд |

Логика:
1. Парсить `update.message.text`
2. Для `/health` и `/scan`: `GET {SUPABASE_URL}/rest/v1/scan_history?...&order=scanned_at.desc&limit=5`
3. Форматировать ответ в Telegram HTML:
```
🛡 Mantle Sentinel — Health Report

USDC.e  ██████████ 83 ✅
Lendle  ████████░░ 81 ✅
WMNT    ███████░░░ 74 ⚠️
USDT    ███████░░░ 70 ⚠️
mETH    ██████░░░░ 68 ⚠️

📊 Last scan: 2 hours ago
```
4. Ответить через `sendMessage` API

**`docs/landing/api/requirements.txt`**:
```
httpx>=0.27
```

**`docs/landing/vercel.json`** — добавить:
```json
{
  "functions": {
    "api/telegram.py": {
      "runtime": "python3.11",
      "maxDuration": 10
    }
  }
}
```

### Установка webhook (одноразово)
```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -d "url=https://mntsentinel.xyz/api/telegram"
```

Добавить эту команду в README (секция Telegram Bot Setup).

### Проверка ITER 2
- Деплой на Vercel
- Установить webhook
- В Telegram: `/start` → ответ
- `/health` → 5 контрактов с баллами
- `/scan 0x09bc...` → детали одного контракта

---

## ITER 3 — Dashboard Drift Chart

### Файл: `docs/landing/dashboard/index.html` — добавить секцию

После существующих health cards добавить:
```
┌─────────────────────────────────────────────────────┐
│  HEALTH SCORE TIMELINE                              │
│                                                     │
│  85 ─┤          ●                    ●              │
│  80 ─┤    ●──────────●         ●────────            │
│  75 ─┤  ●                ●                          │
│  70 ─┤──────────────────────────────────────        │
│      └──┬──────┬──────┬──────┬──────┬──────         │
│       Jun 10  Jun 11  Jun 12  Jun 13  Jun 14        │
│                                                     │
│  ── USDC.e  ── WMNT  ── USDT  ── mETH  ── Lendle   │
└─────────────────────────────────────────────────────┘
```

Реализация:
1. Fetch из Supabase:
```javascript
const SUPABASE_URL = 'https://xxx.supabase.co';
const SUPABASE_KEY = 'eyJ...'; // anon key (read-only, safe for frontend)

async function fetchDriftHistory() {
  const res = await fetch(
    `${SUPABASE_URL}/rest/v1/scan_history?order=scanned_at.desc&limit=200`,
    { headers: { 'apikey': SUPABASE_KEY } }
  );
  return res.json();
}
```

2. Рендер на `<canvas>`:
- Ось X: время (дни)
- Ось Y: health score (0-100)
- 5 линий (по одной на контракт), каждая своего цвета
- Цвета: USDC.e=#22d3ee, WMNT=#f97316, USDT=#5b8c63, mETH=#c79a3a, Lendle=#e05252
- Hover-тултип: контракт, дата, score
- Горизонтальная пунктирная линия на 60 (threshold)
- Стиль: тёмный фон (#111111), сетка (#1f1f1f), как в дашборде

3. **Без внешних библиотек** — чистый Canvas API. Файл не должен зависеть от chart.js и т.п.

4. Легенда под графиком: 5 цветных квадратиков + названия

### Проверка ITER 3
- Открыть `mntsentinel.xyz/dashboard`
- График отображается с данными из Supabase
- Hover показывает тултипы
- Мобильная версия: график масштабируется

---

## ITER 4 — Docs + README + Update

### README.md — добавить секции:

**Telegram Bot** (после SDK секции):
```markdown
## 🤖 Telegram Bot

Interactive monitoring via [@MantleSentinelBot](https://t.me/MantleSentinelBot):

| Command | Description |
|---------|-------------|
| `/health` | Health scores for all monitored contracts |
| `/scan <address>` | Latest scan for a specific contract |
| `/status` | Monitoring uptime and stats |
| `/help` | List of commands |

The bot reads from a Supabase database updated every 4 hours
via GitHub Actions.
```

**Architecture diagram** (обновить если есть):
- Добавить Supabase + Telegram в диаграмму

### Wiki — добавить:
**`docs/wiki/telegram-bot.md`** — setup guide:
- Как установить webhook
- Environment variables
- Как добавить новую команду

### Проверка ITER 4
- README корректный, ссылки рабочие
- Wiki страница есть
- `make check` зелёный

---

## СТИЛЬ / ОГРАНИЧЕНИЯ

- Python: ruff clean, тесты pytest для нового кода
- JS в дашборде: без внешних зависимостей (no npm, no CDN libs)
- Supabase credentials: НИКОГДА не коммитить. Только env vars.
- Telegram bot token: НИКОГДА не коммитить.
- Vercel: free tier лимиты — 10s timeout, 100GB bandwidth
- Canvas chart: responsive, dark theme matching dashboard
