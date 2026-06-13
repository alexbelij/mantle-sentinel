"""Alert-episode collapsing (10-minute merge), shared by Tier 0/1/4 alerts.

Consecutive alerts within EPISODE_COLLAPSE_S of the previous one collapse into a
single episode — this matches how an on-call human experiences an incident and is
the unit used for the FP/contract-day metric (BENCHMARK_PROTOCOL §3.2).
"""
from __future__ import annotations

from sentinel.config import EPISODE_COLLAPSE_S


class EpisodeTracker:
    def __init__(self, prefix: str = "ep", collapse_s: float = EPISODE_COLLAPSE_S):
        self.prefix = prefix
        self.collapse_s = collapse_s
        self._last_ts: float | None = None
        self._count = 0

    def assign(self, ts: float) -> tuple[str, bool]:
        """Return (episode_id, is_new_episode) for an alert at unix-time `ts`."""
        if self._last_ts is None or (ts - self._last_ts) > self.collapse_s:
            self._count += 1
            is_new = True
        else:
            is_new = False
        self._last_ts = ts
        return f"{self.prefix}-{self._count}", is_new
