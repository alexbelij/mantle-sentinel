"""T-17 acceptance tests — BOCPD detector.

Two things are asserted:
1. Interface conformance — BOCPDDetector is a drop-in for StaticThresholdDetector
   (``process(drift, ts) -> Trigger | None``, episode tracking, ``reset()``).
2. AB2 comparison — on an S1-style regime shift (low drift baseline → sustained
   high drift), BOCPD detects the change *no later than* the static θ/k detector.
"""
from __future__ import annotations

import numpy as np

from sentinel.bocpd import BOCPDDetector
from sentinel.detector import StaticThresholdDetector, Trigger


def _feed(det, seq, t0=0.0, step=2.0):
    triggers = []
    for i, d in enumerate(seq):
        tr = det.process(d, t0 + i * step)
        if tr:
            triggers.append((i, tr))
    return triggers


def _s1_drift_series(seed: int = 0, n_base: int = 45, n_shift: int = 40) -> np.ndarray:
    """Low-drift baseline then a sustained high-drift regime (S1 selector flood
    pushes per-window drift from ~baseline to ~1.0 once the novel selector floods
    the window)."""
    rng = np.random.default_rng(seed)
    base = np.clip(rng.normal(0.12, 0.03, n_base), 0.0, 1.0)
    shift = np.clip(rng.normal(0.90, 0.03, n_shift), 0.0, 1.0)
    return np.concatenate([base, shift])


# ── interface conformance ───────────────────────────────────────────────

def test_returns_trigger_type_on_changepoint():
    det = BOCPDDetector(hazard=100, p_thresh=0.5)
    triggers = _feed(det, _s1_drift_series())
    assert len(triggers) >= 1
    assert isinstance(triggers[0][1], Trigger)
    assert triggers[0][1].new_episode is True


def test_no_false_alarm_on_stationary_stream():
    det = BOCPDDetector(hazard=100, p_thresh=0.5)
    rng = np.random.default_rng(7)
    flat = np.clip(rng.normal(0.12, 0.03, 120), 0.0, 1.0)
    assert _feed(det, flat) == []


def test_single_trigger_per_changepoint():
    det = BOCPDDetector(hazard=100, p_thresh=0.5)
    triggers = _feed(det, _s1_drift_series())
    # The run-length collapse is a one-shot event; it must not re-fire every
    # subsequent high-drift window.
    assert len(triggers) == 1


def test_two_changepoints_two_episodes():
    det = BOCPDDetector(hazard=100, p_thresh=0.5)
    rng = np.random.default_rng(3)
    seg = lambda m, n: np.clip(rng.normal(m, 0.03, n), 0.0, 1.0)  # noqa: E731
    seq = np.concatenate([seg(0.12, 40), seg(0.90, 25), seg(0.12, 40), seg(0.90, 25)])
    # 30s spacing keeps episodes < 10 min apart only if close; use big spacing so
    # the two regime shifts land in distinct episodes.
    triggers = _feed(det, seq, step=120.0)
    assert len(triggers) == 2
    assert triggers[0][1].episode_id != triggers[1][1].episode_id


def test_reset_clears_state():
    det = BOCPDDetector(hazard=100, p_thresh=0.5)
    _feed(det, _s1_drift_series())
    det.reset()
    assert det._fired is False
    assert len(det._R) == 1
    assert det._R[0] == 1.0


# ── AB2: BOCPD detects S1 no worse than static ──────────────────────────

def _first_idx(triggers) -> int:
    return triggers[0][0] if triggers else 10**9


def test_bocpd_detects_s1_no_worse_than_static():
    series = _s1_drift_series()
    onset = 45  # first high-drift index

    static = StaticThresholdDetector(theta=0.65, k=3)
    bocpd = BOCPDDetector(hazard=100, p_thresh=0.5)

    s_idx = _first_idx(_feed(static, series))
    b_idx = _first_idx(_feed(bocpd, series))

    # both must actually fire after the onset
    assert s_idx >= onset and s_idx < 10**9, "static should detect the shift"
    assert b_idx >= onset and b_idx < 10**9, "bocpd should detect the shift"
    # "no worse": BOCPD fires no later than the static θ/k detector
    assert b_idx <= s_idx, f"BOCPD ({b_idx}) detected later than static ({s_idx})"


def test_bocpd_detects_across_seeds():
    """Robustness: BOCPD detects the regime shift (and no worse than static) for
    several independent S1 realisations."""
    for seed in range(6):
        series = _s1_drift_series(seed=seed)
        static = StaticThresholdDetector(theta=0.65, k=3)
        bocpd = BOCPDDetector(hazard=100, p_thresh=0.5)
        s_idx = _first_idx(_feed(static, series))
        b_idx = _first_idx(_feed(bocpd, series))
        assert b_idx < 10**9, f"seed {seed}: BOCPD missed the shift"
        assert b_idx <= s_idx, f"seed {seed}: BOCPD ({b_idx}) later than static ({s_idx})"
