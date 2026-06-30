"""sentinel/plugins/circuit_breaker.py — Rate-limiting circuit breaker.

Prevents alert storms: if more than ``max_alerts`` alerts are emitted within
``window_seconds``, the breaker trips to OPEN state and calls are rejected
until the window expires.

States
------
    CLOSED  — normal operation; alerts pass through
    OPEN    — tripped; new alerts are rejected with CircuitOpenError
    HALF    — (auto) one test alert allowed after cooldown; success → CLOSED

Design constraints
------------------
    * No external dependencies — pure stdlib (threading, time, collections).
    * Thread-safe: all public methods hold a reentrant lock.
    * No I/O — callers decide what to do with CircuitOpenError.
    * Overflow guard: counter uses deque with maxlen → no unbounded memory growth.
    * No monkey-patching of time — ``_now`` is injectable for testing.

Usage
-----
    from sentinel.plugins.circuit_breaker import CircuitBreaker, CircuitOpenError

    cb = CircuitBreaker(max_alerts=10, window_seconds=600)

    try:
        cb.record()          # call before dispatching each alert
        send_telegram(alert)
    except CircuitOpenError as e:
        log.warning("Circuit open, alert suppressed: %s", e)
"""
from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from enum import Enum

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CircuitOpenError(Exception):
    """Raised when the circuit breaker is in OPEN state.

    Attributes
    ----------
    reset_at : float
        Unix timestamp when the circuit will allow a half-open probe.
    """

    def __init__(self, reset_at: float) -> None:
        self.reset_at = reset_at
        remaining = max(0.0, reset_at - time.time())
        super().__init__(
            f"Circuit breaker is OPEN — too many alerts. "
            f"Resets in {remaining:.0f}s (at {reset_at:.0f})."
        )


# ---------------------------------------------------------------------------
# State enum
# ---------------------------------------------------------------------------

class BreakerState(Enum):
    CLOSED = "CLOSED"
    OPEN   = "OPEN"
    HALF   = "HALF"


# ---------------------------------------------------------------------------
# CircuitBreaker
# ---------------------------------------------------------------------------

class CircuitBreaker:
    """Sliding-window rate-limiter / circuit breaker.

    Parameters
    ----------
    max_alerts : int
        Maximum number of alerts allowed within *window_seconds* before
        the circuit trips. Must be >= 1.
    window_seconds : float
        Duration of the sliding window in seconds. Must be > 0.
    half_open_probe : int
        Number of successful probes required to close the circuit again
        (default 1).
    _now : callable, optional
        Injectable clock function — ``time.time`` by default. Pass a
        custom callable in tests to control time without sleeping.
    """

    def __init__(
        self,
        max_alerts: int = 10,
        window_seconds: float = 600.0,
        half_open_probe: int = 1,
        _now: Callable[[], float] | None = None,
    ) -> None:
        # --- parameter validation ---
        if not isinstance(max_alerts, int) or max_alerts < 1:
            raise ValueError(
                f"max_alerts must be a positive integer; got {max_alerts!r}"
            )
        if not isinstance(window_seconds, (int, float)) or window_seconds <= 0:
            raise ValueError(
                f"window_seconds must be a positive number; got {window_seconds!r}"
            )
        if not isinstance(half_open_probe, int) or half_open_probe < 1:
            raise ValueError(
                f"half_open_probe must be a positive integer; got {half_open_probe!r}"
            )

        self._max_alerts     = max_alerts
        self._window         = float(window_seconds)
        self._half_open_need = half_open_probe
        self._now            = _now or time.time

        # sliding window: stores timestamps of recent alerts
        # maxlen prevents unbounded memory growth even if caller ignores the error
        self._timestamps: deque[float] = deque(maxlen=max_alerts * 10)

        self._state          = BreakerState.CLOSED
        self._open_until: float = 0.0
        self._half_open_ok: int = 0
        self._lock           = threading.RLock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self) -> None:
        """Record one alert attempt.

        If the sliding window count is below the threshold the call returns
        normally (CLOSED). If the threshold is exceeded the circuit trips to
        OPEN and :class:`CircuitOpenError` is raised.

        Raises
        ------
        CircuitOpenError
            When the circuit is currently OPEN or trips on this call.
        """
        with self._lock:
            now = self._now()
            self._expire_old(now)

            if self._state == BreakerState.OPEN:
                if now < self._open_until:
                    raise CircuitOpenError(self._open_until)
                # Cooldown elapsed → try half-open probe
                self._state = BreakerState.HALF
                self._half_open_ok = 0

            if self._state == BreakerState.HALF:
                # Allow one probe through; success increments counter
                self._timestamps.append(now)
                self._half_open_ok += 1
                if self._half_open_ok >= self._half_open_need:
                    self._state = BreakerState.CLOSED
                return

            # CLOSED: record and check
            self._timestamps.append(now)
            if len(self._timestamps) > self._max_alerts:
                self._trip(now)
                raise CircuitOpenError(self._open_until)

    def reset(self) -> None:
        """Manually close the circuit (operator override)."""
        with self._lock:
            self._timestamps.clear()
            self._state        = BreakerState.CLOSED
            self._open_until   = 0.0
            self._half_open_ok = 0

    @property
    def state(self) -> BreakerState:
        """Current state — non-blocking read."""
        with self._lock:
            now = self._now()
            if self._state == BreakerState.OPEN and now >= self._open_until:
                # Lazily transition to HALF on read so callers can inspect state
                self._state = BreakerState.HALF
            return self._state

    @property
    def alert_count(self) -> int:
        """Number of alerts recorded in the current sliding window."""
        with self._lock:
            self._expire_old(self._now())
            return len(self._timestamps)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _expire_old(self, now: float) -> None:
        """Remove timestamps outside the sliding window."""
        cutoff = now - self._window
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    def _trip(self, now: float) -> None:
        """Trip to OPEN state."""
        self._state      = BreakerState.OPEN
        self._open_until = now + self._window
