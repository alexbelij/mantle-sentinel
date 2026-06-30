# Plugin: `alert_severity`

Classifies any Sentinel alert into one of four severity tiers based on its
`drift` score. Pure function — no I/O, no side-effects, safe to call from
any thread.

## Severity tiers

| Tier        | Drift range   | Recommended action                          |
|-------------|---------------|---------------------------------------------|
| `NONE`      | < 0.50        | Below threshold — no notification           |
| `WARNING`   | 0.50 – 0.70   | Telegram notification                       |
| `CRITICAL`  | 0.70 – 0.90   | Telegram + on-chain `logAlert()`            |
| `EMERGENCY` | 0.90 – 1.00   | All of the above + webhook + PagerDuty      |

## Installation

No extra dependencies. The module lives at `sentinel/plugins/alert_severity.py`.

## Usage

### Basic

```python
from sentinel.plugins.alert_severity import classify, Severity

alert = {"alert_id": "regime_shift-0xabc-1234", "drift": 0.82}
sev = classify(alert)          # Severity.CRITICAL

if sev >= Severity.CRITICAL:
    onchain_anchor(alert)

if sev == Severity.EMERGENCY:
    pagerduty_notify(alert)
```

### With label string

```python
from sentinel.plugins.alert_severity import classify_with_label

sev, label = classify_with_label(alert)
print(f"[{label}] drift={alert['drift']:.2f}")
# → [CRITICAL] drift=0.82
```

### Works with Alert dataclass

```python
from sentinel.alert import Alert
from sentinel.plugins.alert_severity import classify

alert: Alert = pipeline.run(txs)
sev = classify(alert)          # reads alert.drift
```

### Routing pattern

```python
from sentinel.plugins.alert_severity import classify, Severity
from sentinel.plugins.webhook import WebhookNotifier
from sentinel.notify_telegram import send_telegram

wh = WebhookNotifier(url="https://your-endpoint/alerts")

def dispatch(alert):
    sev = classify(alert)
    if sev == Severity.NONE:
        return
    if sev >= Severity.WARNING:
        send_telegram(alert)
    if sev >= Severity.CRITICAL:
        onchain_anchor(alert)
    if sev == Severity.EMERGENCY:
        wh.notify(alert.to_dict())
        pagerduty_notify(alert)
```

## Error handling

The function raises `ValueError` (never returns silently) for:

- `alert` is `None`
- `drift` key missing from dict
- `drift` is `None` or non-numeric
- `drift` outside `[0.0, 1.0]` (overflow / underflow guard)
- `drift` is `NaN` or `Inf`

```python
try:
    sev = classify(alert)
except ValueError as e:
    log.error("Bad alert data: %s", e)
```

## Severity ordering

`Severity` is an `IntEnum` so you can use comparison operators:

```python
assert Severity.NONE < Severity.WARNING < Severity.CRITICAL < Severity.EMERGENCY
if sev >= Severity.CRITICAL:
    ...
```
