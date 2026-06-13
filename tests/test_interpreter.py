"""T-07 acceptance tests (MVP_MATH_SPEC §5): interpreter names the injected feature,
and the emitted Alert JSON validates against contracts/alert.schema.json."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from bench.synth import channel_window, selector_flood, stationary_stream
from sentinel.alert import Alert, iso_ts, make_alert_id
from sentinel.config import WINDOW
from sentinel.hdc import HDCSpace
from sentinel.interpreter import Interpreter, ProtoSet

SCHEMA = json.loads(
    (Path(__file__).resolve().parents[1] / "contracts" / "alert.schema.json").read_text()
)


def _setup():
    space = HDCSpace()
    warm = [f for f, _ in stationary_stream(1200, seed=10)]
    return space, Interpreter(ProtoSet(space, warm))


@pytest.mark.parametrize("channel", ["selector", "gas", "value", "caller"])
def test_interpreter_names_injected_channel(channel):
    space, interp = _setup()
    window = [f for f, _ in channel_window(channel, WINDOW, seed=3)]
    top = interp.attribute(window, branch="hamming")
    assert top, "expected at least one attributed feature"
    assert top[0].name == channel, f"top feature was {top[0].name}, expected {channel}"


def test_timing_branch_direct_attribution():
    space, interp = _setup()
    top = interp.attribute([], branch="timing")
    assert len(top) == 1 and top[0].name == "timing"


def test_emitted_alert_validates_against_schema():
    space, interp = _setup()
    window = [f for f, _ in selector_flood(WINDOW, seed=3)]
    top = interp.attribute(window, branch="hamming")
    contract = "0x013e138ef6008ae5fdfde29700e3f2bc61d21e3a"
    alert = Alert(
        alert_id=make_alert_id("regime_shift", contract, 96_000_123),
        ts=iso_ts(1_781_000_000),
        block=96_000_123,
        contract=contract,
        alert_type="regime_shift",
        drift=0.93,
        branch="hamming",
        top_features=top,
        window_stats={"window": WINDOW, "hamming": 0.41},
        episode_id="regime-1",
    )
    jsonschema.validate(alert.to_dict(), SCHEMA)


def test_top_features_limited_to_two():
    space, interp = _setup()
    window = [f for f, _ in selector_flood(WINDOW, seed=3)]
    top = interp.attribute(window, branch="hamming", top_n=2)
    assert len(top) <= 2
