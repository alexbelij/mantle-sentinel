"""Tier 4 (alt) — Bayesian Online Changepoint Detection (T-17).

A drop-in alternative to :class:`sentinel.detector.StaticThresholdDetector`,
exposing the *same* interface ``process(drift, ts) -> Trigger | None`` so it can
sit behind the frozen Tier-4 slot without touching the pipeline or config.

Algorithm: Adams & MacKay (2007) online changepoint detection on the 1-D drift
signal, with a constant hazard ``H = 1/hazard`` and a Normal–Inverse-Gamma
conjugate observation model (Student-t posterior predictive). A changepoint is
declared when the posterior mass below the established run-length collapses:
``P(r_t < r_map^{prev})`` exceeds ``p_thresh`` AND the new regime has
higher drift (anomaly, not recovery). Episodes are tracked/merged exactly
like the static detector.

This module is intentionally self-contained (numpy only) — no ``ruptures`` /
``bayesian_changepoint`` runtime dependency, so CI stays hermetic.

DEFAULT_DETECTOR in sentinel/config.py is unchanged: BOCPD is an opt-in option.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from sentinel.detector import Trigger
from sentinel.episodes import EpisodeTracker


@dataclass(frozen=True)
class NIGPrior:
    """Normal–Inverse-Gamma prior for the per-run Gaussian observation model."""

    mu: float = 0.0
    kappa: float = 1.0
    alpha: float = 1.0
    beta: float = 1.0


class BOCPDDetector:
    """Bayesian online changepoint detector with the static-detector interface.

    Parameters
    ----------
    hazard:
        Expected run length λ; constant hazard ``H = 1/λ``. Default 100 (spec).
    p_thresh:
        Changepoint declared when ``P(r_t = 0) > p_thresh``. Default 0.5 (spec).
    prior:
        NIG prior. Defaults are weak and scaled for a drift signal in ``[0, 1]``.
    max_run:
        Cap on the run-length vector length (older mass is truncated/renormalised)
        to keep the per-step cost O(max_run).
    """

    def __init__(
        self,
        hazard: float = 100.0,
        p_thresh: float = 0.5,
        prior: NIGPrior | None = None,
        max_run: int = 500,
        episode_prefix: str = "regime",
    ):
        self.hazard = float(hazard)
        self.h = 1.0 / float(hazard)
        self.p_thresh = float(p_thresh)
        self.prior = prior or NIGPrior(mu=0.0, kappa=1.0, alpha=1.0, beta=1.0)
        self.max_run = int(max_run)
        self._episodes = EpisodeTracker(prefix=episode_prefix)
        self._fired = False
        self._init_state()

    # --- state -------------------------------------------------------------
    def _init_state(self) -> None:
        p = self.prior
        # Run-length posterior R; starts certain at run-length 0.
        self._R = np.array([1.0])
        # Per-run NIG sufficient parameters (parallel arrays).
        self._mu = np.array([p.mu])
        self._kappa = np.array([p.kappa])
        self._alpha = np.array([p.alpha])
        self._beta = np.array([p.beta])
        self.last_cp_prob: float = 0.0
        self.cp_prob_r0: float = 0.0
        self.run_length_map: int = 0
        self._established_mean: float = self.prior.mu
        self.cp_is_rise: bool = False

    def reset(self) -> None:
        """Reset detector state (mirrors StaticThresholdDetector.reset)."""
        self._fired = False
        self._init_state()

    # --- predictive (Student-t from NIG) -----------------------------------
    def _pred_prob(self, x: float) -> np.ndarray:
        """Posterior-predictive density of x under each run's NIG params."""
        df = 2.0 * self._alpha
        scale2 = self._beta * (self._kappa + 1.0) / (self._alpha * self._kappa)
        scale = np.sqrt(scale2)
        z = (x - self._mu) / scale
        # Student-t pdf with `df` degrees of freedom (vectorised, no scipy).
        from math import lgamma

        gln = np.vectorize(lgamma)
        log_norm = (
            gln(0.5 * (df + 1.0))
            - gln(0.5 * df)
            - 0.5 * np.log(df * np.pi)
            - np.log(scale)
        )
        log_pdf = log_norm - 0.5 * (df + 1.0) * np.log1p(z * z / df)
        return np.exp(log_pdf)

    def _update_params(self, x: float) -> None:
        """NIG posterior update; prepend a fresh run-0 (the prior) at the front."""
        p = self.prior
        new_mu = (self._kappa * self._mu + x) / (self._kappa + 1.0)
        new_kappa = self._kappa + 1.0
        new_alpha = self._alpha + 0.5
        new_beta = self._beta + (self._kappa * (x - self._mu) ** 2) / (2.0 * (self._kappa + 1.0))
        self._mu = np.concatenate(([p.mu], new_mu))
        self._kappa = np.concatenate(([p.kappa], new_kappa))
        self._alpha = np.concatenate(([p.alpha], new_alpha))
        self._beta = np.concatenate(([p.beta], new_beta))

    def _truncate(self) -> None:
        if len(self._R) <= self.max_run:
            return
        k = self.max_run
        self._R = self._R[:k]
        self._R /= self._R.sum()
        self._mu = self._mu[:k]
        self._kappa = self._kappa[:k]
        self._alpha = self._alpha[:k]
        self._beta = self._beta[:k]

    # --- public step -------------------------------------------------------
    def step(self, x: float) -> float:
        """Advance the filter by one observation; return the changepoint score.

        With a constant hazard the instantaneous ``P(r_t = 0)`` is pinned near the
        hazard and is *not* a usable alarm. The standard BOCPD changepoint readout
        is the **run-length collapse**: when a regime change occurs the posterior
        mass jumps from the long established run to short runs. We therefore report

            cp_score = P(r_t < r_map^{prev})

        — the posterior probability that the current run is *shorter* than the
        previously-established regime length. On a stationary stream this stays at
        the hazard floor; at a changepoint it spikes toward 1 within one step.
        """
        prev_map = int(np.argmax(self._R))
        # Posterior mean of the established regime (before this obs updates it).
        self._established_mean = float(self._mu[prev_map])
        # A changepoint INTO higher drift is an anomaly; a change back DOWN is a
        # recovery ("all clear"). We only alert on the former, keeping the static
        # detector's anomaly-only semantics without re-introducing a fixed θ.
        self.cp_is_rise = x > self._established_mean
        pred = self._pred_prob(x)
        growth = self._R * pred * (1.0 - self.h)
        cp_mass = float((self._R * pred * self.h).sum())
        new_R = np.empty(len(self._R) + 1)
        new_R[0] = cp_mass
        new_R[1:] = growth
        total = new_R.sum()
        if total <= 0 or not np.isfinite(total):
            new_R[:] = 0.0
            new_R[0] = 1.0
            total = 1.0
        new_R /= total
        self._update_params(x)
        self._R = new_R
        self._truncate()
        self.run_length_map = int(np.argmax(self._R))
        self.cp_prob_r0 = float(self._R[0])  # raw P(r_t = 0), for observability
        self.last_cp_prob = float(self._R[:prev_map].sum()) if prev_map > 0 else 0.0
        return self.last_cp_prob

    def process(self, drift: float, ts: float) -> Trigger | None:
        """Same contract as StaticThresholdDetector.process."""
        cp = self.step(float(drift))
        if cp > self.p_thresh and self.cp_is_rise:
            if self._fired:
                return None
            self._fired = True
            episode_id, is_new = self._episodes.assign(ts)
            return Trigger(ts=ts, drift=drift, episode_id=episode_id, new_episode=is_new)
        if cp <= self.p_thresh:
            self._fired = False
        return None
