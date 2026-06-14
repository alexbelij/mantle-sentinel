# Mantle Sentinel — Post-MVP Roadmap

**Текущий статус:** MVP (hackathon). Один контракт, один оператор, HDC pipeline.  
**Горизонт:** 6–18 месяцев после Demo Day.

---

## ВЕРТИКАЛЬНОЕ РАЗВИТИЕ (углубление продукта)

### V1 — Multi-contract & SDK (мес. 1–2)

**Цель:** из PoC → настоящий инструмент мониторинга.

- **Multi-contract:** параллельный мониторинг 5–20 контрактов от одного оператора
- **SDK Python:** `pip install mantle-sentinel-sdk`
  ```python
  from sentinel import SentinelClient
  s = SentinelClient(contract="0x...", rpc=MANTLE_RPC)
  s.on_alert(lambda a: notify(a.z_ai_text))
  s.run()
  ```
- **Webhook output:** POST alert payload на endpoint клиента (вместо только Telegram)
- **Alert deduplication:** не посылать повторные алерты на один windowId
- **Rate limiting:** Circuit breaker — если >N алертов за 10 мин → режим паузы

**KPI:** 3+ beta-пользователя из Mantle ecosystem (protocols)

---

### V2 — Explainability & Confidence (мес. 2–3)

**Цель:** из "что-то изменилось" → "вот что именно и насколько уверен"

- **Confidence score:** P(alert|drift) из BOCPD posterior → вместо binary alert
- **Feature heatmap:** какой из 5 каналов (selector/caller/gas/value/timing) вносит максимум
- **Alert severity tiers:**
  - `WARNING` (driftScore 0.5–0.7) → Telegram
  - `CRITICAL` (> 0.7) → Telegram + on-chain logAlert()
  - `EMERGENCY` (> 0.9) → всё выше + webhook + PagerDuty
- **Baseline drift report:** еженедельный отчёт "контракт ведёт себя нормально / вот трендовые изменения"

---

### V3 — Adaptive Baseline (мес. 3–4)

**Цель:** не требовать ручной перенастройки после protocol upgrades

- **Dream Mode production:** автоматическая ночная консолидация прототипа
- **Safe window labeling:** оператор помечает периоды как "нормальные" → они идут в консолидацию
- **Poison detection (anti-S6):** если консолидация поглощает подозрительный drift → WARNING перед обновлением прототипа
- **Multi-version prototype store:** хранить последние K прототипов → rollback если FP вырос
- **Anomaly calendar:** visualization какие дни были "горячими"

---

### V4 — Enterprise & SaaS (мес. 4–6)

**Цель:** продаваемый продукт

- **Web dashboard (SaaS):** multi-tenant, каждый клиент видит только свои контракты
- **Alert history:** на-chain + off-chain синхронизированная история
- **Pricing:**
  - Free tier: 1 контракт, Telegram only
  - Pro ($99/мес): до 10 контрактов + webhook + dashboard
  - Enterprise: неограниченно + dedicated RPC + SLA
- **On-chain alert NFT:** каждый CRITICAL alert → NFT на Mantle (доказательство работы для клиента)

---

## ГОРИЗОНТАЛЬНОЕ РАЗВИТИЕ (расширение рынка)

### H1 — EVM Multi-chain (мес. 2–3)

**Целевые сети:** Arbitrum, Base, OP Stack, Polygon zkEVM, zkSync

**Что нужно:**
- RPC provider abstraction (уже почти готово — только chainId меняется)
- Chain-specific gas normalization (разные gas profiles на разных L2)
- `SentinelAlertRegistry` deployment на каждой сети
- Верификация контракта на Arbiscan / Basescan / etc.

**KPI:** поддержка 5 EVM сетей, 1 партнёрский protocol на каждой

---

### H2 — DeFi Protocol Partnerships (мес. 3–6)

**Вертикали:**
- **DEX/AMM:** Merchant Moe, AGNI Finance (Mantle native) — мониторинг LP pool поведения
- **Lending:** Lendle, Init Capital — monitoring borrowing pattern drift
- **Bridges:** Stargate, Across — особо ценны (8–9 цифр TVL)

**Формат партнёрства:**
- Протокол платит подписку → Sentinel мониторит их контракты
- Co-marketing: "Protected by Sentinel"
- Revenue share от страховых протоколов (Nexus Mutual, InsureAce)

---

### H3 — Threat Intelligence Marketplace (мес. 6–12)

**Идея:** агрегировать alert-паттерны от всех клиентов → анонимизировать → продавать как threat intelligence feed.

- Если 10 клиентов детектировали drift одного типа одновременно → cross-contract attack pattern
- Новый клиент получает эти паттерны как "known threat signatures" → детект с 0 warm-up
- Монетизация: $X/мес за доступ к feed

**Аналоги:** VirusTotal для смарт-контрактов.

---

### H4 — Insurance Protocol Integration (мес. 6–12)

**Партнёры:** Nexus Mutual, InsureAce, OpenCover

**Механика:**
- Sentinel предоставляет real-time drift score как oracle
- Страховой протокол корректирует premium в зависимости от drift: низкий drift → скидка, высокий → наценка
- При CRITICAL alert → автоматический триггер потенциального клейма

**Revenue model:** % от premium, который Sentinel "сэкономил" клиенту (risk-adjusted pricing)

---

### H5 — AI Agent Integration (мес. 9–18)

**Тренд:** автономные on-chain агенты (Eigenlayer AVS, TEE-based agents)

- Sentinel как AVS (Actively Validated Service) на Eigenlayer: операторы стейкают ETH, подтверждают drift alerts → slashing за ложные
- Sentinel → MCP tool для AI-агентов: `sentinel_check_drift(contract, window)` → returns drift score + Z.ai explanation
- Integration с Safe Wallet: Alert → автоматический Safe proposal "pause contract"

---

## ТЕХНИЧЕСКИЙ ДОЛГ (параллельно с roadmap)

```
[ ] bench/data: загрузить snapshot 3 контрактов (USDC.e + WMNT + AGNI DEX)
[ ] Benchmark P0 (AB1-AB3): detection rate + FP/day vs FreqBase
[ ] bench/REPORT.md с headline числами
[ ] docs/architecture.md: обновлённая архитектура с BOCPD + Dream Mode
[ ] Foundry tests: coverage > 90% на контракте
[ ] Docker: docker-compose для локального запуска Sentinel
[ ] Grafana dashboard: drift metrics в time series
```

---

## КОНКУРЕНТНАЯ ПОЗИЦИЯ

| | Forta | Chainalysis | Hypernative | Sentinel |
|---|---|---|---|---|
| Подход | Rules + ML агенты | Signature DB | LLM + heuristics | HDC algebraic |
| Latency | минуты | минуты–часы | секунды | < 1 window (~2с) |
| GPU | да | да | да | **нет** |
| Training data | нужна | нужна | нужна | **нет** |
| False positive | средний | низкий | высокий | **контролируемый** |
| Price | дорого | enterprise | enterprise | **SaaS от $99** |
| Explainability | ограничена | нет | частичная | **feature attribution** |

**Главный differentiator:** единственный детектор без training data и GPU. Это важно для:
1. Новых протоколов (нет исторических данных)
2. Novel attack vectors (нет сигнатуры)
3. Resource-constrained operators (нет MLOps)
