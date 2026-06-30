"""sentinel/plugins/alert_severity.py — Alert severity classifier.

Classifies an Alert (or alert dict) into WARNING / CRITICAL / EMERGENCY
based on the drift score thresholds defined in the V2 roadmap.

This is a **pure, stateless function module** — no I/O, no threads, no
side-effects. It does not import or mutate any core sentinel module.

Severity tiers
--------------
    WARNING   (0.50 – 0.70)  → Telegram notification
    CRITICAL  (0.70 – 0.90)  → Telegram + on-chain logAlert()
    EMERGENCY (0.90 – 1.00]  → all of the above + webhook + PagerDuty

    NONE      (< 0.50)        → below threshold, no alert dispatched

Usage
-----
    from sentinel.plugins.alert_severity import classify, Severity

    severity = classify(alert)          # Alert dataclass or dict
    if severity >= Severity.CRITICAL:
        onchain_anchor(alert)
    if severity == Severity.EMERGENCY:
        pagerduty_notify(alert)

Thread safety
-------------
    All public functions are pure (no shared mutable state). Safe to call
    from any number of threads simultaneously.

Error handling
--------------
    * Missing or non-numeric drift field → raises ValueError with a clear
      message (never silently returns NONE for bad input).
    * drift outside [0.0, 1.0] → raises ValueError (overflow / underflow
      guard; HDC drift is always in this range).
    * None drift → raises ValueError.
"""
from __future__ import annotations

from enum import IntEnum
from typing import Any

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class Severity(IntEnum):
    """Ordered severity levels — higher value means more severe.

    Using IntEnum so callers can do ``severity >= Severity.CRITICAL``.
    """
    NONE      = 0
    WARNING   = 1
    CRITICAL  = 2
    EMERGENCY = 3

    def label(self) -> str:
        """Human-readable label for notifications / logging."""
        return self.name  # "WARNING", "CRITICAL", etc.


# Drift-score thresholds (inclusive lower bound, exclusive upper bound)
_THRESHOLDS: tuple[tuple[float, float, Severity], ...] = (
    (0.90, 1.01,  Severity.EMERGENCY),   # 1.01 so exactly 1.0 is caught
    (0.70, 0.90,  Severity.CRITICAL),
    (0.50, 0.70,  Severity.WARNING),
)


def classify(alert: dict[str, Any] | Any) -> Severity:
    """Return the :class:`Severity` for *alert*.

    Parameters
    ----------
    alert:
        Either a plain ``dict`` with a ``"drift"`` key, or an ``Alert``
        dataclass instance (or any object with a ``.drift`` attribute).

    Returns
    -------
    Severity
        ``Severity.NONE`` when drift < 0.50; otherwise WARNING / CRITICAL /
        EMERGENCY.

    Raises
    ------
    ValueError
        * ``alert`` is ``None``.
        * The drift field is missing, ``None``, or not numeric.
        * The drift value is outside the valid range ``[0.0, 1.0]``.
    TypeError
        * ``alert`` is neither a dict nor an object with a ``.drift``
          attribute.
    """
    if alert is None:
        raise ValueError("alert must not be None")

    drift = _extract_drift(alert)
    _validate_drift(drift)

    for lo, hi, severity in _THRESHOLDS:
        if lo <= drift < hi:
            return severity
    return Severity.NONE


def classify_with_label(alert: dict[str, Any] | Any) -> tuple[Severity, str]:
    """Convenience wrapper — returns ``(Severity, label_string)``.

    Example::

        sev, label = classify_with_label(alert)
        # sev   → Severity.CRITICAL
        # label → "CRITICAL"
    """
    sev = classify(alert)
    return sev, sev.label()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_drift(alert: Any) -> float:
    """Extract the drift value from a dict or dataclass-like object."""
    if isinstance(alert, dict):
        if "drift" not in alert:
            raise ValueError(
                "alert dict is missing required key 'drift'. "
                f"Available keys: {list(alert.keys())}"
            )
        raw = alert["drift"]
    elif hasattr(alert, "drift"):
        raw = alert.drift
    else:
        raise TypeError(
            "alert must be a dict with key 'drift' or an object with a "
            f".drift attribute; got {type(alert).__name__}"
        )

    if raw is None:
        raise ValueError("alert.drift is None — expected a float in [0.0, 1.0]")

    try:
        return float(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"alert.drift could not be converted to float: {raw!r}"
        ) from exc


def _validate_drift(drift: float) -> None:
    """Guard against overflow / underflow / NaN from upstream computation."""
    import math
    if math.isnan(drift) or math.isinf(drift):
        raise ValueError(
            f"alert.drift is not finite ({drift!r}). "
            "HDC drift must be a finite float in [0.0, 1.0]."
        )
    if not (0.0 <= drift <= 1.0):
        raise ValueError(
            f"alert.drift={drift!r} is outside the valid range [0.0, 1.0]. "
            "HDC Hamming distance is always normalised to this interval."
        )
