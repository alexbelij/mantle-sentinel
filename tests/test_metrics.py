"""Tests for sentinel/plugins/metrics.py.

Covers: decorator, context manager, ring-buffer eviction, overflow,
KeyboardInterrupt/SystemExit handling, concurrency, export, summary stats.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path

import pytest

from sentinel.plugins.metrics import MetricSample, MetricsCollector, track_metrics


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def collector() -> MetricsCollector:
    return MetricsCollector()


# ---------------------------------------------------------------------------
# MetricSample
# ---------------------------------------------------------------------------


class TestMetricSample:
    def test_to_dict(self) -> None:
        s = MetricSample("op", 0.5, 1024, error=False)
        d = s.to_dict()
        assert d == {"operation": "op", "latency_s": 0.5, "memory_delta_bytes": 1024, "error": False}

    def test_error_flag(self) -> None:
        s = MetricSample("op", 0.1, 0, error=True)
        assert s.to_dict()["error"] is True


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------


class TestMeasureContext:
    def test_records_sample(self, collector: MetricsCollector) -> None:
        with collector.measure("test_op"):
            pass
        assert len(collector) == 1
        summary = collector.summary()
        assert summary["count"] == 1
        assert "test_op" in summary["by_operation"]

    def test_latency_positive(self, collector: MetricsCollector) -> None:
        import time
        with collector.measure("slow"):
            time.sleep(0.05)
        summary = collector.summary()
        assert summary["latency_s"]["min"] >= 0.04

    def test_exception_propagated(self, collector: MetricsCollector) -> None:
        with pytest.raises(ValueError):
            with collector.measure("failing_op"):
                raise ValueError("test error")
        assert len(collector) == 1
        assert collector.summary()["error_count"] == 1

    def test_keyboard_interrupt_propagated(self, collector: MetricsCollector) -> None:
        with pytest.raises(KeyboardInterrupt):
            with collector.measure("interrupted"):
                raise KeyboardInterrupt
        assert len(collector) == 1  # sample still recorded

    def test_system_exit_propagated(self, collector: MetricsCollector) -> None:
        with pytest.raises(SystemExit):
            with collector.measure("sysexit"):
                raise SystemExit(0)
        assert len(collector) == 1


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


class TestTrackMetrics:
    def test_decorator_records(self, collector: MetricsCollector) -> None:
        @track_metrics(collector)
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        assert result == 5
        assert len(collector) == 1

    def test_decorator_uses_function_name(self, collector: MetricsCollector) -> None:
        @track_metrics(collector)
        def my_func() -> None:
            pass

        my_func()
        summary = collector.summary()
        assert "my_func" in summary["by_operation"]

    def test_decorator_custom_operation_name(self, collector: MetricsCollector) -> None:
        @track_metrics(collector, operation="custom_op")
        def anything() -> None:
            pass

        anything()
        assert "custom_op" in collector.summary()["by_operation"]

    def test_decorator_propagates_exception(self, collector: MetricsCollector) -> None:
        @track_metrics(collector)
        def boom() -> None:
            raise RuntimeError("boom")

        with pytest.raises(RuntimeError):
            boom()
        assert collector.summary()["error_count"] == 1

    def test_decorator_preserves_return_value(self, collector: MetricsCollector) -> None:
        @track_metrics(collector)
        def get_list() -> list:
            return [1, 2, 3]

        assert get_list() == [1, 2, 3]


# ---------------------------------------------------------------------------
# Ring buffer
# ---------------------------------------------------------------------------


class TestRingBuffer:
    def test_eviction(self) -> None:
        c = MetricsCollector(ring_size=10)
        for i in range(30):
            with c.measure(f"op_{i}"):
                pass
        assert len(c) == 10

    def test_default_size(self, collector: MetricsCollector) -> None:
        assert len(collector) == 0
        for _ in range(5):
            with collector.measure("x"):
                pass
        assert len(collector) == 5

    def test_clear(self, collector: MetricsCollector) -> None:
        with collector.measure("a"):
            pass
        collector.clear()
        assert len(collector) == 0
        assert collector.summary() == {"count": 0}


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------


class TestSummary:
    def test_empty_summary(self, collector: MetricsCollector) -> None:
        assert collector.summary() == {"count": 0}

    def test_summary_fields(self, collector: MetricsCollector) -> None:
        for _ in range(10):
            with collector.measure("process"):
                pass
        s = collector.summary()
        assert s["count"] == 10
        assert "min" in s["latency_s"]
        assert "p95" in s["latency_s"]
        assert "mean" in s["memory_delta_bytes"]

    def test_multiple_operations(self, collector: MetricsCollector) -> None:
        for op in ["encode", "detect", "encode"]:
            with collector.measure(op):
                pass
        s = collector.summary()
        assert s["by_operation"]["encode"]["count"] == 2
        assert s["by_operation"]["detect"]["count"] == 1


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class TestExportJson:
    def test_export_creates_file(self, collector: MetricsCollector, tmp_path: Path) -> None:
        with collector.measure("op"):
            pass
        dest = tmp_path / "metrics.json"
        collector.export_json(dest)
        assert dest.exists()
        data = json.loads(dest.read_text().strip())
        assert len(data) == 1
        assert data[0]["operation"] == "op"

    def test_export_overwrite(self, collector: MetricsCollector, tmp_path: Path) -> None:
        dest = tmp_path / "metrics.json"
        with collector.measure("a"):
            pass
        collector.export_json(dest)
        collector.clear()
        with collector.measure("b"):
            pass
        collector.export_json(dest)  # overwrite
        data = json.loads(dest.read_text().strip())
        assert len(data) == 1
        assert data[0]["operation"] == "b"

    def test_export_append(self, collector: MetricsCollector, tmp_path: Path) -> None:
        dest = tmp_path / "metrics.json"
        with collector.measure("x"):
            pass
        collector.export_json(dest, append=True)
        collector.export_json(dest, append=True)
        lines = dest.read_text().strip().splitlines()
        assert len(lines) == 2

    def test_export_overflow(self, tmp_path: Path) -> None:
        c = MetricsCollector(max_file_bytes=10)
        with c.measure("x"):
            pass
        dest = tmp_path / "metrics.json"
        with pytest.raises(OverflowError, match="max_file_bytes"):
            c.export_json(dest)

    def test_export_creates_parent_dirs(self, collector: MetricsCollector, tmp_path: Path) -> None:
        dest = tmp_path / "a" / "b" / "c" / "metrics.json"
        with collector.measure("op"):
            pass
        collector.export_json(dest)
        assert dest.exists()


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


class TestConcurrency:
    def test_concurrent_measure(self) -> None:
        c = MetricsCollector(ring_size=1000)
        errors: list[Exception] = []

        def worker(op: str, n: int) -> None:
            try:
                for _ in range(n):
                    with c.measure(op):
                        pass
            except Exception as exc:
                errors.append(exc)

        threads = [
            threading.Thread(target=worker, args=(f"op_{i % 5}", 10))
            for i in range(50)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(c) <= 1000
        assert c.summary()["count"] > 0
