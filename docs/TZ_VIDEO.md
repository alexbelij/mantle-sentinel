# TZ — Demo Video (≤3 min)

**Приоритет:** P0 • **Дедлайн:** Jun 15 23:59 UTC+3

---

## Общие требования

- **Длительность:** 150–180 секунд (≤3 мин)
- **Разрешение:** 1920×1080, 30 fps, H.264
- **Аудио:** captions обязательны. Голос/TTS — опционально (на твоё усмотрение)
- **Стиль:** строго в стиле сайта `mntsentinel.xyz` (CSS vars ниже). НЕ дефолтный Remotion/generic
- **Логотип:** в правом верхнем углу на каждом кадре — `mascot-logo.png` (URL: `https://mntsentinel.xyz/assets/mascot-logo.png`, ~26×30px scale up to 48×56 для видео)
- **Выходной файл:** `docs/video/demo.mp4` + commit в main
- **Заливка:** YouTube (personal account). Ссылку вернуть в отчёте

---

## ITER 0 — Превью-кадр (1 секунда)

**Сделать ПЕРВЫМ. Отправить мне на проверку до начала полного рендера.**

Один статичный кадр (1920×1080), 1 секунда:
- Тёмный фон `#090909`
- По центру: логотип `mascot-logo.png` (крупно, ~120px)
- Под ним: `Mantle Sentinel` шрифтом Space Grotesk 700, цвет `#fafafa`
- Ещё ниже: `Behavioral DNA for DeFi Security` шрифтом Inter 400, цвет `#9a9a9a`
- Внизу: мелкая полоска `#f97316` (amber accent)
- Рендер → отправить screenshot .png для апрува

**Не продолжать ITER 1+ пока не получишь "ОК" от Lead.**

---

## Дизайн-токены (из сайта mntsentinel.xyz)

```css
/* Цвета */
--void:    #090909;     /* фон */
--panel:   #111111;     /* карточки */
--panel-2: #0d0d0d;
--line:    #1f1f1f;     /* границы */
--line-2:  #2a2a2a;
--amber:   #f97316;     /* основной акцент */
--amber-bright: #fb923c;
--amber-dim:    #c2570f;
--cyan:    #22d3ee;     /* mascot glow only */
--ink:     #fafafa;     /* заголовки */
--prose:   #d9d9d9;     /* текст */
--muted:   #9a9a9a;     /* вторичный текст */
--faint:   #6a6a6a;     /* третичный */
--ok:      #5b8c63;     /* зелёный */
--warn:    #c79a3a;     /* жёлтый */

/* Шрифты (Google Fonts CDN) */
--display: "Space Grotesk", system-ui, sans-serif;  /* заголовки */
--sans:    "Inter", system-ui, sans-serif;           /* текст */
--mono:    "JetBrains Mono", monospace;              /* код/цифры */

/* Скругления */
--r:    6px;
--r-sm: 4px;
```

**Google Fonts URL:**
```
https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap
```

---

## Сценарий (AIDA структура)

### SEG-0: HOOK (0–8 сек)

**Визуал:** тёмный фон `--void`, крупный текст появляется с печатающим эффектом:

```
$3.6B lost to DeFi exploits in 2024.
Zero were caught by signature scanners.
```

Шрифт: Space Grotesk 700, `--ink`, размер ~56px.
Caption внизу: тот же текст.

---

### SEG-1: PROBLEM (8–25 сек)

**Визуал:** три карточки (панели `--panel`, border `--line`) появляются одна за другой слева направо:

| Карточка | Иконка | Текст |
|----------|--------|-------|
| 1 | 🔍 | **Signature scanners** — only catch known patterns |
| 2 | 🤖 | **LLM monitors** — too slow, too expensive per-tx |
| 3 | ❓ | **Novel attacks** — behave differently, not identically |

Caption: `Current tools miss novel attacks. They look for known signatures — exploits don't repeat.`

Иконки — стилизованные SVG или emoji в amber.

---

### SEG-2: SOLUTION (25–48 сек)

**Визуал:** Pipeline diagram (анимированный):

```
Mantle RPC → [Entropy Filter] → [HDC Encoder] → [Drift Signal] → [BOCPD Detector] → Alert
                                   10,000-dim          ↓
                                  "Behavioral DNA"   Z.ai explains
```

Каждый блок подсвечивается последовательно amber, пока caption объясняет.

Caption (3 фразы, по ~7 сек):
1. `Every contract has a behavioral fingerprint — selector distribution, gas, timing, calldata.`
2. `Sentinel compresses it into a 10,000-dimensional hypervector. No training. No GPU.`
3. `When Hamming distance spikes — something changed. Alert fires in microseconds.`

---

### SEG-3: LIVE DEMO — Терминал (48–95 сек)

**Это ключевой сегмент. Два варианта:**

#### Вариант A: Live run (если env vars доступны)

1. **Dry-run сначала** — проверить что всё работает:
```bash
cd /path/to/mantle-sentinel
python -m bench.self_attack --dry-run
```
Убедиться что `=== Self-Attack Demo (dry-run) ===` выводит алерты.

2. **Live run** — записать терминал (asciinema или Playwright terminal):
```bash
python -m bench.self_attack
```

3. **Ожидаемый вывод:**
```
=== Self-Attack Demo (LIVE) ===
Victim:  0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64  (chainId 5003)
Signer:  0x...
Balance: 0.xxx MNT

[1/4] Sending 30 benign incrementBy() warm-up txs...
      mined 30 warm-up txs (blocks XXXXX..XXXXX)
[2/4] Building Sentinel pipeline on warm-up traffic...
[3/4] Sending 8 high-entropy incrementBy() attack txs...
      🚨 entropy_anomaly @ block XXXXX (drift 1.0, branch entropy) tx 0x...
      🚨 entropy_anomaly @ block XXXXX (drift 1.0, branch entropy) tx 0x...
      ... (8 alerts total)
[4/4] Anchoring first alert on Mantle mainnet SentinelAlertRegistry...
      ✅ anchored: 0x... (status 1, registry count now N)
      🔗 https://mantlescan.xyz/tx/0x...
```

**Env vars нужны:**
```
MANTLE_PRIVATE_KEY=<из .env>
ZAI_API_KEY=<из .env>
```

**Газ:** ~0.01 MNT на один logAlert() tx.

**Если live run не работает → Вариант B.**

#### Вариант B: Pre-recorded output (fallback)

Показать animated typing в стилизованном терминале (`--panel` фон, `--mono` шрифт) с этим текстом:

```
$ python -m bench.self_attack

=== Self-Attack Demo (LIVE) ===
Victim:  0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64  (chainId 5003)
Signer:  0x7438...a8C2
Balance: 0.89 MNT

[1/4] Sending 30 benign incrementBy() warm-up txs...
      mined 30 warm-up txs (blocks 96680100..96680129)

[2/4] Building Sentinel pipeline on warm-up traffic...

[3/4] Sending 8 high-entropy incrementBy() attack txs...
      🚨 entropy_anomaly @ block 96680131 (drift 1.000, branch entropy)
      🚨 entropy_anomaly @ block 96680132 (drift 1.000, branch entropy)
      🚨 entropy_anomaly @ block 96680133 (drift 1.000, branch entropy)
      🚨 entropy_anomaly @ block 96680134 (drift 1.000, branch entropy)
      🚨 entropy_anomaly @ block 96680135 (drift 1.000, branch entropy)
      🚨 entropy_anomaly @ block 96680136 (drift 1.000, branch entropy)
      🚨 entropy_anomaly @ block 96680137 (drift 1.000, branch entropy)
      🚨 entropy_anomaly @ block 96680138 (drift 1.000, branch entropy)

[4/4] Anchoring first alert on Mantle mainnet SentinelAlertRegistry...
      ✅ anchored: 0x4aca92d7...d09a78 (status 1, registry count now 2)
      🔗 https://mantlescan.xyz/tx/0x4aca92d7...d09a78
```

Визуал: фон `--panel` (#111111), текст `--prose` (#d9d9d9), алерты `🚨` строки в `--amber` (#f97316), ✅ в `--ok` (#5b8c63).

Caption последовательно:
- (48-55s) `30 normal transactions — building the behavioral baseline`
- (55-70s) `8 attack transactions injected — high-entropy calldata`
- (70-80s) `All 8 detected instantly as entropy anomalies`
- (80-95s) `First alert anchored on-chain — immutable, verifiable`

---

### SEG-4: DASHBOARD (95–115 сек)

**Визуал:** скриншот `mntsentinel.xyz/dashboard/` (Playwright capture, viewport 1280×800, wait 5s для загрузки данных).

Если есть новый алерт от SEG-3 live run — покажет обновлённый count.
Если pre-recorded — показать существующий dashboard с 1+ алертом.

Можно добавить subtle zoom анимацию на drift gauge и alert row.

Caption:
- `Live dashboard polls the registry contract every 10 seconds`
- `Every alert is on-chain — verifiable on Mantlescan`

---

### SEG-5: PROOF — Числа (115–135 сек)

**Визуал:** 4 крупных числа появляются с count-up анимацией:

```
4.3×              0              ≤2 windows         127
separation     false positives   detection delay    tests passing
```

Числа: `--mono` шрифт, `--amber` цвет, размер ~72px.
Подписи: `--sans`, `--muted`, ~18px.

Под ними строка: `Real Mantle USDC.e data — 3,993 transactions`

Caption: `4.3× clean/attack separation. Zero false positives. Detection in ≤100 transactions. 127 tests, fully deterministic.`

---

### SEG-6: Z.AI (135–155 сек)

**Визуал:** стилизованная карточка "Z.ai explains":

```
┌─────────────────────────────────────────────┐
│  🤖 Z.ai Analysis                          │
│                                             │
│  Contract 0x09bc... showed behavioral       │
│  shift: selector distribution changed 61%,  │
│  gas buckets elevated 22%.                  │
│                                             │
│  Consistent with selector flood pattern.    │
│  Recommend: review recent approvals for     │
│  anomalous spender addresses.               │
└─────────────────────────────────────────────┘
```

Если Z.ai API доступен — сделать реальный запрос и использовать реальный ответ.

**Z.ai fallback response** (если API не отвечает):
```
The contract 0x09bc4e0d... exhibited a significant behavioral shift.
Selector entropy deviated 5.4σ from baseline — dominated by approve(address,uint256)
with max-value parameters. Gas profile elevated 22% above median.
Pattern consistent with a pre-exploit approval flood.
Recommended action: review recent unlimited approvals for anomalous spender addresses.
```

Caption: `Sentinel detects. Z.ai explains why — in plain English. The model is never in the detection loop.`

---

### SEG-7: VISION + CTA (155–180 сек)

**Визуал:**

1. (155-168s) Roadmap строки появляются с fade-in:
```
✅ Mantle mainnet — live
🔜 Multi-chain EVM expansion
🔜 SaaS dashboard (multi-tenant)
🔜 Telegram bot for protocol teams
```

2. (168-180s) CTA slide:
- Логотип `mascot-logo.png` крупно
- `Mantle Sentinel` — Space Grotesk 700
- `github.com/alexbelij/mantle-sentinel` — amber ссылка
- `mntsentinel.xyz` — amber ссылка
- `Built for Mantle AI Hackathon — Turing Test Phase II`
- `Track 02: AI Alpha & Data`

Caption: `Open source. Deterministic. On-chain verifiable. Try it yourself.`

---

## Технические указания

### Метод создания

**Вариант 1: Remotion (предпочтительный)**
- React компоненты для каждого сегмента
- Google Fonts через `@remotion/google-fonts` или link import
- `npx remotion render` → mp4
- При ошибках Remotion → переключиться на вариант 2

**Вариант 2: ffmpeg + Playwright (fallback)**
- Playwright: скриншоты dashboard + Mantlescan
- Python + Pillow: генерация кадров для text-слайдов
- ffmpeg: склейка кадров + crossfade transitions + captions

### Скриншоты для видео (Playwright)

Захватить заранее:
1. `https://mntsentinel.xyz` — hero section (1920×1080)
2. `https://mntsentinel.xyz/dashboard/` — полный dashboard (1920×1080, wait 5s)
3. `https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c` — anchor tx (1920×1080)
4. `https://mantlescan.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187` — registry contract (1920×1080)

---

## Казусы и fallback

| Казус | Защита |
|-------|--------|
| RPC timeout при live run | dry-run сначала; fallback на pre-recorded output (Вариант B в SEG-3) |
| Z.ai не отвечает | cached response выше в SEG-6 |
| Dashboard не загрузился | wait 5s + retry 2x; fallback на Playwright screenshot |
| Remotion render fail | ffmpeg fallback |
| Mantlescan страница изменилась | использовать pre-captured screenshot |
| Контракт revert | невозможен — logAlert() не имеет ограничений |

---

## Отчёт после рендера

Закоммитить `docs/VIDEO_RENDER_LOG.md`:

```markdown
# Video Render Log

## Segments
| Seg | Status | Notes |
|-----|--------|-------|
| 0 HOOK | ✅/❌ | ... |
| 1 PROBLEM | ✅/❌ | ... |
| ... | ... | ... |

## Live run
- dry-run: ✅/❌
- live-run: ✅/❌ (or skipped → pre-recorded)
- anchor tx: 0x...
- new alert count: N

## Render
- Tool: Remotion / ffmpeg
- Duration: Xs
- Resolution: 1920×1080
- Codec: H.264
- File size: X MB
- YouTube URL: ...

## Errors
(list any errors and how resolved)
```

---

## Адреса и данные для видео

- **Registry contract (mainnet):** `0x0899E1507CFfefF8620455721F5bd528Bb072187`
- **Victim contract (Sepolia):** `0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64`
- **Existing anchor tx:** `0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c`
- **Landing:** `https://mntsentinel.xyz`
- **Dashboard:** `https://mntsentinel.xyz/dashboard/`
- **GitHub:** `https://github.com/alexbelij/mantle-sentinel`
- **Mantlescan explorer:** `https://mantlescan.xyz`
- **Z.ai endpoint:** `https://api.z.ai/api/paas/v4` (model: `glm-4.5-flash`, max_tokens: 800)

## Идентификация

Помечай себя как `[Developer Viktor]` в отчётах.
