# TZ-PATCH: Health Score recalibration + badge + Routescan fallback

**Приоритет:** P0 • **Один коммит.**

---

## FIX A: Health Score recalibration

Файл: `sentinel/scan.py`, функция `compute_health_score()`.

**Было:**
```python
penalty += min(50, n_episodes * 5)
```

**Стало:**
```python
penalty += min(30, n_episodes * 2)
```

Остальные penalty строки (drift_p99, drift_median) — без изменений.

### Тесты

В `tests/test_scan.py` обновить `test_many_alerts_low_score`:
- 15 алертов × 2 = 30 (cap 30) + drift penalty. С `drift_median=0.5, drift_p99=0.8` это 30 + 15 + 6 = 51 penalty → score=49 < 50 ✅ тест всё ещё проходит.

Проверить что `test_clean_high_score` и `test_score_deterministic` не сломались (не должны — они не зависят от episode коэффициента).

---

## FIX B: Routescan fallback в scan

Файл: `sentinel/scan.py`, функция `scan_contract()`.

**Было:**
```python
def scan_contract(address: str, n_txs: int = 2000, explain: bool = False) -> dict:
    key = os.environ.get("ETHERSCAN_KEY", "")
    if not key:
        print("ERROR: set ETHERSCAN_KEY env var (free at etherscan.io)", file=sys.stderr)
        sys.exit(1)

    txs = fetch_txlist(address, n_txs, key)
```

**Стало:**
```python
def scan_contract(address: str, n_txs: int = 2000, explain: bool = False) -> dict:
    key = os.environ.get("ETHERSCAN_KEY", "")
    if key:
        txs = fetch_txlist(address, n_txs, key)
    else:
        # Routescan fallback (no API key needed)
        from sentinel.watch import fetch_txlist_from_block
        txs = fetch_txlist_from_block(address, start_block=0, n=n_txs)
```

Далее `to_raw()` работает одинаково — формат Etherscan/Routescan совместим.

> Если `fetch_txlist_from_block` возвращает Etherscan-format rows (он так и делает), то `to_raw(txs, address)` отработает без изменений.

---

## FIX C: Badge 118 → 127

Файл: `README.md`.

**Было:**
```markdown
![118 tests](https://img.shields.io/badge/tests-118%20passed-brightgreen)
```

**Стало:**
```markdown
![127 tests](https://img.shields.io/badge/tests-127%20passed-brightgreen)
```

---

## FIX D: Перегенерировать отчёты

После FIX A + FIX B:

```bash
# Без ETHERSCAN_KEY — Routescan fallback
for addr in \
  0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9 \
  0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8 \
  0x201eba5cc46d216ce6dc03f6a759e8e766e956ae \
  0xcda86a272531e8640cd7f1a92c01839911b90bb0 \
  0xcfa5ae76e8e1a1a8e47f2e5c9c1e4803c6a1b089; do   # ← проверь адрес Lendle
  python -m sentinel scan "$addr" --n 3000
done
```

Обновить:
- `bench/reports/*.json` — 5 файлов
- `bench/reports/SUMMARY.md` — таблица с новыми скорами
- Таблицу в `README.md` (секция "Live Scan — Top Mantle DeFi Contracts") — новые скоры

---

## Верификация

- `make check` (lint + 127 tests) — зелёный
- Health Score USDC.e ≥ 60
- `python -m sentinel scan 0x09bc4e... --json` работает БЕЗ ETHERSCAN_KEY
