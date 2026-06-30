"""Tests for sentinel/plugins/circuit_breaker.py"""
from __future__ import annotations

import threading

import pytest

from sentinel.plugins.circuit_breaker import (
    BreakerState,
    CircuitBreaker,
    CircuitOpenError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeClock:
    """Injectable clock for deterministic time control in tests."""
    def __init__(self, t: float = 0.0):
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------

def test_invalid_max_alerts_zero():
    with pytest.raises(ValueError, match="max_alerts"):
        CircuitBreaker(max_alerts=0)

def test_invalid_max_alerts_negative():
    with pytest.raises(ValueError, match="max_alerts"):
        CircuitBreaker(max_alerts=-1)

def test_invalid_window_zero():
    with pytest.raises(ValueError, match="window_seconds"):
        CircuitBreaker(window_seconds=0)

def test_invalid_window_negative():
    with pytest.raises(ValueError, match="window_seconds"):
        CircuitBreaker(window_seconds=-10)

def test_invalid_half_open_probe():
    with pytest.raises(ValueError, match="half_open_probe"):
        CircuitBreaker(half_open_probe=0)


# ---------------------------------------------------------------------------
# CLOSED state — normal operation
# ---------------------------------------------------------------------------

def test_closed_by_default():
    cb = CircuitBreaker(max_alerts=5, window_seconds=60)
    assert cb.state == BreakerState.CLOSED

def test_records_up_to_max_without_tripping():
    clk = FakeClock()
    cb  = CircuitBreaker(max_alerts=5, window_seconds=60, _now=clk)
    for _ in range(5):
        cb.record()  # must not raise
    assert cb.state == BreakerState.CLOSED
    assert cb.alert_count == 5

def test_trips_on_max_plus_one():
    clk = FakeClock()
    cb  = CircuitBreaker(max_alerts=3, window_seconds=60, _now=clk)
    for _ in range(3):
        cb.record()
    with pytest.raises(CircuitOpenError):
        cb.record()
    assert cb.state == BreakerState.OPEN


# ---------------------------------------------------------------------------
# OPEN state — rejects calls
# ---------------------------------------------------------------------------

def test_open_rejects_all_calls():
    clk = FakeClock()
    cb  = CircuitBreaker(max_alerts=1, window_seconds=60, _now=clk)
    cb.record()
    with pytest.raises(CircuitOpenError):
        cb.record()
    # Further calls also rejected
    with pytest.raises(CircuitOpenError):
        cb.record()

def test_circuit_open_error_has_reset_at():
    clk = FakeClock(t=1000.0)
    cb  = CircuitBreaker(max_alerts=1, window_seconds=60, _now=clk)
    cb.record()
    with pytest.raises(CircuitOpenError) as exc_info:
        cb.record()
    err = exc_info.value
    assert err.reset_at > clk.t


# ---------------------------------------------------------------------------
# HALF-OPEN state — cooldown + auto-close
# ---------------------------------------------------------------------------

def test_half_open_after_cooldown():
    clk = FakeClock(t=0.0)
    cb  = CircuitBreaker(max_alerts=1, window_seconds=60, _now=clk)
    cb.record()
    with pytest.raises(CircuitOpenError):
        cb.record()
    clk.advance(61)  # past the window
    assert cb.state == BreakerState.HALF

def test_half_open_probe_closes_circuit():
    clk = FakeClock(t=0.0)
    cb  = CircuitBreaker(max_alerts=1, window_seconds=60, _now=clk)
    cb.record()
    with pytest.raises(CircuitOpenError):
        cb.record()
    clk.advance(61)
    cb.record()  # probe — should not raise
    assert cb.state == BreakerState.CLOSED


# ---------------------------------------------------------------------------
# Sliding window expiry
# ---------------------------------------------------------------------------

def test_old_alerts_expire():
    clk = FakeClock(t=0.0)
    cb  = CircuitBreaker(max_alerts=3, window_seconds=60, _now=clk)
    for _ in range(3):
        cb.record()
    clk.advance(61)          # window expired
    cb.record()              # must not raise — old alerts gone
    assert cb.alert_count == 1


# ---------------------------------------------------------------------------
# Manual reset
# ---------------------------------------------------------------------------

def test_manual_reset_closes_open_circuit():
    clk = FakeClock()
    cb  = CircuitBreaker(max_alerts=1, window_seconds=60, _now=clk)
    cb.record()
    with pytest.raises(CircuitOpenError):
        cb.record()
    cb.reset()
    assert cb.state == BreakerState.CLOSED
    cb.record()  # must not raise


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

def test_thread_safety_no_race():
    """Multiple threads recording simultaneously must not corrupt state."""
    cb      = CircuitBreaker(max_alerts=100, window_seconds=3600)
    errors  = []
    tripped = []

    def worker():
        for _ in range(20):
            try:
                cb.record()
            except CircuitOpenError:
                tripped.append(1)
            except Exception as e:
                errors.append(e)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Unexpected exceptions: {errors}"
