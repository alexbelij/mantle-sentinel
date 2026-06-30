# Plugin: `prototype_store`

Versioned, persistent store for HDC prototype vectors. Keeps the last **K=5**
versions so the operator can roll back if the False Positive rate spikes after
a Dream Mode consolidation.

## Design

- **Atomic writes** — `os.replace()` ensures no partial state on crash.
- **Overflow guard** — capped at `max_versions`; oldest auto-evicted.
- **Compact storage** — vectors are gzip+base64 encoded (D=10 000 int8 ≈ 4 KB on disk).
- **Thread-safe** — reentrant lock on all mutations.
- **Crash recovery** — corrupt index file renamed to `.corrupt.json`, fresh store starts automatically.

## Installation

Requires `numpy`. Module: `sentinel/plugins/prototype_store.py`.

## Usage

### Save after each Dream Mode consolidation

```python
from sentinel.plugins.prototype_store import PrototypeStore

store = PrototypeStore("/data/sentinel/prototypes", contract="0xABC...")

# After dream consolidation
epoch_id = store.save(
    vector=new_prototype,       # numpy int8 array shape (D,)
    consolidation_count=42,
    drift_median=0.12,          # must be in [0.0, 1.0]
)
print(f"Saved epoch {epoch_id}")
```

### List available versions

```python
for rec in store.list():        # newest first
    print(rec["epoch_id"], rec["timestamp"], rec["drift_median"])
```

Sample output:
```
3f8a1c2d  2024-01-15T03:00:00Z  0.12
b7e4d901  2024-01-14T03:00:00Z  0.09
```

### Load a specific version

```python
vector = store.load(epoch_id)   # numpy int8 array
pipeline.set_prototype(vector)  # restore
```

### Rollback to previous version

```python
versions = store.list()         # newest first
prev = versions[1]              # one step back
vector = store.load(prev["epoch_id"])
pipeline.set_prototype(vector)
print(f"Rolled back to {prev['epoch_id']} ({prev['timestamp']})")
```

### Poison detection — block consolidation if drift is high

```python
from sentinel.plugins.prototype_store import PrototypeStore

POISON_THRESHOLD = 0.3

def maybe_consolidate(pipeline, store, drift_median):
    if drift_median > POISON_THRESHOLD:
        log.warning(
            "Consolidation blocked — drift_median=%.2f > %.1f (poison guard)",
            drift_median, POISON_THRESHOLD,
        )
        return False

    new_proto = pipeline.dream_consolidate()
    store.save(new_proto, consolidation_count=pipeline.consolidation_count,
               drift_median=drift_median)
    return True
```

### Delete a specific version

```python
store.delete(epoch_id)
```

### Clear all versions

```python
store.clear()   # irreversible — use with caution
```

## Metadata fields per version

| Field                | Type    | Description                                      |
|----------------------|---------|--------------------------------------------------|
| `epoch_id`           | str     | Unique version identifier (UUID4 or custom)      |
| `timestamp`          | str     | ISO-8601 UTC timestamp                           |
| `consolidation_count`| int     | Dream Mode counter at save time                  |
| `contract`           | str     | Contract address this prototype guards           |
| `drift_median`       | float   | Median drift over consolidation window [0, 1]    |
| `dim`                | int     | HDC dimension (length of the vector)             |

## Error handling

`save()` raises `ValueError` for:
- `vector` is None, empty, or 2-D
- `consolidation_count` < 0
- `drift_median` outside [0.0, 1.0] or NaN/Inf

`load()` / `delete()` raise `KeyError` if epoch_id not found.

```python
try:
    store.save(vector, consolidation_count=c, drift_median=d)
except ValueError as e:
    log.error("Cannot save prototype: %s", e)
```

## Parameters

| Parameter      | Default | Description                              |
|----------------|---------|------------------------------------------|
| `directory`    | —       | Directory for store file (created if absent) |
| `contract`     | —       | Contract address (required, non-empty)   |
| `max_versions` | 5       | Maximum versions to retain (≥ 1)         |
