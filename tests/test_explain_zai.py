"""Tests for sentinel.explain_zai — T-19."""
from sentinel.alert import Alert, FeatureContribution
from sentinel.explain_zai import explain_alert, profile_contract


def _make_alert(**overrides) -> Alert:
    defaults = dict(
        alert_id="regime_shift-0xdeadbeef-100",
        ts="2025-01-01T00:00:00Z",
        block=100,
        contract="0xDeaDbeeF00000000000000000000000000000001",
        alert_type="regime_shift",
        drift=0.456,
        branch="hamming",
        top_features=[
            FeatureContribution(name="gas_used", contribution=0.12),
            FeatureContribution(name="value_wei", contribution=0.08),
        ],
    )
    defaults.update(overrides)
    return Alert(**defaults)


def test_import():
    """explain_alert is importable and callable."""
    assert callable(explain_alert)


def test_dry_run_returns_nonempty():
    """dry_run=True returns a non-empty string without any API call."""
    alert = _make_alert()
    result = explain_alert(alert, dry_run=True)
    assert isinstance(result, str)
    assert len(result) > 0


def test_dry_run_contains_contract():
    """Canned explanation references the contract address."""
    alert = _make_alert()
    result = explain_alert(alert, dry_run=True)
    assert alert.contract[:10] in result


def test_dry_run_no_features():
    """Works when top_features is empty."""
    alert = _make_alert(top_features=[])
    result = explain_alert(alert, dry_run=True)
    assert isinstance(result, str)
    assert len(result) > 0


def test_profile_contract_dry():
    """profile_contract dry-run returns a summary with health score."""
    report = {
        "contract": "0xtest123456",
        "txs_analyzed": 500,
        "health_score": 92,
        "unique_selectors": 4,
        "drift_median": 0.08,
        "drift_p99": 0.14,
        "alerts": 0,
    }
    result = profile_contract(report, dry_run=True)
    assert "92" in result
    assert "stable" in result


def test_profile_contract_elevated():
    """profile_contract dry-run shows elevated risk for mid scores."""
    report = {
        "contract": "0xtest999999",
        "txs_analyzed": 300,
        "health_score": 55,
        "unique_selectors": 6,
        "drift_median": 0.35,
        "drift_p99": 0.7,
        "alerts": 5,
    }
    result = profile_contract(report, dry_run=True)
    assert "elevated risk" in result
