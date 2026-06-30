"""Tests for sentinel/plugins/dedup.py"""

from __future__ import annotations

import time

from sentinel.plugins.dedup import AlertDeduplicator


def test_first_alert_is_new():
    dedup = AlertDeduplicator()
    assert dedup.is_new({"window_id": "w1"}) is True


def test_duplicate_within_ttl_is_not_new():
    dedup = AlertDeduplicator(ttl_seconds=60)
    dedup.is_new({"window_id": "w1"})
    assert dedup.is_new({"window_id": "w1"}) is False


def test_different_window_ids_are_both_new():
    dedup = AlertDeduplicator()
    assert dedup.is_new({"window_id": "w1"}) is True
    assert dedup.is_new({"window_id": "w2"}) is True


def test_expired_alert_is_new_again():
    dedup = AlertDeduplicator(ttl_seconds=1)
    dedup.is_new({"window_id": "w1"})
    time.sleep(1.1)
    assert dedup.is_new({"window_id": "w1"}) is True


def test_fallback_hash_when_key_field_absent():
    dedup = AlertDeduplicator(key_field="window_id")
    alert = {"drift_score": 0.9}  # no window_id
    assert dedup.is_new(alert) is True
    assert dedup.is_new(alert) is False


def test_reset_clears_state():
    dedup = AlertDeduplicator()
    dedup.is_new({"window_id": "w1"})
    dedup.reset()
    assert dedup.is_new({"window_id": "w1"}) is True


def test_len_reflects_seen_count():
    dedup = AlertDeduplicator()
    assert len(dedup) == 0
    dedup.is_new({"window_id": "w1"})
    dedup.is_new({"window_id": "w2"})
    assert len(dedup) == 2


def test_mark_seen_prevents_future_is_new():
    dedup = AlertDeduplicator()
    alert = {"window_id": "w99"}
    dedup.mark_seen(alert)
    assert dedup.is_new(alert) is False


def test_thread_safety():
    import threading
    dedup = AlertDeduplicator(ttl_seconds=60)
    results = []
    lock = threading.Lock()

    def worker(i: int) -> None:
        result = dedup.is_new({"window_id": "shared"})
        with lock:
            results.append(result)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Exactly one thread should see it as new
    assert results.count(True) == 1
    assert results.count(False) == 19
