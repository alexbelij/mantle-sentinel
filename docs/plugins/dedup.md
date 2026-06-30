# Alert Deduplication Plugin

`sentinel/plugins/dedup.py` — thread-safe in-memory deduplicator. Does **not** touch
`pipeline.py`, `bocpd.py`, or `watch.py`.

## Quick start

```python
from sentinel.plugins.dedup import AlertDeduplicator

dedup = AlertDeduplicator(ttl_seconds=600)  # 10-minute window

alert = {"window_id": "0xabc-42", "drift_score": 0.75}

dedup.is_new(alert)   # True  — first time we see this window
dedup.is_new(alert)   # False — duplicate within TTL, suppress it
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ttl_seconds` | `600` | How long to remember a seen alert (seconds) |
| `key_field` | `"window_id"` | Alert dict field used as dedup key |

If `key_field` is absent in the alert, the plugin falls back to a SHA-256
of the full payload — so it always works regardless of alert shape.

## Integration pattern

```python
from sentinel.plugins.dedup import AlertDeduplicator

dedup = AlertDeduplicator(ttl_seconds=300)

# Anywhere you currently call notify_telegram / send_alert:
if dedup.is_new(alert_dict):
    notify_telegram(alert_dict)
```

## Explicit mark + circuit breaker pattern

```python
dedup = AlertDeduplicator(ttl_seconds=600)

# High-volume scenario: check first, then process
if dedup.is_new(alert):
    result = process_alert(alert)    # expensive operation
    if result.sent:
        dedup.mark_seen(alert)       # only register on successful send
```

## Combining with webhook

```python
from sentinel.plugins.dedup import AlertDeduplicator
from sentinel.plugins.webhook import WebhookNotifier

dedup = AlertDeduplicator(ttl_seconds=600)
wh    = WebhookNotifier(url="https://hooks.example.com/sentinel")

def on_alert(alert: dict) -> None:
    if dedup.is_new(alert):
        wh.notify(alert)             # non-blocking POST
```
