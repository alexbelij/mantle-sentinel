"""T-17c — Tier-4 detector selection (env flag / build_pipeline / replay).

The static θ/k detector stays the frozen default; BOCPD is an opt-in drop-in
behind the same `process(drift, ts)` interface, selected via SENTINEL_DETECTOR
or the `detector=` argument. Both must raise alerts on an injected attack replay.
"""
from __future__ import annotations

from bench.snapshot import synth_records
from sentinel import config
from sentinel.bocpd import BOCPDDetector
from sentinel.detector import StaticThresholdDetector
from sentinel.pipeline import _make_detector, build_pipeline
from sentinel.replay import run_replay


def _regime(alerts):
    return [a for a in alerts if a["alert_type"] == "regime_shift"]


def test_default_is_static():
    assert config.DEFAULT_DETECTOR == "static"
    assert isinstance(_make_detector(None), StaticThresholdDetector)
    assert isinstance(_make_detector("static"), StaticThresholdDetector)


def test_bocpd_selected_explicitly():
    assert isinstance(_make_detector("bocpd"), BOCPDDetector)
    assert isinstance(_make_detector("BOCPD"), BOCPDDetector)  # case-insensitive


def test_env_flag_resolves(monkeypatch):
    monkeypatch.setenv("SENTINEL_DETECTOR", "bocpd")
    assert config.detector_name() == "bocpd"
    assert isinstance(_make_detector(None), BOCPDDetector)
    monkeypatch.setenv("SENTINEL_DETECTOR", "static")
    assert config.detector_name() == "static"
    assert isinstance(_make_detector(None), StaticThresholdDetector)


def test_build_pipeline_honours_detector_arg():
    warm = synth_records(200, seed=5)
    assert isinstance(build_pipeline("0xabc", warm, detector="bocpd").detector, BOCPDDetector)
    assert isinstance(build_pipeline("0xabc", warm).detector, StaticThresholdDetector)


def test_both_detectors_alert_on_injected_replay():
    records = synth_records(3000, seed=11)
    for det in ("static", "bocpd"):
        inj = run_replay(records, inject="S1", onset_frac=0.5, seed=7, detector=det)
        assert _regime(inj), f"{det} detector raised no regime_shift on injected S1"


def test_env_drives_replay(monkeypatch):
    records = synth_records(1500, seed=3)
    monkeypatch.setenv("SENTINEL_DETECTOR", "bocpd")
    # detector=None ⇒ resolved from env; must still detect the injected attack
    inj = run_replay(records, inject="S1", onset_frac=0.5, seed=7)
    assert _regime(inj), "env-selected BOCPD raised no regime_shift on injected S1"
