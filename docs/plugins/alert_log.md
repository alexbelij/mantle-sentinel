# Plugin: `alert_log` — Persistent Alert Log

`sentinel/plugins/alert_log.py`

Provides an **append-only NDJSON file + SQLite index** for all alerts emitted by
the Sentinel pipeline. Designed as a zero-dependency drop-in: no changes to core
code are required.

---

## Quick start

```python
from sentinel.plugins import AlertLog

log = AlertLog("/var/lib/sentinel/logs")

# Append an alert (dict, Alert dataclass, or any object with .to_dict())
log.append(alert)

# Query the index
results = log.query(contract="0x013e13...", block_min=1000, block_max=2000)

# Operator marks a false positive
log.mark_fp("spam_attack-0x013e13-12345")
```

---

## Constructor

```python
AlertLog(directory: str | Path, max_bytes: int = 512 * 1024 * 1024)
```

| Parameter   | Default  | Description                                              |
|-------------|----------|----------------------------------------------------------|
| `directory` | —        | Directory for `alerts.ndjson` and `alerts.db`. Created if missing. |
| `max_bytes` | 512 MB   | Max NDJSON file size. `OverflowError` when exceeded.     |

---

## Methods

### `append(alert) → None`

Atomically appends *alert* to the NDJSON file and indexes it in SQLite.

**Accepted types:**
- `dict` with at least `alert_id` key
- Any `@dataclass` (serialised via `dataclasses.asdict`)
- Any object with a `.to_dict()` method (e.g. `sentinel.alert.Alert`)

**Raises:**
- `ValueError` — `alert_id` is empty, too long (>256 chars), or contains unsafe characters (`../`, spaces, SQL metacharacters). Only `A-Za-z0-9_-` are allowed.
- `OverflowError` — appending would exceed `max_bytes`.
- `TypeError` — unsupported object type.

Duplicate `alert_id` values are silently ignored (`INSERT OR IGNORE`).

---

### `mark_fp(alert_id: str) → bool`

Marks an alert as a **false positive** in the SQLite index (`fp_flag = 1`).

Returns `True` if found and updated, `False` if the `alert_id` does not exist.
Calling `mark_fp` on an already-FP alert is **idempotent**.

This is the first-stage hook for the FP feedback loop — downstream threshold
retraining can poll `query(fp_flag=1)` to collect operator-confirmed FPs.

---

### `query(...) → list[dict]`

Queries the SQLite index. Returns raw alert dicts, newest-first.

```python
log.query(
    contract="0xABC",        # exact match
    alert_type="spam_attack",
    branch="hamming",
    fp_flag=0,               # 0 = non-FP, 1 = FP
    block_min=1000,
    block_max=5000,
    limit=100,               # default 100
)
```

All filters are combined with `AND`. All values are passed as DB-API `?`
placeholders — **SQL injection safe**.

---

## Storage layout

```
/var/lib/sentinel/logs/
  alerts.ndjson    append-only, one JSON object per line, fsync'd on write
  alerts.db        SQLite (WAL mode)
    └─ alerts      alert_id PK, ts, block, contract, alert_type, drift,
                   branch, fp_flag, raw_json
```

---

## Security notes

| Concern              | Mitigation                                                    |
|----------------------|---------------------------------------------------------------|
| SQL injection        | All query values via `?` placeholders; column names are hardcoded from an allowlist |
| Path traversal       | `alert_id` validated against `^[A-Za-z0-9_\-]+$` before use  |
| Concurrent writes    | `threading.RLock` + SQLite WAL; 50-thread stress-tested       |
| File overflow        | `OverflowError` raised before write when `max_bytes` exceeded |
| Interrupted write    | `KeyboardInterrupt`/`SystemExit` re-raised; partial line visible in NDJSON (safe: incomplete JSON lines are skipped by readers) |

---

## Tests

```
pytest tests/test_alert_log.py -v    # 29 tests, all passing
```

Coverage: validation, append, duplicates, overflow, mark_fp idempotency,
query filters, SQL injection, concurrent appends, DB reinit.
