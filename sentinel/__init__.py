"""Mantle Sentinel — HDC Behavioral DNA anomaly detection pipeline."""
from __future__ import annotations

__version__ = "0.1.0"

from sentinel.client import ScanReport, SentinelClient

__all__ = ["SentinelClient", "ScanReport", "__version__"]
