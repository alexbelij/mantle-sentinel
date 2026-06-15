# TZ_PITCH_V2 — Исправление слайдов (Demo Day)

> Для Dev Viktor. Слайды из первой итерации (4821a85) — неприемлемы.
> Нужно полностью переделать `docs/pitch/slides.pdf`.

---

## КРИТИЧЕСКИЕ ПРОБЛЕМЫ

1. **Маскот** — на слайде 1 какой-то муравей вместо нашего кибер-богомола.
2. **Emojis** — везде стандартные emoji. В презентации для хакатона — недопустимо.
3. **Мало инфографики** — слайды выглядят как текстовые карточки, нет визуальной подачи данных.
4. **`[Name]`** — в `speech.md` вместо реального имени стоит плейсхолдер.

---

## ЧТО ИСПРАВИТЬ

### 0. Ассеты

Маскот и лого — скачать с нашего лендинга (НЕ генерировать новые):
```
https://mntsentinel.xyz/assets/mascot-hero.png   — полный маскот (кибер-богомол, синий/cyan, скрещённые руки)
https://mntsentinel.xyz/assets/mascot-logo.png    — логотип (щит с силуэтом)
https://mntsentinel.xyz/assets/favicon.png        — иконка
```

Скачать `curl -o` перед генерацией слайдов и встроить в HTML.

### 1. Слайд 1 (Title)

- Крупный маскот `mascot-hero.png` справа
- Логотип `mascot-logo.png` + текст "MANTLE SENTINEL" слева
- Подзаголовок: "Behavioral Anomaly Detection for Smart Contracts"
- Внизу: "Hackathon Track: AI Alpha & Data"
- **НЕТ emoji**

### 2. Слайд 2 (Problem)

- "$3.4B" — крупная цифра, orange (#f97316), доминирует на слайде
- 3 проблемы — как карточки/блоки с SVG-иконками (не emoji):
  - Замок с крестом → "Signature-based tools miss novel attacks"
  - Часы/таймер → "LLM monitors are slow and non-deterministic"
  - Пустой график → "Zero historical data to train on"
- Иконки рисовать inline SVG в HTML (простые, 1-цветные, white или amber)

### 3. Слайд 3 (Solution)

- Визуализация: "Normal Pattern" → "Drifted Pattern" (два блока, стрелка между ними)
- Можно схематично: grid/heatmap нормального поведения vs аномального
- Ключевые числа внизу как badges: `10,000 dim` · `0 training` · `0 GPU`

### 4. Слайд 4 (Pipeline) — КЛЮЧЕВОЙ СЛАЙД

- Горизонтальная диаграмма пайплайна со стрелками:
  ```
  TX Stream → Entropy Filter → HDC Encoder → Drift Signal → Detector → Attribution → Z.ai → Alert
  ```
- Каждый шаг — блок с иконкой и 1 строкой описания
- Под пайплайном: плашка "LLM is NEVER in the detection loop" (amber border)
- Это ИНФОГРАФИКА, не список текста

### 5. Слайд 5 (Z.ai)

- Визуал: structured finding (блок слева) → стрелка → Z.ai → plain English brief (блок справа)
- Показать пример трансформации (код-подобный → человеческий текст)
- Плашка: "Without API key → deterministic fallback"

### 6. Слайд 6 (Results) — ДАННЫЕ

- Health scores как 5 горизонтальных progress bars (цветных):
  ```
  USDC.e  ████████░░ 83  ✅
  Lendle  ████████░░ 81  ✅
  WMNT    ███████░░░ 74  ⚠️
  USDT    ███████░░░ 70  ⚠️
  mETH    ██████░░░░ 68  ⚠️
  ```
- ✅ и ⚠️ — рисовать SVG-кружки (зелёный/жёлтый), НЕ emoji
- Метрики внизу как 3 больших числа: `4.3×` / `0 FP` / `129 tests`
- По возможности — мини-скриншот дашборда или его стилизация

### 7. Слайд 7 (On-chain Proof)

- Стилизованный блок "транзакции" (имитация Mantlescan)
- Адрес контракта крупно, моноширинным шрифтом
- Плашка: "Immutable · Verifiable · Mantle Mainnet"

### 8. Слайд 8 (Developer Experience)

- Стилизованный терминал (тёмный фон, зелёный/amber текст):
  ```
  $ python -m sentinel scan 0x09bc... --min-health 60
  ```
- Три блока: CI/CD badge, Pre-commit hook, Telegram alert
- Каждый блок — иконка + 1 строка

### 9. Слайд 9 (Roadmap)

- 3 колонки с линией прогресса:
  - NOW (зелёная точка) → NEXT (amber) → FUTURE (серая)
  - Пункты под каждой колонкой
- Визуально похоже на timeline, не на список

### 10. Слайд 10 (CTA)

- Маскот `mascot-hero.png` крупно по центру
- "MANTLE SENTINEL" + "Detect Before They Hit"
- Ссылки — как аккуратные плашки с иконками (не emoji!)
- QR-код на GitHub repo (сгенерировать `qrcode` python lib)

---

## СТИЛЬ (обязательно!)

```css
Background:  #0a0a0a (void)
Panel:       #111111
Orange:      #f97316 (accent, CTA, highlights)
Cyan:        #22d3ee (только для mascot glow)
Text:        #fafafa (заголовки), #d9d9d9 (основной), #9a9a9a (muted)
Border:      #1f1f1f
Font title:  Space Grotesk 700
Font body:   Inter 400/500
Font code:   JetBrains Mono
```

Грузить шрифты через Google Fonts в HTML.

---

## SPEECH.MD — исправить

Заменить `[Name]` → `Aleksandr` в строке:
```
Hi everyone. I'm [Name], and this is Mantle Sentinel
```
→
```
Hi everyone. I'm Aleksandr, and this is Mantle Sentinel
```

---

## ФОРМАТ ВЫХОДА

```
docs/pitch/slides.pdf   — 10 слайдов, 16:9, пересозданные
docs/pitch/speech.md     — исправлено [Name] → Aleksandr
docs/pitch/qa.md         — без изменений
```

1 коммит. Проверка: визуально открыть PDF, убедиться что маскот на месте,
нет emoji, есть инфографика, шрифты и цвета соответствуют стилю.
