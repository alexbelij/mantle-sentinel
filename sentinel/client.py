"""sentinel.client — high-level SDK interface.

Usage::

    from sentinel import SentinelClient

    client = SentinelClient()
    report = client.scan("0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9")
    print(report.health_score)  # 83
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Optional


class SentinelHealthError(Exception):
    """Raised when a contract's health score is below the required threshold."""

    def __init__(self, address: str, score: int, threshold: int) -> None:
        self.address = address
        self.score = score
        self.threshold = threshold
        super().__init__(
            f"Health check failed for {address}: {score} < {threshold}"
        )


@dataclass
class ScanReport:
    """Result of a behavioral scan."""

    address: str
    health_score: int  # 0-100
    drift_median: float
    drift_p99: float
    alert_count: int
    alerts: list[dict] = field(default_factory=list)
    selector_count: int = 0
    window_count: int = 0
    z_ai_brief: Optional[str] = None

    @property
    def is_healthy(self) -> bool:
        """True if health_score >= 70."""
        return self.health_score >= 70

    def to_dict(self) -> dict:
        """Serialize to plain dict (JSON-safe)."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


class SentinelClient:
    """One-line behavioral audit for any Mantle contract.

    Usage::

        from sentinel import SentinelClient

        client = SentinelClient()
        report = client.scan("0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9")
        print(f"Health: {report.health_score}/100")
    """

    def __init__(
        self,
        rpc_url: str = "https://rpc.mantle.xyz",
        explorer_api: str | None = None,
        zai_api_key: str | None = None,
    ) -> None:
        self.rpc_url = rpc_url
        self.explorer_api = explorer_api or (
            "https://api.routescan.io/v2/network/mainnet/evm/5000/etherscan/api"
        )
        self.zai_api_key = zai_api_key or os.environ.get("ZAI_API_KEY")

    def scan(
        self,
        address: str,
        *,
        tx_limit: int = 5000,
        explain: bool = True,
        min_health: int | None = None,
    ) -> ScanReport:
        """Run full HDC pipeline on a contract. Returns :class:`ScanReport`.

        Args:
            address: Contract address (0x...).
            tx_limit: Maximum transactions to fetch.
            explain: Call Z.ai for a plain-English brief (requires ZAI_API_KEY).
            min_health: If set, raise :class:`SentinelHealthError` when
                        health_score < min_health.
        """
        from sentinel.scan import scan_contract

        should_explain = explain and self.zai_api_key is not None
        raw = scan_contract(address, n_txs=tx_limit, explain=should_explain)
        report = self._raw_to_report(raw)

        if min_health is not None and report.health_score < min_health:
            raise SentinelHealthError(address, report.health_score, min_health)

        return report

    def scan_multiple(
        self,
        addresses: list[str],
        **kwargs,
    ) -> list[ScanReport]:
        """Scan multiple contracts sequentially. Returns list of :class:`ScanReport`."""
        return [self.scan(addr, **kwargs) for addr in addresses]

    @staticmethod
    def _raw_to_report(raw: dict) -> ScanReport:
        """Convert internal report dict to :class:`ScanReport`."""
        return ScanReport(
            address=raw["contract"],
            health_score=raw["health_score"],
            drift_median=raw["drift_median"],
            drift_p99=raw["drift_p99"],
            alert_count=raw["alerts"],
            alerts=raw.get("alert_details", []),
            selector_count=raw.get("unique_selectors", 0),
            window_count=raw.get("txs_analyzed", 0),
            z_ai_brief=raw.get("zai_profile"),
        )
