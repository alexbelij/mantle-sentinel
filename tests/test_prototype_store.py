"""Tests for sentinel/plugins/prototype_store.py"""
from __future__ import annotations

import threading

import pytest

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

pytestmark = pytest.mark.skipif(not HAS_NUMPY, reason="numpy required")


from sentinel.plugins.prototype_store import PrototypeStore  # noqa: E402

CONTRACT = "0xABCDEF1234567890"


@pytest.fixture
def store(tmp_path):
    return PrototypeStore(tmp_path, contract=CONTRACT, max_versions=5)


def make_vector(dim: int = 100, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(-1, 2, size=dim, dtype=np.int8)


# ---------------------------------------------------------------------------
# Constructor validation
# ---------------------------------------------------------------------------

def test_invalid_contract_empty(tmp_path):
    with pytest.raises(ValueError, match="contract"):
        PrototypeStore(tmp_path, contract="")

def test_invalid_max_versions_zero(tmp_path):
    with pytest.raises(ValueError, match="max_versions"):
        PrototypeStore(tmp_path, contract=CONTRACT, max_versions=0)


# ---------------------------------------------------------------------------
# Save / load round-trip
# ---------------------------------------------------------------------------

def test_save_and_load(store):
    v = make_vector()
    eid = store.save(v, consolidation_count=1, drift_median=0.1)
    loaded = store.load(eid)
    np.testing.assert_array_equal(v, loaded)


def test_save_returns_epoch_id(store):
    eid = store.save(make_vector(), consolidation_count=0, drift_median=0.0)
    assert isinstance(eid, str) and len(eid) > 0


def test_custom_epoch_id(store):
    eid = store.save(make_vector(), consolidation_count=1, drift_median=0.2, epoch_id="myepoch")
    assert eid == "myepoch"
    store.load("myepoch")  # must not raise


# ---------------------------------------------------------------------------
# List / latest
# ---------------------------------------------------------------------------

def test_list_newest_first(store):
    ids = [store.save(make_vector(seed=i), consolidation_count=i, drift_median=0.1) for i in range(3)]
    listed = [r["epoch_id"] for r in store.list()]
    assert listed == list(reversed(ids))


def test_latest_is_most_recent(store):
    ids = [store.save(make_vector(seed=i), consolidation_count=i, drift_median=0.1) for i in range(3)]
    assert store.latest()["epoch_id"] == ids[-1]


def test_latest_empty_store(store):
    assert store.latest() is None


def test_list_excludes_vector_blob(store):
    store.save(make_vector(), consolidation_count=1, drift_median=0.1)
    for rec in store.list():
        assert "vector_b64gz" not in rec


# ---------------------------------------------------------------------------
# Eviction — max_versions cap
# ---------------------------------------------------------------------------

def test_evicts_oldest_when_over_capacity(tmp_path):
    s = PrototypeStore(tmp_path, contract=CONTRACT, max_versions=3)
    ids = [s.save(make_vector(seed=i), consolidation_count=i, drift_median=0.1) for i in range(5)]
    kept = [r["epoch_id"] for r in s.list()]
    assert len(kept) == 3
    assert ids[0] not in kept  # oldest evicted
    assert ids[1] not in kept
    assert ids[2] in kept


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

def test_delete_removes_version(store):
    eid = store.save(make_vector(), consolidation_count=1, drift_median=0.1)
    store.delete(eid)
    assert all(r["epoch_id"] != eid for r in store.list())


def test_delete_missing_raises(store):
    with pytest.raises(KeyError, match="notfound"):
        store.delete("notfound")


def test_clear_removes_all(store):
    for i in range(3):
        store.save(make_vector(seed=i), consolidation_count=i, drift_median=0.1)
    store.clear()
    assert store.list() == []


# ---------------------------------------------------------------------------
# Validation — bad input to save()
# ---------------------------------------------------------------------------

def test_save_raises_on_none_vector(store):
    with pytest.raises(ValueError, match="None"):
        store.save(None, consolidation_count=0, drift_median=0.0)


def test_save_raises_on_2d_vector(store):
    with pytest.raises(ValueError, match="1-D"):
        store.save(np.zeros((10, 10), dtype=np.int8), consolidation_count=0, drift_median=0.0)


def test_save_raises_on_empty_vector(store):
    with pytest.raises(ValueError, match="empty"):
        store.save(np.array([], dtype=np.int8), consolidation_count=0, drift_median=0.0)


def test_save_raises_on_negative_consolidation(store):
    with pytest.raises(ValueError, match="consolidation_count"):
        store.save(make_vector(), consolidation_count=-1, drift_median=0.0)


def test_save_raises_on_drift_above_1(store):
    with pytest.raises(ValueError, match=r"\[0\.0, 1\.0\]"):
        store.save(make_vector(), consolidation_count=0, drift_median=1.1)


def test_save_raises_on_drift_nan(store):
    import math
    with pytest.raises(ValueError, match="finite"):
        store.save(make_vector(), consolidation_count=0, drift_median=math.nan)


def test_load_missing_raises(store):
    with pytest.raises(KeyError):
        store.load("doesnotexist")


# ---------------------------------------------------------------------------
# Persistence — survives process restart
# ---------------------------------------------------------------------------

def test_persists_across_instances(tmp_path):
    s1 = PrototypeStore(tmp_path, contract=CONTRACT)
    v  = make_vector(seed=42)
    eid = s1.save(v, consolidation_count=5, drift_median=0.15)

    s2 = PrototypeStore(tmp_path, contract=CONTRACT)
    loaded = s2.load(eid)
    np.testing.assert_array_equal(v, loaded)


def test_corrupt_file_recovers(tmp_path):
    index_path = tmp_path / f"prototype_store_{CONTRACT.lower().replace('0x','')[:40]}.json"
    index_path.write_text("NOT_VALID_JSON")
    s = PrototypeStore(tmp_path, contract=CONTRACT)  # must not raise
    assert s.list() == []
    backup = list(tmp_path.glob("*.corrupt.json"))
    assert len(backup) == 1


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

def test_concurrent_saves(tmp_path):
    s      = PrototypeStore(tmp_path, contract=CONTRACT, max_versions=20)
    errors = []

    def worker(seed):
        try:
            s.save(make_vector(seed=seed), consolidation_count=seed, drift_median=0.1)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Errors in threads: {errors}"
    assert len(s.list()) <= 20
