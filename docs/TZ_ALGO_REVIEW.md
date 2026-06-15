# TZ — Algorithmic Review (subagent multi-role)

**Цель:** Найти баги, ошибки в формулах, edge cases и логические дыры в алгоритмах Sentinel ДО сабмита.
**Формат:** Каждый субагент — отдельная роль. Читает ТОЛЬКО конкретные файлы, пишет VERDICT + список findings.

---

## Роли и файлы

### ROLE 1: HDC Mathematician
**Файлы:** `sentinel/hdc.py`, `sentinel/interpreter.py`, `sentinel/dream.py`, `sentinel/config.py`

Проверить:
- [ ] Level encoding: bucket 0 random, каждый следующий flips `D/(2*(B-1))` бит. При B=16, D=10000 → 333 flip на шаг. Bucket 0 vs bucket 15 должен быть ~ортогонален (cosine ≈ 0). Верна ли формула `flip_count = D // (2 * (B - 1))`?
- [ ] Binding (role-filler): `R_f ⊙ F_f` — поэлементное умножение bipolar → bipolar. Корректно ли для int8 {-1,+1}?
- [ ] Bundling: `sign(Σ V_tx)` — majority vote. Ties → +1 (`acc >= 0`). Верно ли что это стандартный MAP bundling?
- [ ] Hamming distance: `count_nonzero(a != b)`. Для bipolar {-1,+1} это правильная мера? Связь с cosine: `cos = (D - 2*hamming)/D` — верна ли формула?
- [ ] Interpreter ablation: `contribution_f = hamming(V_win, P) − hamming(V_win^{-f}, P^{-f})`. Знаковое вычитание — может ли contribution быть отрицательным? Это ожидаемо?
- [ ] Dream mode: `V_new = sign(λ·V_old + Σ V_safe)` где `λ = alpha·N`. Верно ли что при N safe windows и alpha (по умолчанию) старый прототип получает пропорциональный вес? Не может ли λ быть слишком большим и заглушить обновление?

### ROLE 2: Signal Processing / Anomaly Detection Specialist
**Файлы:** `sentinel/drift.py`, `sentinel/detector.py`, `sentinel/bocpd.py`, `sentinel/config.py`

Проверить:
- [ ] Robust normalization: `z = (x - median) / (1.4826 * MAD + ε)`, потом `squash(z) = clip(z/6, 0, 1)`. Верен ли коэффициент 1.4826 (это Gaussian consistency factor для MAD)? Правильно ли применять его к НЕ-Gaussian drift distribution?
- [ ] `_RobustNormalizer.normalize()`: при MAD=0 (>50% значений одинаковы) — что происходит? Есть ли guard? (Строка D-09 в коде.) Корректен ли fallback?
- [ ] Drift formula: `drift = max(norm(hamming), norm(timing))`. Max а не weighted sum — теряем ли мы информацию? Может ли один канал маскировать другой?
- [ ] Timing signal: `|log(Δt) − median_window(log(Δt))|`. Логарифм Δt — что если Δt=0 (два tx в одном блоке)? Есть ли `max(Δt, 1)` guard?
- [ ] Static detector: θ=0.65, k=3 hysteresis. Drift в [0,1] после squash. 0.65 — это z-score 3.9σ (squash = z/6). Достаточно ли чувствительно? Слишком чувствительно?
- [ ] BOCPD: Adams & MacKay с NIG prior. `cp_score = P(r_t < r_map^{prev})` — это НЕ стандартный `P(r_t=0)`. Почему? Корректна ли метрика? Hazard=100, p_thresh=0.5 — обосновано ли?
- [ ] BOCPD Student-t: `lgamma` через `np.vectorize(lgamma)` — не медленно ли для production? Численная стабильность при больших df?
- [ ] BOCPD truncation: `max_run=500`, renormalization после truncation. Теряем ли мы хвостовую массу?

### ROLE 3: Blockchain Security / DeFi Analyst
**Файлы:** `sentinel/entropy.py`, `sentinel/pipeline.py`, `sentinel/scan.py`, `sentinel/config.py`, `bench/reports/SUMMARY.md`

Проверить:
- [ ] Entropy filter: Shannon entropy calldata body, 4σ threshold. Может ли легитимный контракт (multicall, permit, complex ABI) триггерить false positive по entropy?
- [ ] Per-(selector, length_bucket) baseline — корректна ли группировка? Что если контракт имеет upgradeability и новые селекторы появляются после деплоя?
- [ ] Pipeline: entropy alert → bypass Tier 4. Значит entropy anomaly НЕ влияет на drift/prototype? Может ли это маскировать реальную атаку?
- [ ] Health Score (рекалиброванный): `episodes*2` (cap 30) + drift penalties. USDC.e имеет 13 эпизодов — это реальные regime shifts. Не слишком ли чувствительный детектор для стабильных контрактов?
- [ ] Реальные атаки: selector flood (S1), gas shift (S3), timing burst (S5), payload mutation (S7). Покрывает ли это основные DeFi attack vectors? Чего не хватает? (flash loan? governance attack? reentrancy?)
- [ ] Warmup 40% — достаточно ли для baseline? Что если warmup содержит аномалии (контракт уже под атакой)?
- [ ] `EPISODE_COLLAPSE_S = 600` (10 min) — адекватно ли для Mantle (~2s blocks)?

### ROLE 4: Numerical Stability & Edge Case Engineer
**Файлы:** все `sentinel/*.py`

Проверить:
- [ ] Division by zero: everywhere MAD=0, std=0, total=0, empty arrays
- [ ] Integer overflow: int8 в accumulator для bundling — `acc` растёт как сумма int8, может overflow? (Hint: numpy upcasts int8 sum to int64 — проверить.)
- [ ] Empty window: `len(vec_window) < WINDOW` — пропускаем drift. Но `_feat_window` всё ещё растёт. Синхронизированы ли они?
- [ ] Single-element arrays: `np.median([x])` = x, `np.percentile([x], 99)` = x. ОК для drift_arr?
- [ ] Log of zero: `log(Δt)` в timing signal. Δt = block_timestamp[i] - block_timestamp[i-1]. Если одинаковый timestamp → dt=0 → log(0) = -inf. Guard?
- [ ] calldata = "0x" или пустой — `body_of("0x")` → b"" → `byte_entropy(b"")` → 0.0. Корректно ли?
- [ ] `_quantile_edges` с одинаковыми значениями: если все gas одинаковы → все edges одинаковы → `searchsorted` всё в bucket 0 или последний. Проверить.
- [ ] `selector_of` на calldata < 4 bytes → "0x". Это ожидаемо для ETH transfers?

---

## Формат ответа каждого субагента

```markdown
# ROLE N: <name>

## VERDICT: PASS / PASS-WITH-NOTES / FAIL

## 🔴 CRITICAL (блокирует сабмит)
- <описание бага + файл:строка + предложенный фикс>

## ⚠️ WARNING (не блокирует, но рекомендуется)
- <описание + файл:строка>

## ✅ VERIFIED
- <что проверено и корректно>
```

---

## Выполнение

1. Создай 4 субагента (по 1 на роль)
2. Каждый субагент ЧИТАЕТ указанные файлы из репо
3. Каждый пишет свой VERDICT
4. После завершения всех 4 — собери CONSOLIDATED REPORT:
   - Все 🔴 CRITICAL → обязательный фикс
   - Все ⚠️ WARNING → оценить severity
   - Финальный VERDICT: SHIP / FIX-THEN-SHIP / BLOCK

5. Закоммить `docs/ALGO_REVIEW.md` с consolidated report

---

## Constraints

- НЕ менять код. Только ревью.
- Если найден 🔴 CRITICAL — описать минимальный фикс (1-3 строки).
- Если все 4 роли дают PASS — пишем SHIP.
- Максимум 30 минут на всё (4 субагента параллельно).
