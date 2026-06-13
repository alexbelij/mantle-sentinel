"""Feature extraction: raw tx records → encoder-ready TxFeatures (+ dt).

Bucket edges (gas/value/timing) are equal-frequency quantiles computed on the
warm-up split and frozen (MVP_MATH_SPEC §1). Caller properties are streaming:
novelty is "unseen so far"; frequency tier is a quantile of warm-up caller counts.
"""
from __future__ import annotations

import numpy as np

from sentinel.config import CALLER_FREQ_TIERS, N_BUCKETS
from sentinel.entropy import selector_of
from sentinel.hdc import TxFeatures

RawTx = dict  # {block_number, block_timestamp, tx_hash, contract, caller, calldata, gas_used, value, caller_is_contract?}


def _quantile_edges(values: list[float], n_buckets: int) -> np.ndarray:
    if not values:
        return np.array([0.0])
    qs = [i / n_buckets for i in range(1, n_buckets)]
    return np.quantile(np.asarray(values, dtype=float), qs)


class FeatureExtractor:
    def __init__(self, n_buckets: int = N_BUCKETS):
        self.n_buckets = n_buckets
        self.gas_edges = np.array([0.0])
        self.value_edges = np.array([0.0])
        self.timing_edges = np.array([0.0])
        self.freq_edges = np.array([0.0])
        self._seen: set[str] = set()
        self._caller_count: dict[str, int] = {}
        self._prev_ts: float | None = None

    # --- fitting (warm-up) -------------------------------------------------
    def fit(self, warmup: list[RawTx]) -> FeatureExtractor:
        gas, val, dts = [], [], []
        counts: dict[str, int] = {}
        prev = None
        for r in warmup:
            gas.append(float(r.get("gas_used", 0) or 0))
            val.append(float(r.get("value", 0) or 0))
            ts = float(r["block_timestamp"])
            if prev is not None:
                dts.append(max(ts - prev, 0.0))
            prev = ts
            c = (r.get("caller") or "").lower()
            counts[c] = counts.get(c, 0) + 1
        self.gas_edges = _quantile_edges(gas, self.n_buckets)
        self.value_edges = _quantile_edges(val, self.n_buckets)
        self.timing_edges = _quantile_edges(dts, self.n_buckets)
        self.freq_edges = _quantile_edges(list(counts.values()), CALLER_FREQ_TIERS)
        # Freeze warm-up caller counts so frequency tiers reflect warm-up (not test).
        # Streaming state (_seen, _prev_ts) is left untouched and populated on extract().
        self._caller_count = dict(counts)
        return self

    def _bucket(self, x: float, edges: np.ndarray) -> int:
        return int(np.searchsorted(edges, x, side="right"))

    # --- streaming extraction ---------------------------------------------
    def extract(self, r: RawTx) -> tuple[TxFeatures, float]:
        ts = float(r["block_timestamp"])
        dt = max(ts - self._prev_ts, 0.0) if self._prev_ts is not None else 0.0
        self._prev_ts = ts

        caller = (r.get("caller") or "").lower()
        novel = int(caller not in self._seen)
        self._seen.add(caller)
        warm_count = self._caller_count.get(caller, 0)
        freq_tier = int(np.searchsorted(self.freq_edges, warm_count, side="right"))
        freq_tier = min(freq_tier, CALLER_FREQ_TIERS - 1)

        calldata = r.get("calldata", "0x") or "0x"
        feat = TxFeatures(
            selector=selector_of(calldata),
            gas_bucket=self._bucket(float(r.get("gas_used", 0) or 0), self.gas_edges),
            value_bucket=self._bucket(float(r.get("value", 0) or 0), self.value_edges),
            timing_bucket=self._bucket(dt, self.timing_edges),
            caller_novel=novel,
            caller_freq_tier=freq_tier,
            caller_is_contract=int(r.get("caller_is_contract", 0) or 0),
        )
        return feat, dt
