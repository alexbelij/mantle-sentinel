"""
sentinel/plugins/dedup.py
=========================
Isolated alert-deduplication plugin — does NOT touch pipeline.py / bocpd.py / watch.py.

Usage (opt-in, one line in your runner):
    from sentinel.plugins.dedup import AlertDeduplicator
    dedup = AlertDeduplicator(ttl_seconds=600)
    if dedup.is_new(alert_dict):
        send_to_telegram(alert_dict)

The plugin is completely standalone. Import it where you need it, or ignore it.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any


class AlertDeduplicator:
    """
    Thread-safe in-memory deduplicator for Sentinel alerts.

    An alert is considered a *duplicate* if an alert with the same
    ``window_id`` (or, as fallback, the same content hash) was already
    seen within *ttl_seconds*.

    Parameters
    ----------
    ttl_seconds : int
        How long to remember a seen alert (default 600 = 10 min).
    key_field : str
        Alert dict key used as the dedup key (default ``"window_id"``).
        If the field is absent the plugin falls back to a SHA-256 of
        the full payload so it always works regardless of alert shape.

    Example
    -------
    >>> dedup = AlertDeduplicator(ttl_seconds=300)
    >>> alert = {"window_id": "0xabc-42", "drift_score": 0.75}
    >>> dedup.is_new(alert)   # True  — first time we see this window
    True
    >>> dedup.is_new(alert)   # False — duplicate within TTL
    False
    """

    def __init__(self, ttl_seconds: int = 600, key_field: str = "window_id") -> None:
        self._ttl = ttl_seconds
        self._key_field = key_field
        self._seen: dict[str, float] = {}   # key → first-seen timestamp
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_new(self, alert: dict[str, Any]) -> bool:
        """
        Return *True* if this alert has NOT been seen within the TTL
        window, and register it. Return *False* if it is a duplicate.
        """
        key = self._extract_key(alert)
        now = time.monotonic()

        with self._lock:
            self._evict(now)
            if key in self._seen:
                return False
            self._seen[key] = now
            return True

    def mark_seen(self, alert: dict[str, Any]) -> None:
        """Explicitly mark an alert as seen (without checking)."""
        key = self._extract_key(alert)
        with self._lock:
            self._seen[key] = time.monotonic()

    def reset(self) -> None:
        """Clear all dedup state (useful in tests)."""
        with self._lock:
            self._seen.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._seen)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _extract_key(self, alert: dict[str, Any]) -> str:
        if self._key_field in alert:
            return str(alert[self._key_field])
        # Fallback: stable hash of the full payload
        raw = json.dumps(alert, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _evict(self, now: float) -> None:
        """Remove expired entries (called while lock is held)."""
        cutoff = now - self._ttl
        expired = [k for k, ts in self._seen.items() if ts < cutoff]
        for k in expired:
            del self._seen[k]
