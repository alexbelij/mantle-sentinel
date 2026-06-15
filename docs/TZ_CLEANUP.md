# TZ_CLEANUP — Fix CI + Release v1.0.0 + Repo Cleanup

> Для Dev Viktor. 2 итерации, 2 коммита. Порядок строгий: 1→2.
> Архитектура frozen. Код менять ТОЛЬКО для lint-fix (1 файл, 2 строки).

---

## ITER 1 — Fix CI + GitHub Release v1.0.0

### 1A. Fix ruff UP045 (CI blocker)

CI `check` job fails: `ruff check` → UP045 в `sentinel/client.py`.

Файл `sentinel/client.py`:

```python
# Строка 16 — УДАЛИТЬ целиком:
from typing import Optional

# Строка 43 — заменить:
# Было:
z_ai_brief: Optional[str] = None
# Стало:
z_ai_brief: str | None = None
```

`from __future__ import annotations` (строка 12) уже есть — `str | None` работает.

### 1B. Добавить ссылки на блог и X thread в README.md

Строка 13 — добавить 2 ссылки в конец:

Было:
```markdown
[Live Demo](https://mntsentinel.xyz) · [Dashboard](https://mntsentinel.xyz/dashboard/) · [Contract on Mantlescan](https://mantlescan.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187)
```

Стало:
```markdown
[Live Demo](https://mntsentinel.xyz) · [Dashboard](https://mntsentinel.xyz/dashboard/) · [Contract on Mantlescan](https://mantlescan.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187) · [Blog](https://alexbelij.medium.com/how-we-detect-smart-contract-exploits-without-training-data-using-hyperdimensional-computing-on-e94d5d83e6b8) · [X Thread](https://x.com/alexbelij/status/2066546074576109803)
```

Строка 273 — добавить Blog и Video перед Track:

Было:
```markdown
**Track:** AI Alpha & Data · **Hackathon:** [Mantle Turing Test Phase II](https://dorahacks.io/hackathon/mantle-ai/detail)
```

Стало:
```markdown
**Blog:** [How We Detect Smart Contract Exploits Without Training Data](https://alexbelij.medium.com/how-we-detect-smart-contract-exploits-without-training-data-using-hyperdimensional-computing-on-e94d5d83e6b8) · **Video:** [YouTube Demo](https://www.youtube.com/watch?v=s-OED4oZ8ho) · **Track:** AI Alpha & Data · **Hackathon:** [Mantle Turing Test Phase II](https://dorahacks.io/hackathon/mantle-ai/detail)
```

### 1C. Коммит + проверка + Release

```bash
# Проверка ПЕРЕД коммитом:
ruff check sentinel tests bench
# Ожидаемый результат: All checks passed!

pytest tests/ -q
# 129+ passed
```

Коммит:
```
fix: lint UP045 + add blog/video/X links to README
```

Затем создать GitHub Release:

```bash
gh release create v1.0.0 \
  --repo alexbelij/mantle-sentinel \
  --title "v1.0.0 — Mantle AI Hackathon MVP" \
  --notes "$(cat <<'EOF'
## Mantle Sentinel v1.0.0

**Training-free behavioral anomaly detection for Mantle smart contracts.**

### Highlights
- 🧬 10,000-dim HDC behavioral DNA encoding
- 🔍 Full pipeline: entropy filter → HDC → drift → BOCPD → attribution → Z.ai
- 📡 On-chain alert anchoring on Mantle mainnet
- 🤖 Telegram alerts via @MantleSentinelBot
- 📊 Live dashboard at mntsentinel.xyz/dashboard
- 🔬 129 tests, 0 false positives
- ⚡ CI/CD: GitHub Actions + pre-commit health gate

### Scan Results (Top 5 Mantle DeFi)
| Contract | Health | Alerts |
|----------|--------|--------|
| USDC.e   | 83/100 | 4      |
| Lendle   | 81/100 | 4      |
| WMNT     | 74/100 | 6      |
| USDT     | 70/100 | 12     |
| mETH     | 68/100 | 4      |

### Quick Start
```bash
git clone https://github.com/alexbelij/mantle-sentinel
cd mantle-sentinel && pip install -e ".[dev]"
python -m sentinel scan 0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9
```

### Links
- 🌐 [mntsentinel.xyz](https://mntsentinel.xyz)
- 📊 [Dashboard](https://mntsentinel.xyz/dashboard/)
- 📝 [Blog](https://alexbelij.medium.com/how-we-detect-smart-contract-exploits-without-training-data-using-hyperdimensional-computing-on-e94d5d83e6b8)
- 🎥 [Video Demo](https://www.youtube.com/watch?v=s-OED4oZ8ho)
- 🐦 [X Thread](https://x.com/alexbelij/status/2066546074576109803)
- 📜 [Contract](https://mantlescan.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187)
- 🤖 [Telegram](https://t.me/MantleSentinelBot)
- 🏆 [DoraHacks BUIDL](https://dorahacks.io/buidl/45170)

Built for [Mantle AI Hackathon — Turing Test Phase II](https://dorahacks.io/hackathon/mantle-ai/detail)
EOF
)"
```

### Проверка ITER 1

```bash
# CI green
ruff check sentinel tests bench && echo "LINT OK"
pytest tests/ -q

# README ссылки
grep -c "medium.com" README.md    # → 2
grep -c "x.com" README.md         # → 1
grep -c "youtube.com" README.md   # → 1

# Release exists
gh release view v1.0.0 --repo alexbelij/mantle-sentinel
```

### Файлы ITER 1

```
sentinel/client.py  — 2 строки (убран import Optional, заменён тип)
README.md           — 2 строки (ссылки на blog/X/video)
+ GitHub Release v1.0.0
```

---

## ITER 2 — Удалить stale TZ файлы

### Задачи

Удалить ВСЕ TZ-файлы из `docs/`:

```bash
git rm docs/TZ_FINAL_POLISH.md
git rm docs/TZ_VIDEO.md
git rm docs/TZ_BLOG.md
git rm docs/TZ_FIX_BLOG_IMAGES.md
git rm docs/TZ_FIXES.md
git rm docs/TZ_CLEANUP.md
```

⚠️ НЕ удалять:
- `docs/TZ_SDK.md` — ещё нужен (SDK для Demo Day)
- `docs/TZ_PITCH.md` — ещё нужен (Pitch для Demo Day)

### Проверка

```bash
# Осталось только 2 TZ
ls docs/TZ_*.md
# Ожидаемый результат:
# docs/TZ_PITCH.md
# docs/TZ_SDK.md

# CI всё ещё green
make check
```

### Коммит

```
chore: remove completed task specs
```

### Файлы

```
docs/TZ_FINAL_POLISH.md     — DELETED
docs/TZ_VIDEO.md            — DELETED
docs/TZ_BLOG.md             — DELETED
docs/TZ_FIX_BLOG_IMAGES.md  — DELETED
docs/TZ_FIXES.md            — DELETED
docs/TZ_CLEANUP.md          — DELETED (self-destruct)
```
