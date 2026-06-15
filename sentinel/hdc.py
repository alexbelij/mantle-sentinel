"""Tier 2 — Hyperdimensional encoder (Behavioral DNA).

Implements MVP_MATH_SPEC §1 exactly:
- bipolar {-1,+1} hypervectors, D=10,000, int8 storage
- deterministic item memory seeded from MASTER_SEED (no Python hash() — it is salted)
- level encoding for ordinal buckets (adjacent buckets similar, far buckets ~orthogonal)
- role-filler binding (element-wise multiply) + majority-sign bundling (ties -> +1)
- V_tx = sign(Σ_f R_f ⊙ F_f); window bundle and prototype are sign-of-sum of V_tx

The encoder is pure: it consumes an already-computed feature dict (see TxFeatures)
so it can be unit-tested independently of data capture / bucketing state.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from sentinel.config import MASTER_SEED, N_BUCKETS, D

# The five attribution feature groups (interpreter / ablation use these names).
FEATURE_GROUPS = ("caller", "selector", "gas", "value", "timing")


@dataclass(frozen=True)
class TxFeatures:
    """Pre-extracted, encoder-ready features for one transaction."""

    selector: str                 # 4-byte hex selector, e.g. "0xa9059cbb"
    gas_bucket: int               # ordinal bucket index in [0, N_BUCKETS)
    value_bucket: int
    timing_bucket: int
    caller_novel: int             # 0/1 — caller unseen in history so far
    caller_freq_tier: int         # 0..CALLER_FREQ_TIERS-1
    caller_is_contract: int       # 0/1


def _seed_from(*parts: object) -> int:
    """Deterministic 64-bit seed from parts (stable across processes)."""
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:8], "big")


class HDCSpace:
    """Item memory + encoder for one contract's behavioral DNA."""

    def __init__(self, d: int = D, n_buckets: int = N_BUCKETS, master_seed: int = MASTER_SEED):
        self.d = d
        self.n_buckets = n_buckets
        self.master_seed = master_seed
        self._items: dict[tuple[str, str], np.ndarray] = {}
        self._roles: dict[str, np.ndarray] = {}
        self._levels: dict[str, np.ndarray] = {}  # name -> (n_buckets, d) int8

    # --- primitives -------------------------------------------------------
    def _rand_bipolar(self, *seed_parts: object) -> np.ndarray:
        rng = np.random.default_rng(_seed_from(self.master_seed, *seed_parts))
        return (rng.integers(0, 2, self.d, dtype=np.int8) * 2 - 1).astype(np.int8)

    def role(self, name: str) -> np.ndarray:
        if name not in self._roles:
            self._roles[name] = self._rand_bipolar("role", name)
        return self._roles[name]

    def item(self, namespace: str, value: str) -> np.ndarray:
        key = (namespace, value)
        if key not in self._items:
            self._items[key] = self._rand_bipolar("item", namespace, value)
        return self._items[key]

    def _level_table(self, name: str) -> np.ndarray:
        """Level-encoded ordinal table: bucket 0 random; each next bucket flips a
        fixed disjoint block of D/(2(B-1)) coordinates. Disjoint blocks ⇒ similarity
        decreases monotonically and bucket 0 vs B-1 is ~orthogonal."""
        if name in self._levels:
            return self._levels[name]
        base = self._rand_bipolar("level0", name)
        rng = np.random.default_rng(_seed_from(self.master_seed, "levelperm", name))
        perm = rng.permutation(self.d)
        if self.n_buckets <= 1:  # W-NUM-2: single bucket → just the base vector
            table = np.empty((1, self.d), dtype=np.int8)
            table[0] = self._rand_bipolar("level0", name)
            self._levels[name] = table
            return table
        flip_count = self.d // (2 * (self.n_buckets - 1))
        table = np.empty((self.n_buckets, self.d), dtype=np.int8)
        cur = base.copy()
        table[0] = cur
        for b in range(1, self.n_buckets):
            idx = perm[(b - 1) * flip_count : b * flip_count]
            cur = cur.copy()
            cur[idx] *= -1
            table[b] = cur
        self._levels[name] = table
        return table

    def level(self, name: str, bucket: int) -> np.ndarray:
        b = int(np.clip(bucket, 0, self.n_buckets - 1))
        return self._level_table(name)[b]

    # --- binding / bundling ----------------------------------------------
    def _terms(self, feat: TxFeatures, ablate: str | None = None):
        """Yield (group, bound_vector) pairs for a transaction.

        Design note (W-HDC-1): caller sub-features (novel, freq, is_contract)
        collectively hold 3/7 vote weight in the bundle. This is intentional:
        caller identity is the strongest behavioral axis for contract monitoring.
        Gas/value/timing/selector each contribute 1/7.
        """
        if ablate != "selector":
            yield "selector", self.role("selector") * self.item("selector", feat.selector)
        if ablate != "gas":
            yield "gas", self.role("gas") * self.level("gas", feat.gas_bucket)
        if ablate != "value":
            yield "value", self.role("value") * self.level("value", feat.value_bucket)
        if ablate != "timing":
            yield "timing", self.role("timing") * self.level("timing", feat.timing_bucket)
        if ablate != "caller":
            yield "caller", self.role("caller_novel") * self.item(
                "caller_novel", str(feat.caller_novel)
            )
            yield "caller", self.role("caller_freq") * self.item(
                "caller_freq", str(feat.caller_freq_tier)
            )
            yield "caller", self.role("caller_isc") * self.item(
                "caller_isc", str(feat.caller_is_contract)
            )

    def encode_tx(self, feat: TxFeatures, ablate: str | None = None) -> np.ndarray:
        """V_tx = sign(Σ_f R_f ⊙ F_f). Ties (sum == 0) resolve to +1."""
        acc = np.zeros(self.d, dtype=np.int32)
        for _group, vec in self._terms(feat, ablate=ablate):
            acc += vec
        return self._sign(acc)

    @staticmethod
    def _sign(acc: np.ndarray) -> np.ndarray:
        return np.where(acc >= 0, 1, -1).astype(np.int8)

    def bundle(self, vecs: np.ndarray | list[np.ndarray]) -> np.ndarray:
        """Majority-sign bundle of bipolar vectors (ties -> +1)."""
        arr = np.asarray(vecs, dtype=np.int32)
        if arr.ndim == 1:
            return self._sign(arr)
        return self._sign(arr.sum(axis=0))

    # --- similarity -------------------------------------------------------
    @staticmethod
    def hamming(a: np.ndarray, b: np.ndarray) -> int:
        return int(np.count_nonzero(a != b))

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine for bipolar vectors = (D - 2*hamming)/D, in [-1, 1]."""
        return (self.d - 2 * self.hamming(a, b)) / self.d
