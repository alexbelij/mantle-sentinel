# TZ — FINAL POLISH (pre-submission)

**Приоритет:** P0 • **Дедлайн:** Jun 15 23:59 UTC+3

---

## ITER 12 — Удалить AI-trace файлы

Удалить из main одним коммитом `chore: remove internal task specs`:

```
docs/TZ_ALGO_FIXES.md
docs/TZ_ALGO_REVIEW.md
docs/TZ_FINAL_BUNDLE.md
docs/TZ_PATCH_HEALTH.md
docs/TZ_SCAN_BUNDLE.md
docs/TASKS.md
```

**НЕ удалять** (легитимные project docs):
- `ALGO_REVIEW.md` — показывает тщательность ревью
- `BUIDL_SUBMISSION.md`, `DEMO_SCRIPT.md` — для сабмишена
- `ARCHITECTURE_FREEZE.md`, `MVP_MATH_SPEC.md`, `MVP_IMPLEMENTATION_FREEZE.md` — спеки
- `BENCHMARK_PROTOCOL.md`, `DECISIONS.md`, `KNOWN_LIMITATIONS.md`, `ROADMAP.md` — docs
- `zai_prompt.md` — Z.ai integration doc
- `docs/wiki/*` — wiki pages

---

## ITER 13 — Health cards на dashboard

**Файл:** `docs/landing/dashboard/index.html`

Добавить секцию *"Monitored Contracts"* **над** таблицей алертов. 5 карточек из статических данных (hardcoded из `bench/reports/*.json`):

```
┌─────────────────────────────────────────────────┐
│  MONITORED CONTRACTS                            │
│                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │ USDC.e   │ │ WMNT     │ │ USDT     │        │
│  │ 83/100 🟢│ │ 74/100 🟡│ │ 70/100 🟡│        │
│  │ 4 alerts │ │ 6 alerts │ │ 12 alerts│        │
│  │ Stablecoin│ │ Wrapped  │ │Stablecoin│        │
│  └──────────┘ └──────────┘ └──────────┘        │
│  ┌──────────┐ ┌──────────┐                      │
│  │ mETH     │ │ Lendle   │                      │
│  │ 68/100 🟡│ │ 81/100 🟢│                      │
│  │ 4 alerts │ │ 4 alerts │                      │
│  │ LST      │ │ Lending  │                      │
│  └──────────┘ └──────────┘                      │
└─────────────────────────────────────────────────┘
```

**Данные для карточек (hardcode):**

| Contract | Protocol | Type | Health | Alerts | Drift med | Drift p99 | Selectors |
|----------|----------|------|--------|--------|-----------|-----------|-----------|
| 0x09bc4e… | USDC.e | Stablecoin | 83 | 4 | 0.222 | 0.730 | 4 |
| 0x78c1b0… | WMNT | Wrapped | 74 | 6 | 0.282 | 0.778 | 10 |
| 0x201eba… | USDT | Stablecoin | 70 | 12 | 0.153 | 0.656 | 2 |
| 0xcda86a… | mETH | LST | 68 | 4 | 0.274 | 0.978 | 2 |
| 0xcfA5aE… | Lendle Pool | Lending | 81 | 4 | 0.317 | 0.706 | 5 |

**Дизайн карточек:**
- Сохранить существующий стиль dashboard (тёмная тема, CSS variables из текущего файла)
- Score ≥ 80 → зелёный (`#22c55e`), 60–79 → жёлтый/amber (`#f59e0b`), < 60 → красный
- Каждая карточка: protocol name, score круговой/arc, alert count, type badge, ссылка на Mantlescan адреса
- Responsive: 3+2 на desktop, 2+2+1 или стек на mobile
- Health score как крупная цифра (или mini ring/arc)
- Под каждой карточкой мелким шрифтом: `drift median / p99`

**Важно:** данные статические (не fetch). Это pre-computed bench/reports.

---

## ITER 14 — Скриншоты для README

Сделать headless-скриншоты (Playwright или Puppeteer) и закоммитить в `docs/images/`:

1. **`landing-hero.png`** — `mntsentinel.xyz`, viewport 1280×800, full hero above fold
2. **`dashboard.png`** — `mntsentinel.xyz/dashboard/`, viewport 1280×800, после того как карточки + алерты загрузятся (wait 3s для ethers.js poll)
3. **`dashboard-mobile.png`** — `mntsentinel.xyz/dashboard/`, viewport 390×844 (iPhone 14)

После скриншотов — обновить `README.md`:
- Добавить секцию `## Screenshots` после `## Results` (или встроить в существующие секции)
- Markdown: `![Landing](docs/images/landing-hero.png)` и т.д.

**Порядок:** ITER 13 (health cards) деплоится на Vercel → ITER 14 (скриншоты) ПОСЛЕ деплоя.

⚠️ Между ITER 13 и ITER 14 нужно дождаться Vercel deploy (обычно ~30 сек после push). Проверить: `curl -sI https://mntsentinel.xyz/dashboard/ | head -5`.

---

## Верификация

- [ ] 6 TZ/TASKS файлов удалены из `docs/`
- [ ] Dashboard показывает 5 карточек с health scores
- [ ] Карточки responsive (desktop/mobile)
- [ ] 3 скриншота в `docs/images/`
- [ ] README обновлён со скриншотами
- [ ] `make check` green
- [ ] Визуальная проверка: `mntsentinel.xyz/dashboard/` показывает 5 контрактов + 1 on-chain алерт
