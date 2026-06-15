"""Tests for sentinel.client — Python SDK."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from bench.snapshot import synth_records
from sentinel.client import ScanReport, SentinelClient, SentinelHealthError
from sentinel.scan import analyze_records


def _make_report(address: str = "0xtest", health: int = 85) -> dict:
    """Build a minimal raw report dict for mocking."""
    records = synth_records(1000, seed=42)
    addr = records[0]["contract"]
    raw = analyze_records(records, addr)
    raw["contract"] = address
    raw["health_score"] = health
    return raw


class TestScanReport:
    def test_dataclass_creation(self):
        r = ScanReport(
            address="0xabc",
            health_score=83,
            drift_median=0.22,
            drift_p99=0.73,
            alert_count=4,
        )
        assert r.address == "0xabc"
        assert r.health_score == 83

    def test_is_healthy_true(self):
        r = ScanReport(address="0x1", health_score=70, drift_median=0.1, drift_p99=0.2, alert_count=0)
        assert r.is_healthy is True

    def test_is_healthy_false(self):
        r = ScanReport(address="0x1", health_score=69, drift_median=0.1, drift_p99=0.2, alert_count=0)
        assert r.is_healthy is False

    def test_to_dict(self):
        r = ScanReport(address="0x1", health_score=80, drift_median=0.1, drift_p99=0.2, alert_count=0)
        d = r.to_dict()
        assert isinstance(d, dict)
        assert d["address"] == "0x1"
        assert d["health_score"] == 80

    def test_serialization_json(self):
        r = ScanReport(address="0x1", health_score=80, drift_median=0.1, drift_p99=0.2, alert_count=0)
        s = r.to_json()
        parsed = json.loads(s)
        assert parsed["health_score"] == 80


class TestSentinelClient:
    def test_defaults(self):
        c = SentinelClient()
        assert "mantle" in c.rpc_url
        assert "routescan" in c.explorer_api

    def test_scan_mocked(self):
        raw = _make_report("0xtest", 85)
        with patch("sentinel.scan.scan_contract", return_value=raw):
            c = SentinelClient()
            report = c.scan("0xtest", explain=False)
        assert isinstance(report, ScanReport)
        assert report.health_score == 85
        assert report.address == "0xtest"

    def test_scan_no_zai(self):
        raw = _make_report("0xtest", 85)
        with patch("sentinel.scan.scan_contract", return_value=raw) as mock_scan:
            c = SentinelClient(zai_api_key=None)
            report = c.scan("0xtest", explain=True)
        # explain=True but no key → scan_contract called with explain=False
        mock_scan.assert_called_once_with("0xtest", n_txs=5000, explain=False)
        assert report.z_ai_brief is None

    def test_min_health_pass(self):
        raw = _make_report("0xtest", 85)
        with patch("sentinel.scan.scan_contract", return_value=raw):
            c = SentinelClient()
            report = c.scan("0xtest", explain=False, min_health=60)
        assert report.health_score >= 60

    def test_min_health_fail(self):
        raw = _make_report("0xtest", 40)
        with patch("sentinel.scan.scan_contract", return_value=raw):
            c = SentinelClient()
            with pytest.raises(SentinelHealthError) as exc_info:
                c.scan("0xtest", explain=False, min_health=60)
        assert exc_info.value.score == 40
        assert exc_info.value.threshold == 60

    def test_scan_multiple(self):
        raw1 = _make_report("0xa", 83)
        raw2 = _make_report("0xb", 74)
        with patch("sentinel.scan.scan_contract", side_effect=[raw1, raw2]):
            c = SentinelClient()
            reports = c.scan_multiple(["0xa", "0xb"], explain=False)
        assert len(reports) == 2
        assert reports[0].address == "0xa"
        assert reports[1].address == "0xb"
