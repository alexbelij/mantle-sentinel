# TZ_PITCH — Demo Day Presentation & Speech

> Для Dev Viktor. Задача: сгенерировать PDF-презентацию (10 слайдов)
> + полный текст спитча на английском.
> Demo Day: Jul 2–3, 2026. Формат: 3–5 мин pitch + Q&A.

---

## ОБЩИЕ ПРАВИЛА

1. Язык: английский. Спитч должен быть простым, без jargon перегруза.
2. Каждый слайд = 1 мысль. Минимум текста, максимум визуала.
3. Стиль: тёмный фон (#0a0a0a), оранжевый акцент (#f97316), белый текст.
   Шрифт: Inter или Space Grotesk. Совпадает с mntsentinel.xyz.
4. Маскот (кибер-богомол) — на титульном слайде и CTA.
5. Спитч: 3 мин = ~450 слов. Каждый слайд ~30–40 сек.
6. Tone: confident, data-driven, не overselling. Hackathon judges ≠ investors.

---

## СЛАЙД 1 — TITLE (20 сек)

**На экране:**
- Logo + маскот
- "MANTLE SENTINEL"
- "Behavioral Anomaly Detection for Smart Contracts"
- "Hackathon Track: AI Alpha & Data"

**Спитч:**
> Hi everyone. I'm [Name], and this is Mantle Sentinel — a training-free behavioral anomaly detector for smart contracts on Mantle.

---

## СЛАЙД 2 — PROBLEM (30 сек)

**На экране:**
- "$3.4B stolen in crypto hacks in 2025"
- 3 пункта:
  - Signature-based tools miss novel attacks
  - LLM monitors are slow and non-deterministic
  - New protocols have zero historical data to train on
- Иконки: 🔒❌ / 🤖⏳ / 📊=0

**Спитч:**
> Three point four billion dollars stolen in 2025 alone. The problem? Current security tools are reactive — they catch known patterns, not new ones. Signature databases miss novel exploits. LLM-based monitors are slow, expensive, and non-deterministic. And the newest protocols — the ones most at risk — have zero historical data to train on.

---

## СЛАЙД 3 — SOLUTION (30 сек)

**На экране:**
- "Every contract has a behavioral fingerprint"
- "Sentinel detects the moment it changes"
- Визуал: нормальный паттерн → аномальный паттерн (drift)
- Ключевые числа: "10,000 dimensions · 0 training · 0 GPU"

**Спитч:**
> Sentinel takes a different approach. Every smart contract has a behavioral fingerprint — a pattern of who calls it, which functions, how much gas, what value, at what time. We encode this into a ten-thousand-dimensional hypervector using HDC — Hyperdimensional Computing. When the fingerprint drifts, we catch it. No training data. No GPU. No signatures. Works on any EVM contract from block one.

---

## СЛАЙД 4 — HOW IT WORKS (40 сек)

**На экране:**
- Pipeline diagram (горизонтальная):
  ```
  TX Stream → Entropy Filter → HDC Encoder → Drift Signal → Detector → Attribution → Z.ai → Alert
  ```
- Под каждым шагом: 1-строчное описание
- Выделить: "LLM is NEVER in the detection loop"

**Спитч:**
> Here's the pipeline. Transactions flow through a Shannon entropy pre-filter, then into our HDC encoder which produces a behavioral DNA hypervector every window. We measure drift using Hamming distance and timing deviation. A Bayesian changepoint detector — or a static threshold fallback — fires the alert. Then we attribute which feature caused the shift, and Z.ai translates that into plain English. Critically, the LLM is never in the detection loop. Detection is deterministic and reproducible, byte for byte.

---

## СЛАЙД 5 — Z.AI INTEGRATION (30 сек)

**На экране:**
- Z.ai logo
- Пример алерта: structured finding → Z.ai → plain English brief
- "Strict template: may only restate Tier-5 findings"
- "Without API key → deterministic fallback (CI-safe)"

**Спитч:**
> Z.ai powers the explanation layer. Every confirmed alert gets a structured finding — which features drifted, by how much, what changed. Z.ai's GLM model translates that into a plain-English brief operators can act on. The prompt is strict: no hallucinated severity, no invented causes. And if the API is unavailable, detection continues with a deterministic canned brief. CI never touches the live API.

---

## СЛАЙД 6 — LIVE DEMO RESULTS (30 сек)

**На экране:**
- Таблица health scores:
  ```
  Contract     Health  Status
  USDC.e         83    Healthy ✅
  Lendle         81    Healthy ✅
  WMNT           74    Moderate ⚠️
  USDT           70    Moderate ⚠️
  mETH           68    Moderate ⚠️
  ```
- "129 tests · 0 false positives · 4.3× separation ratio"
- Dashboard screenshot (mntsentinel.xyz/dashboard)

**Спитч:**
> We scanned the top five Mantle contracts by TVL. USDC.e scores eighty-three, Lendle eighty-one — healthy. WMNT, USDT, and mETH show moderate behavioral variance. Our injection benchmark — seven synthetic attack scenarios — produced a four-point-three-x separation ratio between normal and attack drift. Zero false positives across one hundred twenty-nine tests.

---

## СЛАЙД 7 — ON-CHAIN PROOF (25 сек)

**На экране:**
- SentinelAlertRegistry contract address
- Mantlescan TX screenshot
- "Immutable. Verifiable. On Mantle Mainnet."
- Anchor TX hash (укороченный)

**Спитч:**
> Every alert is anchored on-chain to our SentinelAlertRegistry on Mantle mainnet. This isn't a database entry — it's an immutable, verifiable record. Anyone can audit alert history directly on Mantlescan. Contract address: zero-eight-nine-nine on Mantle five-thousand.

---

## СЛАЙД 8 — DEVELOPER EXPERIENCE (25 сек)

**На экране:**
- Terminal: `python -m sentinel scan 0x09bc... --min-health 60`
- "One command. Full behavioral profile."
- CI/CD badges: GitHub Actions, pre-commit
- Telegram alert screenshot (@MantleSentinelBot)

**Спитч:**
> For developers: one command gives you a full behavioral profile. Sentinel integrates into GitHub Actions as a health gate — your CI fails if a monitored contract's health drops below threshold. Pre-commit hooks block risky pushes. And operators get real-time Telegram alerts through our bot.

---

## СЛАЙД 9 — ROADMAP (25 сек)

**На экране:**
- 3 колонки: NOW / NEXT / FUTURE
  - NOW: Single-contract monitoring, CLI, Telegram, On-chain alerts
  - NEXT: Multi-contract, Python SDK, Confidence scoring, Alert tiers
  - FUTURE: EVM multi-chain, SaaS dashboard, Insurance oracle, MCP integration

**Спитч:**
> Where we're going: multi-contract monitoring with a Python SDK, probabilistic confidence scores instead of binary alerts, and tiered severity. Longer term: EVM multi-chain expansion, a SaaS dashboard, and insurance oracle integration — using drift scores for dynamic premium pricing.

---

## СЛАЙД 10 — CTA (20 сек)

**На экране:**
- Маскот (крупно)
- "MANTLE SENTINEL"
- "Detect Before They Hit"
- Links:
  - 🌐 mntsentinel.xyz
  - 📊 mntsentinel.xyz/dashboard
  - 💻 github.com/alexbelij/mantle-sentinel
  - 🤖 @MantleSentinelBot
- QR-код на GitHub repo

**Спитч:**
> Mantle Sentinel: training-free behavioral anomaly detection, on-chain alert anchoring, Z.ai-powered explanations. Try it now — scan any Mantle contract in one command. Links are on screen. Thank you.

---

## Q&A PREPARATION (не на слайдах)

Жюри могут спросить. Подготовить ответы:

**Q: Why HDC instead of ML/neural nets?**
> HDC gives us three things ML can't here: zero training, deterministic output, and algebraic feature attribution. We can tell you exactly which behavioral feature caused the alert — not a black-box confidence score.

**Q: What about flash loans / MEV?**
> Honest answer: Sentinel monitors multi-window behavioral drift. Single-transaction atomic attacks like flash loans and mempool-level MEV are out of scope by design. Those need separate, complementary systems. We document this in KNOWN_LIMITATIONS.md.

**Q: How does this compare to Forta?**
> Forta relies on community-written detection bots — each one is a signature for a known pattern. Sentinel detects behavioral deviation without any signatures. We catch the unknown unknowns. Complementary, not competing.

**Q: Can this scale to hundreds of contracts?**
> The HDC encoder is O(features × D) per window. D=10,000 is fixed. On a single core, we process a window in <50ms. Multi-contract is a scheduling problem, not a compute problem. Phase 1 roadmap.

**Q: What if the contract is already compromised when you start monitoring?**
> Known limitation #1 — warmup poisoning. If attack patterns are in the warmup window, they become "normal." Phase 3 adds operator-guided safe period labeling. For now, we recommend starting monitoring during known-good periods.

---

## ФОРМАТ ВЫХОДА

Dev Viktor должен создать:
1. `docs/pitch/slides.pdf` — 10 слайдов, 16:9, тёмная тема
2. `docs/pitch/speech.md` — полный текст спитча (~450 слов)
3. `docs/pitch/qa.md` — Q&A карточки (5 вопросов + ответов)

Генерировать слайды через HTML→PDF (Puppeteer/Playwright)
или Python (python-pptx → PDF). НЕ через API-генераторы слайдов.

Все тексты слайдов и спитча — ТОЧНО как в этом ТЗ.
Не менять формулировки, не добавлять маркетинговые фразы.
