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


# ── T-22: verify _fired reset allows new episode detection ──────────────

def test_new_episode_detected_after_previous_ends():
    """T-22 regression: after a drift episode ends (drift drops below threshold
    for k windows), a *new* drift episode must still be detectable. The _fired
    flag must be reset when _consecutive_count drops to 0."""
    det = StaticThresholdDetector(theta=0.65, k=3)

    # Episode 1: 3 consecutive above θ → triggers
    ep1 = _feed(det, [0.9, 0.9, 0.9], t0=0.0, step=2.0)
    assert len(ep1) == 1, "Episode 1 should fire"

    # Drift drops below threshold for several windows → episode ends
    below = _feed(det, [0.1, 0.1, 0.1, 0.1, 0.1], t0=100.0, step=2.0)
    assert below == [], "No triggers while below threshold"

    # Episode 2: 3 more consecutive above θ → must trigger again
    # Use t0 far enough apart to get a distinct episode via episode collapsing
    ep2 = _feed(det, [0.9, 0.9, 0.9], t0=1200.0, step=2.0)
    assert len(ep2) == 1, "Episode 2 must fire — _fired was reset when drift dropped"
    assert ep2[0].new_episode is True
    assert ep1[0].episode_id != ep2[0].episode_id


def test_multiple_episodes_cycle():
    """T-22: verify multiple episode start/end cycles work."""
    det = StaticThresholdDetector(theta=0.65, k=3)
    all_triggers = []

    for cycle in range(5):
        t0 = cycle * 2000.0  # well beyond 10-min episode collapse
        # Trigger episode
        trigs = _feed(det, [0.9, 0.9, 0.9], t0=t0, step=2.0)
        all_triggers.extend(trigs)
        # Cool down
        _feed(det, [0.1] * 5, t0=t0 + 100, step=2.0)

    assert len(all_triggers) == 5, f"Expected 5 episodes, got {len(all_triggers)}"
    episode_ids = [t.episode_id for t in all_triggers]
    assert len(set(episode_ids)) == 5, "All 5 episodes should have distinct IDs"


def test_reset_method():
    """T-22: verify explicit reset() clears detector state."""
    det = StaticThresholdDetector(theta=0.65, k=3)

    # Fire first episode
    _feed(det, [0.9, 0.9, 0.9])
    assert det._fired is True
    assert det._consec == 3

    # Reset
    det.reset()
    assert det._fired is False
    assert det._consec == 0
