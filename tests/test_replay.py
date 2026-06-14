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


# --- T-18d: Dream-Mode prototype consolidation in the live pipeline -------------

def _regime(alerts):
    return [a for a in alerts if a["alert_type"] == "regime_shift"]


def test_dream_mode_clean_zero_fp():
    """Dream Mode on a clean stream raises no regime FP and actually consolidates."""
    from sentinel.pipeline import build_pipeline, split_warmup

    records = synth_records(3000, seed=3)
    warm, test = split_warmup(records)
    pipe = build_pipeline(records[0].get("contract", "0x"), warm, dream_mode=True)
    regime = []
    for r in test:
        regime += [a.to_dict() for a in pipe.process_tx(r) if a.alert_type == "regime_shift"]
    assert regime == [], f"dream-mode clean replay raised {len(regime)} regime_shift FP"
    assert pipe.dream_count > 0, "dream consolidation never fired on a clean stream"


def test_dream_mode_no_fp_regression():
    """Enabling Dream Mode must never increase the clean false-positive count."""
    records = synth_records(3000, seed=11)
    base = len(_regime(run_replay(records, dream_mode=False)))
    dream = len(_regime(run_replay(records, dream_mode=True)))
    assert dream <= base, f"dream mode increased clean FP ({base} -> {dream})"


def test_dream_mode_still_detects_attack():
    records = synth_records(3000, seed=11)
    alerts = run_replay(records, inject="S1", onset_frac=0.5, seed=7, dream_mode=True)
    assert _regime(alerts), "dream mode suppressed the injected S1 attack"


def test_dream_mode_deterministic():
    import json

    records = synth_records(1500, seed=3)
    a = json.dumps(run_replay(records, inject="S1", seed=1, dream_mode=True), sort_keys=True)
    b = json.dumps(run_replay(records, inject="S1", seed=1, dream_mode=True), sort_keys=True)
    assert a == b, "dream-mode replay is not deterministic"


# --- T-18e: S6 slow-drift survives Dream Mode (boil-the-frog robustness) --------

def test_s6_slow_drift_detected_with_and_without_dream():
    """The slow-drift attack must be caught whether or not Dream Mode is active —
    the rolling-median safe-window gate keeps rising-drift attack windows out of
    consolidation, so the creeping attack is not folded into the baseline."""
    records = synth_records(3000, seed=11)
    base = run_replay(records, inject="S6", onset_frac=0.5, seed=7, dream_mode=False)
    dream = run_replay(records, inject="S6", onset_frac=0.5, seed=7, dream_mode=True)
    assert _regime(base), "S6 slow-drift not detected (dream OFF)"
    assert _regime(dream), "dream mode masked the S6 slow-drift attack"
