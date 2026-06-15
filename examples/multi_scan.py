"""Scan top 5 Mantle DeFi contracts."""
from sentinel import SentinelClient

CONTRACTS = {
    "USDC.e": "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9",
    "WMNT":   "0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8",
    "USDT":   "0x201eba5cc46d216ce6dc03f6a759e8e766e956ae",
    "mETH":   "0xcda86a272531e8640cd7f1a92c01839911b90bb0",
    "Lendle": "0xcfA5aEbab31D0b7c02db0B3e05aeA3EEAfb96daB",
}

client = SentinelClient()
for name, addr in CONTRACTS.items():
    report = client.scan(addr)
    status = "✅" if report.is_healthy else "⚠️"
    print(f"{name:10s} {report.health_score:3d}/100 {status}  alerts={report.alert_count}")
