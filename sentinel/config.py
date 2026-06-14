"""Frozen configuration constants (see docs/MVP_MATH_SPEC.md).

All randomness in the system derives from MASTER_SEED. Do not introduce any
unseeded randomness or wall-clock dependence into the pipeline.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# Global master seed — every random hypervector is derived from this (MVP_MATH_SPEC).
MASTER_SEED = 1337

# Tier 2 — HDC hypervector space
D = 10_000                # hypervector dimension (D-02)
N_BUCKETS = 16            # ordinal feature buckets (gas, value, timing); B in spec
WINDOW = 50              # window bundle size W
CALLER_FREQ_TIERS = 4    # caller frequency-tier quantile levels

# Tier 3 — drift normalization
TIMING_WINDOW = 500      # rolling window (tx) for median log-interval
NORM_HIST = 2_000        # rolling window (windows) for median/MAD of drift inputs
SQUASH_SIGMA = 6.0       # z-score that squashes to 1.0
EPS = 1e-9

# Tier 0 — spam pre-filter
MIN_INTERVAL_Q = 0.001   # quantile of inter-tx intervals on warm-up
K_SPAM = 20              # consecutive sub-MIN_INTERVAL intervals to flag spam

# Tier 1 — entropy filter
ENTROPY_SIGMA = 4.0      # |H - mean| > 4*std
ENTROPY_MIN_SAMPLES = 20
# calldata length buckets (bytes): {0-4, 5-36, 37-100, 101-516, >516}
LEN_BUCKET_EDGES = (4, 36, 100, 516)

# Tier 4 — static threshold detector
THETA = 0.65             # drift alert threshold
K_HYSTERESIS = 3         # consecutive windows above theta
EPISODE_COLLAPSE_S = 600  # 10 minutes

# Tier 4 — detector selection. The frozen default is the static θ/k detector;
# BOCPD (T-17) is an opt-in drop-in behind the same `process(drift, ts)` interface,
# selectable at runtime via the SENTINEL_DETECTOR env var without touching the spec.
DEFAULT_DETECTOR = "static"          # {"static", "bocpd"}
SENTINEL_DETECTOR = os.getenv("SENTINEL_DETECTOR", DEFAULT_DETECTOR)


def detector_name() -> str:
    """Resolve the active Tier-4 detector name from the env (read fresh each call)."""
    return os.getenv("SENTINEL_DETECTOR", DEFAULT_DETECTOR).strip().lower()

# Replay / benchmark splits (fractions of the snapshot, strict time order)
WARMUP_FRAC = 0.4
CALIB_FRAC = 0.2         # next 20%; remaining 40% = test


@dataclass(frozen=True)
class Config:
    """Runtime config bundle; defaults are the frozen spec values."""

    master_seed: int = MASTER_SEED
    d: int = D
    n_buckets: int = N_BUCKETS
    window: int = WINDOW
    theta: float = THETA
    k_hysteresis: int = K_HYSTERESIS


DEFAULT_CONFIG = Config()
