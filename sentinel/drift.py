"""Tier 3 — drift signal (MVP_MATH_SPEC §2).

    hamming(t) = HammingDistance(V_win, P) / D                      in [0,1]
    timing(t)  = |log(Δt) − median_w(log Δt)|       (w = 500-tx rolling)
    norm(x)    = squash( (x − median_hist(x)) / (1.4826·MAD_hist(x) + ε) )
    squash(z)  = clip(z / 6, 0, 1)
    drift(t)   = max( norm(hamming(t)), norm(timing(t)) )

median_hist / MAD_hist are rolling over the last NORM_HIST (=2000) windows of the
contract's own history, initialised on warm-up. Robust (median/MAD) by D-03.
"""
from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass

import numpy as np

from sentinel.config import EPS, NORM_HIST, SQUASH_SIGMA, TIMING_WINDOW, D
from sentinel.hdc import HDCSpace

_MAD_SCALE = 1.4826


@dataclass(frozen=True)
class DriftResult:
    drift: float
    branch: str            # "hamming" | "timing"
    hamming: float         # raw normalized hamming distance in [0,1]
    timing: float          # raw timing deviation
    hamming_norm: float
    timing_norm: float


def _squash(z: float) -> float:
    return float(np.clip(z / SQUASH_SIGMA, 0.0, 1.0))


class _RobustNormalizer:
    """squash(robust z-score) using a rolling median/MAD over raw history."""

    def __init__(self, maxlen: int = NORM_HIST, min_history: int = 50):
        self._hist: deque[float] = deque(maxlen=maxlen)
        self._min_history = min_history

    def normalize(self, x: float) -> float:
        # Use history *before* adding x so the current point cannot define its own scale.
        if len(self._hist) >= self._min_history:
            arr = np.fromiter(self._hist, dtype=float)
            med = float(np.median(arr))
            mad = float(np.median(np.abs(arr - med)))
            scale = _MAD_SCALE * mad
            # D-09: guard against a degenerate MAD (>50% of history identical ⇒ MAD=0),
            # which would otherwise divide by ~ε and explode. Fall back to the robust
            # std of history; only if both vanish do we treat the signal as flat.
            if scale <= EPS:
                scale = float(np.std(arr))
            z = (x - med) / (scale + EPS)
            out = _squash(z)
        else:
            out = 0.0
        self._hist.append(x)
        return out

    def seed(self, x: float) -> None:
        self._hist.append(x)


class DriftTracker:
    """Stateful per-contract drift estimator. Feed one evaluation per transaction;
    windows slide by 1 tx."""

    def __init__(self, space: HDCSpace, prototype: np.ndarray):
        self.space = space
        self.prototype = prototype
        self.d = space.d if space is not None else D
        self._log_dt: deque[float] = deque(maxlen=TIMING_WINDOW)
        self._hamming_norm = _RobustNormalizer()
        self._timing_norm = _RobustNormalizer()

    # raw signals -----------------------------------------------------------
    def _hamming(self, v_win: np.ndarray) -> float:
        return self.space.hamming(v_win, self.prototype) / self.d

    def _timing(self, dt: float) -> float:
        ldt = math.log(max(dt, EPS))
        if self._log_dt:
            med = float(np.median(np.fromiter(self._log_dt, dtype=float)))
            dev = abs(ldt - med)
        else:
            dev = 0.0
        self._log_dt.append(ldt)
        return dev

    # main step -------------------------------------------------------------
    def update(self, v_win: np.ndarray, dt: float) -> DriftResult:
        h_raw = self._hamming(v_win)
        t_raw = self._timing(dt)
        h_norm = self._hamming_norm.normalize(h_raw)
        t_norm = self._timing_norm.normalize(t_raw)
        if t_norm > h_norm:
            branch, drift = "timing", t_norm
        else:
            branch, drift = "hamming", h_norm
        return DriftResult(
            drift=drift,
            branch=branch,
            hamming=h_raw,
            timing=t_raw,
            hamming_norm=h_norm,
            timing_norm=t_norm,
        )
