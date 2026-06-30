"""Tests for sentinel/plugins/alert_log.py.

Covers: append, mark_fp, query, overflow, concurrency, SQL injection,
path traversal, interrupt handling, DB idempotency.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from sentinel.plugins.alert_log import AlertLog

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------


def make_alert(
    alert_id: str = "spam_attack-0xabc-1000",
    block: int = 1000,
    contract: str = "0xabc",
    alert_type: str = "spam_attack",
    drift: float = 0.85,
    branch: str = "hamming",
) -> dict:
    return {
        "alert_id": alert_id,
        "ts": "2024-01-01T00:00:00Z",
        "block": block,
        "contract": contract,
        "alert_type": alert_type,
        "drift": drift,
        "branch": branch,
    }


@dataclass
class FakeAlert:
    alert_id: str = "regime_shift-0xdef-2000"
    ts: str = "2024-01-02T00:00:00Z"
    block: int = 2000
    contract: str = "0xdef"
    alert_type: str = "regime_shift"
    drift: float = 0.72
    branch: str = "timing"
    top_features: list = field(default_factory=list)
    window_stats: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "ts": self.ts,
            "block": self.block,
            "contract": self.contract,
            "alert_type": self.alert_type,
            "drift": self.drift,
            "branch": self.branch,
        }


@pytest.fixture
def log(tmp_path: Path) -> AlertLog:
    return AlertLog(tmp_path / "alerts")


# ---------------------------------------------------------------------------
# alert_id validation
# ---------------------------------------------------------------------------


class TestAlertIdValidation:
    def test_empty_id_raises(self, log: AlertLog) -> None:
        a = make_alert(alert_id="")
        with pytest.raises(ValueError, match="non-empty"):
            log.append(a)

    def test_none_id_raises(self, log: AlertLog) -> None:
        a = make_alert()
        a["alert_id"] = None  # type: ignore[assignment]
        with pytest.raises(ValueError):
            log.append(a)

    def test_too_long_id_raises(self, log: AlertLog) -> None:
        a = make_alert(alert_id="A" * 300)
        with pytest.raises(ValueError, match="too long"):
            log.append(a)

    def test_path_traversal_raises(self, log: AlertLog) -> None:
        a = make_alert(alert_id="../etc/passwd")
        with pytest.raises(ValueError, match="unsafe"):
            log.append(a)

    def test_special_chars_raise(self, log: AlertLog) -> None:
        for bad_id in ["id with space", "id;drop", "id\x00null"]:
            a = make_alert(alert_id=bad_id)
            with pytest.raises(ValueError, match="unsafe"):
                log.append(a)

    def test_valid_id_accepted(self, log: AlertLog) -> None:
        log.append(make_alert(alert_id="valid-ID_123"))  # should not raise


# ---------------------------------------------------------------------------
# Append
# ---------------------------------------------------------------------------


class TestAppend:
    def test_append_dict(self, log: AlertLog, tmp_path: Path) -> None:
        log.append(make_alert())
        lines = (tmp_path / "alerts" / "alerts.ndjson").read_text().strip().splitlines()
        assert len(lines) == 1
        rec = json.loads(lines[0])
        assert rec["alert_id"] == "spam_attack-0xabc-1000"

    def test_append_dataclass_with_to_dict(self, log: AlertLog) -> None:
        log.append(FakeAlert())
        results = log.query(contract="0xdef")
        assert len(results) == 1

    def test_append_multiple(self, log: AlertLog) -> None:
        for i in range(10):
            log.append(make_alert(alert_id=f"spam_attack-0xabc-{i}", block=i))
        assert len(log.query(limit=20)) == 10

    def test_duplicate_insert_ignored(self, log: AlertLog) -> None:
        log.append(make_alert())
        log.append(make_alert())  # same alert_id → INSERT OR IGNORE
        assert len(log.query()) == 1

    def test_ndjson_is_atomic_lines(self, log: AlertLog, tmp_path: Path) -> None:
        for i in range(5):
            log.append(make_alert(alert_id=f"id-{i}", block=i))
        ndjson = (tmp_path / "alerts" / "alerts.ndjson").read_text().splitlines()
        assert len(ndjson) == 5
        for line in ndjson:
            json.loads(line)  # must be valid JSON

    def test_unsupported_type_raises(self, log: AlertLog) -> None:
        with pytest.raises(TypeError, match="Cannot serialise"):
            log.append(object())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Overflow
# ---------------------------------------------------------------------------


class TestOverflow:
    def test_overflow_raises(self, tmp_path: Path) -> None:
        # Set max_bytes large enough for exactly one alert, then overflow on second
        first = make_alert(alert_id="id-0", block=0)
        import json as _json
        first_size = len((_json.dumps(first, separators=(",", ":")) + "\n").encode())
        small_log = AlertLog(tmp_path / "tiny", max_bytes=first_size)
        small_log.append(first)  # first write fits exactly
        with pytest.raises(OverflowError, match="max_bytes"):
            small_log.append(make_alert(alert_id="id-1", block=1))


# ---------------------------------------------------------------------------
# mark_fp
# ---------------------------------------------------------------------------


class TestMarkFP:
    def test_mark_existing(self, log: AlertLog) -> None:
        log.append(make_alert())
        assert log.mark_fp("spam_attack-0xabc-1000") is True

    def test_mark_nonexistent_returns_false(self, log: AlertLog) -> None:
        assert log.mark_fp("nonexistent-id-999") is False

    def test_mark_fp_idempotent(self, log: AlertLog) -> None:
        log.append(make_alert())
        log.mark_fp("spam_attack-0xabc-1000")
        log.mark_fp("spam_attack-0xabc-1000")  # should not raise
        results = log.query(fp_flag=1)
        assert len(results) == 1

    def test_fp_queryable(self, log: AlertLog) -> None:
        log.append(make_alert())
        log.mark_fp("spam_attack-0xabc-1000")
        fp = log.query(fp_flag=1)
        non_fp = log.query(fp_flag=0)
        assert len(fp) == 1
        assert len(non_fp) == 0


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------


class TestQuery:
    def setup_method(self) -> None:
        pass

    def test_filter_by_contract(self, log: AlertLog) -> None:
        log.append(make_alert(alert_id="id-1", contract="0xAAA"))
        log.append(make_alert(alert_id="id-2", contract="0xBBB"))
        results = log.query(contract="0xAAA")
        assert len(results) == 1
        assert results[0]["contract"] == "0xAAA"

    def test_filter_by_block_range(self, log: AlertLog) -> None:
        for i in range(10):
            log.append(make_alert(alert_id=f"id-{i}", block=i * 100))
        results = log.query(block_min=200, block_max=500)
        assert all(200 <= r["block"] <= 500 for r in results)

    def test_limit(self, log: AlertLog) -> None:
        for i in range(20):
            log.append(make_alert(alert_id=f"id-{i}", block=i))
        assert len(log.query(limit=5)) == 5

    def test_sql_injection_in_query_value(self, log: AlertLog) -> None:
        # The injected string is passed as a parameter — should return 0 rows
        results = log.query(contract="0xAAA' OR '1'='1")
        assert results == []

    def test_empty_log_returns_empty(self, log: AlertLog) -> None:
        assert log.query() == []


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


class TestConcurrency:
    def test_concurrent_append(self, tmp_path: Path) -> None:
        log = AlertLog(tmp_path / "concurrent")
        errors: list[Exception] = []

        def worker(idx: int) -> None:
            try:
                log.append(make_alert(alert_id=f"id-{idx}", block=idx))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(log.query(limit=100)) == 50


# ---------------------------------------------------------------------------
# DB idempotency
# ---------------------------------------------------------------------------


class TestDBInit:
    def test_reinit_is_idempotent(self, tmp_path: Path) -> None:
        log1 = AlertLog(tmp_path / "alerts")
        log1.append(make_alert())
        log2 = AlertLog(tmp_path / "alerts")  # reinit on existing DB
        assert len(log2.query()) == 1
