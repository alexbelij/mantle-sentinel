"""T-10: Tests for detection scorer."""
from __future__ import annotations

from bench.scorer import detection_delay, false_positive_rate
from sentinel.alert import Alert


def _make_alert(block: int, episode_id: str = "ep-1", alert_type: str = "regime_shift") -> Alert:
    return Alert(
        alert_id=f"test-alert-{block}",
        ts="2026-01-01T00:00:00Z",
        block=block,
        contract="0xtest",
        alert_type=alert_type,
        drift=0.9,
        branch="hamming",
        episode_id=episode_id,
    )


class TestDetectionDelay:
    def test_single_alert_delay(self):
        alerts = [_make_alert(block=105)]
        result = detection_delay(alerts, inject_start_block=100)
        assert result["delay_blocks_median"] == 5.0
        assert result["delay_blocks_p90"] == 5.0
        assert result["missed"] == 0

    def test_multiple_alerts(self):
        alerts = [_make_alert(block=102), _make_alert(block=106), _make_alert(block=110)]
        result = detection_delay(alerts, inject_start_block=100)
        assert result["delay_blocks_median"] == 6.0  # median of [2, 6, 10]
        assert result["missed"] == 0

    def test_missed_detection(self):
        # Alert fires 30 blocks after start (beyond 10-window = 20-block limit)
        alerts = [_make_alert(block=130)]
        result = detection_delay(alerts, inject_start_block=100)
        assert result["missed"] == 1

    def test_no_alerts(self):
        result = detection_delay([], inject_start_block=100)
        assert result["missed"] == 1
        assert result["delay_blocks_median"] == float("inf")

    def test_alert_before_injection_ignored(self):
        # Alerts before injection start should not count
        alerts = [_make_alert(block=90)]
        result = detection_delay(alerts, inject_start_block=100)
        assert result["missed"] == 1

    def test_zero_delay(self):
        alerts = [_make_alert(block=100)]
        result = detection_delay(alerts, inject_start_block=100)
        assert result["delay_blocks_median"] == 0.0
        assert result["missed"] == 0


class TestFalsePositiveRate:
    def test_no_alerts_zero_fp(self):
        result = false_positive_rate([], n_windows_clean=1000)
        assert result["fp_episodes_per_day"] == 0.0

    def test_single_episode(self):
        alerts = [_make_alert(block=100, episode_id="ep-1")]
        # 1000 windows × 4 sec/window = 4000 sec ≈ 0.0463 days
        result = false_positive_rate(alerts, n_windows_clean=1000)
        assert result["fp_episodes_per_day"] > 0

    def test_multiple_episodes(self):
        alerts = [
            _make_alert(block=100, episode_id="ep-1"),
            _make_alert(block=110, episode_id="ep-1"),  # same episode
            _make_alert(block=200, episode_id="ep-2"),  # different episode
        ]
        result = false_positive_rate(alerts, n_windows_clean=1000)
        # 2 episodes in 4000 seconds
        expected_days = 1000 * 4.0 / 86400.0
        expected_fp = 2.0 / expected_days
        assert abs(result["fp_episodes_per_day"] - round(expected_fp, 4)) < 0.01

    def test_zero_windows(self):
        result = false_positive_rate([], n_windows_clean=0)
        assert result["fp_episodes_per_day"] == 0.0

    def test_episode_deduplication(self):
        # 5 alerts all in same episode → counts as 1 episode
        alerts = [_make_alert(block=100 + i, episode_id="ep-1") for i in range(5)]
        result = false_positive_rate(alerts, n_windows_clean=21600)  # ~1 day
        assert result["fp_episodes_per_day"] > 0
        assert result["fp_episodes_per_day"] < 2.0  # just 1 episode
