"""T-05b acceptance tests (MVP_MATH_SPEC §0)."""
from __future__ import annotations

import numpy as np

from bench.synth import stationary_stream
from sentinel.config import K_SPAM
from sentinel.hdc import HDCSpace
from sentinel.prefilter import SpamPrefilter


def test_min_interval_from_warmup_quantile():
    rng = np.random.default_rng(0)
    intervals = list(abs(rng.normal(12.0, 1.0, 5000)) + 0.5)
    pf = SpamPrefilter().fit(intervals)
    assert 0.0 < pf.min_interval < 12.0  # 0.001-quantile sits in the low tail


def test_burst_one_episode_and_prototype_unchanged():
    """Synthetic burst (1000 tx, near-zero intervals) ⇒ one spam_attack episode and
    the (frozen) prototype is unchanged by spam txs."""
    # warm-up: normal intervals ⇒ MIN_INTERVAL in the low tail
    warm = stationary_stream(1500, seed=5)
    intervals = [dt for _, dt in warm]
    pf = SpamPrefilter().fit(intervals)

    # frozen behavioral prototype built from non-spam warm-up txs
    space = HDCSpace()
    prototype = space.bundle([space.encode_tx(f) for f, _ in warm])

    # spam burst: 1000 tx with near-zero intervals
    burst_n = 1000
    alerts = 0
    spam_flagged = 0
    for _ in range(burst_n):
        res = pf.process(1e-6)
        alerts += int(res.alert)
        spam_flagged += int(res.is_spam)

    assert alerts == 1, f"expected exactly one spam_attack onset, got {alerts}"
    # everything past the first (k_spam-1) intervals is flagged ⇒ excluded from baselines
    assert spam_flagged == burst_n - (K_SPAM - 1)

    # prototype is frozen (MVP) ⇒ spam cannot poison it
    proto_after = space.bundle([space.encode_tx(f) for f, _ in warm])
    assert np.array_equal(prototype, proto_after)


def test_normal_traffic_no_spam():
    warm = stationary_stream(800, seed=2)
    intervals = [dt for _, dt in warm]
    pf = SpamPrefilter().fit(intervals)
    # replay normal intervals: none should trip spam
    alerts = sum(pf.process(dt).alert for dt in intervals)
    assert alerts == 0
