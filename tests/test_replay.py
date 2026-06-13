"""T-08 acceptance tests: end-to-end replay, injection detection, determinism (§7)."""
from __future__ import annotations

from bench.snapshot import synth_records
from sentinel.replay import run_replay


def test_clean_replay_finite_and_low_fp():
    records = synth_records(3000, seed=11)
    alerts = run_replay(records)
    # finite, ordered list; clean traffic ⇒ at most a negligible FP rate (the
    # frozen θ/k detector; the 0-FP target is measured at the spike gate).
    assert isinstance(alerts, list)
    regime = [a for a in alerts if a["alert_type"] == "regime_shift"]
    assert len(regime) <= 2, f"clean replay raised {len(regime)} regime_shift alerts (too many)"


def test_injected_replay_detects_attack_with_attribution():
    records = synth_records(3000, seed=11)
    alerts = run_replay(records, inject="S1", onset_frac=0.5, seed=7)
    regime = [a for a in alerts if a["alert_type"] == "regime_shift"]
    assert regime, "S1 selector flood was not detected"
    # S1 injects a novel selector by a novel caller at 3x cadence — any of those
    # channels is a correct explanation; the interpreter must name one of them.
    injected_channels = {"selector", "caller", "timing"}
    named = [
        a for a in regime
        if a.get("top_features") and a["top_features"][0]["name"] in injected_channels
    ]
    assert named, f"attribution missed all injected channels; got {[a.get('top_features') for a in regime]}"


def test_determinism_byte_identical():
    records = synth_records(1500, seed=3)
    import json

    a = json.dumps(run_replay(records, inject="S1", seed=1), sort_keys=True)
    b = json.dumps(run_replay(records, inject="S1", seed=1), sort_keys=True)
    assert a == b, "replay is not deterministic"
