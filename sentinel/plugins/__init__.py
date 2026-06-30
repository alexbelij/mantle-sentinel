"""Mantle Sentinel — optional plugins.

Each plugin is a self-contained module that can be imported independently.
No plugin modifies core sentinel code; all integration is opt-in.

Available plugins:
    alert_log  — Persistent append-only alert log (NDJSON + SQLite index)
    metrics    — Per-transaction latency/memory performance tracking
"""

from .alert_log import AlertLog
from .metrics import MetricsCollector, track_metrics

__all__ = ["AlertLog", "MetricsCollector", "track_metrics"]
