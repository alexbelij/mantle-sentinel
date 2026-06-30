# Plugin: `circuit_breaker`

Sliding-window rate-limiter for the alert pipeline. If more than `max_alerts`
alerts fire within `window_seconds`, the circuit trips to **OPEN** and further
calls raise `CircuitOpenError` until the window expires.

Prevents alert storms from flooding Telegram / webhooks / on-chain txs during
a high-noise incident.

## States

```
CLOSED  →  alert count ≤ max_alerts  →  normal operation
         ↓  threshold crossed
OPEN    →  all calls rejected with CircuitOpenError
         ↓  window expires
HALF    →  one probe allowed through
         ↓  probe succeeds
CLOSED  (circuit re-closes automatically)
```

## Installation

No extra dependencies — pure stdlib. Module: `sentinel/plugins/circuit_breaker.py`.

## Usage

### Basic

```python
from sentinel.plugins.circuit_breaker import CircuitBreaker, CircuitOpenError

cb = CircuitBreaker(max_alerts=10, window_seconds=600)  # 10 alerts / 10 min

try:
    cb.record()          # call before every alert dispatch
    send_telegram(alert)
except CircuitOpenError as e:
    log.warning("Alert suppressed — circuit open, resets at %s", e.reset_at)
```

### Combined with alert_severity

```python
from sentinel.plugins.alert_severity import classify, Severity
from sentinel.plugins.circuit_breaker import CircuitBreaker, CircuitOpenError

cb = CircuitBreaker(max_alerts=10, window_seconds=600)

def dispatch(alert):
    sev = classify(alert)
    if sev == Severity.NONE:
        return
    try:
        cb.record()
    except CircuitOpenError:
        # Always let EMERGENCY through even when circuit is open
        if sev < Severity.EMERGENCY:
            return
    send_telegram(alert)
```

### Combined with dedup + circuit breaker

```python
from sentinel.plugins.dedup import AlertDeduplicator
from sentinel.plugins.circuit_breaker import CircuitBreaker, CircuitOpenError

dedup = AlertDeduplicator(ttl_seconds=300)
cb    = CircuitBreaker(max_alerts=15, window_seconds=600)

def dispatch(alert_dict):
    if dedup.is_duplicate(alert_dict):
        return                          # already seen this window_id
    try:
        cb.record()
    except CircuitOpenError as e:
        log.warning("Circuit open: %s", e)
        return
    send_telegram(alert_dict)
```

### Manual reset (operator override)

```python
cb.reset()   # force CLOSED — use after confirming false-positive storm
```

### Inspect state

```python
from sentinel.plugins.circuit_breaker import BreakerState

print(cb.state)         # BreakerState.CLOSED / OPEN / HALF
print(cb.alert_count)   # alerts in current sliding window
```

## Parameters

| Parameter        | Default | Description                                      |
|------------------|---------|--------------------------------------------------|
| `max_alerts`     | 10      | Max alerts before tripping (must be ≥ 1)         |
| `window_seconds` | 600     | Sliding window duration in seconds (must be > 0) |
| `half_open_probe`| 1       | Successful probes needed to re-close circuit     |

## Error handling

`CircuitOpenError` carries `reset_at` (Unix timestamp):

```python
except CircuitOpenError as e:
    remaining = e.reset_at - time.time()
    log.warning("Circuit open for another %.0fs", remaining)
```

Constructor raises `ValueError` for invalid parameters (zero/negative values).

## Thread safety

All public methods hold a reentrant lock. Safe to call from multiple threads
(e.g. parallel contract monitors).
