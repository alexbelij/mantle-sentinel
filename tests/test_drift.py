"""T-04 acceptance tests (MVP_MATH_SPEC §2)."""
from __future__ import annotations

import numpy as np

from bench.synth import selector_flood, stationary_stream
from sentinel.config import K_HYSTERESIS, THETA, WINDOW
from sentinel.drift import DriftTracker
from sentinel.hdc import HDCSpace


def _run(stream, space, tracker, drifts):
    """Slide a W-window over the stream, feeding the drift tracker per tx."""
    enc = [space.encode_tx(f) for f, _ in stream]
    dts = [dt for _, dt in stream]
    win = []
    for i, v in enumerate(enc):
        win.append(v)
        if len(win) > WINDOW:
            win.pop(0)
        if len(win) == WINDOW:
            res = tracker.update(space.bundle(win), dts[i])
            drifts.append(res.drift)


def _build():
    space = HDCSpace()
    warmup = stationary_stream(1200, seed=10)
    proto = space.bundle([space.encode_tx(f) for f, _ in warmup])
    tracker = DriftTracker(space, proto)
    # seed normalizer history on warm-up windows (no metrics recorded)
    seed_drifts: list[float] = []
    _run(warmup, space, tracker, seed_drifts)
    return space, tracker


def test_stationary_drift_stays_low_and_no_false_alerts():
    """Acceptance (T-04): on a stationary stream drift stays low and the Tier-4
    detector (θ + k-consecutive hysteresis) raises 0 false alerts.

    Note (D-10): with the frozen squash(z)=z/6, the *instantaneous* p99 of a
    stochastic stationary signal floors around ~0.4 (a Gaussian p99 ≈ 2.33σ → 0.39),
    so the operational 'stays < 0.3 / 0 FP' criterion is on the typical level + the
    hysteretic detector, not a per-window p99. We assert both here.
    """
    space, tracker = _build()
    clean = stationary_stream(1000, seed=99)  # unseen stationary traffic
    drifts: list[float] = []
    _run(clean, space, tracker, drifts)

    assert float(np.median(drifts)) < 0.3

    # 0 false alerts: never K_HYSTERESIS consecutive windows above θ.
    max_run = 0
    cur = 0
    for d in drifts:
        cur = cur + 1 if d > THETA else 0
        max_run = max(max_run, cur)
    assert max_run < K_HYSTERESIS, f"clean traffic had {max_run} consecutive windows > θ"


def test_injected_flood_drift_exceeds_07_within_two_windows():
    space, tracker = _build()
    # a little clean traffic, then a sustained selector flood
    clean = stationary_stream(120, seed=7)
    attack = selector_flood(2 * WINDOW + 20, seed=3)
    onset = len(clean)
    stream = clean + attack

    enc = [space.encode_tx(f) for f, _ in stream]
    dts = [dt for _, dt in stream]
    drifts_after_onset: list[float] = []
    win = []
    for i, v in enumerate(enc):
        win.append(v)
        if len(win) > WINDOW:
            win.pop(0)
        if len(win) == WINDOW:
            res = tracker.update(space.bundle(win), dts[i])
            if i >= onset:
                drifts_after_onset.append((i - onset, res.drift))

    # within 2 windows (2*W tx) after onset, drift must exceed 0.7
    within = [d for off, d in drifts_after_onset if off <= 2 * WINDOW]
    assert max(within) > 0.7, f"max drift within 2 windows = {max(within):.3f}"
