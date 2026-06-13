"""Telegram alert notifier — T-21.

Sends an Alert summary to a Telegram group/chat via the Bot API.
Requires ``TELEGRAM_BOT_TOKEN`` in the environment; falls back to
dry-run mode when the token is absent.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentinel.alert import Alert

logger = logging.getLogger(__name__)

TELEGRAM_CHAT_ID = int(os.getenv("TELEGRAM_CHAT_ID", "-5274090071"))
_TIMEOUT = 10  # seconds


def _format_message(alert: "Alert") -> str:
    """Build the HTML-formatted Telegram message body."""
    short_addr = f"{alert.contract[:10]}...{alert.contract[-6:]}"
    lines = [
        "\U0001f6a8 <b>Mantle Sentinel Alert</b>",
        f"Contract: <code>{short_addr}</code>",
        f"Type: {alert.alert_type}",
        f"Drift: {alert.drift:.3f} | Branch: {alert.branch}",
        f"Block: {alert.block}",
    ]
    if alert.top_features:
        feat_names = ", ".join(f.name for f in alert.top_features[:2])
        lines.append(f"Top features: {feat_names}")
    if alert.explanation:
        lines.append(f"\U0001f4ac {alert.explanation}")
    lines.append(
        f"\U0001f517 https://explorer.mantle.xyz/address/{alert.contract}"
    )
    return "\n".join(lines)


def notify_telegram(alert: "Alert", dry_run: bool = False) -> bool:
    """Send *alert* to the configured Telegram group.

    Parameters
    ----------
    alert:
        A fully-populated :class:`Alert` with optional ``explanation``.
    dry_run:
        If *True* or ``TELEGRAM_BOT_TOKEN`` is unset, print instead of sending.

    Returns
    -------
    bool
        *True* if the message was sent (or dry-run printed), *False* on error.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if dry_run or not token:
        msg = _format_message(alert)
        logger.info("DRY-RUN: would send to Telegram")
        print("DRY-RUN: would send to Telegram")
        print(msg)
        return True

    try:
        import httpx  # noqa: delay import

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": _format_message(alert),
            "parse_mode": "HTML",
        }
        resp = httpx.post(url, json=payload, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        if data.get("ok"):
            logger.info("Telegram alert sent (message_id=%s)", data["result"]["message_id"])
            return True
        logger.warning("Telegram API returned ok=false: %s", data)
        return False

    except Exception:
        logger.exception("Failed to send Telegram alert")
        return False
