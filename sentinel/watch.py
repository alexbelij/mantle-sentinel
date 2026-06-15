"""sentinel watch — live behavioral monitoring for a Mantle contract.

Polls Etherscan V2 (or Routescan) every ``--interval`` seconds for new
transactions, streams them through the pipeline, and prints drift + health
status in real time.  Ctrl+C to stop.

Usage:
    python -m sentinel watch 0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9 --interval 30
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime

from sentinel.pipeline import build_pipeline
from sentinel.scan import compute_health_score

# ── Etherscan fetch helpers ────────────────────────────────────────────

ROUTESCAN_V2 = "https://api.routescan.io/v2/network/mainnet/evm/5000/etherscan/api"
ETHERSCAN_V2 = "https://api.etherscan.io/v2/api"


def _api_base() -> tuple[str, str]:
    """Return (base_url, api_key). Prefers ETHERSCAN_KEY; falls back to Routescan."""
    key = os.environ.get("ETHERSCAN_KEY", "")
    if key:
        return ETHERSCAN_V2, key
    return ROUTESCAN_V2, ""


def _selector(input_hex: str) -> str:
    h = input_hex[2:] if input_hex.startswith("0x") else input_hex
    return "0x" + h[:8] if len(h) >= 8 else "0x"


def fetch_txlist_from_block(
    address: str, start_block: int, n: int = 10000
) -> list[dict]:
    """Fetch txlist starting at ``start_block``.

    Returns raw Etherscan-format rows sorted chronologically.
    """
    base, key = _api_base()
    address = address.lower()
    params: dict = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": start_block,
        "endblock": 99999999,
        "page": 1,
        "offset": min(n, 10000),
        "sort": "asc",
    }
    if "etherscan.io" in base:
        params["chainid"] = 5000
        params["apikey"] = key
    url = base + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=40) as resp:
        data = json.loads(resp.read().decode())
    if data.get("status") != "1" or not isinstance(data.get("result"), list):
        return []
    return data["result"]


def _to_raw(txs: list[dict], contract: str) -> list[dict]:
    """Convert Etherscan rows to sentinel raw-tx format."""
    out = []
    for t in txs:
        if (t.get("to") or "").lower() != contract.lower():
            continue
        if t.get("isError") == "1":
            continue
        inp = t.get("input", "0x") or "0x"
        out.append({
            "block_number": int(t["blockNumber"]),
            "block_timestamp": int(t["timeStamp"]),
            "tx_hash": t["hash"],
            "contract": contract.lower(),
            "caller": (t.get("from") or "").lower(),
            "calldata": inp,
            "selector": _selector(inp),
            "gas_used": int(t.get("gasUsed", 0) or 0),
            "value": int(t.get("value", 0) or 0),
            "caller_is_contract": 0,
        })
    out.sort(key=lambda r: (r["block_number"], r["tx_hash"]))
    return out


# ── Progress bar ───────────────────────────────────────────────────────

def _bar(score: int, width: int = 11) -> str:
    filled = max(0, min(width, round(score * width / 100)))
    return "▓" * filled + "░" * (width - filled)


def _status(score: int) -> str:
    if score >= 80:
        return "OK"
    if score >= 50:
        return "⚠️  ELEVATED"
    return "🔴 ALERT"


# ── Main watch loop ───────────────────────────────────────────────────

def watch(
    address: str,
    interval: int = 30,
    warmup_n: int = 500,
) -> None:
    """Run the continuous watch loop. Blocks until Ctrl+C."""
    address = address.lower()

    # Phase 1: warmup
    print(f"Warming up on {warmup_n} historical txs for {address[:10]}…")
    warmup_rows = fetch_txlist_from_block(address, start_block=0, n=warmup_n)
    warmup_raw = _to_raw(warmup_rows, address)
    if len(warmup_raw) < 50:
        print(f"ERROR: only {len(warmup_raw)} txs — need ≥50 for warmup", file=sys.stderr)
        sys.exit(1)

    pipe = build_pipeline(address, warmup_raw)
    # Process warmup through the pipeline to set baselines
    for r in warmup_raw:
        pipe.process_tx(r)

    last_block = max(r["block_number"] for r in warmup_raw)
    all_alerts: list[dict] = []
    drifts: list[float] = []
    print(f"Warmup done. Last block: {last_block}. Polling every {interval}s.\n")

    # Phase 2: poll loop
    try:
        while True:
            rows = fetch_txlist_from_block(address, last_block + 1)
            raw = _to_raw(rows, address)

            if not raw:
                now = datetime.now(UTC).strftime("%H:%M:%S")
                print(f"[{now}] block {last_block}  (no new txs)  polling…")
                time.sleep(interval)
                continue

            for r in raw:
                alerts = pipe.process_tx(r)
                if pipe.last_drift is not None:
                    drifts.append(pipe.last_drift)

                drift = pipe.last_drift or 0.0
                alert_dicts = [{"episode_id": a.episode_id} for a in alerts]
                all_alerts.extend(alert_dicts)

                d_med = drifts[-1] if drifts else 0.0
                d_p99 = drifts[-1] if drifts else 0.0
                score = compute_health_score(alert_dicts, d_med, d_p99)

                now = datetime.now(UTC).strftime("%H:%M:%S")
                block = r["block_number"]
                bar = _bar(score)
                status = _status(score)

                alert_text = ""
                if alerts:
                    types = ", ".join(a.alert_type for a in alerts)
                    alert_text = f": {types}"

                print(
                    f"[{now}] block {block}  drift={drift:.3f}  "
                    f"score={score}  {bar}  {status}{alert_text}"
                )
                last_block = max(last_block, block)

            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\nStopped. Processed up to block {last_block}.")
