# TZ_FIX_BLOG_IMAGES — Исправить битые ссылки на картинки в блог-посте

> Для Dev Viktor. Архитектура frozen, НЕ менять текст статьи — ТОЛЬКО ссылки на картинки.
> Файл: `docs/blog/BLOG_POST.md`

---

## ПРОБЛЕМА

В `docs/blog/BLOG_POST.md` четыре заглушки `IMAGE_PLACEHOLDER_1..4` вместо реальных картинок:

```
![Hero — Dashboard showing live health scores](IMAGE_PLACEHOLDER_1)
![Pipeline diagram — T0 through T5 flow](IMAGE_PLACEHOLDER_2)
![Health scores table for top 5 Mantle contracts](IMAGE_PLACEHOLDER_3)
![On-chain alert transaction on Mantlescan](IMAGE_PLACEHOLDER_4)
```

## ИМЕЮЩИЕСЯ АССЕТЫ

```
docs/images/
├── dashboard.png          ← 59 KB, скриншот дашборда
├── dashboard-mobile.png   ← 93 KB
├── landing-hero.png       ← 151 KB
└── self-attack-output.png ← 78 KB, вывод scan/self-attack
```

## МАППИНГ

| Placeholder          | Описание                     | Решение                                        |
|----------------------|------------------------------|-------------------------------------------------|
| IMAGE_PLACEHOLDER_1  | Hero — dashboard             | `../images/dashboard.png` (уже есть)            |
| IMAGE_PLACEHOLDER_2  | Pipeline T0→T5               | **СОЗДАТЬ** `docs/images/pipeline-diagram.png`   |
| IMAGE_PLACEHOLDER_3  | Health scores таблица        | `../images/self-attack-output.png` (уже есть)   |
| IMAGE_PLACEHOLDER_4  | Mantlescan TX скриншот       | **СОЗДАТЬ** `docs/images/mantlescan-alert-tx.png`|

---

## ITER 1 — Заменить заглушки + создать pipeline-диаграмму

### Задачи

1. **Заменить IMAGE_PLACEHOLDER_1 и IMAGE_PLACEHOLDER_3** на существующие картинки:

   ```
   IMAGE_PLACEHOLDER_1  →  ../images/dashboard.png
   IMAGE_PLACEHOLDER_3  →  ../images/self-attack-output.png
   ```

2. **Создать `docs/images/pipeline-diagram.png`** — диаграмма пайплайна T0→T5:

   - Использовать Python (matplotlib или Pillow) для генерации, **НЕ SVG** (Medium не поддерживает SVG)
   - Layout: горизонтальный поток, слева направо
   - 6 блоков:
     ```
     [T0 Entropy Filter] → [T1 HDC Encoder] → [T2 Drift Signal] → [T3 Detector] → [T4 Attribution] → [T5 Z.ai]
     ```
   - Входная стрелка слева: "Transactions"
   - Выходная стрелка справа: "Alert + Explanation"
   - Стиль: тёмный фон (#0f172a), блоки с бордерами (#3b82f6), белый текст
   - Размер: 1200×400px, чёткий текст
   - Файл: `docs/images/pipeline-diagram.png`

3. **Заменить IMAGE_PLACEHOLDER_2**:

   ```
   IMAGE_PLACEHOLDER_2  →  ../images/pipeline-diagram.png
   ```

4. **Заменить IMAGE_PLACEHOLDER_4** — пока нет скриншота, заменить на styled link:

   Было:
   ```markdown
   ![On-chain alert transaction on Mantlescan](IMAGE_PLACEHOLDER_4)
   ```

   Стало:
   ```markdown
   > 🔗 **On-chain proof:** [View alert transaction on Mantlescan](https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c) — immutable anchor at block 96,680,154.
   ```

### Проверка

```bash
# Ни одного IMAGE_PLACEHOLDER не осталось
grep -c "IMAGE_PLACEHOLDER" docs/blog/BLOG_POST.md
# Ожидаемый результат: 0

# pipeline-diagram.png существует и > 10KB
ls -la docs/images/pipeline-diagram.png

# Все картинки из BLOG_POST.md существуют
grep -oP '\.\./images/[a-z0-9_-]+\.png' docs/blog/BLOG_POST.md | while read f; do
  test -f "docs/blog/$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

### Коммит

```
fix(blog): replace broken IMAGE_PLACEHOLDER links with real assets

- IMAGE_PLACEHOLDER_1 → dashboard.png
- IMAGE_PLACEHOLDER_2 → pipeline-diagram.png (new, generated)
- IMAGE_PLACEHOLDER_3 → self-attack-output.png
- IMAGE_PLACEHOLDER_4 → Mantlescan link (screenshot in ITER 2)
```

### Файлы

```
docs/blog/BLOG_POST.md              — 4 замены плейсхолдеров
docs/images/pipeline-diagram.png    — NEW, T0→T5 диаграмма
```

---

## ITER 2 — Скриншот Mantlescan + гайд для Medium

### Задачи

1. **Создать скриншот Mantlescan** с помощью playwright:

   ```python
   # pip install playwright && playwright install chromium
   from playwright.sync_api import sync_playwright

   url = "https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c"

   with sync_playwright() as p:
       browser = p.chromium.launch()
       page = browser.new_page(viewport={"width": 1280, "height": 900})
       page.goto(url, wait_until="networkidle")
       page.wait_for_timeout(3000)  # дождаться рендера
       # Скриншот верхней части страницы (transaction details)
       page.screenshot(path="docs/images/mantlescan-alert-tx.png", clip={"x": 0, "y": 0, "width": 1280, "height": 800})
       browser.close()
   ```

   - Если playwright не доступен или Mantlescan блочит — оставить Mantlescan link из ITER 1 как есть (fallback)
   - Размер: 1280×800px, обрезать browser chrome

2. **Если скриншот успешен**, заменить Mantlescan link-блок в BLOG_POST.md на картинку:

   Было (из ITER 1):
   ```markdown
   > 🔗 **On-chain proof:** [View alert transaction on Mantlescan](https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c) — immutable anchor at block 96,680,154.
   ```

   Стало:
   ```markdown
   ![On-chain alert transaction on Mantlescan](../images/mantlescan-alert-tx.png)

   *[View transaction on Mantlescan →](https://mantlescan.xyz/tx/0x086cf07ace1ef1623ce43e40dc4a7e0b24f29dd206fdc7142fcd6bc5e79fa91c)*
   ```

3. **Создать `docs/blog/BLOG_IMAGES.md`** — гайд для публикации на Medium:

   ```markdown
   # Blog Images — Medium Upload Guide

   Upload these images in order when publishing on Medium:

   | # | File                                      | Section                | Alt text                                      |
   |---|-------------------------------------------|------------------------|-----------------------------------------------|
   | 1 | `docs/images/dashboard.png`               | After title (hero)     | Dashboard showing live health scores          |
   | 2 | `docs/images/pipeline-diagram.png`        | How It Works section   | Pipeline diagram — T0 through T5 flow         |
   | 3 | `docs/images/self-attack-output.png`      | Results section        | Health scores table for top 5 Mantle contracts|
   | 4 | `docs/images/mantlescan-alert-tx.png`     | On-chain proof section | On-chain alert transaction on Mantlescan      |

   Medium tip: drag images into the editor at the corresponding placeholder positions.
   ```

### Проверка

```bash
# Все картинки из BLOG_POST.md существуют
grep -oP '\.\./images/[a-z0-9_-]+\.png' docs/blog/BLOG_POST.md | sort -u | while read f; do
  full="docs/blog/$f"
  test -f "$full" && echo "OK: $f ($(du -h "$full" | cut -f1))" || echo "MISSING: $f"
done

# Ни одного IMAGE_PLACEHOLDER
grep -c "IMAGE_PLACEHOLDER" docs/blog/BLOG_POST.md
# 0

# BLOG_IMAGES.md существует
test -f docs/blog/BLOG_IMAGES.md && echo "OK" || echo "MISSING"
```

### Коммит

```
feat(blog): add Mantlescan screenshot and Medium upload guide

- mantlescan-alert-tx.png screenshot (or kept as link fallback)
- BLOG_IMAGES.md — image upload guide for Medium publishing
```

### Файлы

```
docs/images/mantlescan-alert-tx.png  — NEW (если скриншот удался)
docs/blog/BLOG_POST.md              — обновлён PLACEHOLDER_4 (если скриншот удался)
docs/blog/BLOG_IMAGES.md            — NEW, гайд для Medium
```

---

## ПРАВИЛА

- **НЕ менять текст статьи** — только ссылки на картинки
- **НЕ менять существующие картинки** в `docs/images/`
- Формат картинок: **PNG** (Medium не поддерживает SVG)
- Относительные пути от `docs/blog/`: `../images/filename.png`
- Если playwright недоступен → ITER 2 task 1-2 skip, оставить fallback link
