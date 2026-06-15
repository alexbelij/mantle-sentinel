# TZ_FIXES — Remaining Fixes Before Demo Day

> Для Dev Viktor. Мелкие правки и финальный polish.
> Каждый ITER — отдельный коммит. Порядок: сверху вниз.

---

## ITER 1 — README badge fix

Файл: `README.md`

Badge `127 tests` устарел. Сейчас 129 тестов (CI/CD добавил +2).

Заменить:
```
![127 tests](https://img.shields.io/badge/tests-127%20passed-brightgreen)
```
На:
```
![129 tests](https://img.shields.io/badge/tests-129%20passed-brightgreen)
```

---

## ITER 2 — GitHub Release v1.0.0

Создать через CLI:
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
- 📜 [Contract](https://mantlescan.xyz/address/0x0899E1507CFfefF8620455721F5bd528Bb072187)
- 🤖 [Telegram](https://t.me/MantleSentinelBot)

Built for [Mantle AI Hackathon — Turing Test Phase II](https://dorahacks.io/hackathon/mantle-ai/detail)
EOF
)"
```

---

## ITER 3 — Удалить старые ветки

В репо висят ~20 старых `task/*` веток. Удалить все кроме `main`:

```bash
# Список всех веток
gh api /repos/alexbelij/mantle-sentinel/branches --jq '.[].name' | grep -v main

# Удалить каждую:
for branch in $(gh api /repos/alexbelij/mantle-sentinel/branches --paginate --jq '.[].name' | grep -v main); do
  gh api --method DELETE "/repos/alexbelij/mantle-sentinel/git/refs/heads/$branch"
done
```

⚠️ НЕ удалять `main`. Только task/* и прочие рабочие ветки.

---

## ITER 4 — BUIDL_SUBMISSION.md update

Файл: `docs/BUIDL_SUBMISSION.md`

1. Заменить `<DORAHACKS_BUIDL_URL>` на `https://dorahacks.io/buidl/...` (URL будет после регистрации — пока оставить как TODO-плейсхолдер, НЕ удалять).
2. Обновить количество тестов: `109` → `129` (2 места).
3. Обновить секцию Results: добавить `129 Python tests` (было 109).

---

## ITER 5 — Удалить stale TZ файлы

После выполнения всех ТЗ, удалить из `docs/`:
```
docs/TZ_FINAL_POLISH.md
docs/TZ_VIDEO.md
docs/TZ_PITCH.md
docs/TZ_SDK.md      (если будет запушен)
docs/TZ_BLOG.md     (если будет запушен)
docs/TZ_FIXES.md    (сам этот файл)
```

1 коммит: `chore: remove completed task specs`

⚠️ Выполнять ПОСЛЕДНИМ, после того как все TZ выполнены.

---

## ФОРМАТ ВЫХОДА

5 итераций, 5 коммитов. Порядок строгий: 1→2→3→4→5.
ITER 5 — только после завершения ВСЕХ остальных ТЗ.
