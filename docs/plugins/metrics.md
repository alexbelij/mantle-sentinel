# Plugin: `metrics` — Per-Transaction Performance Metrics

`sentinel/plugins/metrics.py`

Tracks **latency (wall-clock seconds)** and **memory delta (RSS bytes)** for any
callable or code block inside the Sentinel pipeline. Integrates as an optional
decorator or context manager — no changes to core code required.

---

## Quick start

```python
from sentinel.plugins import MetricsCollector, track_metrics

collector = MetricsCollector()

# As a decorator
@track_metrics(collector)
def process_tx(tx):
    ...

# As a context manager
with collector.measure("encode_hd"):
    encode(tx)

# Aggregate stats
print(collector.summary())

# Export to JSON
collector.export_json("/var/lib/sentinel/metrics.json")
```

---

## Constructor

```python
MetricsCollector(ring_size: int = 10_000, max_file_bytes: int = 256 * 1024 * 1024)
```

| Parameter        | Default  | Description                                              |
|------------------|----------|----------------------------------------------------------|
| `ring_size`      | 10 000   | Max samples in memory. Oldest are evicted automatically. |
| `max_file_bytes` | 256 MB   | Max export file size. `OverflowError` when exceeded.     |

---

## Methods

### `measure(operation: str)` — context manager

Records latency and memory delta for the enclosed block.

```python
with collector.measure("detect"):
    result = run_detection(tx)
```

- `KeyboardInterrupt` and `SystemExit` are **re-raised** after the sample is saved.
- Other exceptions are propagated normally; the sample is recorded with `error=True`.
- `tracemalloc` failures are logged as warnings and never crash the caller.

---

### `@track_metrics(collector, operation=None)` — decorator

Wraps a function; each call records one sample.

```python
@track_metrics(collector, operation="hdc_encode")
def encode(tx):
    ...
```

`operation` defaults to `func.__name__` when omitted.

---

### `summary() → dict`

Returns aggregate statistics over all samples in the ring buffer.

```json
{
  "count": 500,
  "error_count": 2,
  "latency_s": { "min": 0.0001, "max": 0.012, "mean": 0.0008, "p50": 0.0007, "p95": 0.0011, "p99": 0.0015 },
  "memory_delta_bytes": { "min": -4096, "max": 32768, "mean": 1024 },
  "by_operation": {
    "hdc_encode": { "count": 300, "mean_latency_s": 0.0006 },
    "detect":     { "count": 200, "mean_latency_s": 0.0011 }
  }
}
```

Returns `{"count": 0}` when the buffer is empty.

---

### `export_json(path, *, append=False) → None`

Exports all ring-buffer samples to a JSON file (fsync'd).

| Parameter | Default | Description                                |
|-----------|---------|--------------------------------------------|
| `path`    | —       | Destination file. Parent dirs created if missing. |
| `append`  | `False` | If `True`, appends a new line (LDJSON format). |

**Raises** `OverflowError` if the file would exceed `max_file_bytes`.

---

### `record(sample: MetricSample) → None`

Low-level: append a pre-built `MetricSample` directly.

---

### `clear() → None`

Empties the ring buffer.

---

## `MetricSample` schema

| Field                | Type    | Description                        |
|----------------------|---------|------------------------------------|
| `operation`          | `str`   | Operation label                    |
| `latency_s`          | `float` | Wall-clock seconds                 |
| `memory_delta_bytes` | `int`   | RSS delta (tracemalloc); 0 if unavailable |
| `error`              | `bool`  | `True` if the call raised an exception |

---

## Security & reliability notes

| Concern                    | Mitigation                                                  |
|----------------------------|-------------------------------------------------------------|
| Ring-buffer overflow       | `collections.deque(maxlen=N)` — oldest sample evicted automatically |
| Export file overflow       | `OverflowError` raised before write                        |
| KeyboardInterrupt/SystemExit | Sample saved, exception re-raised                        |
| tracemalloc unavailability | Logged as warning; `memory_delta_bytes` = 0               |
| Concurrent access          | `threading.RLock` on all mutations; 50-thread stress-tested |

---

## Tests

```
pytest tests/test_metrics.py -v    # 24 tests, all passing
```

Coverage: decorator, context manager, ring eviction, overflow, interrupt handling,
concurrency, export overwrite/append, summary stats with multiple operations.
