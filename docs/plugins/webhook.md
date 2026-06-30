# Webhook Plugin

`sentinel/plugins/webhook.py` — isolated HTTP POST notifier. Does **not** touch
`pipeline.py`, `bocpd.py`, or `watch.py`.

## Quick start

```python
from sentinel.plugins.webhook import WebhookNotifier

wh = WebhookNotifier(url="https://your-endpoint.example.com/alerts")

# Fire-and-forget (non-blocking, background thread)
wh.notify(alert_dict)

# Or synchronous (blocks until delivered or retries exhausted)
success = wh.notify_sync(alert_dict)
```

## With a shared secret header

```python
wh = WebhookNotifier(
    url="https://hooks.example.com/sentinel",
    secret_header="X-Sentinel-Secret",
    secret_value="my-shared-secret",
)
wh.notify(alert_dict)
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `url` | required | Endpoint receiving JSON POST |
| `timeout` | `10` | Request timeout in seconds |
| `max_retries` | `3` | Retry attempts on transient errors |
| `retry_delay` | `1.0` | Seconds between retries |
| `secret_header` | `None` | Optional header name for auth |
| `secret_value` | `None` | Optional header value for auth |

## Payload shape

The plugin POSTs the alert dict serialised as JSON. For a typical Sentinel alert:

```json
{
  "window_id": "0xabc-42",
  "drift_score": 0.82,
  "alert_type": "regime_shift",
  "top_features": ["selector", "gas"],
  "timestamp": "2025-01-15T12:34:56Z"
}
```

## Combining with dedup

```python
from sentinel.plugins.dedup import AlertDeduplicator
from sentinel.plugins.webhook import WebhookNotifier

dedup = AlertDeduplicator(ttl_seconds=600)
wh = WebhookNotifier(url="https://hooks.example.com/sentinel")

def on_alert(alert: dict) -> None:
    if dedup.is_new(alert):
        wh.notify(alert)
```
