"""T-11: FreqBase — frequency-based baseline detector for AB3 comparison.

A simple baseline that tracks selector frequencies per window and alerts when
any selector's frequency exceeds k × its baseline (warmup) frequency.

Same interface as the Sentinel pipeline: process_tx(tx) → list[Alert] | None.
Used to produce the AB3 comparison table (Sentinel vs FreqBase).
"""
from __future__ import annotations

from collections import Counter

from sentinel.alert import Alert, iso_ts, make_alert_id
from sentinel.config import WINDOW
from sentinel.entropy import selector_of
from sentinel.episodes import EpisodeTracker


class FreqBaseDetector:
    """Frequency-based baseline: alert if any selector in the current window
    exceeds k × its average warmup-window frequency.

    Fit on warmup transactions, then score on held-out test stream.
    """

    def __init__(self, window: int = WINDOW, k: float = 3.0):
        self.window = window
        self.k = k
        self._baseline_freq: dict[str, float] = {}  # selector → avg freq per window
        self._buffer: list[dict] = []
        self._episodes = EpisodeTracker(prefix="freqbase")
        self.contract: str = ""

    def fit(self, warmup: list[dict]) -> FreqBaseDetector:
        """Compute per-selector average frequency across warmup windows."""
        if warmup:
            self.contract = warmup[0].get("contract", "").lower()

        # Count selectors per window
        window_counts: list[Counter] = []
        for i in range(0, len(warmup), self.window):
            chunk = warmup[i : i + self.window]
            if len(chunk) < self.window:
                break
            cnt: Counter = Counter()
            for r in chunk:
                sel = selector_of(r.get("calldata", "0x") or "0x")
                cnt[sel] += 1
            window_counts.append(cnt)

        if not window_counts:
            return self

        # Average frequency per selector across windows
        all_selectors: set[str] = set()
        for cnt in window_counts:
            all_selectors.update(cnt.keys())

        n_windows = len(window_counts)
        for sel in all_selectors:
            total = sum(cnt.get(sel, 0) for cnt in window_counts)
            self._baseline_freq[sel] = total / n_windows

        return self

    def process_tx(self, tx: dict) -> list[Alert]:
        """Process one transaction. Returns alerts when a full window is evaluated."""
        self._buffer.append(tx)
        if len(self._buffer) < self.window:
            return []

        # Evaluate window
        window_txs = self._buffer[-self.window :]
        alerts = self._evaluate_window(window_txs)

        # Slide by 1 (keep last window - 1 txs)
        if len(self._buffer) > self.window:
            self._buffer = self._buffer[-(self.window) :]

        return alerts

    def _evaluate_window(self, window_txs: list[dict]) -> list[Alert]:
        cnt: Counter = Counter()
        for r in window_txs:
            sel = selector_of(r.get("calldata", "0x") or "0x")
            cnt[sel] += 1

        alerts: list[Alert] = []
        last_tx = window_txs[-1]
        ts = float(last_tx.get("block_timestamp", 0))
        block = int(last_tx.get("block_number", 0))

        for sel, freq in cnt.items():
            baseline = self._baseline_freq.get(sel, 0.0)
            threshold = self.k * baseline if baseline > 0 else self.window * 0.5
            if freq > threshold:
                ep_id, is_new = self._episodes.assign(ts)
                alerts.append(
                    Alert(
                        alert_id=make_alert_id("freq_anomaly", self.contract, block),
                        ts=iso_ts(ts),
                        block=block,
                        contract=self.contract,
                        alert_type="freq_anomaly",
                        drift=round(freq / max(baseline, 1.0), 4),
                        branch="selector",
                        top_features=[],
                        window_stats={"selector": sel, "freq": freq, "baseline": baseline},
                        episode_id=ep_id,
                    )
                )
                break  # one alert per window max

        return alerts


def build_freqbase(contract: str, warmup: list[dict], k: float = 3.0) -> FreqBaseDetector:
    """Construct a FreqBase detector fitted on warmup data."""
    det = FreqBaseDetector(k=k)
    det.contract = contract.lower()
    det.fit(warmup)
    return det
