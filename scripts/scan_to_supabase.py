"""Scan 5 Mantle contracts and push results to Supabase scan_history.

Usage:
    SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/scan_to_supabase.py

Runs as GitHub Actions cron every 4 hours.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

from sentinel.scan import scan_contract

CONTRACTS: dict[str, str] = {
    "0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9": "USDC.e",
    "0x78c1b0c915c4faa5fffa6cabf0219da63d7f4cb8": "WMNT",
    "0x201eba5cc46d216ce6dc03f6a759e8e766e956ae": "USDT",
    "0xcda86a272531e8640cd7f1a92c01839911b90bb0": "mETH",
    "0xcfa5ae7c2ce8fadc6426c1ff872ca45378fb7cf3": "Lendle",
}


def push_to_supabase(rows: list[dict]) -> None:
    """POST rows to Supabase REST API."""
    url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1/scan_history"
    key = os.environ["SUPABASE_SERVICE_KEY"]
    body = json.dumps(rows).encode()
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status not in (200, 201):
            print(f"Supabase error: {resp.status} {resp.read().decode()}", file=sys.stderr)
            sys.exit(1)


def main() -> None:
    for var in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY"):
        if var not in os.environ:
            print(f"ERROR: {var} not set", file=sys.stderr)
            sys.exit(1)

    rows: list[dict] = []
    for address, name in CONTRACTS.items():
        print(f"Scanning {name} ({address[:10]}...) ", end="", flush=True)
        try:
            report = scan_contract(address, n_txs=2000, explain=False)
            row = {
                "contract": address,
                "contract_name": name,
                "health_score": report["health_score"],
                "drift_median": report["drift_median"],
                "drift_p99": report["drift_p99"],
                "alert_count": report["alerts"],
                "tx_analyzed": report["txs_analyzed"],
            }
            rows.append(row)
            print(f"→ health={report['health_score']}")
        except Exception as e:
            print(f"FAILED: {e}", file=sys.stderr)
            # Push a row with score=-1 to indicate failure
            rows.append({
                "contract": address,
                "contract_name": name,
                "health_score": -1,
                "drift_median": 0.0,
                "drift_p99": 0.0,
                "alert_count": 0,
                "tx_analyzed": 0,
            })

    print(f"\nPushing {len(rows)} rows to Supabase...")
    push_to_supabase(rows)
    print("Done.")


if __name__ == "__main__":
    main()
