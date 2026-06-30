"""
sentinel/plugins/webhook.py
===========================
Isolated webhook output plugin — does NOT touch pipeline.py / bocpd.py / watch.py.

Usage (opt-in, one line in your runner):
    from sentinel.plugins.webhook import WebhookNotifier
    wh = WebhookNotifier(url="https://your-endpoint.example.com/alerts")
    wh.notify(alert_dict)        # fire-and-forget POST

The plugin is completely standalone: import it where you need it, or ignore it.
"""

from __future__ import annotations

import json
import logging
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    url: str
    timeout: int = 10          # seconds
    max_retries: int = 3
    retry_delay: float = 1.0   # seconds between retries
    secret_header: str | None = None   # e.g. "X-Sentinel-Secret"
    secret_value: str | None = None


class WebhookNotifier:
    """
    Fire-and-forget HTTP POST notifier.

    Parameters
    ----------
    url : str
        Endpoint that receives alert payloads as JSON POST bodies.
    timeout : int
        Request timeout in seconds (default 10).
    max_retries : int
        Number of retry attempts on transient errors (default 3).
    secret_header / secret_value : str | None
        Optional HMAC-style shared-secret header for request verification.

    Example
    -------
    >>> wh = WebhookNotifier(url="https://hooks.example.com/sentinel")
    >>> wh.notify({"alert_type": "regime_shift", "drift_score": 0.82})
    """

    def __init__(
        self,
        url: str,
        timeout: int = 10,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        secret_header: str | None = None,
        secret_value: str | None = None,
    ) -> None:
        if not url.startswith(("https://", "http://")):
            raise ValueError(f"WebhookNotifier: url must start with https:// or http://, got {url!r}")
        self._cfg = WebhookConfig(
            url=url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            secret_header=secret_header,
            secret_value=secret_value,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def notify(self, payload: dict[str, Any]) -> None:
        """Send *payload* asynchronously (non-blocking)."""
        t = threading.Thread(target=self._send_with_retry, args=(payload,), daemon=True)
        t.start()

    def notify_sync(self, payload: dict[str, Any]) -> bool:
        """Send *payload* synchronously. Returns True on success."""
        return self._send_with_retry(payload)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _send_with_retry(self, payload: dict[str, Any]) -> bool:
        import time

        body = json.dumps(payload, default=str).encode()
        headers = {"Content-Type": "application/json"}
        if self._cfg.secret_header and self._cfg.secret_value:
            headers[self._cfg.secret_header] = self._cfg.secret_value

        for attempt in range(1, self._cfg.max_retries + 1):
            try:
                req = urllib.request.Request(
                    self._cfg.url, data=body, headers=headers, method="POST"
                )
                with urllib.request.urlopen(req, timeout=self._cfg.timeout) as resp:
                    status = resp.status
                if status < 300:
                    logger.debug("Webhook delivered (attempt %d, status %d)", attempt, status)
                    return True
                logger.warning("Webhook HTTP %d (attempt %d/%d)", status, attempt, self._cfg.max_retries)
            except urllib.error.URLError as exc:
                logger.warning("Webhook error (attempt %d/%d): %s", attempt, self._cfg.max_retries, exc)
            except Exception as exc:  # noqa: BLE001
                logger.error("Webhook unexpected error: %s", exc)
                return False

            if attempt < self._cfg.max_retries:
                time.sleep(self._cfg.retry_delay)

        logger.error("Webhook failed after %d attempts to %s", self._cfg.max_retries, self._cfg.url)
        return False
