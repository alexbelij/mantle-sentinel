"""Tier 0 — timing spam pre-filter (MVP_MATH_SPEC §0).

    MIN_INTERVAL = 0.001-quantile of inter-tx intervals Δt on the warm-up split (floor 0).
    spam_attack iff the last k_spam (=20) consecutive intervals are all < MIN_INTERVAL.
    10-min episode collapsing (applied at the alert layer).

Spam-flagged transactions are excluded everywhere — window bundles, prototype,
rolling drift history, and entropy baselines (baseline-poisoning protection).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sentinel.config import K_SPAM, MIN_INTERVAL_Q


@dataclass(frozen=True)
class SpamResult:
    is_spam: bool      # this tx is inside a sustained spam burst ⇒ exclude from baselines
    alert: bool        # a spam_attack alert fires on this tx (burst onset)


class SpamPrefilter:
    def __init__(self, k_spam: int = K_SPAM, min_interval_q: float = MIN_INTERVAL_Q):
        self.k_spam = k_spam
        self.min_interval_q = min_interval_q
        self.min_interval: float = 0.0
        self._consec = 0

    def fit(self, intervals: list[float]) -> SpamPrefilter:
        if intervals:
            q = float(np.quantile(np.asarray(intervals, dtype=float), self.min_interval_q))
            self.min_interval = max(q, 0.0)
        return self

    def process(self, dt: float) -> SpamResult:
        """Feed one inter-tx interval. Returns spam/alert flags for this tx."""
        if dt < self.min_interval:
            self._consec += 1
        else:
            self._consec = 0
        is_spam = self._consec >= self.k_spam
        # Fire exactly once at burst onset (the instant the run reaches k_spam);
        # downstream 10-min episode collapsing merges nearby onsets.
        alert = self._consec == self.k_spam
        return SpamResult(is_spam=is_spam, alert=alert)
