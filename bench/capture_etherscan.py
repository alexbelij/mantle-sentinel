"""T-02 — capture a real Mantle contract snapshot via Etherscan V2 (chainid=5000).

Pulls external transactions TO a contract (account/txlist), maps to the raw schema
(BENCHMARK_PROTOCOL §1.2), and writes raw.jsonl + .sha256 manifest. The API key is
read from $ETHERSCAN_KEY — never commit it.

    uv run python -m bench.capture_etherscan <address> [--n 3000]
"""
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request

from bench.snapshot import write_snapshot

V2 = "https://api.etherscan.io/v2/api"
MANTLE = 5000


def _selector(input_hex: str) -> str:
    h = input_hex[2:] if input_hex.startswith("0x") else input_hex
    return "0x" + h[:8] if len(h) >= 8 else "0x"


def fetch_txlist(address: str, n: int, key: str) -> list[dict]:
    address = address.lower()
    rows: list[dict] = []
    page, offset = 1, min(n, 10000)
    while len(rows) < n:
        params = {
            "chainid": MANTLE, "module": "account", "action": "txlist",
            "address": address, "startblock": 0, "endblock": 99999999,
            "page": page, "offset": offset, "sort": "desc", "apikey": key,
        }
        url = V2 + "?" + urllib.parse.urlencode(params)
        with urllib.request.urlopen(url, timeout=40) as resp:
            data = json.loads(resp.read().decode())
        if data.get("status") != "1" or not data.get("result"):
            break
        rows.extend(data["result"])
        if len(data["result"]) < offset:
            break
        page += 1
        time.sleep(0.25)
    return rows[:n]


def to_raw(txs: list[dict], contract: str) -> list[dict]:
    out = []
    for t in txs:
        if (t.get("to") or "").lower() != contract.lower():
            continue  # only direct calls to the contract
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
    # chronological order for replay
    out.sort(key=lambda r: (r["block_number"], r["tx_hash"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("address")
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    key = os.environ["ETHERSCAN_KEY"]
    txs = fetch_txlist(args.address, args.n, key)
    raw = to_raw(txs, args.address)
    out = args.out or f"bench/data/{args.address.lower()}/raw.jsonl"
    write_snapshot(raw, out)
    print(f"captured {len(raw)} direct txs -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
