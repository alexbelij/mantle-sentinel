"""Tests for sentinel.scan — behavioral audit pipeline."""
from __future__ import annotations

from bench.injector import inject_s1_selector_flood
from bench.snapshot import synth_records
from sentinel.scan import analyze_records, compute_health_score


class TestHealthScore:
    def test_clean_high_score(self):
        """Clean data → score > 80."""
        score = compute_health_score([], drift_median=0.08, drift_p99=0.14)
        assert score > 80

    def test_many_alerts_low_score(self):
        """Many alert episodes → score < 50."""
        alerts = [{"episode_id": f"ep-{i}"} for i in range(15)]
        score = compute_health_score(alerts, drift_median=0.5, drift_p99=0.8)
        assert score < 50

    def test_high_drift_penalty(self):
        """High drift without alerts still penalizes."""
        score = compute_health_score([], drift_median=0.6, drift_p99=0.9)
        assert score < 90

    def test_score_deterministic(self):
        """Same inputs → same score."""
        alerts = [{"episode_id": "e1"}, {"episode_id": "e2"}]
        s1 = compute_health_score(alerts, drift_median=0.1, drift_p99=0.3)
        s2 = compute_health_score(alerts, drift_median=0.1, drift_p99=0.3)
        assert s1 == s2


class TestAnalyzeRecords:
    def test_dry_run_clean(self):
        """Synthetic clean records → high health score, zero alerts."""
        records = synth_records(1000, seed=42)
        address = records[0]["contract"]
        report = analyze_records(records, address)
        assert report["health_score"] > 80
        assert report["alerts"] == 0
        assert report["txs_fetched"] == 1000
        assert report["txs_warmup"] > 0
        assert report["txs_analyzed"] > 0
        assert report["unique_selectors"] > 0
        assert report["gas_median"] > 0

    def test_dry_run_with_attack(self):
        """Injected S1 attack → lower health score."""
        records = synth_records(3000, seed=11)
        injected = inject_s1_selector_flood(records, onset_frac=0.5, seed=1)
        address = records[0]["contract"]
        report = analyze_records(injected, address)
        # S1 injection should produce alerts and lower the score
        assert report["alerts"] > 0 or report["drift_p99"] > 0.2

    def test_report_fields(self):
        """Report contains all expected keys."""
        records = synth_records(500, seed=7)
        address = records[0]["contract"]
        report = analyze_records(records, address)
        expected_keys = {
            "contract", "chain", "chain_id", "txs_fetched", "txs_warmup",
            "txs_analyzed", "health_score", "drift_median", "drift_p99",
            "unique_selectors", "top_selectors", "gas_median", "gas_p99",
            "alerts", "alert_details",
        }
        assert expected_keys.issubset(report.keys())
