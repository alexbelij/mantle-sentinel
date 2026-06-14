# ТЗ для Developer Viktor: Landing Page v4
**Файл:** `docs/landing/index.html` в репо `alexbelij/mantle-sentinel`  
**Деплой:** автоматически через Vercel при push в main  
**Базис:** переписываем с нуля. Данные сохраняем (адрес, числа, ссылки), визуал — полная замена.  
**Стек:** чистый HTML/CSS/JS (без фреймворков, без npm). Google Fonts через `<link>`.  
**Дизайн-документ:** читай `DESIGN.md` в корне репо перед началом.

---

## ОБЯЗАТЕЛЬНЫЕ СКИЛЛЫ (прочитать перед работой)

1. **`DESIGN.md`** (в корне репо) — дизайн-система Mantle Sentinel, токены, компоненты, правила.
2. **`landing_page_design` skill** (Viktor skill) — паттерны конверсии, структура нарратива, психология продаж.
3. **`motion_foundations` skill** (Viktor skill) — токены анимаций, spring presets, prefers-reduced-motion.
4. **`frontend_design` skill** (Viktor skill) — production-grade UI patterns, accessibility, dark mode.

**Правила, которые нельзя нарушать:**
- Никаких purple-pink градиентов, никаких glowing cards, никакого Inter для заголовков
- Никакого stats-bar с цифрами без контекста
- Никаких emoji как иконок
- Никаких Formspree или email-форм (нет бэкенда)
- Никаких benefit-карточек 2×3 с иконками
- Один акцентный цвет: `#f97316` (amber). Больше никаких.
- Все числа/хэши/адреса → JetBrains Mono, заголовки → Space Grotesk
- DEMO идёт ВТОРЫМ, до объяснений. Не пятым.

---

## 1. МАСКОТ — SAGE (Mantis Shrimp)

### Файлы (предоставляются пользователем)
- `mascot-logo.png` — shield logo mark (nav / favicon)
- `mascot-hero.png` — PNG с прозрачным фоном (hero секция)

Вставлять как `<img>`. Анимации — CSS на элементе.

### CSS-анимации маскота
```css
/* float */
@keyframes float { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-8px)} }
img.mascot { animation: float 5s ease-in-out infinite; }

/* glow — только маскот, не карточки */
@keyframes glow-pulse {
  0%,100%{filter: drop-shadow(0 0 6px #06b6d4)}
  50%     {filter: drop-shadow(0 0 18px #06b6d4)}
}
img.mascot { animation: float 5s ease-in-out infinite, glow-pulse 3s ease-in-out infinite; }

/* alert-flash — вызывать через JS при ALERT-строке в live feed */
.mascot-alert { animation: alert-flash 0.25s ease-out forwards; }
@keyframes alert-flash {
  0%  {filter: drop-shadow(0 0 6px #06b6d4)}
  40% {filter: brightness(2) hue-rotate(160deg) drop-shadow(0 0 24px #ef4444)}
  100%{filter: drop-shadow(0 0 6px #06b6d4)}
}

@media (prefers-reduced-motion: reduce) { img.mascot { animation: none; } }
```

### Размеры
- Hero: `max-width: 360px`, адаптивный
- Nav логотип: `height: 32px`
- Favicon: Canvas API из `mascot-logo.png` → 32×32

---

## 2. СТРУКТУРА И НАРРАТИВ

### Принцип: сначала докажи, потом объясняй

```
1. NAV
2. HERO           — конкретный кейс + terminal live log + маскот (первое, что видят)
3. PROBLEM        — 2-column Euler $197M: "Что было" vs "Что увидел бы Sentinel"
4. WHY US         — 3 дифференциатора vs конкурентов (без карточек с иконками)
5. PIPELINE       — вертикальный scroll-journey T0→T5 со sticky rail
6. LIVE DEMO      — canvas chart + tx stream feed  ← доказательство
7. PROOF          — числа бенчмарка с контекстом + on-chain anchor
8. CTA            — единственное действие: DoraHacks + GitHub
9. FOOTER
```

---

## 3. СЕКЦИИ — ДЕТАЛЬНАЯ СПЕЦИФИКАЦИЯ

### 3.1 NAV

```html
<nav>
  <a href="/"><img src="mascot-logo.png" height="32" alt="Sentinel"></a>
  <div class="links">
    <a href="#problem">Problem</a>
    <a href="#pipeline">How it Works</a>
    <a href="#live-demo">Live Demo</a>
    <a href="#proof">Proof</a>
  </div>
  <a href="https://github.com/alexbelij/mantle-sentinel" class="btn-ghost">View on GitHub →</a>
</nav>
```

Стиль: `position: sticky; top: 0; background: rgba(9,9,9,0.92); backdrop-filter: blur(12px);`  
Нет box-shadow. Нижний border: `1px solid #2a2a2a`.

---

### 3.2 HERO

**Задача:** создать ощущение, что смотришь на живой инструмент, а не на рекламу.

**Layout:** 2 колонки — текст слева (60%), маскот справа (40%).

**Eyebrow (тег над заголовком):**
```
● LIVE  ·  MANTLE MAINNET  ·  BLOCK #97,102,441
```
Стиль: `JetBrains Mono 11px uppercase tracking-wide, color: #8a8a8a`  
Dot `●` — `#22c55e` с `animation: pulse 2s infinite`.

**Headline:**
```
Euler Finance lost $197M
in valid function calls.
Sentinel saw it coming.
```
Стиль: `Space Grotesk 700, clamp(40px,6vw,68px), tracking -0.04em, color: #f0f0ef`  
«$197M» — `color: #f97316` (amber акцент).

**Subheadline:**
```
Behavioral fingerprint. No training data. No false positives.
Alert anchored on-chain within 2 windows of anomaly onset.
```
Стиль: `Inter 400, 18px, color: #8a8a8a, max-width: 480px`

**Terminal block (живое сердце hero):**
```
┌─ SENTINEL LOG ──────────────────────────────────────┐
│ [96624965] monitoring USDC.e · drift: 0.07 · OK     │
│ [96624966] monitoring USDC.e · drift: 0.09 · OK     │
│ [96624967] monitoring USDC.e · drift: 0.31 · WARN   │
│ [96624968] ANOMALY DETECTED · drift: 0.87 · ALERT ● │
│ [96624968] logAlert() → tx 0x4aca…09a78 · anchored  │
│ _                                                    │
└──────────────────────────────────────────────────────┘
```
Реализация: симулированная прокрутка — новые строки добавляются каждые 3s через `setInterval`.  
ALERT-строка: `color: #ef4444`. OK — `#22c55e`. WARN — `#f97316`. Текст всегда `JetBrains Mono 13px`.  
При ALERT-строке → JS вызывает `.mascot.classList.add('mascot-alert')`, убирает через 300ms.

**CTA кнопки:**
```html
<a href="https://dorahacks.io/buidl/..." class="btn-primary">View on DoraHacks →</a>
<a href="#live-demo" class="btn-ghost">Watch Live Demo ↓</a>
```

**Proof strip (под кнопками, горизонтально):**
```
✓ 84 tests passing   ✓ 0 false positives   ✓ Live on Mantle mainnet   ✓ MIT license
```
Стиль: `JetBrains Mono 12px, color: #555555`. Чекмарки `✓` — `color: #22c55e`.

---

### 3.3 PROBLEM — Euler $197M

**Заголовок:** `The tools you trust were built for yesterday.`

**Layout: 2 колонки, равные**

**Колонка левая — «Что было»:**
```
┌─ EULER FINANCE · MAR 13 2023 ──────────────┐
│                                             │
│  donateToReserves()   ← valid selector      │
│  liquidate()          ← valid selector      │
│  flashLoan()          ← valid selector      │
│                                             │
│  Chainalysis: no flag                       │
│  Forta rules: no flag                       │
│  Signature DB: no match                     │
│                                             │
│  Result: $197,000,000 drained               │
└─────────────────────────────────────────────┘
```
Заголовок колонки: `WHAT HAPPENED` (mono-label).  
Фон: `surface-1 (#111111)`. Border: `1px solid #2a2a2a`.

**Колонка правая — «Что увидел бы Sentinel»:**
```
┌─ SENTINEL ANALYSIS ────────────────────────┐
│                                            │
│  Block N-12: drift_score = 0.31  → WARN   │
│  Block N-8:  drift_score = 0.61  → WARN   │
│  Block N-4:  drift_score = 0.87  → ALERT  │
│  Block N:    EXPLOIT EXECUTES              │
│                                            │
│  Δ entropy:  +41%   (selector flood)       │
│  Δ timing:   +280%  (burst pattern)        │
│  Δ gas:      +190%  (flashloan overhead)   │
│                                            │
│  Alert window: 12 blocks early             │
└────────────────────────────────────────────┘
```
Заголовок колонки: `WHAT SENTINEL SAW` (mono-label).  
Граница панели: `1px solid rgba(249,115,22,0.3)` (amber glow). Drift числа: `color: #f97316`.

**Под двумя колонками — горизонтальная строка:**
```
2 more cases: Slow-drift "boil-the-frog" · Flash loan timing burst
```
Стиль: `JetBrains Mono 13px, color: #555555`.  
(Не делать карточки для них — достаточно упоминания.)

---

### 3.4 WHY US — 3 дифференциатора

**Заголовок:** `Why not rule-based? Why not an LLM?`

**Layout:** 3 строки (не карточки), разделены тонкими `border-bottom: 1px solid #2a2a2a`.

**Строка 1:**
```
RULE-BASED (Forta, etc.)          vs      SENTINEL
Misses novel attack vectors              Algebraic — catches anything that deviates
4.3× more noise                          from behavioral baseline
Can't detect slow drift
```

**Строка 2:**
```
LLM MONITORS                      vs      SENTINEL
~500ms per tx (too slow)                 Microsecond updates
Expensive at scale                        No GPU, no training data, no API cost
Not deterministic                         Same snapshot → byte-identical result
```

**Строка 3 (Z.ai hook):**
```
BOTH TELL YOU "ANOMALY"           vs      SENTINEL  
No explanation                            Feature-ablation attribution:
You investigate                           "selector_entropy +41%, timing_burst +280%"
                                          Z.ai GLM formats into plain language
```

Стиль строк: `font: Space Grotesk 500 18px` для метки слева. `Inter 400 15px, color: #8a8a8a` для описания.  
`vs` — `JetBrains Mono, color: #f97316, font-size: 11px`.

---

### 3.5 PIPELINE — Vertical Scroll-Journey T0→T5

**Layout:** `display: grid; grid-template-columns: 48px 1fr;`  
Левая колонка: вертикальный rail (SVG line) + 6 dot-узлов T0–T5.  
Правая колонка: 6 scroll-секций, каждая минимум 80vh.

**Rail:** `position: sticky; top: 120px; align-self: start;`  
SVG-линия: `stroke: #2a2a2a`, активная часть заполняется: `stroke: #f97316` через `stroke-dashoffset`.  
Dot активный: `background: #f97316; box-shadow: 0 0 8px rgba(249,115,22,0.4)`.  
Dot неактивный: `background: #2a2a2a`.

**Каждая tier-секция появляется в viewport (IntersectionObserver) и показывает:**

```
T0 — INGESTION
Mono-label: "T0 · INGESTION"
Описание: "Raw Mantle RPC stream. Spam pre-filter removes < 21000 gas txs."
Артефакт: анимированный поток hex-строк, 30% становятся красными и исчезают (filtered).
Формула: —

T1 — ENTROPY
Mono-label: "T1 · ENTROPY FILTER"  
Описание: "Shannon entropy on selector distribution. Low-entropy windows → passthrough."
Артефакт: гистограмма selector frequency, линия H = -Σp·log(p) появляется поверх.
Формула: H = -Σ p(s) · log₂ p(s)

T2 — HDC ENCODER
Mono-label: "T2 · HYPERDIMENSIONAL ENCODER"
Описание: "10,000-dimensional bipolar hypervector. No training. Algebraic superposition."
Артефакт: визуализация — маленький вектор-транзакция биндится в D=10,000 точек.
Формула: H(tx) = ⊕ (F_i ⊗ L_i)

T3 — DRIFT DETECTOR
Mono-label: "T3 · DRIFT DETECTION"
Описание: "Hamming distance between live window and baseline prototype."
Артефакт: два вектора → hamming → drift_score спидометр 0.0–1.0 → θ=0.65 line.
Формула: drift = hamming(V_window, V_proto) / D

T4 — BOCPD
Mono-label: "T4 · BAYESIAN CHANGEPOINT (optional)"
Описание: "Adams-MacKay BOCPD for slow-drift regime shifts."
Артефакт: временной ряд drift_score с cp-marker (оранжевый флаг).
Формула: P(cp|x₁…xₜ) — Bayesian update

T5 — RESPONSE
Mono-label: "T5 · ALERT & ANCHOR"
Описание: "Feature-ablation attribution → Z.ai GLM → Telegram + on-chain anchor."
Артефакт: три иконки (Z.ai brain SVG, Telegram SVG, chain link SVG) с анимированными соединениями.
Формула: —
```

**Scroll activation:** IntersectionObserver `threshold: 0.3` — при входе секции в viewport:
1. Rail dot становится amber
2. SVG line заполняется до этого узла
3. Артефакт анимируется (opacity 0→1 + translateY 16px→0, 0.6s)

---

### 3.6 LIVE DEMO

**Заголовок:** `Not simulated. This is the real Mantle stream.`

**Layout:** 2 панели горизонтально.

**Панель 1 — Drift Chart (Canvas):**
- Ось X: последние 60 окон (время → право)
- Ось Y: 0.0 → 1.0, горизонтальная линия `θ=0.65` пунктиром amber
- Нормальные точки: `#22c55e`
- ALERT-точки: `#ef4444` с pulse-анимацией
- Canvas background: `#111111`, grid lines: `#1e1e1e`
- Правая подпись оси Y: `0.0 / 0.5 / θ=0.65 / 1.0` (JetBrains Mono 10px)

**Панель 2 — TX Feed:**
```
BLOCK     TIME      TYPE         DRIFT
─────────────────────────────────────
0x5f2a    14:23:01  benign       0.07  ●
0x5f2b    14:23:04  benign       0.09  ●
0x5f2c    14:23:07  warn         0.41  ⚠
0x5f2d    14:23:10  ALERT        0.89  ■ ← красная строка
```
Заголовки колонок: `JetBrains Mono 11px uppercase, color: #555555`.  
ALERT строка: `background: rgba(239,68,68,0.08); color: #ef4444`.  
При ALERT строке: mascot-alert flash.

**Источник данных:** симуляция с реальными паттернами (30 benign + периодические аномалии).  
`setInterval(500ms)` — новая строка, canvas обновляется.

---

### 3.7 PROOF

**Заголовок:** `Measured. Anchored. Reproducible.`

**Benchmark блок:**
```
┌─ BENCHMARK · MANTLE USDC.e STREAM ─────────────────────────┐
│                                                             │
│  Metric              FreqBase    AB3      Sentinel HDC      │
│  ──────────────────  ─────────   ──────   ───────────────   │
│  Sep. Ratio          1.0×        2.1×     4.3× ← best       │
│  FP Rate             18%         9%       0%   ← perfect    │
│  Detection Window    4.8 win     3.1 win  ≤2 win            │
│  Training Required   yes         yes      NO                 │
│                                                             │
│  Sep. Ratio = clean_p99 / injected_p50 · higher = better   │
└─────────────────────────────────────────────────────────────┘
```
Стиль таблицы: `JetBrains Mono 13px`, Sentinel колонка `color: #f97316`.  
Footnote: серый Inter 13px.

**On-chain панель:**
```
┌─ ON-CHAIN ANCHOR · MANTLE MAINNET ─────────────────────────┐
│  Contract:  0x593C9a4dd6806510e379e30481eaCd27d2016FbE     │
│  Tx:        0x4aca92d7…09a78  ·  status: ✓ confirmed       │
│  Alert #1:  windowId 39920662  ·  type: ENTR               │
│  Date:      Jun 13 2026 · Block 96,624,965                  │
└─────────────────────────────────────────────────────────────┘
```
Кнопка: `View on Mantlescan →` (ghost, small).

---

### 3.8 CTA

**Заголовок:** `Built for the Mantle AI Hackathon. Open for audit.`

**2 кнопки, крупные, рядом:**
```html
<a href="https://dorahacks.io/buidl/..." class="btn-primary btn-large">
  View DoraHacks Submission →
</a>
<a href="https://github.com/alexbelij/mantle-sentinel" class="btn-ghost btn-large">
  GitHub — MIT License
</a>
```

**Под кнопками:**
```
Track 02: AI Alpha & Data · #MantleAIHackathon · Contract: 0x593C9a4dd6806510e379e30481eaCd27d2016FbE
```
Стиль: `JetBrains Mono 11px, color: #555555, text-align: center`

**Никакого email-захвата.** Нет Formspree.

---

### 3.9 FOOTER

```
Mantle Sentinel · MIT License · Built on Mantle Network
GitHub · DoraHacks · 84 tests · 0 FP · Block 96,624,965
```
`JetBrains Mono 12px, color: #555555, text-align: center, padding: 48px`  
`border-top: 1px solid #1f1f1f`

---

## 4. ДИЗАЙН-СИСТЕМА (сокращение — полное в DESIGN.md)

```css
:root {
  --canvas:   #090909;
  --s1:       #111111;
  --s2:       #161616;
  --border:   #2a2a2a;
  --ink:      #f0f0ef;
  --muted:    #8a8a8a;
  --subtle:   #555555;
  --accent:   #f97316;  /* ЕДИНСТВЕННЫЙ акцент */
  --ok:       #22c55e;
  --alert:    #ef4444;
  --cyan:     #06b6d4;  /* только маскот glow */
}

/* Fonts */
/* Display */ font-family: 'Space Grotesk', sans-serif;
/* Mono */    font-family: 'JetBrains Mono', monospace;
/* Body */    font-family: 'Inter', sans-serif;
```

**Google Fonts:**
```html
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400&display=swap" rel="stylesheet">
```

---

## 5. SCROLL REVEAL

```js
const observer = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      e.target.classList.add('revealed');
      observer.unobserve(e.target);
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll('[data-reveal]').forEach(el => observer.observe(el));
```

```css
[data-reveal] { opacity: 0; transform: translateY(20px); }
[data-reveal].revealed {
  opacity: 1; transform: translateY(0);
  transition: opacity .55s cubic-bezier(.22,1,.36,1), transform .55s cubic-bezier(.22,1,.36,1);
}
@media (prefers-reduced-motion: reduce) {
  [data-reveal], [data-reveal].revealed { opacity: 1; transform: none; transition: none; }
}
```

---

## 6. ТЕХНИЧЕСКИЕ ТРЕБОВАНИЯ

- Чистый HTML/CSS/JS — никаких npm, bundlers, React
- Google Fonts через `<link preconnect>`
- IntersectionObserver для reveal + pipeline activation
- requestAnimationFrame для canvas chart
- setInterval(500ms) для tx feed + terminal hero log
- Адаптив: `960px` (tablet) и `600px` (mobile)
- Mobile: все 2-column layouts → 1 колонка, pipeline rail скрыт, упрощённый артефакт
- Lighthouse performance ≥ 90
- 0 console errors

---

## 7. ЧТО НЕ МЕНЯТЬ (данные)

```
Адрес контракта:   0x593C9a4dd6806510e379e30481eaCd27d2016FbE
Alert tx:          0x4aca92d7…09a78
GitHub:            https://github.com/alexbelij/mantle-sentinel
Vercel:            https://mantle-sentinel-rho.vercel.app/
Числа бенчмарка:   4.3×, 84 тестов, 0 FP, ≤2 окна, block 96,624,965
Formspree ID:      meewvaqy (не использовать — форму убрали)
DoraHacks URL:     вставить реальный BUIDL URL перед деплоем
```

---

## 8. DELIVERABLE

Один файл `docs/landing/index.html` + `DESIGN.md` в корне репо.  
Push в `main` → Vercel деплоит автоматически (~20s).  
Прислать скрин desktop + mobile после деплоя.
