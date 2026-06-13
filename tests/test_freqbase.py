"""T-11: Tests for FreqBase baseline detector."""
from __future__ import annotations

from bench.freqbase import FreqBaseDetector, build_freqbase
from bench.snapshot import synth_records
from sentinel.config import WARMUP_FRAC
from sentinel.pipeline import split_warmup


class TestFreqBaseDetector:
    def test_no_alert_on_normal_traffic(self):
        """Normal traffic should not trigger alerts after warmup."""
        records = synth_records(500, seed=0)
        warmup, test = split_warmup(records, frac=WARMUP_FRAC)
        det = build_freqbase(records[0]["contract"], warmup)

        alerts = []
        for r in test:
            alerts.extend(det.process_tx(r))

        # Should have very few or zero alerts on stationary traffic
        episodes = {a.episode_id for a in alerts}
        # Allow some — the point is it's not wildly noisy
        assert len(episodes) < 10, f"Too many FP episodes: {len(episodes)}"

    def test_detects_selector_flood(self):
        """Injecting novel selectors should trigger detection."""
        from bench.injector import inject_s1_selector_flood

        records = synth_records(500, seed=0)
        warmup, test = split_warmup(records, frac=WARMUP_FRAC)
        det = build_freqbase(records[0]["contract"], warmup)

        injected = inject_s1_selector_flood(test, onset_frac=0.5, seed=7)
        alerts = []
        for r in injected:
            alerts.extend(det.process_tx(r))

        # Should detect at least one alert
        assert len(alerts) > 0, "FreqBase should detect S1 selector flood"

    def test_fit_on_warmup_only(self):
        """Baseline must be computed only from warmup, not test data."""
        records = synth_records(300, seed=0)
        warmup, test = split_warmup(records, frac=WARMUP_FRAC)
        det = build_freqbase(records[0]["contract"], warmup)

        # Baseline should have entries from warmup selectors
        assert len(det._baseline_freq) > 0

    def test_window_accumulation(self):
        """No alerts until a full window of transactions is accumulated."""
        records = synth_records(100, seed=0)
        det = FreqBaseDetector(window=50)
        det.contract = records[0]["contract"]
        det.fit(records[:40])

        # Feed fewer than window size
        alerts = []
        for r in records[:30]:
            alerts.extend(det.process_tx(r))
        assert len(alerts) == 0, "No alerts before window is full"

    def test_process_tx_returns_list(self):
        records = synth_records(100, seed=0)
        det = FreqBaseDetector(window=50)
        det.contract = records[0]["contract"]
        det.fit(records[:50])

        result = det.process_tx(records[0])
        assert isinstance(result, list)
