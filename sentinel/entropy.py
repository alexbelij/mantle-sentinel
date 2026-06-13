"""Tier 1 — Shannon entropy filter (MVP_MATH_SPEC §3).

Per (selector, calldata-length-bucket) baseline of byte-level Shannon entropy of
the calldata *body* (bytes after the 4-byte selector). Hard threshold:

    alert iff |H(tx) − mean| > 4·std  AND  the baseline cell has ≥ 20 samples
    otherwise abstain (never alert from an unpopulated cell).

Bypasses Tier 4; emits its own alert type `entropy_anomaly`.
"""
from __future__ import annotations

from collections import defaultdict

import numpy as np

from sentinel.config import ENTROPY_MIN_SAMPLES, ENTROPY_SIGMA, LEN_BUCKET_EDGES


def calldata_to_bytes(calldata: str) -> bytes:
    s = calldata[2:] if calldata.startswith(("0x", "0X")) else calldata
    if len(s) % 2:
        s = "0" + s
    try:
        return bytes.fromhex(s)
    except ValueError:
        return b""


def selector_of(calldata: str) -> str:
    b = calldata_to_bytes(calldata)
    return "0x" + b[:4].hex() if len(b) >= 4 else "0x"


def body_of(calldata: str) -> bytes:
    b = calldata_to_bytes(calldata)
    return b[4:] if len(b) > 4 else b""


def byte_entropy(data: bytes) -> float:
    """Shannon entropy (bits/byte) of the byte distribution, in [0, 8]."""
    if not data:
        return 0.0
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
    p = counts[counts > 0] / len(data)
    return float(-(p * np.log2(p)).sum())


def length_bucket(n_bytes: int) -> int:
    return int(np.searchsorted(LEN_BUCKET_EDGES, n_bytes, side="right"))


class EntropyFilter:
    """Per-(selector, length-bucket) entropy baseline + 4σ hard threshold."""

    def __init__(self, sigma: float = ENTROPY_SIGMA, min_samples: int = ENTROPY_MIN_SAMPLES):
        self.sigma = sigma
        self.min_samples = min_samples
        self._samples: dict[tuple[str, int], list[float]] = defaultdict(list)
        self._stats: dict[tuple[str, int], tuple[float, float, int]] = {}

    def _cell(self, calldata: str) -> tuple[str, int]:
        body = body_of(calldata)
        return selector_of(calldata), length_bucket(len(body))

    def fit_one(self, calldata: str) -> None:
        self._samples[self._cell(calldata)].append(byte_entropy(body_of(calldata)))

    def fit(self, calldatas: list[str]) -> EntropyFilter:
        for cd in calldatas:
            self.fit_one(cd)
        self.freeze()
        return self

    def freeze(self) -> None:
        """Compute mean/std/n per cell; frozen after warm-up."""
        self._stats = {}
        for cell, vals in self._samples.items():
            arr = np.asarray(vals, dtype=float)
            self._stats[cell] = (float(arr.mean()), float(arr.std()), len(arr))

    def check(self, calldata: str) -> bool:
        """True ⇒ entropy_anomaly alert; False ⇒ normal or abstain."""
        cell = self._cell(calldata)
        stats = self._stats.get(cell)
        if stats is None or stats[2] < self.min_samples:
            return False  # abstain — unpopulated cell
        mean, std, _ = stats
        h = byte_entropy(body_of(calldata))
        return abs(h - mean) > self.sigma * std
