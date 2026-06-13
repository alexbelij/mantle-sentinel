"""T-06 acceptance tests (MVP_MATH_SPEC §4): trigger, hysteresis, episode merge."""
from __future__ import annotations

from sentinel.detector import StaticThresholdDetector


def _feed(det, seq, t0=0.0, step=2.0):
    """Feed (drift) values at `step`-second spacing; return list of Triggers."""
    triggers = []
    for i, d in enumerate(seq):
        tr = det.process(d, t0 + i * step)
        if tr:
            triggers.append(tr)
    return triggers


def test_trigger_after_k_consecutive():
    det = StaticThresholdDetector(theta=0.65, k=3)
    triggers = _feed(det, [0.9, 0.9, 0.9])
    assert len(triggers) == 1
    assert triggers[0].new_episode is True


def test_no_trigger_below_k():
    det = StaticThresholdDetector(theta=0.65, k=3)
    assert _feed(det, [0.9, 0.9]) == []  # only 2 consecutive


def test_hysteresis_resets_on_dip():
    det = StaticThresholdDetector(theta=0.65, k=3)
    # 2 high, 1 below (reset), 2 high ⇒ never 3 consecutive ⇒ no trigger
    assert _feed(det, [0.9, 0.9, 0.1, 0.9, 0.9]) == []


def test_single_trigger_per_sustained_run():
    det = StaticThresholdDetector(theta=0.65, k=3)
    triggers = _feed(det, [0.9] * 10)  # one long burst
    assert len(triggers) == 1  # fires once, suppressed until it drops below θ


def test_retrigger_after_drop():
    det = StaticThresholdDetector(theta=0.65, k=3)
    # burst, drop, burst again far apart in time ⇒ two triggers, two episodes
    seq = [0.9, 0.9, 0.9] + [0.0] * 5 + [0.9, 0.9, 0.9]
    triggers = _feed(det, seq, step=120.0)  # 2-min spacing ⇒ second burst > 10 min later
    assert len(triggers) == 2
    assert triggers[0].episode_id != triggers[1].episode_id


def test_episode_merge_within_10_min():
    det = StaticThresholdDetector(theta=0.65, k=3)
    # two triggers close in time (within 10 min) ⇒ same episode
    seq = [0.9, 0.9, 0.9] + [0.0] + [0.9, 0.9, 0.9]
    triggers = _feed(det, seq, step=30.0)  # 30s spacing ⇒ < 10 min apart
    assert len(triggers) == 2
    assert triggers[0].episode_id == triggers[1].episode_id
    assert triggers[1].new_episode is False
