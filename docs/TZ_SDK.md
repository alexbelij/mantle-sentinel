# TZ_SDK — Python SDK (`pip install mantle-sentinel`)

> Для Dev Viktor. Задача: превратить существующий пакет `sentinel` в
> устанавливаемый SDK с удобным Python API.
> Цель: жюри (и любой разработчик) могут за 3 строки кода
> просканировать контракт на Mantle.

---

## ОБЩИЕ ПРАВИЛА

1. НЕ создавать новый пакет. Мы **расширяем** существующий `mantle-sentinel`.
2. НЕ ломать CLI (`python -m sentinel scan …`). Всё обратно совместимо.
3. НЕ менять алгоритмы, пороги, формулы. Только обёртка.
4. Все новые функции должны быть покрыты тестами.
5. Код — Python 3.11+, type hints, docstrings.

---

## ITER 1 — Public Python API (файл `sentinel/client.py`)

Создать `sentinel/client.py` — высокоуровневый API:

```python
"""sentinel.client — high-level SDK interface."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class ScanReport:
    """Result of a behavioral scan."""
    address: str
    health_score: int          # 0-100
    drift_median: float
    drift_p99: float
    alert_count: int
    alerts: list[dict]
    selector_count: int
    window_count: int
    z_ai_brief: Optional[str]  # None if no ZAI_API_KEY

    @property
    def is_healthy(self) -> bool:
        return self.health_score >= 70

    def to_dict(self) -> dict:
        """Serialize to plain dict (JSON-safe)."""
        ...

class SentinelClient:
    """One-line behavioral audit for any Mantle contract.

    Usage:
        from sentinel import SentinelClient
        client = SentinelClient()
        report = client.scan("0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9")
        print(report.health_score)  # 83
    """

    def __init__(
        self,
        rpc_url: str = "https://rpc.mantle.xyz",
        explorer_api: str | None = None,    # auto-detect
        zai_api_key: str | None = None,     # or from ZAI_API_KEY env
    ):
        ...

    def scan(
        self,
        address: str,
        *,
        tx_limit: int = 5000,
        explain: bool = True,        # call Z.ai if key available
        min_health: int | None = None,  # raise if score < min_health
    ) -> ScanReport:
        """Run full HDC pipeline on contract. Returns ScanReport."""
        ...

    def scan_multiple(
        self,
        addresses: list[str],
        **kwargs,
    ) -> list[ScanReport]:
        """Scan multiple contracts sequentially. Returns list of ScanReport."""
        ...
```

**Реализация:**
- `scan()` внутри вызывает существующий `sentinel.scan.analyze_records()` + `fetch_txlist()`.
- `scan_multiple()` — цикл по адресам.
- `zai_api_key` — из аргумента или `os.environ.get("ZAI_API_KEY")`.
- `min_health` — если задан и `health_score < min_health`, выбросить `SentinelHealthError`.

**Обновить `sentinel/__init__.py`:**
```python
from sentinel.client import SentinelClient, ScanReport

__all__ = ["SentinelClient", "ScanReport"]
```

---

## ITER 2 — Тесты (`tests/test_client.py`)

Минимум 8 тестов:

```
test_scan_report_dataclass        — создание, to_dict, is_healthy
test_client_scan_mocked           — mock fetch_txlist, проверить ScanReport
test_client_scan_no_zai           — без API key, z_ai_brief=None
test_client_scan_min_health_pass  — score >= min_health → ok
test_client_scan_min_health_fail  — score < min_health → SentinelHealthError
test_client_scan_multiple         — 2 адреса, 2 репорта
test_client_defaults              — rpc_url default, zai from env
test_scan_report_serialization    — to_dict → json.dumps → ok
```

Все тесты offline (mock network calls). Не трогать existующие тесты.

---

## ITER 3 — README секция + pyproject.toml

**README.md** — добавить секцию `## Python SDK` сразу после `## Quick Start`:

```markdown
## Python SDK

```python
from sentinel import SentinelClient

client = SentinelClient()
report = client.scan("0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9")

print(f"Health: {report.health_score}/100")
print(f"Alerts: {report.alert_count}")
print(f"Healthy: {report.is_healthy}")

# Scan multiple contracts
reports = client.scan_multiple([
    "0x09bc4e...",  # USDC.e
    "0x78c1b0...",  # WMNT
])
for r in reports:
    print(f"{r.address[:10]}… → {r.health_score}/100")
```

**pyproject.toml** — добавить console script:
```toml
[project.scripts]
sentinel = "sentinel.__main__:main"
```

И обновить description:
```toml
description = "Training-free behavioral anomaly detection for Mantle smart contracts"
```

---

## ITER 4 — `examples/` директория

Создать `examples/quick_scan.py`:
```python
"""Quick scan example — 3 lines to audit a contract."""
from sentinel import SentinelClient

client = SentinelClient()
report = client.scan("0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9")
print(f"USDC.e health: {report.health_score}/100 ({'✅' if report.is_healthy else '⚠️'})")
```

Создать `examples/multi_scan.py`:
```python
"""Scan top 5 Mantle DeFi contracts."""
from sentinel import SentinelClient

CONTRACTS = {
    "USDC.e": "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9",
    "WMNT":   "0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8",
    "USDT":   "0x201eba5cc46d216ce6dc03f6a759e8e766e956ae",
    "mETH":   "0xcda86a272531e8640cd7f1a92c01839911b90bb0",
    "Lendle": "0xcfA5aEbab31D0b7c02db0B3e05aeA3EEAfb96daB",
}

client = SentinelClient()
for name, addr in CONTRACTS.items():
    report = client.scan(addr)
    status = "✅" if report.is_healthy else "⚠️"
    print(f"{name:10s} {report.health_score:3d}/100 {status}  alerts={report.alert_count}")
```

---

## ФОРМАТ ВЫХОДА

```
sentinel/client.py          — ~120-150 строк
tests/test_client.py        — ~100-120 строк (8+ тестов)
examples/quick_scan.py      — ~5 строк
examples/multi_scan.py      — ~20 строк
README.md                   — +SDK секция
pyproject.toml              — +scripts, description update
sentinel/__init__.py        — +imports
```

Порядок: ITER 1 → ITER 2 (тесты зелёные) → ITER 3 → ITER 4.

Каждый ITER = отдельный коммит.
