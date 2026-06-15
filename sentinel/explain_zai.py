"""Z.ai-powered alert explainer — T-19.

Given a filled Alert object, call Z.ai (OpenAI-compatible) and return a
2-3 sentence human explanation.  STRICT template — may only restate Tier 5
structured findings.  No hallucination.

Dry-run mode (``ZAI_API_KEY`` unset or ``dry_run=True``) returns a canned
explanation so CI never touches the live API.
"""
from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentinel.alert import Alert

logger = logging.getLogger(__name__)

# Verified working Z.ai endpoint + free-tier model (override via env).
# glm-4.5-flash is free; glm-4.6 / glm-4.5-air require a paid resource package (429).
ZAI_BASE_URL = os.getenv("ZAI_BASE_URL", "https://api.z.ai/api/paas/v4")
ZAI_MODEL = os.getenv("ZAI_MODEL", "glm-4.5-flash")
_TIMEOUT = 30  # seconds (glm-4.5-flash is a reasoning model; 10s truncates the live call)


def _canned(alert: Alert) -> str:
    """Pre-generated explanation used in dry-run / fallback mode."""
    feats = ", ".join(f.name for f in (alert.top_features or [])[:2]) or "N/A"
    return (
        f"Contract {alert.contract[:10]}… triggered a {alert.alert_type} alert "
        f"at block {alert.block} with drift score {alert.drift:.3f} "
        f"(branch: {alert.branch}). Top features: {feats}."
    )


def explain_alert(alert: Alert, dry_run: bool = False) -> str:
    """Return a 2-3 sentence plain-English explanation of *alert*.

    Parameters
    ----------
    alert:
        A fully-populated :class:`Alert` instance.
    dry_run:
        If *True* (or ``ZAI_API_KEY`` is not set), skip the API call and
        return a deterministic canned explanation.

    Returns
    -------
    str
        Human-readable explanation (never empty).
    """
    api_key = os.getenv("ZAI_API_KEY", "")
    if dry_run or not api_key:
        logger.info("explain_alert: dry-run mode (no API call)")
        return _canned(alert)

    # --- live call ---
    try:
        import httpx  # local import keeps module import-light

        features_list = [f.name for f in (alert.top_features or [])]
        system_msg = (
            "You are a concise security explainer for blockchain monitoring "
            "alerts. Report only what the data shows. Max 3 sentences."
        )
        user_msg = (
            f"Contract {alert.contract} triggered a {alert.alert_type} alert "
            f"at block {alert.block}. Drift score: {alert.drift:.3f} "
            f"(branch: {alert.branch}). Top contributing features: "
            f"{features_list}. Explain in plain English for a DeFi user."
        )

        resp = httpx.post(
            f"{ZAI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": ZAI_MODEL,
                "messages": [
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": user_msg},
                ],
                # GLM-4.5 family are reasoning models: the hidden thinking phase
                # consumes completion tokens, so a small cap (e.g. 200) can truncate
                # the visible answer to empty. Give enough room for thinking + answer.
                "max_tokens": 800,
                "temperature": 0.3,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        text: str = data["choices"][0]["message"]["content"].strip()
        if text:
            return text
        logger.warning("Z.ai returned empty content — falling back to canned")
        return _canned(alert)

    except Exception:
        logger.exception("Z.ai call failed — falling back to canned explanation")
        return _canned(alert)
