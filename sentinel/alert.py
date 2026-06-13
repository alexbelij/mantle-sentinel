"""Alert JSON model (contracts/alert.schema.json) — T-07.

Deterministic, serialisable alert records emitted by every tier. The schema is the
contract between the pipeline, the Z.ai explainer (T-19), Telegram (T-21) and the
on-chain anchor (T-13).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime


def iso_ts(unix_ts: float) -> str:
    return datetime.fromtimestamp(int(unix_ts), tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_alert_id(alert_type: str, contract: str, block: int) -> str:
    return f"{alert_type}-{contract.lower()}-{block}"


@dataclass
class FeatureContribution:
    name: str
    contribution: float


@dataclass
class Alert:
    alert_id: str
    ts: str                      # ISO date-time
    block: int
    contract: str
    alert_type: str             # spam_attack | entropy_anomaly | regime_shift
    drift: float
    branch: str                 # hamming | timing | entropy | spam
    top_features: list[FeatureContribution] = field(default_factory=list)
    window_stats: dict = field(default_factory=dict)
    episode_id: str | None = None
    explanation: str | None = None
    onchain_tx: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        # drop optionals that are None so the record stays schema-clean
        for k in ("episode_id", "explanation", "onchain_tx"):
            if d[k] is None:
                d.pop(k)
        if not d["top_features"]:
            d.pop("top_features")
        if not d["window_stats"]:
            d.pop("window_stats")
        return d
