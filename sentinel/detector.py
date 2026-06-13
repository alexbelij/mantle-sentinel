"""Tier 4 — StaticThresholdDetector (MVP_MATH_SPEC §4).

    alert iff drift(t) > θ for k consecutive evaluations (hysteresis); θ = 0.65, k = 3.
    Episode collapsing: alerts within 10 min merge into one episode.

BOCPD (T-17) is a deferred drop-in behind this same interface (process → Trigger | None).
"""
from __future__ import annotations

from dataclasses import dataclass

from sentinel.config import K_HYSTERESIS, THETA
from sentinel.episodes import EpisodeTracker


@dataclass(frozen=True)
class Trigger:
    ts: float
    drift: float
    episode_id: str
    new_episode: bool


class StaticThresholdDetector:
    def __init__(
        self,
        theta: float = THETA,
        k: int = K_HYSTERESIS,
        episode_prefix: str = "regime",
    ):
        self.theta = theta
        self.k = k
        self._consec = 0
        self._fired = False  # suppress re-fire within one continuous over-θ run
        self._episodes = EpisodeTracker(prefix=episode_prefix)

    def process(self, drift: float, ts: float) -> Trigger | None:
        if drift > self.theta:
            self._consec += 1
        else:
            # T-22 fix: reset _fired when drift drops below threshold so that
            # a *new* episode (after the current one ends) can be detected.
            # Without this reset, _fired stays True forever after the first
            # episode and silently suppresses all subsequent detections.
            self._consec = 0
            self._fired = False
            return None

        if self._consec >= self.k and not self._fired:
            self._fired = True
            episode_id, is_new = self._episodes.assign(ts)
            return Trigger(ts=ts, drift=drift, episode_id=episode_id, new_episode=is_new)
        return None

    def reset(self) -> None:
        """Explicitly reset detector state (e.g. when starting a new evaluation run)."""
        self._consec = 0
        self._fired = False
