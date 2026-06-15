# TZ_BLOG — Medium Technical Blog Post

> Для Dev Viktor. Задача: написать технический блог-пост для Medium.
> Формат: markdown файл `docs/blog/BLOG_POST.md` в репо.
> Публикацию на Medium делает пользователь вручную.

---

## ОБЩИЕ ПРАВИЛА

1. Язык: английский.
2. Tone: technical but accessible. Не академическая статья, но и не маркетинговый fluff.
3. Аудитория: Web3 разработчики, DeFi security researchers, hackathon judges.
4. Длина: 1500–2000 слов (7-10 мин чтения).
5. Структура: hook → problem → innovation → how it works → results → try it → what's next.
6. Code snippets — реальные, рабочие, из репо.
7. Все числа, метрики, адреса — ТОЧНЫЕ из текущего состояния проекта.
8. НЕ упоминать AI-агентов, Viktor, процесс разработки.

---

## СТРУКТУРА СТАТЬИ

### Title
`How We Detect Smart Contract Exploits Without Training Data — Using Hyperdimensional Computing on Mantle`

### Subtitle
`A deep dive into Mantle Sentinel: training-free behavioral anomaly detection with 10,000-dimensional hypervectors, on-chain proof, and Z.ai explainability.`

---

### 1. Hook (150 слов)

Начать с $3.4B stolen in 2025. Bybit $1.5B — крупнейший hack в истории. Проблема: каждый exploit уникален, сигнатурные инструменты опоздали. Вопрос: можно ли детектить аномалию БЕЗ знания паттерна атаки?

### 2. The Problem with Current Approaches (200 слов)

Три подхода и их ограничения:
- **Signature-based** (Chainalysis, Elliptic): база известных паттернов. Miss novel attacks.
- **ML-based** (Forta bots): нужны тренировочные данные, GPU, per-model maintenance.
- **LLM-based**: медленные, недетерминированные, дорогие.

Общий дефект: все три *реагируют* на известное. Никто не детектирует *изменение поведения как таковое*.

### 3. The Core Idea: Behavioral DNA (200 слов)

Каждый контракт генерирует поток транзакций с характерным паттерном: кто звонит, какие функции, сколько газа, в какое время. Это *поведенческий отпечаток*.

HDC (Hyperdimensional Computing) позволяет закодировать этот отпечаток в один вектор размерности 10,000. При нормальной работе отпечатки похожи. При атаке — резко меняются.

Ключевое: для этого не нужны тренировочные данные, GPU, или знание конкретной атаки.

### 4. How It Works — The T0–T5 Pipeline (400 слов)

Описать каждый tier с code snippets:

**T0: Shannon Entropy Filter**
- Мониторит распределение селекторов в calldata
- Hard threshold — bypass BOCPD

**T1: HDC Encoder**
- 5 features: caller, selector, gas bucket, value bucket, timing
- Каждый feature → random hypervector (seed-based, deterministic)
- Binding + bundling → bipolar hypervector D=10,000

Code snippet (упрощённый):
```python
# Каждая транзакция → точка в 10,000-мерном пространстве
window_vector = sign(sum(
    bind(caller_hv, selector_hv, gas_hv, value_hv, timing_hv)
    for tx in window
))
```

**T2: Drift Signal**
```python
drift = max(
    hamming_distance(current, baseline) / D,
    abs(timing_current - timing_baseline) / timing_std
)
```

**T3: Detector**
- BOCPD (Bayesian Online Change Point Detection) — адаптивный
- Static threshold — MVP fallback

**T4: Attribution**
- Feature ablation: убираем feature, пересчитываем drift
- Если drift падает → этот feature виноват

**T5: Z.ai Explanation**
- Structured finding → Z.ai GLM → plain English brief
- LLM НИКОГДА в detection loop

### 5. Results — Real Mantle Data (200 слов)

Таблица: 5 контрактов, health scores.
Injection benchmark: 7 сценариев, 4.3× separation, 0 FP.
129 тестов.
On-chain anchor TX на Mantle mainnet.

### 6. Try It Yourself (150 слов)

```bash
git clone https://github.com/alexbelij/mantle-sentinel
pip install -e .
python -m sentinel scan 0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9
```

Или Python SDK:
```python
from sentinel import SentinelClient
report = SentinelClient().scan("0x09bc4e...")
print(report.health_score)
```

Live dashboard: mntsentinel.xyz/dashboard
Telegram: @MantleSentinelBot

### 7. What's Next (150 слов)

- Multi-contract monitoring
- Probabilistic confidence (beyond binary alerts)
- EVM multi-chain (Arbitrum, Base, OP Stack)
- Insurance oracle integration

### 8. Closing (50 слов)

Link to repo, landing, DoraHacks BUIDL. "Built for Mantle AI Hackathon 2026."

---

## ИЛЛЮСТРАЦИИ

Описать в markdown где нужны изображения (автор добавит сам):

1. Hero image — dashboard screenshot или pipeline diagram
2. Pipeline diagram — T0→T5 flow
3. Health scores table — визуальная
4. Mantlescan TX screenshot — on-chain proof

Placeholder: `![Description](IMAGE_PLACEHOLDER_N)`

---

## ДОПОЛНИТЕЛЬНЫЕ ФАЙЛЫ

Создать `docs/blog/` директорию:

```
docs/blog/
├── BLOG_POST.md           — полный текст статьи
└── BLOG_META.md           — title, subtitle, tags для Medium
```

`BLOG_META.md`:
```markdown
# Blog Post Metadata

- **Title:** How We Detect Smart Contract Exploits Without Training Data — Using Hyperdimensional Computing on Mantle
- **Subtitle:** Training-free behavioral anomaly detection with HDC, on-chain proof, and Z.ai
- **Tags:** Blockchain, DeFi, Security, AI, Smart Contracts
- **Read time:** ~8 min
- **Canonical URL:** https://github.com/alexbelij/mantle-sentinel
```

---

## ФОРМАТ ВЫХОДА

1 коммит:
```
docs/blog/BLOG_POST.md    — ~1800 слов
docs/blog/BLOG_META.md    — метадата
```
