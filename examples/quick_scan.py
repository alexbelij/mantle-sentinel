"""Quick scan example — 3 lines to audit a contract."""
from sentinel import SentinelClient

client = SentinelClient()
report = client.scan("0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9")
print(f"USDC.e health: {report.health_score}/100 ({'✅' if report.is_healthy else '⚠️'})")
