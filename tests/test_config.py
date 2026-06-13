from __future__ import annotations

from sentinel import config


def test_master_seed_frozen():
    assert config.MASTER_SEED == 1337


def test_frozen_dimensions():
    assert config.D == 10_000
    assert config.N_BUCKETS == 16
    assert config.WINDOW == 50
    assert config.THETA == 0.65
    assert config.K_HYSTERESIS == 3
