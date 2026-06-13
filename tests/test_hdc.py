"""T-03 acceptance tests (MVP_MATH_SPEC §1)."""
from __future__ import annotations

import numpy as np

from sentinel.config import N_BUCKETS
from sentinel.hdc import HDCSpace, TxFeatures


def _feat(**kw) -> TxFeatures:
    base = dict(
        selector="0xa9059cbb",
        gas_bucket=5,
        value_bucket=3,
        timing_bucket=4,
        caller_novel=0,
        caller_freq_tier=2,
        caller_is_contract=0,
    )
    base.update(kw)
    return TxFeatures(**base)


def test_a_same_tx_identical_vector():
    """(a) same tx ⇒ identical vector (determinism)."""
    s1 = HDCSpace()
    s2 = HDCSpace()
    v1 = s1.encode_tx(_feat())
    v2 = s1.encode_tx(_feat())
    v3 = s2.encode_tx(_feat())  # fresh space, same seed
    assert np.array_equal(v1, v2)
    assert np.array_equal(v1, v3)
    assert v1.dtype == np.int8
    assert set(np.unique(v1)).issubset({-1, 1})


def test_b_adjacent_buckets_more_similar_than_random():
    """(b) adjacent gas buckets ⇒ similarity > random pair."""
    s = HDCSpace()
    adj = s.similarity(s.encode_tx(_feat(gas_bucket=5)), s.encode_tx(_feat(gas_bucket=6)))
    far = s.similarity(s.encode_tx(_feat(gas_bucket=0)), s.encode_tx(_feat(gas_bucket=15)))
    # two independent random hypervectors ~ 0 similarity
    rng = np.random.default_rng(0)
    r1 = (rng.integers(0, 2, s.d) * 2 - 1).astype(np.int8)
    r2 = (rng.integers(0, 2, s.d) * 2 - 1).astype(np.int8)
    rand_pair = s.similarity(r1, r2)
    assert adj > far
    assert adj > rand_pair + 0.05


def test_level_table_monotone_and_orthogonal_extremes():
    s = HDCSpace()
    tbl = s._level_table("gas")
    sim_adj = s.similarity(tbl[0], tbl[1])
    sim_far = s.similarity(tbl[0], tbl[N_BUCKETS - 1])
    assert sim_adj > 0.8           # adjacent very similar
    assert abs(sim_far) < 0.1      # extremes ~orthogonal


def test_c_window_bundle_closer_to_prototype_than_single_tx():
    """(c) window bundle vs prototype similarity > single-tx vs prototype."""
    s = HDCSpace()
    rng = np.random.default_rng(42)
    selectors = ["0xa9059cbb", "0x23b872dd", "0x095ea7b3"]

    def sample():
        return _feat(
            selector=selectors[rng.integers(0, 3)],
            gas_bucket=int(np.clip(rng.normal(6, 1.2), 0, 15)),
            value_bucket=int(np.clip(rng.normal(4, 1.0), 0, 15)),
            timing_bucket=int(np.clip(rng.normal(5, 1.0), 0, 15)),
            caller_freq_tier=int(rng.integers(0, 4)),
        )

    warmup = [s.encode_tx(sample()) for _ in range(500)]
    prototype = s.bundle(warmup)
    window = s.bundle([s.encode_tx(sample()) for _ in range(50)])
    single = s.encode_tx(sample())

    assert s.similarity(window, prototype) > s.similarity(single, prototype)


def test_ablation_drops_feature_terms():
    s = HDCSpace()
    full = s.encode_tx(_feat())
    no_gas = s.encode_tx(_feat(), ablate="gas")
    # ablating a feature changes the vector but keeps it bipolar
    assert not np.array_equal(full, no_gas)
    assert set(np.unique(no_gas)).issubset({-1, 1})
