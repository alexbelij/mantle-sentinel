# TZ — sentinel scan + Z.ai profiling + Mantle reports + watch

**Приоритет:** P0–P2 • **Дедлайн:** сегодня (Jun 15 23:59 UTC+3)
**Контекст:** хакатон 1530 участников, жюри оценивают Technical (30%), Ecosystem Fit (20%), Innovation (20%), Business (20%), UX (10%). Нужно закрыть дыры в feature completeness и ecosystem fit.

---

## ITER 7 — P0: Fix CI (15 min)

### Проблема
CI workflow (`make check`) падает: 8 тестов не собираются — `ModuleNotFoundError: No module named 'bench'`. Тесты импортируют `from bench.synth import ...`, `from bench.scorer import ...` и т.д., но `bench` не указан как пакет.

### Фикс
В `pyproject.toml` секция `[tool.setuptools]`:

**Было:**
```toml
[tool.setuptools]
packages = ["sentinel"]
```

**Стало:**
```toml
[tool.setuptools]
packages = ["sentinel", "bench"]
```

### Верификация
- `make check` должен проходить (lint + test) — CI badge зелёный
- Все 109 тестов pass

---

## ITER 8 — P0: `sentinel scan <address>` (2–3 ч)

### Что делает
Одна команда — полный поведенческий аудит ЛЮБОГО Mantle-контракта:

```bash
# Minimal (бесплатный Etherscan ключ):
python -m sentinel scan 0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9

# С Z.ai объяснением:
ZAI_API_KEY=... python -m sentinel scan 0x09bc4e... --explain
```

### Вывод (stdout, human-readable + JSON-файл)

```
Mantle Sentinel — Behavioral Scan
══════════════════════════════════
Contract:     0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9
Chain:        Mantle (5000)
Transactions: 2000 fetched, 800 warmup, 1200 analyzed
─────────────────────────────────

Health Score: 94 / 100  ✅

Drift (median):    0.087
Drift (p99):       0.142
Unique selectors:  4
Top selectors:     transfer (78%), approve (11%), transferFrom (8%), permit (3%)
Gas (median):      49,218
Gas (p99):         61,340
Alerts:            0
Spam episodes:     0
Entropy anomalies: 0

Z.ai Profile:
  "This contract exhibits a highly stable behavioral DNA with a dominant
   transfer() pattern (78% of calls). Gas consumption is tightly distributed
   (49-61k range). No anomalous drift detected across 1200 transactions.
   Classification: stable token contract, low behavioral risk."

Report saved: bench/reports/0x09bc4e...df9.json
```

### Архитектура

Новый файл: `sentinel/scan.py` (~150–200 строк). Переиспользует:
- `bench.capture_etherscan.fetch_txlist()` + `bench.capture_etherscan.to_raw()` — загрузка txs
- `sentinel.pipeline.build_pipeline()` + `sentinel.pipeline.split_warmup()` — анализ
- `sentinel.explain_zai` — Z.ai вызов (новая функция `profile_contract()`, см. ITER 9)

```python
# sentinel/scan.py — псевдокод структуры

"""sentinel scan — one-command behavioral audit for any Mantle contract."""

import json, os, sys
from pathlib import Path

from bench.capture_etherscan import fetch_txlist, to_raw
from sentinel.pipeline import build_pipeline, split_warmup


def compute_health_score(alerts: list, drift_median: float, drift_p99: float) -> int:
    """0–100 score. 100 = perfectly stable, 0 = critical anomaly.

    Formula:
      base = 100
      - 5  per alert episode
      - 20 * max(0, drift_p99 - 0.5)   # drift penalty
      - 10 * max(0, drift_median - 0.3) # sustained drift penalty
      floor at 0
    """
    ...


def scan_contract(address: str, n_txs: int = 2000, explain: bool = False) -> dict:
    """Fetch txs, run pipeline, compute health score, return report dict."""
    key = os.environ.get("ETHERSCAN_KEY", "")
    if not key:
        print("ERROR: set ETHERSCAN_KEY env var (free at etherscan.io)", file=sys.stderr)
        sys.exit(1)

    # 1. Fetch
    txs = fetch_txlist(address, n_txs, key)
    raw = to_raw(txs, address)
    if len(raw) < 100:
        print(f"WARNING: only {len(raw)} txs found — need ≥100 for meaningful analysis", file=sys.stderr)
        if len(raw) < 20:
            print("ERROR: too few transactions for analysis", file=sys.stderr)
            sys.exit(1)

    # 2. Pipeline
    warmup, test = split_warmup(raw)  # 40% warmup, 60% test
    pipe = build_pipeline(address.lower(), warmup)
    alerts = []
    drifts = []
    for r in test:
        for a in pipe.process_tx(r):
            alerts.append(a.to_dict())
        if pipe.last_drift is not None:
            drifts.append(pipe.last_drift)

    # 3. Stats
    import numpy as np
    drift_arr = np.array(drifts) if drifts else np.array([0.0])
    drift_median = float(np.median(drift_arr))
    drift_p99 = float(np.percentile(drift_arr, 99))

    # Selector distribution
    from collections import Counter
    selectors = Counter(r.get("selector", r.get("calldata", "0x")[:10]) for r in raw)
    total_sel = sum(selectors.values())
    top_selectors = {k: round(v / total_sel, 4) for k, v in selectors.most_common(10)}

    # Gas stats
    gas_vals = [int(r.get("gas_used", 0)) for r in raw if int(r.get("gas_used", 0)) > 0]
    gas_median = int(np.median(gas_vals)) if gas_vals else 0
    gas_p99 = int(np.percentile(gas_vals, 99)) if gas_vals else 0

    score = compute_health_score(alerts, drift_median, drift_p99)

    report = {
        "contract": address.lower(),
        "chain": "mantle",
        "chain_id": 5000,
        "txs_fetched": len(raw),
        "txs_warmup": len(warmup),
        "txs_analyzed": len(test),
        "health_score": score,
        "drift_median": round(drift_median, 4),
        "drift_p99": round(drift_p99, 4),
        "unique_selectors": len(selectors),
        "top_selectors": top_selectors,
        "gas_median": gas_median,
        "gas_p99": gas_p99,
        "alerts": len(alerts),
        "alert_details": alerts,
    }

    # 4. Z.ai profile (optional)
    if explain:
        from sentinel.explain_zai import profile_contract
        report["zai_profile"] = profile_contract(report)

    return report


def print_report(report: dict) -> None:
    """Pretty-print report to stdout."""
    score = report["health_score"]
    icon = "✅" if score >= 80 else "⚠️" if score >= 50 else "🔴"
    print(f"""
Mantle Sentinel — Behavioral Scan
══════════════════════════════════
Contract:     {report['contract']}
Chain:        Mantle ({report['chain_id']})
Transactions: {report['txs_fetched']} fetched, {report['txs_warmup']} warmup, {report['txs_analyzed']} analyzed
──────────────────────────────────

Health Score: {score} / 100  {icon}

Drift (median):    {report['drift_median']:.3f}
Drift (p99):       {report['drift_p99']:.3f}
Unique selectors:  {report['unique_selectors']}
Top selectors:     {', '.join(f"{k} ({v:.0%})" for k, v in list(report['top_selectors'].items())[:5])}
Gas (median):      {report['gas_median']:,}
Gas (p99):         {report['gas_p99']:,}
Alerts:            {report['alerts']}
""")
    if "zai_profile" in report:
        print(f"Z.ai Profile:\n  \"{report['zai_profile']}\"\n")
```

### CLI интеграция

В `sentinel/__main__.py` добавить субкоманду `scan`:

```python
scan = sub.add_parser("scan", help="behavioral audit of any Mantle contract")
scan.add_argument("address", help="contract address (0x...)")
scan.add_argument("--n", type=int, default=2000, help="max transactions to fetch")
scan.add_argument("--explain", action="store_true", help="include Z.ai behavioral profile")
scan.add_argument("--out", default=None, help="write JSON report to path (default: bench/reports/<addr>.json)")
scan.add_argument("--json", action="store_true", help="output JSON instead of human-readable")
```

В `main()`:
```python
if args.command == "scan":
    from sentinel.scan import scan_contract, print_report
    report = scan_contract(args.address, n_txs=args.n, explain=args.explain)
    out_path = args.out or f"bench/reports/{args.address.lower()}.json"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(report, indent=2) + "\n")
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
        print(f"Report saved: {out_path}")
    return 0
```

### Health Score формула

```
base = 100
penalty  = 0
penalty += min(50, len(alert_episodes) * 5)      # до -50 за алерты
penalty += min(25, 50 * max(0, drift_p99 - 0.5))  # drift высокий
penalty += min(15, 30 * max(0, drift_median - 0.3)) # drift устойчиво высокий
penalty += min(10, 3 * max(0, spam_episodes))      # спам

score = max(0, base - penalty)
```

Эпизоды алертов считать по `alert_details` (группировать по `episode_id`).

### Тесты

Добавить `tests/test_scan.py`:
- `test_scan_dry_run()` — используя synthetic records из `bench.snapshot.synth_records()`, вызвать scan logic напрямую (без Etherscan API). Мокнуть `fetch_txlist` или вынести pipeline-часть в отдельную функцию `analyze_records(records, explain=False)`.
- `test_health_score_clean()` — score > 80 на чистых данных
- `test_health_score_attack()` — score < 50 на данных с инъекцией S1

---

## ITER 9 — P1: Z.ai Contract Profiling (1 ч)

### Что делает
Новая функция в `sentinel/explain_zai.py` — `profile_contract(report)`. Вызывается из `scan --explain`. Генерирует поведенческий профиль контракта (не алерт, а общий анализ).

### Код

В `sentinel/explain_zai.py` добавить:

```python
def profile_contract(report: dict, dry_run: bool = False) -> str:
    """Generate a Z.ai behavioral profile for a scanned contract.

    Unlike explain_alert (alert-specific), this produces a general behavioral
    DNA summary from scan results.
    """
    api_key = os.getenv("ZAI_API_KEY", "")
    if dry_run or not api_key:
        # Deterministic canned profile for CI/dry-run
        score = report.get("health_score", 0)
        status = "stable" if score >= 80 else "elevated risk" if score >= 50 else "critical"
        return (
            f"Contract {report['contract'][:10]}… analyzed over "
            f"{report.get('txs_analyzed', 0)} transactions. "
            f"Health score: {score}/100 ({status}). "
            f"{report.get('unique_selectors', 0)} unique selectors, "
            f"median drift {report.get('drift_median', 0):.3f}."
        )

    try:
        import httpx

        system_msg = (
            "You are a blockchain security analyst. Given behavioral scan data "
            "for a smart contract, produce a 3-4 sentence behavioral DNA profile. "
            "Describe the contract's transaction patterns, stability, and risk level. "
            "Be factual and specific. Use the exact numbers provided."
        )
        user_msg = (
            f"Contract: {report['contract']}\n"
            f"Chain: Mantle (5000)\n"
            f"Transactions analyzed: {report.get('txs_analyzed', 0)}\n"
            f"Health Score: {report.get('health_score', 0)}/100\n"
            f"Drift median: {report.get('drift_median', 0):.4f}\n"
            f"Drift p99: {report.get('drift_p99', 0):.4f}\n"
            f"Unique selectors: {report.get('unique_selectors', 0)}\n"
            f"Top selectors: {json.dumps(report.get('top_selectors', {}))}\n"
            f"Gas median: {report.get('gas_median', 0)}\n"
            f"Gas p99: {report.get('gas_p99', 0)}\n"
            f"Alerts: {report.get('alerts', 0)}\n"
            f"Generate a behavioral DNA profile for this contract."
        )

        resp = httpx.post(
            f"{ZAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": ZAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                "max_tokens": 800,
                "temperature": 0.3,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        text = data["choices"][0]["message"]["content"].strip()
        return text or profile_contract(report, dry_run=True)

    except Exception:
        logger.exception("Z.ai profile call failed — falling back to canned")
        return profile_contract(report, dry_run=True)
```

Добавить `import json` в начало файла (если ещё нет).

### Тест

В `tests/test_explain_zai.py` добавить:
```python
def test_profile_contract_dry():
    report = {"contract": "0xtest", "txs_analyzed": 500, "health_score": 92,
              "unique_selectors": 4, "drift_median": 0.08, "drift_p99": 0.14,
              "alerts": 0}
    from sentinel.explain_zai import profile_contract
    result = profile_contract(report, dry_run=True)
    assert "92" in result
    assert "stable" in result
```

---

## ITER 10 — P1: Pre-computed Mantle DeFi Reports (1 ч после scan)

### Что делает
Прогнать `sentinel scan` на 5 крупнейших Mantle DeFi контрактах, закоммитить результаты.

### Контракты

| # | Протокол | Адрес | Тип |
|---|----------|-------|-----|
| 1 | USDC.e | `0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9` | Stablecoin |
| 2 | WMNT (Wrapped MNT) | `0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8` | Wrapped native |
| 3 | USDT | `0x201eba5cc46d216ce6dc03f6a759e8e766e956ae` | Stablecoin |
| 4 | mETH | `0xcda86a272531e8640cd7f1a92c01839911b90bb0` | LST |
| 5 | Agni Finance Router | `0x319b69888b0d11cec22caa5034e25fff6cbc3431` | DEX |

> Уточни адреса через Mantlescan топ-контрактов. Используй те, у которых ≥1000 txs.

### Выполнение

```bash
export ETHERSCAN_KEY=...
for addr in 0x09bc4e... 0x78c1b0... 0x201eba... 0xcda86a... 0x319b69...; do
  python -m sentinel scan "$addr" --n 3000
done
```

### Структура результатов

```
bench/reports/
├── 0x09bc4e0d...df9.json
├── 0x78c1b0c9...cb8.json
├── 0x201eba5c...b0e.json
├── 0xcda86a27...bb0.json
├── 0x319b6988...431.json
└── SUMMARY.md          ← таблица Health Score всех контрактов
```

`SUMMARY.md` формат:
```markdown
# Mantle DeFi — Behavioral Health Report

Generated by `sentinel scan` on Jun 15, 2026.

| Contract | Protocol | Health | Drift (median) | Drift (p99) | Selectors | Alerts |
|----------|----------|--------|----------------|-------------|-----------|--------|
| 0x09bc…  | USDC.e   | 94/100 | 0.087          | 0.142       | 4         | 0      |
| ...      | ...      | ...    | ...            | ...         | ...       | ...    |

All top Mantle DeFi contracts show stable behavioral DNA with zero anomalies detected.
```

### В README

Добавить секцию после "Results":
```markdown
## Mantle Ecosystem Health

We scanned the top 5 Mantle DeFi contracts. All show stable behavioral DNA:

| Protocol | Health Score | Alerts |
|----------|-------------|--------|
| USDC.e   | 94/100 ✅   | 0      |
| WMNT     | 97/100 ✅   | 0      |
| ...      | ...         | ...    |

*Run your own scan: `python -m sentinel scan <any-mantle-address>`*
```

---

## ITER 11 — P2: `sentinel watch <address>` (2 ч после scan)

### Что делает
Непрерывный мониторинг контракта в реальном времени. Поллит RPC каждые N секунд, стримит drift в stdout, триггерит алерты.

```bash
python -m sentinel watch 0x09bc4e... --interval 30
```

Вывод:
```
[12:01:15] block 96681000  drift=0.092  score=94  ▓▓▓▓▓▓▓▓▓░░  OK
[12:01:45] block 96681012  drift=0.088  score=94  ▓▓▓▓▓▓▓▓▓░░  OK
[12:02:15] block 96681025  drift=0.341  score=72  ▓▓▓▓▓▓▓░░░░  ⚠️  ELEVATED
[12:02:45] block 96681038  drift=0.872  score=31  ▓▓▓░░░░░░░░  🔴 ALERT: entropy_anomaly
```

### Архитектура

Новый файл: `sentinel/watch.py` (~100–150 строк).

Подход:
1. Начальный scan (warmup) — первые `--warmup` txs (по умолчанию 500)
2. Запомнить последний обработанный блок
3. Каждые `--interval` секунд:
   - Fetch новые txs с `startblock=last_block+1` через Etherscan API
   - Прогнать через pipeline
   - Вывести drift + score
   - Если алерт — вывести + опционально Telegram

```python
# sentinel/watch.py — псевдокод

def watch_contract(address: str, interval: int = 30, warmup_n: int = 500, explain: bool = False):
    key = os.environ.get("ETHERSCAN_KEY", "")
    # 1. Initial warmup
    print(f"Warming up on {warmup_n} historical txs...")
    txs = fetch_txlist(address, warmup_n, key)
    raw = to_raw(txs, address)
    warmup, _ = split_warmup(raw, frac=1.0)  # all warmup
    pipe = build_pipeline(address.lower(), warmup)
    last_block = max(int(r["block_number"]) for r in raw)
    print(f"Baseline established. Monitoring from block {last_block}...")

    # 2. Poll loop
    while True:
        time.sleep(interval)
        new_txs = fetch_txlist_from_block(address, last_block + 1, key)  # new helper
        new_raw = to_raw(new_txs, address)
        for r in new_raw:
            alerts = pipe.process_tx(r)
            drift = pipe.last_drift or 0.0
            score = compute_health_score_live(drift, alerts)
            print_live_line(r, drift, score, alerts)
            if alerts and explain:
                for a in alerts:
                    a.explanation = explain_alert(a)
                    print(f"  Z.ai: {a.explanation}")
            last_block = max(last_block, int(r["block_number"]))
```

Нужна вспомогательная `fetch_txlist_from_block()` в `capture_etherscan.py`:
```python
def fetch_txlist_from_block(address: str, start_block: int, key: str, n: int = 100) -> list[dict]:
    """Fetch txs starting from a specific block (for watch mode polling)."""
    params = {
        "chainid": MANTLE, "module": "account", "action": "txlist",
        "address": address, "startblock": start_block, "endblock": 99999999,
        "page": 1, "offset": n, "sort": "asc", "apikey": key,
    }
    url = V2 + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=40) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "1" or not data.get("result"):
        return []
    return data["result"]
```

### CLI интеграция

В `sentinel/__main__.py`:
```python
watch = sub.add_parser("watch", help="live-monitor a Mantle contract")
watch.add_argument("address", help="contract address (0x...)")
watch.add_argument("--interval", type=int, default=30, help="poll interval in seconds")
watch.add_argument("--warmup", type=int, default=500, help="historical txs for warmup")
watch.add_argument("--explain", action="store_true", help="call Z.ai on alerts")
```

### Тесты

- `test_watch_warmup()` — мокнуть fetch, убедиться что pipeline создаётся корректно
- Интеграционный тест не нужен (это polling loop)

---

## Порядок выполнения

```
ITER 7  → fix CI (pyproject.toml)        → push → verify CI green
ITER 8  → sentinel scan                   → push → verify dry-run test
ITER 9  → Z.ai profile_contract          → push → verify dry-run test
ITER 10 → run scans + commit reports      → push → verify SUMMARY.md
ITER 11 → sentinel watch                  → push → verify warmup test
```

Каждый ITER — отдельный коммит с описанием `ITER-N: <description>`.

## Файлы, которые меняются / создаются

### Новые файлы:
- `sentinel/scan.py`
- `sentinel/watch.py`
- `tests/test_scan.py`
- `bench/reports/SUMMARY.md`
- `bench/reports/*.json` (5 файлов)

### Изменяемые файлы:
- `pyproject.toml` — добавить `bench` в packages
- `sentinel/__main__.py` — добавить `scan` и `watch` субкоманды
- `sentinel/explain_zai.py` — добавить `profile_contract()`
- `tests/test_explain_zai.py` — добавить `test_profile_contract_dry`
- `README.md` — добавить секцию "Mantle Ecosystem Health" + обновить Quick Start с `sentinel scan`
- `Makefile` — можно добавить `scan` target (опционально)

## Ограничения

- `ETHERSCAN_KEY` нужен для ITER 10 (отчёты). Бесплатный ключ: https://etherscan.io/apis
- Z.ai вызовы в тестах всегда `dry_run=True` — CI не должен трогать live API
- Health Score формула детерминистична — те же данные = тот же score
- `sentinel watch` — Ctrl+C для остановки, graceful shutdown не обязателен для MVP
