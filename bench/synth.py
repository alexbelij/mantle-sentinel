"""Synthetic transaction streams for unit tests and the viability spike fallback.

Deterministic (seeded). Produces encoder-ready TxFeatures plus an inter-tx
interval (dt). This is *not* part of the live pipeline — it is evaluation tooling.
A stationary stream emulates a contract's normal behaviour; injectors transform
the stream to emulate attack scenarios (S1 selector flood, S5 timing burst).
"""
from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from sentinel.config import N_BUCKETS
from sentinel.hdc import TxFeatures

NORMAL_SELECTORS = ("0xa9059cbb", "0x23b872dd", "0x095ea7b3", "0x2e1a7d4d")
NOVEL_SELECTOR = "0xdeadbeef"


def _bucket(rng: np.random.Generator, center: float, spread: float) -> int:
    return int(np.clip(round(rng.normal(center, spread)), 0, N_BUCKETS - 1))


# Realistic normal traffic for a token-like contract: transfer() dominates,
# a long tail of approve/transferFrom/withdraw. Tight bucket distributions —
# a stationary contract's per-window fingerprint has low variance by definition.
NORMAL_SELECTOR_WEIGHTS = (0.80, 0.10, 0.07, 0.03)


def stationary_stream(n: int, seed: int = 0, base_dt: float = 12.0) -> list[tuple[TxFeatures, float]]:
    """A stationary 'normal traffic' stream: stable selector mix, gas/value/timing
    distributions, mostly-returning callers, near-constant inter-tx interval."""
    rng = np.random.default_rng(seed)
    out: list[tuple[TxFeatures, float]] = []
    for _ in range(n):
        feat = TxFeatures(
            selector=NORMAL_SELECTORS[rng.choice(len(NORMAL_SELECTORS), p=NORMAL_SELECTOR_WEIGHTS)],
            gas_bucket=_bucket(rng, 7, 0.7),
            value_bucket=_bucket(rng, 4, 0.7),
            timing_bucket=_bucket(rng, 6, 0.7),
            caller_novel=int(rng.random() < 0.03),
            caller_freq_tier=1 if rng.random() < 0.85 else int(rng.integers(0, 4)),
            caller_is_contract=int(rng.random() < 0.15),
        )
        dt = float(abs(rng.normal(base_dt, base_dt * 0.05))) + 0.1
        out.append((feat, dt))
    return out


def selector_flood(n: int, seed: int = 1) -> list[tuple[TxFeatures, float]]:
    """S1: a flood of a never-before-seen selector at ~3x rate."""
    rng = np.random.default_rng(seed)
    out: list[tuple[TxFeatures, float]] = []
    for _ in range(n):
        feat = TxFeatures(
            selector=NOVEL_SELECTOR,
            gas_bucket=_bucket(rng, 7, 1.2),
            value_bucket=_bucket(rng, 4, 1.0),
            timing_bucket=_bucket(rng, 2, 1.0),   # faster ⇒ lower interval bucket
            caller_novel=1,
            caller_freq_tier=0,
            caller_is_contract=1,
        )
        dt = float(abs(rng.normal(4.0, 0.5))) + 0.05   # 3x rate
        out.append((feat, dt))
    return out


def sliding_windows(
    encoded: list[np.ndarray], window: int
) -> Iterator[tuple[int, np.ndarray]]:
    """Yield (index, window-bundle) for each position once `window` vectors exist."""
    from sentinel.hdc import HDCSpace

    space = HDCSpace()
    for i in range(window - 1, len(encoded)):
        yield i, space.bundle(encoded[i - window + 1 : i + 1])
