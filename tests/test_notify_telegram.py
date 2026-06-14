"""Tests for sentinel.notify_telegram — T-21."""

from sentinel.alert import Alert, FeatureContribution
from sentinel.notify_telegram import notify_telegram


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
        explanation="This is a test explanation.",
    )
    defaults.update(overrides)
    return Alert(**defaults)


def test_dry_run_returns_true():
    """dry_run=True returns True without sending anything."""
    alert = _make_alert()
    result = notify_telegram(alert, dry_run=True)
    assert result is True


def test_missing_token_falls_back(monkeypatch):
    """When TELEGRAM_BOT_TOKEN is unset, falls back to dry-run and returns True."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    alert = _make_alert()
    result = notify_telegram(alert)
    assert result is True


def test_message_format():
    """_format_message produces expected HTML structure."""
    from sentinel.notify_telegram import _format_message

    alert = _make_alert()
    msg = _format_message(alert)
    assert "<b>Mantle Sentinel Alert</b>" in msg
    assert alert.alert_type in msg
    assert "explorer.mantle.xyz" in msg


def test_no_features_no_explanation():
    """Works when top_features is empty and explanation is None."""
    alert = _make_alert(top_features=[], explanation=None)
    result = notify_telegram(alert, dry_run=True)
    assert result is True
