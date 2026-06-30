"""Tests for sentinel/plugins/alert_severity.py"""
from __future__ import annotations

import math

import pytest

from sentinel.plugins.alert_severity import Severity, classify, classify_with_label

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def alert_dict(drift: float) -> dict:
    return {"alert_id": "x", "drift": drift, "alert_type": "regime_shift"}


class FakeAlert:
    def __init__(self, drift):
        self.drift = drift


# ---------------------------------------------------------------------------
# Happy path — correct tier assignment
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("drift,expected", [
    (0.0,   Severity.NONE),
    (0.49,  Severity.NONE),
    (0.50,  Severity.WARNING),
    (0.60,  Severity.WARNING),
    (0.699, Severity.WARNING),
    (0.70,  Severity.CRITICAL),
    (0.80,  Severity.CRITICAL),
    (0.899, Severity.CRITICAL),
    (0.90,  Severity.EMERGENCY),
    (0.95,  Severity.EMERGENCY),
    (1.00,  Severity.EMERGENCY),
])
def test_classify_dict_thresholds(drift, expected):
    assert classify(alert_dict(drift)) == expected


@pytest.mark.parametrize("drift,expected", [
    (0.0,  Severity.NONE),
    (0.50, Severity.WARNING),
    (0.70, Severity.CRITICAL),
    (0.90, Severity.EMERGENCY),
])
def test_classify_dataclass_like(drift, expected):
    assert classify(FakeAlert(drift)) == expected


def test_classify_with_label_returns_tuple():
    sev, label = classify_with_label(alert_dict(0.75))
    assert sev == Severity.CRITICAL
    assert label == "CRITICAL"


def test_severity_ordering():
    assert Severity.NONE < Severity.WARNING < Severity.CRITICAL < Severity.EMERGENCY


def test_severity_label():
    assert Severity.EMERGENCY.label() == "EMERGENCY"


# ---------------------------------------------------------------------------
# Edge cases — boundary values
# ---------------------------------------------------------------------------

def test_exact_lower_bound_warning():
    assert classify(alert_dict(0.50)) == Severity.WARNING


def test_exact_lower_bound_critical():
    assert classify(alert_dict(0.70)) == Severity.CRITICAL


def test_exact_lower_bound_emergency():
    assert classify(alert_dict(0.90)) == Severity.EMERGENCY


def test_exactly_1_0_is_emergency():
    assert classify(alert_dict(1.0)) == Severity.EMERGENCY


# ---------------------------------------------------------------------------
# Error handling — bad input
# ---------------------------------------------------------------------------

def test_raises_on_none_alert():
    with pytest.raises(ValueError, match="None"):
        classify(None)


def test_raises_on_missing_drift_key():
    with pytest.raises(ValueError, match="missing required key"):
        classify({"alert_type": "regime_shift"})


def test_raises_on_none_drift():
    with pytest.raises(ValueError, match="is None"):
        classify({"drift": None})


def test_raises_on_non_numeric_drift():
    with pytest.raises(ValueError, match="could not be converted"):
        classify({"drift": "high"})


def test_raises_on_negative_drift():
    with pytest.raises(ValueError, match="outside the valid range"):
        classify(alert_dict(-0.1))


def test_raises_on_drift_above_1():
    with pytest.raises(ValueError, match="outside the valid range"):
        classify(alert_dict(1.01))


def test_raises_on_nan():
    with pytest.raises(ValueError, match="not finite"):
        classify(alert_dict(math.nan))


def test_raises_on_inf():
    with pytest.raises(ValueError, match="not finite"):
        classify(alert_dict(math.inf))


def test_raises_on_bad_type():
    with pytest.raises(TypeError, match=".drift"):
        classify(42)
