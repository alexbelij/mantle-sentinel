"""T-18 acceptance tests — Dream Mode prototype consolidation."""
from __future__ import annotations

import numpy as np

from sentinel.dream import dream_update


def _bipolar(rng, d):
    return (rng.integers(0, 2, d, dtype=np.int8) * 2 - 1).astype(np.int8)


def _hamming_sim(a, b):
    """Fraction of agreeing dimensions (1.0 == identical)."""
    return float(np.mean(np.asarray(a) == np.asarray(b)))


def test_output_is_bipolar_int8_same_shape():
    rng = np.random.default_rng(0)
    d = 1000
    V_old = _bipolar(rng, d)
    safe = np.stack([_bipolar(rng, d) for _ in range(20)])
    V_new = dream_update(V_old, safe, alpha=1.0)
    assert V_new.dtype == np.int8
    assert V_new.shape == V_old.shape
    assert set(np.unique(V_new)).issubset({-1, 1})


def test_ties_resolve_to_plus_one():
    # λ=0 (alpha=0) and two opposing safe vectors → column sums are exactly 0
    # everywhere → every tie must resolve to +1.
    d = 64
    a = np.ones(d, dtype=np.int8)
    b = (-np.ones(d, dtype=np.int8)).astype(np.int8)
    V_new = dream_update(np.full(d, -1, dtype=np.int8), np.stack([a, b]), alpha=0.0)
    assert np.all(V_new == 1)


def test_large_alpha_preserves_old_prototype():
    rng = np.random.default_rng(1)
    d = 2000
    V_old = _bipolar(rng, d)
    safe = np.stack([_bipolar(rng, d) for _ in range(10)])
    # Huge inertia ⇒ old prototype dominates the majority vote ⇒ V_new == V_old.
    V_new = dream_update(V_old, safe, alpha=1e6)
    assert np.array_equal(V_new, V_old)


def test_zero_alpha_equals_safe_bundle():
    rng = np.random.default_rng(2)
    d = 1500
    V_old = _bipolar(rng, d)
    safe = np.stack([_bipolar(rng, d) for _ in range(7)])
    V_new = dream_update(V_old, safe, alpha=0.0)
    expected = np.where(safe.sum(axis=0) >= 0, 1, -1).astype(np.int8)
    assert np.array_equal(V_new, expected)


def test_prototype_moves_toward_safe_windows():
    """V_new must be strictly more similar to the safe prototype than V_old was,
    and must differ from V_old (T-18: V_new ≠ V_old)."""
    rng = np.random.default_rng(3)
    d = 5000
    safe_proto = _bipolar(rng, d)
    # Safe windows = noisy copies of a coherent safe prototype.
    safe = []
    for _ in range(30):
        v = safe_proto.copy()
        flip = rng.random(d) < 0.2          # 20% noise
        v[flip] *= -1
        safe.append(v)
    safe = np.stack(safe)
    # Start far from the safe prototype.
    V_old = (-safe_proto).astype(np.int8)

    V_new = dream_update(V_old, safe, alpha=1.0)
    assert not np.array_equal(V_new, V_old), "dream update must move the prototype"
    assert _hamming_sim(V_new, safe_proto) > _hamming_sim(V_old, safe_proto)


def test_iterated_dreaming_converges():
    """Repeated consolidation against the same safe distribution drives the
    prototype's similarity to the safe prototype monotonically up to a high floor."""
    rng = np.random.default_rng(4)
    d = 5000
    safe_proto = _bipolar(rng, d)
    V = (-safe_proto).astype(np.int8)

    sims = []
    for _ in range(8):
        safe = []
        for _ in range(25):
            v = safe_proto.copy()
            v[rng.random(d) < 0.15] *= -1
            safe.append(v)
        V = dream_update(V, np.stack(safe), alpha=0.5)
        sims.append(_hamming_sim(V, safe_proto))

    assert sims[-1] > 0.95, f"did not converge: final sim {sims[-1]:.3f}"
    assert sims[-1] >= sims[0]


def test_empty_safe_batch_raises():
    V_old = np.ones(16, dtype=np.int8)
    try:
        dream_update(V_old, np.empty((0, 16), dtype=np.int8))
    except ValueError:
        return
    raise AssertionError("expected ValueError on empty safe batch")
