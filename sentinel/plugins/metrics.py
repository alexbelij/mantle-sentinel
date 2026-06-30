"""sentinel/plugins/metrics.py — Per-transaction performance metrics plugin.

Tracks latency (wall-clock seconds) and memory delta (RSS bytes) for any
callable or code block. Integrates with the Sentinel pipeline as an optional
decorator / context-manager — no changes to core code required.

Features
--------
- @track_metrics decorator and MetricsCollector context manager
- Per-call samples: operation name, latency_s, memory_delta_bytes, error flag
- Ring-buffer storage (configurable size, default 10 000 samples)
- JSON export with optional file-append mode
- Overflow guard: raises OverflowError when export file exceeds max_file_bytes
- Thread-safe: RLock on all mutations
- KeyboardInterrupt / SystemExit are re-raised after recording the sample
- tracemalloc failures are logged as warnings, never crash the caller

Usage
-----
    from sentinel.plugins.metrics import MetricsCollector, track_metrics

    collector = MetricsCollector()

    # As a decorator
    @track_metrics(collector)
    def process_tx(tx):
        ...

    # As a context manager
    with collector.measure("encode_hd"):
        encode(tx)

    # Export
    collector.export_json("/var/lib/sentinel/metrics.json")
    summary = collector.summary()
"""

from __future__ import annotations

import collections
import functools
import json
import logging
import os
import threading
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

_DEFAULT_RING_SIZE = 10_000
_DEFAULT_MAX_FILE_BYTES = 256 * 1024 * 1024  # 256 MB


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


class MetricSample:
    """Single performance observation."""

    __slots__ = ("operation", "latency_s", "memory_delta_bytes", "error")

    def __init__(
        self,
        operation: str,
        latency_s: float,
        memory_delta_bytes: int,
        error: bool = False,
    ) -> None:
        self.operation = operation
        self.latency_s = latency_s
        self.memory_delta_bytes = memory_delta_bytes
        self.error = error

    def to_dict(self) -> dict:
        return {
            "operation": self.operation,
            "latency_s": self.latency_s,
            "memory_delta_bytes": self.memory_delta_bytes,
            "error": self.error,
        }


# ---------------------------------------------------------------------------
# MetricsCollector
# ---------------------------------------------------------------------------


class MetricsCollector:
    """Collects per-transaction performance samples.

    Parameters
    ----------
    ring_size:
        Maximum number of samples retained in memory (ring buffer).
        Older samples are evicted automatically.  Default: 10 000.
    max_file_bytes:
        Maximum size for the export JSON file.  Raises ``OverflowError``
        when the limit would be exceeded.  Default: 256 MB.

    Example
    -------
    >>> collector = MetricsCollector(ring_size=5000)
    >>> with collector.measure("detect"):
    ...     run_detection(tx)
    >>> print(collector.summary())
    """

    def __init__(
        self,
        ring_size: int = _DEFAULT_RING_SIZE,
        max_file_bytes: int = _DEFAULT_MAX_FILE_BYTES,
    ) -> None:
        self._ring_size = ring_size
        self._max_file_bytes = max_file_bytes
        self._samples: collections.deque[MetricSample] = collections.deque(maxlen=ring_size)
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(self, sample: MetricSample) -> None:
        """Append a pre-built sample to the ring buffer."""
        with self._lock:
            self._samples.append(sample)

    def measure(self, operation: str):
        """Context manager that records latency + memory delta for *operation*.

        KeyboardInterrupt and SystemExit are re-raised after the sample is
        saved so the runtime can still shut down cleanly.
        """
        return _MeasureContext(self, operation)

    def summary(self) -> dict:
        """Return aggregate statistics over all samples in the ring buffer."""
        with self._lock:
            samples = list(self._samples)

        if not samples:
            return {"count": 0}

        latencies = [s.latency_s for s in samples]
        mem_deltas = [s.memory_delta_bytes for s in samples]
        errors = sum(1 for s in samples if s.error)

        ops: dict[str, list[float]] = {}
        for s in samples:
            ops.setdefault(s.operation, []).append(s.latency_s)

        return {
            "count": len(samples),
            "error_count": errors,
            "latency_s": {
                "min": min(latencies),
                "max": max(latencies),
                "mean": sum(latencies) / len(latencies),
                "p50": _percentile(latencies, 50),
                "p95": _percentile(latencies, 95),
                "p99": _percentile(latencies, 99),
            },
            "memory_delta_bytes": {
                "min": min(mem_deltas),
                "max": max(mem_deltas),
                "mean": int(sum(mem_deltas) / len(mem_deltas)),
            },
            "by_operation": {
                op: {
                    "count": len(lats),
                    "mean_latency_s": sum(lats) / len(lats),
                }
                for op, lats in ops.items()
            },
        }

    def export_json(self, path: str | Path, *, append: bool = False) -> None:
        """Export all ring-buffer samples to a JSON file.

        Parameters
        ----------
        path:
            Destination file path.
        append:
            If ``True``, append to an existing file (line-delimited JSON).
            If ``False`` (default), overwrite the file.

        Raises
        ------
        OverflowError
            If the file would exceed ``max_file_bytes``.
        """
        with self._lock:
            samples = [s.to_dict() for s in self._samples]

        payload = json.dumps(samples, separators=(",", ":")) + "\n"
        encoded = payload.encode("utf-8")

        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        mode = "ab" if append else "wb"
        existing = dest.stat().st_size if (append and dest.exists()) else 0
        if existing + len(encoded) > self._max_file_bytes:
            raise OverflowError(
                f"Metrics export would exceed max_file_bytes={self._max_file_bytes}."
            )

        with dest.open(mode) as fh:
            fh.write(encoded)
            fh.flush()
            os.fsync(fh.fileno())

    def clear(self) -> None:
        """Remove all samples from the ring buffer."""
        with self._lock:
            self._samples.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._samples)


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class _MeasureContext:
    def __init__(self, collector: MetricsCollector, operation: str) -> None:
        self._collector = collector
        self._operation = operation
        self._t0: float = 0.0
        self._mem_before: int = 0

    def __enter__(self) -> _MeasureContext:
        self._t0 = time.perf_counter()
        try:
            if not tracemalloc.is_tracing():
                tracemalloc.start()
            snap = tracemalloc.take_snapshot()
            self._mem_before = sum(s.size for s in snap.statistics("lineno"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("tracemalloc unavailable: %s", exc)
            self._mem_before = 0
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        latency = time.perf_counter() - self._t0
        mem_after = 0
        try:
            snap = tracemalloc.take_snapshot()
            mem_after = sum(s.size for s in snap.statistics("lineno"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("tracemalloc snapshot failed: %s", exc)

        is_interrupt = exc_type in (KeyboardInterrupt, SystemExit)
        is_error = exc_type is not None

        sample = MetricSample(
            operation=self._operation,
            latency_s=round(latency, 9),
            memory_delta_bytes=mem_after - self._mem_before,
            error=is_error,
        )
        self._collector.record(sample)

        if is_interrupt:
            return False  # re-raise KeyboardInterrupt / SystemExit

        return False  # always propagate other exceptions


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


def track_metrics(
    collector: MetricsCollector, operation: str | None = None
) -> Callable[[F], F]:
    """Decorator that records latency + memory for each call to the wrapped function.

    Parameters
    ----------
    collector:
        A ``MetricsCollector`` instance.
    operation:
        Label for the operation.  Defaults to ``func.__name__``.

    Example
    -------
    >>> @track_metrics(collector)
    ... def detect(tx):
    ...     ...
    """

    def decorator(func: F) -> F:
        op_name = operation or func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with collector.measure(op_name):
                return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def _percentile(data: list[float], pct: int) -> float:
    if not data:
        return 0.0
    sorted_data = sorted(data)
    idx = (len(sorted_data) - 1) * pct / 100
    lo, hi = int(idx), min(int(idx) + 1, len(sorted_data) - 1)
    frac = idx - lo
    return sorted_data[lo] + frac * (sorted_data[hi] - sorted_data[lo])
