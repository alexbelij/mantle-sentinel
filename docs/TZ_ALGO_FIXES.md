# TZ — ALGO_REVIEW Fixes (все 9 warnings)

**Приоритет:** P0 • **Один коммит** `fix: address 9 algo review warnings`.

---

## FIX 1 — W-ENT-1 (HIGH): Entropy std floor

**Файл:** `sentinel/entropy.py`, метод `check()`

**Было (строка ~90):**
```python
        return abs(h - mean) > self.sigma * std
```

**Стало:**
```python
        effective_std = max(std, 0.05)  # W-ENT-1: floor prevents FP when all samples identical
        return abs(h - mean) > self.sigma * effective_std
```

> Также обновить `freeze()` (строка 80) — добавить комментарий:
```python
            self._stats[cell] = (float(arr.mean()), float(arr.std()), len(arr))
            # NOTE: std may be 0 for homogeneous cells (e.g. stable ERC-20 transfer);
            # check() applies a floor via W-ENT-1 fix.
```

---

## FIX 2 — W-SIG-4 (LOW): Timing Δt=0 graded response

**Файл:** `sentinel/drift.py`, метод `_timing()`

**Было (строка 87):**
```python
        ldt = math.log(max(dt, EPS))
```

**Стало:**
```python
        ldt = math.log(max(dt, 1.0))  # W-SIG-4: same-block (dt≤1s) → log(1)=0, no -inf spike
```

> `max(dt, 1.0)` означает: если dt < 1 секунды (включая 0 для same-block) — считаем 1с. Это даёт `log(1)=0`, а не `log(1e-9)=-20.7`. Timing deviation всё равно зафиксирует отклонение от медианы если same-block — это аномалия, но без сатурации squash.

---

## FIX 3 — W-SIG-2 (LOW): BOCPD docstring fix

**Файл:** `sentinel/bocpd.py`, строки 9-12

**Было:**
```python
conjugate observation model (Student-t posterior predictive). A changepoint is
declared when the posterior mass on run-length 0, ``P(r_t = 0 | x_{1:t})``,
exceeds ``p_thresh`` — i.e. the model believes the drift stream just reset to a
new regime. Episodes are tracked/merged exactly like the static detector.
```

**Стало:**
```python
conjugate observation model (Student-t posterior predictive). A changepoint is
declared when the posterior mass below the established run-length collapses:
``P(r_t < r_map^{prev})`` exceeds ``p_thresh`` AND the new regime has
higher drift (anomaly, not recovery). Episodes are tracked/merged exactly
like the static detector.
```

---

## FIX 4 — W-NUM-2 (LOW): Guard n_buckets=1

**Файл:** `sentinel/hdc.py`, метод `_level_table()`

**Было (строка ~81):**
```python
        flip_count = self.d // (2 * (self.n_buckets - 1))
```

**Стало:**
```python
        if self.n_buckets <= 1:  # W-NUM-2: single bucket → just the base vector
            table = np.empty((1, self.d), dtype=np.int8)
            table[0] = self._rand_bipolar(name, "level", 0)
            self._levels[name] = table
            return table
        flip_count = self.d // (2 * (self.n_buckets - 1))
```

---

## FIX 5 — W-HDC-1 (MEDIUM): Document caller 3/7 weight

**Файл:** `sentinel/hdc.py`, метод `_terms()`, добавить комментарий перед yield'ами:

```python
    def _terms(self, feat: TxFeatures, ablate: str | None = None):
        # Design note (W-HDC-1): caller sub-features (novel, freq, is_contract)
        # collectively hold 3/7 vote weight in the bundle. This is intentional:
        # caller identity is the strongest behavioral axis for contract monitoring.
        # Gas/value/timing/selector each contribute 1/7.
```

---

## FIX 6 — W-SIG-1 (MEDIUM): Document max vs weighted design choice

**Файл:** `sentinel/drift.py`, метод `update()`, перед строкой `if t_norm > h_norm:`:

```python
        # Design note (W-SIG-1): max(hamming, timing) is deliberate over weighted sum.
        # Pro: one LOW channel cannot mask a HIGH channel; no tuning parameter.
        # Con: joint evidence lost (both at 0.55 → 0.55 < θ=0.65). Accepted tradeoff.
```

---

## FIX 7 — W-DRM-1 (LOW): Document tie-breaking bias

**Файл:** `sentinel/dream.py`, метод `_sign()`:

**Было:**
```python
def _sign(acc: np.ndarray) -> np.ndarray:
    """Bipolar sign with ties (== 0) resolving to +1 (HDC convention)."""
    return np.where(acc >= 0, 1, -1).astype(np.int8)
```

**Стало:**
```python
def _sign(acc: np.ndarray) -> np.ndarray:
    """Bipolar sign with ties (== 0) resolving to +1 (HDC convention).

    W-DRM-1: tie→+1 introduces a negligible positive bias (exact ties require
    all contributing vectors to cancel, probability ≈ 2^{-N} per dimension).
    """
    return np.where(acc >= 0, 1, -1).astype(np.int8)
```

---

## FIX 8 — W-SEC-1/2/3/5 (MEDIUM): KNOWN_LIMITATIONS.md

**Создать файл `docs/KNOWN_LIMITATIONS.md`:**

```markdown
# Known Limitations

Design-scope boundaries documented during the algorithmic review (ALGO_REVIEW.md).

## 1. Warmup poisoning (W-SEC-1)
If the monitored contract is already under attack when monitoring starts, the 40%
warmup period will learn attack patterns as baseline "normal" behavior. Median/MAD
normalization partially mitigates sparse outliers but not systematic contamination.
**Mitigation (Phase 3):** Operator-guided safe period labeling.

## 2. Out-of-scope DeFi vectors (W-SEC-2)
Sentinel monitors single-contract behavioral drift. It does NOT detect:
- Flash loan attacks (single-tx atomic, no multi-tx drift)
- Sandwich / MEV (tx ordering, mempool-level)
- Oracle manipulation (cross-contract state dependency)
- Governance attacks (parameter semantics, not behavioral patterns)
These require cross-contract and mempool-level analysis — separate systems.

## 3. Frozen entropy baseline (W-SEC-3)
The entropy filter baseline is computed once during warmup and never updated.
New selectors introduced via proxy upgrades post-warmup are invisible to the
entropy tier. HDC Tier-2 and drift Tier-3 still cover behavioral changes.
**Mitigation (Phase 2):** Streaming entropy baseline with exponential decay.

## 4. Sustained high-drift suppression (W-SEC-5)
The static detector fires ONE alert per episode during sustained high-drift.
Subsequent windows above θ do not generate new alerts until drift drops and
re-triggers. By design: reduces alert noise. Individual alert timestamps and
drift values are preserved in window_stats.

## 5. Episode merging on Mantle (W-SEC-4)
EPISODE_COLLAPSE_S=600 (10 minutes ≈ 300 Mantle blocks). Multi-phase attacks
within 10 minutes merge into a single episode. Alert-level timestamps are
preserved. Configurable per-deployment via future operator settings.
```

---

## FIX 9 — Regenerate reports + update ALGO_REVIEW

После FIX 1 + FIX 2:

```bash
for addr in \
  0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9 \
  0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8 \
  0x201eba5cc46d216ce6dc03f6a759e8e766e956ae \
  0xcda86a272531e8640cd7f1a92c01839911b90bb0 \
  0xcfa5ae76e8e1a1a8e47f2e5c9c1e4803c6a1b089; do
  python -m sentinel scan "$addr" --n 3000
done
```

Обновить `bench/reports/*.json`, `SUMMARY.md`, README таблицу с новыми скорами.

Обновить `docs/ALGO_REVIEW.md` — добавить секцию в конце:
```markdown
## Post-Review Fixes Applied

All 9 warnings addressed in commit `<sha>`:
- W-ENT-1: entropy std floor `max(std, 0.05)` — reduces USDC.e false positives
- W-SIG-4: timing guard `max(dt, 1.0)` — graded response instead of saturation
- W-SIG-2: BOCPD docstring corrected
- W-NUM-2: n_buckets=1 guard
- W-HDC-1, W-SIG-1, W-DRM-1: design decisions documented in-code
- W-SEC-1/2/3/4/5: `docs/KNOWN_LIMITATIONS.md`
- Reports regenerated with entropy fix
```

---

## Тесты

- `make check` зелёный (lint + 127+ tests)
- Проверить что entropy тест с `std=0` ячейкой больше не даёт false positive
- USDC.e score ≥ 70 (ожидаем ~75-80 с entropy fix)
- Если тесты ломаются из-за `max(dt, 1.0)` — обновить timing expectations

---

## Верификация

- [ ] `make check` green
- [ ] USDC.e health score ≥ 70
- [ ] `docs/KNOWN_LIMITATIONS.md` exists and linked from README
- [ ] ALGO_REVIEW.md updated
- [ ] 5 JSON reports regenerated
