# ТЗ: Финальный бандл задач перед подачей и Demo Day

> **Для:** Developer Viktor  
> **Приоритет:** ITER 1–3 до подачи (Jun 15), ITER 4–5 до Demo Day (Jul 2–3)  
> **Репо:** `alexbelij/mantle-sentinel`, ветка `main`  
> **Контракт v2 (mainnet):** `0x0899E1507CFfefF8620455721F5bd528Bb072187`  
> **Live anchor tx:** `0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c` (block 96,680,154)  
> **VictimCounter (Sepolia):** `0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64`  
> **Landing:** `https://mntsentinel.xyz` (Vercel, root: `docs/landing/index.html`)  
> **Dashboard:** `dashboard/index.html` (ethers.js → mainnet RPC, live)  
> **Tests:** 109 Python + 6 Foundry

---

## ITER 1 — Очистка репозитория от AI-артефактов

### 1A. Удалить файлы (28 файлов + 2 директории)

```
AGENTS.md
DESIGN.md
todo.md
docs/REVIEW_PROTOCOL.md
docs/TZ_DEVELOPER_FINAL.md
docs/TZ_LANDING_V4.md
docs/skills/frontend_design.md
docs/skills/landing_page_design.md
docs/skills/motion_foundations.md
docs/status/LOG.md
docs/status/SPIKE.md
docs/status/T13C_LIVE.md
docs/status/spike_lbrouter.png
docs/status/spike_usdce.png
docs/archive/gpt_drafts/ARCHITECTURE_FREEZE.md
docs/archive/gpt_drafts/ARCHIVE_NOTE.md
docs/archive/gpt_drafts/FINAL_FREEZE.md
docs/archive/gpt_drafts/HACKATHON_DELIVERABLES.md
docs/archive/gpt_drafts/LITE_MODE_SPEC.md
docs/archive/gpt_drafts/MVP_IMPLEMENTATION_FREEZE.md
docs/archive/gpt_drafts/MVP_MATH_SPEC.md
docs/archive/gpt_drafts/PROJECT_CONTEXT.md
docs/archive/gpt_drafts/README.md
docs/archive/gpt_drafts/TEAM_CHARTER.md
docs/archive/gpt_drafts/WEBSITE_IMPLEMENTATION_PLAN.md
docs/archive/gpt_drafts/contracts/agent.schema.json
docs/archive/gpt_drafts/contracts/alert.schema.json
docs/archive/gpt_drafts/contracts/evolution.schema.json
docs/archive/gpt_drafts/contracts/prediction.schema.json
```

Если после удаления `docs/archive/` и `docs/skills/` и `docs/status/` станут пустыми — удалить директории целиком.

### 1B. Вычистить AI-следы из оставшихся файлов

**`docs/DEMO_SCRIPT.md`:**
- Удалить строку `> Kurator Viktor. Podat' v repo kak ...`
- Переименовать секцию «Prikhmechaniya dlya Developer Viktor» → «Production notes» (или убрать вообще)
- Заменить все транслитерированный русский на английский
- Обновить стейл-данные (см. 1C)

**`docs/DECISIONS.md`:**
- Строка «Curator audits this file every review» → убрать, оставить просто «Format: D-NN | date | gap | choice | rationale»

**Поиск по всем .md:** `grep -ri "kurator\|curator\|developer viktor\|dev viktor\|podat\|cherez\|agent onboarding\|todo.md\|subagent" *.md docs/**/*.md` — каждое вхождение удалить или переформулировать нейтрально.

### 1C. Обновить стейл-данные в DEMO_SCRIPT.md

| Что | Было | Стало |
|-----|------|-------|
| Anchor tx | `0x4aca92d7…09a78` | `0x086cf07a…fa91c` |
| Explorer | `explorer.mantle.xyz` | `mantlescan.xyz` |
| Тесты | 91 | 109 |
| Контракт | (не указан) | `0x0899E1…2187` (mainnet) |

### 1D. Удалить 22 ветки `task/*`

```bash
task/T-01-scaffold    task/T-09-injector     task/T-17c-bocpd-env
task/T-02-data        task/T-10-scorer       task/T-18-dream
task/T-03-hdc-encoder task/T-13b-victim      task/T-18d-dream-pipeline
task/T-04-drift       task/T-13c-live        task/T-18e-s6-bench
task/T-05-entropy     task/T-13c-selfattack  task/T-19-explain
task/T-05b-prefilter  task/T-17-bocpd        task/T-20-frontend
task/T-06-detector                           task/T-21-telegram
task/T-07-interpreter
task/T-08-replay
```

### 1E. Обновить docs/TASKS.md

Все задачи T-01 по T-21 выполнены. Проставить `[x]` у каждой.

---

## ITER 2 — README: профессиональный уровень

### Текущие проблемы (review жюри / маркетолог / разработчик):

**Жюри:**
1. Один badge — мало. Нет визуального статуса проекта наверху.
2. Нет скриншота / GIF демо — «стена текста». Жюри пролистает.
3. Секция «Why Sentinel» — один абзац, слабо. Нет таблицы сравнения.
4. Нет упоминания хакатона / трека — жюри ищет это.
5. Нет ссылки на Dashboard.

**Маркетолог:**
1. Tagline «Your smart contracts have a behavioral fingerprint» — хорош, но визуально не выделен.
2. CTA (призыв к действию) — нет. Где «Try it» кнопка?
3. Нет визуальной иерархии: pipeline ASCII уводит внимание от Results.
4. Results — самое сильное (4.3×, 0 FP) — должны быть выше.
5. Business model / Target customers — убрать из README (это для pitch, не для GitHub).

**Разработчик:**
1. Quick Start ссылается на `raw.jsonl` — который gitignored. Нужен fallback.
2. `.env.example` — есть ли в репо? Проверить.
3. Нет License badge, Python version badge.
4. `make demo` не упомянут — а это самый быстрый путь.

### Что сделать:

**Badges (строка 2, сразу под H1):**
```markdown
[![Tests](https://github.com/alexbelij/mantle-sentinel/actions/workflows/pytest.yml/badge.svg)](...)
![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue)
![License MIT](https://img.shields.io/badge/license-MIT-green)
![Mantle Mainnet](https://img.shields.io/badge/Mantle-Mainnet-blue?logo=data:...)
![109 tests](https://img.shields.io/badge/tests-109%20passed-brightgreen)
```

**Структура README (новый порядок):**

```
# Mantle Sentinel — HDC Behavioral DNA Agent
[badges row]

> Tagline (1 строка)

**Built for Mantle AI Hackathon — Turing Test Phase II, Track 02: AI Alpha & Data**

[Live Demo](https://mntsentinel.xyz) · [Dashboard](ссылка) · [Contract](mantlescan link)

---

## The Problem (2-3 строки)

## How It Works (pipeline diagram — KEEP as is, it's good)

## Results (MOVE UP — this is the killer section)
[таблица как есть]
[injection scenarios как есть]

## Quick Start (упростить)
```bash
git clone ... && cd mantle-sentinel
pip install -r requirements.txt
python bench/self_attack.py --dry-run    # ← zero config, works immediately
```
Для live режима: [см. docs/wiki/self-attack-demo.md]

## Comparison
| | Sentinel | Forta | Chainalysis | LLM monitor |
|---|---|---|---|---|
| Training | None | Per-bot | Signatures | Fine-tune |
| Detection | Algebraic | Rule/ML | Pattern DB | Prompt |
| Speed | <1µs/tx | Seconds | Batch | 1-5s/tx |
| GPU | No | Optional | No | Required |
| Novel attacks | ✅ | ❌ | ❌ | Partial |

## Architecture
[repo layout — keep]

## Contract
[contract table — keep]

## CI / Tests
109 Python + 6 Foundry

---
**Track:** AI Alpha & Data · **Hackathon:** Mantle Turing Test Phase II
```

**Убрать из README:**
- «Target customers» / «Business model» абзац → в pitch
- «Why Sentinel» секцию → заменить на Comparison table

---

## ITER 3 — Landing: FAQ + Roadmap секции

### 3A. FAQ секция (после секции Proof/Results, перед footer)

Формат: «Нет, но...» / «Да, и...» — контринтуитивные ответы, цепляющие внимание.

```
FAQ

Q: Is this just a threshold alert?
A: No. HDC encodes behavior into a 10,000-dimensional hypervector.
   Hamming distance measures semantic behavioral drift —
   not a number crossing a line.

Q: Do you use an LLM for detection?
A: No. Z.ai only explains alerts AFTER algebraic detection.
   The model is never in the detection loop. <1µs per transaction.

Q: Can it detect novel/zero-day attacks?
A: Yes. Sentinel detects behavioral change itself — not known
   patterns. If an exploit changes how a contract behaves,
   Sentinel sees it.

Q: What if the contract legitimately upgrades?
A: Dream Mode adapts: V_new = sign(λ·V_old + Σ V_safe).
   The baseline evolves to safe behavior without retraining.

Q: Can I run it locally?
A: Yes. `python bench/self_attack.py --dry-run` — zero API keys,
   zero config. Full pipeline demo in 30 seconds.
```

Стиль: тёмный фон как у остального landing, моноширинный шрифт для Q/A, amber акценты для ключевых терминов.

### 3B. Roadmap секция (после FAQ, перед footer)

Абстрактная версия (без цен, KPI, конкретных цепочек):

```
Roadmap

Now (MVP)
  ✅ HDC pipeline (5 tiers)
  ✅ BOCPD changepoint detection
  ✅ Dream Mode baseline adaptation
  ✅ On-chain alert anchoring
  ✅ Z.ai explanations
  ✅ Self-attack demo

Next
  → Multi-contract parallel monitoring
  → Python SDK (pip install)
  → Webhook alert delivery
  → Confidence scoring (BOCPD probability)

Future
  → Feature attribution heatmap
  → Alert severity tiers
  → SaaS dashboard (multi-tenant)
  → EVM multi-chain expansion
  → AI agent integration (MCP / Safe)
```

Стиль: timeline или 3-column grid (Now / Next / Future). Зелёные чекмарки для MVP, amber стрелки для Next/Future.

---

## ITER 4 — Dashboard deploy

### Задача
`dashboard/index.html` — полностью рабочий (ethers.js → Mantle mainnet RPC → `getAlertCount()` → drift gauge + alert table). Нужно задеплоить как отдельную страницу.

### Вариант: отдельный Vercel проект
1. Создать `vercel.json` в корне `dashboard/`:
```json
{
  "buildCommand": "",
  "outputDirectory": ".",
  "framework": null
}
```
2. Или: добавить `dashboard/index.html` как `/dashboard` route в текущий Vercel проект через rewrites.

### Предпочтительный вариант: subpath в текущем проекте
В корень репо добавить `vercel.json`:
```json
{
  "rewrites": [
    { "source": "/dashboard", "destination": "/dashboard/index.html" }
  ]
}
```
Тогда Dashboard будет на `https://mntsentinel.xyz/dashboard`.

### После деплоя
- Добавить ссылку на dashboard в README
- Добавить ссылку на dashboard в landing (кнопка «Live Dashboard»)
- Обновить BUIDL_SUBMISSION.md если нужно

---

## ITER 5 — Demo Video (стория + ТЗ)

### Психология внимания (структура «hook → pain → solution → proof → magic → CTA»)

**Формат:** Screen recording + text overlays (lower thirds + captions) + лёгкая фоновая музыка. Без голоса. Длительность: 2:30–3:00.

### Покадровый сценарий

| # | Время | Экран | Текст на экране (overlay) | Цель |
|---|-------|-------|---------------------------|------|
| 0 | 0–5s | Чёрный → fade-in логотип Sentinel + tagline | `Mantle Sentinel` / `Behavioral DNA for DeFi` | Брендинг |
| 1 | 5–12s | Заголовки из новостей об эксплойтах (Euler $197M, Ronin $625M) | `$3.8B stolen from DeFi in 2024` / `Every exploit was a "valid" transaction` | БОЛЬ — захват внимания |
| 2 | 12–22s | Анимация: нормальные транзакции → пульс → аномалия | `What if contracts had a behavioral fingerprint?` / `And you could see when it changes?` | ИНТРИГА — вопрос |
| 3 | 22–35s | Terminal: `python bench/self_attack.py --warmup 30` — 30 benign txs, drift ~0.09 | `Normal behavior: drift stays low ≈ 0.09` / `30 transactions. Stable baseline.` | РЕШЕНИЕ — показать норму |
| 4 | 35–55s | Terminal продолжается: 8 attack txs → `entropy_anomaly` → drift spike | `Attack injected. 8 anomalous transactions.` / `Detected in ≤2 windows. Zero false positives.` | PROOF — атака поймана |
| 5 | 55–70s | Mantlescan: anchor tx `0x086cf07a…` status=1 | `Alert anchored on Mantle mainnet` / `Immutable. Verifiable. On-chain proof.` | ON-CHAIN — не просто консоль |
| 6 | 70–85s | Dashboard: drift gauge spike → alert table with ENTR row | `Live dashboard polls mainnet every 10s` / `getAlertCount() = 1` | ВИЗУАЛ — красиво |
| 7 | 85–100s | Z.ai response: «selector distribution changed 61%, gas elevated 22%» | `Z.ai explains WHY — not a black box` / `LLM only explains. Never detects.` | ОБЪЯСНИМОСТЬ |
| 8 | 100–115s | Код: `sentinel/dream.py` строка V_new + `sentinel/bocpd.py` строка R | `Dream Mode: baseline self-heals` / `BOCPD: Bayesian regime detection` | TECH DEPTH — реальный код |
| 9 | 115–130s | Pipeline diagram (из README) с подсветкой каждого tier | `5 tiers. <500 lines core. 109 tests.` / `No GPU. No training. Pure math.` | СВОДКА |
| 10 | 130–145s | Comparison table (Sentinel vs Forta vs LLM) | `Training-free. Microsecond. Deterministic.` | КОНКУРЕНТНОЕ ПРЕИМУЩЕСТВО |
| 11 | 145–155s | GitHub repo + mntsentinel.xyz + mantlescan contract | `Open source. Try it yourself.` / links | CTA |

### Технические требования
- Разрешение: 1920×1080 (16:9)
- Музыка: ambient electronic, тихая (royalty-free)
- Шрифт overlays: Space Grotesk (bold) + JetBrains Mono (code) — как на landing
- Цвета: тёмный фон (#090909), amber (#f97316) акценты, белый текст
- Текстовые метки появляются с fade-in, исчезают с fade-out
- Terminal: настоящий запуск self_attack.py (можно ускорить 2×)
- Финальный экран 10с: logo + GitHub + landing URL + contract address

### Музыка (рекомендации)
- Pixabay / Uppbeat: «corporate ambient», «tech background», «minimal electronic»
- Громкость: -20dB от terminal звуков (если есть)

---

## ITER 6 — Pitch / Presentation

### Структура слайдов (8–10 слайдов, 3–5 мин)

| # | Слайд | Содержание | Время |
|---|-------|------------|-------|
| 1 | Title | Mantle Sentinel logo + tagline + Track 02 | 15s |
| 2 | Problem | $3.8B stolen. Exploits = valid txs. Signatures fail on novel attacks. | 30s |
| 3 | Insight | Contracts have behavioral DNA. Exploits break the pattern. | 20s |
| 4 | Solution | HDC pipeline diagram. 10,000-dim vector. Hamming drift. | 40s |
| 5 | How It Works | 5-tier flow: Entropy → HDC → Drift → Detect → Explain | 40s |
| 6 | Results | 4.3× separation, 0 FP, ≤2 windows. Table + chart. | 30s |
| 7 | Live Proof | Contract address, anchor tx, dashboard screenshot. | 30s |
| 8 | Differentiators | Comparison: vs Forta vs Chainalysis vs LLM. No GPU/training. | 30s |
| 9 | Roadmap | Now → Next → Future (abstract). | 20s |
| 10 | CTA | GitHub, mntsentinel.xyz, contract. «Your contracts have DNA. Do you know when it changes?» | 15s |

### Спитч (текст для каждого слайда)

**Slide 1:** «Mantle Sentinel. We detect behavioral drift in smart contracts — before exploits complete.»

**Slide 2:** «In 2024, DeFi lost 3.8 billion dollars. Euler lost 197 million in transactions that passed every validity check. The problem? Signature-based tools can't catch what they've never seen.»

**Slide 3:** «Every smart contract has a behavioral fingerprint — a pattern of selectors, gas usage, timing, calldata structure. Sentinel learns this fingerprint as a 10,000-dimensional hypervector. When something changes — we know.»

**Slide 4:** «Our pipeline has 5 tiers. First, an entropy pre-filter catches selector flooding. Then HDC encodes 50 transactions into a single bipolar hypervector. Hamming distance measures behavioral drift. A detector — static or Bayesian — fires the alert. Finally, feature attribution tells you exactly WHAT changed, and Z.ai translates it to English.»

**Slide 5:** «This is algebraic, not statistical. No training data. No GPU. Microsecond updates. The LLM is never in the detection loop — it only explains what the math already found.»

**Slide 6:** «On real Mantle USDC.e data: 4.3 times separation between clean and attack. Zero false positives. Detection within 2 windows — that's under 100 transactions.»

**Slide 7:** «This isn't a simulation. Our alert is anchored on Mantle mainnet — contract 0x0899, block 96 million 680 thousand 154. You can verify it right now on Mantlescan. The live dashboard polls the contract every 10 seconds.»

**Slide 8:** «Compared to Forta: no bot training. Compared to Chainalysis: catches zero-day. Compared to LLM monitors: 1 microsecond vs 5 seconds, and fully deterministic — same input, same output, every time.»

**Slide 9:** «Next: multi-contract monitoring, Python SDK, webhook delivery, confidence scoring. Future: SaaS dashboard, EVM multi-chain, AI agent integration.»

**Slide 10:** «Mantle Sentinel. Your smart contracts have behavioral DNA. Do you know when it changes? Try it: mntsentinel.xyz, GitHub open source, contract on Mantle mainnet.»

### Дизайн слайдов
- Тёмный фон (#090909), amber акценты (#f97316)
- Шрифты: Space Grotesk + JetBrains Mono (как landing)
- Минимум текста на слайде — ключевые цифры + визуал
- Слайд Results: большие цифры «4.3×», «0 FP», «≤2 windows»
- Слайд Proof: скриншот mantlescan tx + dashboard

---

## Сводка ITER'ов

| ITER | Что | Приоритет |
|------|-----|-----------|
| 1 | Очистка репо (28 файлов, 22 ветки, AI-следы, TASKS.md) | P0 — до подачи |
| 2 | README: badges, restructure, comparison table | P0 — до подачи |
| 3 | Landing: FAQ + Roadmap секции | P0 — до подачи |
| 4 | Dashboard deploy (subpath /dashboard) | P1 — до подачи |
| 5 | Demo video (screen recording + overlays) | P2 — до Demo Day |
| 6 | Pitch/presentation (slides + script) | P2 — до Demo Day |

Каждый ITER — отдельный коммит с описанием.
