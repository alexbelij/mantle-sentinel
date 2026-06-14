"""T-13c: Self-attack demo — warm up Sentinel on VictimCounter normal traffic,
then inject anomalies and verify detection + on-chain alert logging.

Usage:
    python bench/self_attack.py --dry-run
    python bench/self_attack.py --victim 0x... --rpc https://rpc.sepolia.mantle.xyz
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Synthetic transaction generators (for --dry-run and on-chain warmup/attack)
# ---------------------------------------------------------------------------

# VictimCounter ABI selectors (verified on-chain via keccak of the signatures)
SEL_INCREMENT = "0xd09de08a"        # increment()
SEL_RESET = "0xd826f88f"            # reset()
SEL_INCREMENT_BY = "0x03df179c"     # incrementBy(uint256)

# SentinelAlertRegistry selectors
SEL_LOG_ALERT = "0xe6e7b44b"        # logAlert(uint256,uint32,bytes4)
SEL_GET_ALERT_COUNT = "0x40411fc8"  # getAlertCount()

# Mantle mainnet SentinelAlertRegistry (T-13)
MAINNET_REGISTRY = "0x0899E1507CFfefF8620455721F5bd528Bb072187"
MAINNET_RPC = "https://rpc.mantle.xyz"

# 4-byte on-chain tags per alert type (bytes4)
ALERT_TYPE_TAG = {
    "entropy_anomaly": b"ENTR",
    "regime_shift": b"REGM",
    "spam_attack": b"SPAM",
}


def _synth_normal_tx(
    idx: int, contract: str, caller: str, block: int, ts: float, seed: int,
) -> dict:
    """Generate a single normal increment() transaction record."""
    rng = np.random.default_rng(seed + idx)
    return {
        "block_number": block,
        "block_timestamp": round(ts, 3),
        "tx_hash": "0x" + hashlib.sha256(f"norm-{seed}-{idx}".encode()).hexdigest(),
        "contract": contract.lower(),
        "caller": caller.lower(),
        "calldata": SEL_INCREMENT,
        "gas_used": int(abs(rng.normal(50_000, 3_000))),
        "value": 0,
        "caller_is_contract": 0,
    }


def _synth_attack_tx(
    idx: int, contract: str, caller: str, block: int, ts: float, seed: int,
) -> dict:
    """Generate an attack transaction: incrementBy(999999) + random calldata."""
    rng = np.random.default_rng(seed + idx + 10000)
    # S1 + S7 hybrid: novel-ish selector with randomized payload
    random_body = rng.integers(0, 256, 64, dtype=np.uint8).tobytes().hex()
    # Alternate between incrementBy and randomized selectors
    if idx % 2 == 0:
        calldata = SEL_INCREMENT_BY + hex(999999)[2:].zfill(64)
    else:
        calldata = "0xdeadbeef" + random_body
    return {
        "block_number": block,
        "block_timestamp": round(ts, 3),
        "tx_hash": "0x" + hashlib.sha256(f"atk-{seed}-{idx}".encode()).hexdigest(),
        "contract": contract.lower(),
        "caller": caller.lower(),
        "calldata": calldata,
        "gas_used": int(abs(rng.normal(120_000, 15_000))),
        "value": 0,
        "caller_is_contract": 1,
        "label": "attack",
    }


def _generate_dry_run_stream(contract: str, n_warmup: int = 100, n_attack: int = 50, seed: int = 42):
    """Generate a full synthetic stream for dry-run mode."""
    rng = np.random.default_rng(seed)
    caller = "0x" + rng.integers(0, 256, 20, dtype=np.uint8).tobytes().hex()

    block = 39_920_100
    ts = 1_781_100_000.0
    records = []

    # Warmup: 100 normal increment() calls
    for i in range(n_warmup):
        dt = float(abs(rng.normal(12.0, 0.6))) + 0.1
        ts += dt
        block += max(1, round(dt / 2))
        records.append(_synth_normal_tx(i, contract, caller, block, ts, seed))

    inject_start_block = block + 1

    # Attack: 50 anomalous calls (S1+S7 hybrid)
    attacker = "0x" + rng.integers(0, 256, 20, dtype=np.uint8).tobytes().hex()
    for i in range(n_attack):
        dt = float(abs(rng.normal(3.0, 0.5))) + 0.05  # 4× faster
        ts += dt
        block += 1
        records.append(_synth_attack_tx(i, contract, attacker, block, ts, seed))

    return records, inject_start_block


# ---------------------------------------------------------------------------
# Main demo
# ---------------------------------------------------------------------------

def _load_deployments() -> dict:
    """Load contract deployments from contracts/deployments.json."""
    candidates = [
        Path(__file__).resolve().parent.parent / "contracts" / "deployments.json",
        Path("contracts/deployments.json"),
    ]
    for p in candidates:
        if p.exists():
            return json.loads(p.read_text())
    return {}


def run_dry_run(victim_addr: str, verbose: bool = True) -> dict:
    """Execute the self-attack demo in dry-run mode (no RPC calls)."""
    # Lazy imports to avoid import errors if sentinel isn't on PYTHONPATH
    from sentinel.config import WARMUP_FRAC
    from sentinel.pipeline import build_pipeline, split_warmup

    print("=== Self-Attack Demo (dry-run) ===")
    print(f"Victim contract: {victim_addr}")

    records, inject_start_block = _generate_dry_run_stream(victim_addr)
    print(f"Generated {len(records)} synthetic transactions")
    print("  Warmup: 100 normal increment() calls")
    print("  Attack: 50 anomalous calls (S1+S7 hybrid)")
    print(f"  Injection starts at block {inject_start_block}")

    # Split warmup/test using config WARMUP_FRAC
    warmup, test = split_warmup(records, frac=WARMUP_FRAC)
    print(f"  Pipeline warmup: {len(warmup)} txs, test: {len(test)} txs")

    # Build pipeline and run
    pipe = build_pipeline(victim_addr.lower(), warmup)

    all_alerts = []
    for r in test:
        alerts = pipe.process_tx(r)
        for a in alerts:
            all_alerts.append(a)
            if verbose:
                print(f"\n🚨 ALERT at block {a.block}:")
                print(f"   Type: {a.alert_type}")
                print(f"   Branch: {a.branch}")
                print(f"   Drift: {a.drift}")
                print(f"   Episode: {a.episode_id}")
                if a.explanation:
                    print(f"   Explanation: {a.explanation[:120]}...")

    print("\n=== Results ===")
    print(f"Total alerts: {len(all_alerts)}")
    episodes = {a.episode_id for a in all_alerts}
    print(f"Unique episodes: {len(episodes)}")

    regime_alerts = [a for a in all_alerts if a.alert_type == "regime_shift"]
    print(f"Regime shift alerts: {len(regime_alerts)}")

    if regime_alerts:
        first = regime_alerts[0]
        delay = first.block - inject_start_block
        print(f"First regime alert delay: {delay} blocks after injection start")
        print("\nFirst alert JSON:")
        print(json.dumps(first.to_dict(), indent=2))
    else:
        print("⚠️  No regime shift alerts detected (may need more attack txs)")

    # In dry-run, skip on-chain alert logging
    print("\n(dry-run: skipped on-chain alert logging to SentinelAlertRegistry)")
    print("In live mode, would call logAlert() on mainnet registry")
    print("Registry: 0x0899E1507CFfefF8620455721F5bd528Bb072187 (Mantle mainnet)")

    return {
        "alerts": [a.to_dict() for a in all_alerts],
        "inject_start_block": inject_start_block,
        "total_alerts": len(all_alerts),
        "regime_alerts": len(regime_alerts),
        "episodes": len(episodes),
    }


def _w3(rpc_url: str):
    from web3 import Web3

    return Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 30}))


def _send_calls(w3, acct, to: str, datas: list[str], gas: int = 250_000) -> list[str]:
    """Send a batch of contract calls from one signer using locally-incremented
    nonces (Mantle Sepolia's sequencer lags `latest`, so we never re-query mid-batch).
    Returns the list of tx hashes in order."""
    chain_id = w3.eth.chain_id
    gas_price = w3.eth.gas_price
    nonce = w3.eth.get_transaction_count(acct.address, "pending")
    hashes = []
    for i, data in enumerate(datas):
        tx = {
            "to": w3.to_checksum_address(to),
            "data": data,
            "value": 0,
            "gas": gas,
            "gasPrice": gas_price,
            "nonce": nonce + i,
            "chainId": chain_id,
        }
        signed = acct.sign_transaction(tx)
        h = w3.eth.send_raw_transaction(signed.raw_transaction)
        hashes.append(h.hex() if not isinstance(h, str) else h)
    return ["0x" + hh if not hh.startswith("0x") else hh for hh in hashes]


def _wait_receipts(w3, hashes: list[str], timeout: int = 180) -> list[dict]:
    receipts = []
    for h in hashes:
        rcpt = w3.eth.wait_for_transaction_receipt(h, timeout=timeout)
        receipts.append(rcpt)
    return receipts


def _incrementby_calldata(value: int) -> str:
    return SEL_INCREMENT_BY + hex(value)[2:].zfill(64)


def _hx(h) -> str:
    """Normalise a web3 tx-hash (bytes/HexBytes/str) to a 0x-prefixed hex string."""
    s = h if isinstance(h, str) else h.hex()
    return s if s.startswith("0x") else "0x" + s


def run_live(
    victim_addr: str,
    rpc_url: str,
    pk: str,
    n_warmup: int = 30,
    n_attack: int = 8,
    anchor: bool = True,
) -> dict:
    """Execute the self-attack demo with REAL on-chain transactions.

    Reliable-detection recipe (see docs/status notes): warm the entropy filter
    with >=20 low-entropy incrementBy(small) calls (same selector + length
    bucket), then send incrementBy(random 256-bit) high-entropy calls which fire
    an `entropy_anomaly` per tx (Tier 1, no window needed). The first alert is
    anchored on the Mantle mainnet SentinelAlertRegistry via logAlert().
    """
    import numpy as np
    from eth_abi import encode as abi_encode
    from eth_account import Account

    from sentinel.pipeline import build_pipeline

    acct = Account.from_key(pk)
    w3 = _w3(rpc_url)
    victim = w3.to_checksum_address(victim_addr)
    rng = np.random.default_rng(1337)
    ts_cache: dict[int, int] = {}

    print("=== Self-Attack Demo (LIVE) ===")
    print(f"Victim:  {victim}  (chainId {w3.eth.chain_id})")
    print(f"Signer:  {acct.address}")
    print(f"Balance: {w3.from_wei(w3.eth.get_balance(acct.address), 'ether')} MNT")

    # --- 1. Warm-up: low-entropy incrementBy(k) ---------------------------
    print(f"\n[1/4] Sending {n_warmup} benign incrementBy() warm-up txs...")
    warm_calldatas = [_incrementby_calldata(1 + (i % 9)) for i in range(n_warmup)]
    warm_hashes = _send_calls(w3, acct, victim, warm_calldatas)
    warm_rcpts = _wait_receipts(w3, warm_hashes)
    warmup = []
    for rcpt, cd in zip(warm_rcpts, warm_calldatas, strict=True):
        blk = int(rcpt["blockNumber"])
        if blk not in ts_cache:
            ts_cache[blk] = int(w3.eth.get_block(blk)["timestamp"])
        warmup.append({
            "block_number": blk,
            "block_timestamp": float(ts_cache[blk]),
            "tx_hash": _hx(rcpt["transactionHash"]),
            "contract": victim.lower(),
            "caller": acct.address.lower(),
            "calldata": cd,
            "gas_used": int(rcpt["gasUsed"]),
            "value": 0,
            "caller_is_contract": 0,
        })
    print(f"      mined {len(warmup)} warm-up txs (blocks "
          f"{warmup[0]['block_number']}..{warmup[-1]['block_number']})")

    # --- 2. Build pipeline on real warm-up traffic ------------------------
    print("[2/4] Building Sentinel pipeline on warm-up traffic...")
    pipe = build_pipeline(victim.lower(), warmup)

    # --- 3. Attack: high-entropy incrementBy(random 256-bit) --------------
    print(f"[3/4] Sending {n_attack} high-entropy incrementBy() attack txs...")
    atk_calldatas = [
        SEL_INCREMENT_BY + rng.integers(0, 256, 32, dtype=np.uint8).tobytes().hex()
        for _ in range(n_attack)
    ]
    atk_hashes = _send_calls(w3, acct, victim, atk_calldatas)
    atk_rcpts = _wait_receipts(w3, atk_hashes)

    alerts = []
    for rcpt, cd in zip(atk_rcpts, atk_calldatas, strict=True):
        blk = int(rcpt["blockNumber"])
        if blk not in ts_cache:
            ts_cache[blk] = int(w3.eth.get_block(blk)["timestamp"])
        rec = {
            "block_number": blk,
            "block_timestamp": float(ts_cache[blk]),
            "tx_hash": _hx(rcpt["transactionHash"]),
            "contract": victim.lower(),
            "caller": acct.address.lower(),
            "calldata": cd,
            "gas_used": int(rcpt["gasUsed"]),
            "value": 0,
            "caller_is_contract": 0,
        }
        for a in pipe.process_tx(rec):
            alerts.append((a, rec))
            print(f"      🚨 {a.alert_type} @ block {a.block} "
                  f"(drift {a.drift}, branch {a.branch}) tx {rec['tx_hash']}")

    if not alerts:
        print("      ⚠️  No alert fired — aborting on-chain anchor.")
        return {"status": "no_alert", "warmup": len(warmup), "attack": n_attack}

    # --- 4. Anchor first alert on Mantle mainnet registry -----------------
    first_alert, first_rec = alerts[0]
    result = {
        "status": "ok",
        "victim": victim,
        "chain_id": w3.eth.chain_id,
        "warmup_txs": len(warmup),
        "attack_txs": n_attack,
        "alerts": len(alerts),
        "first_alert": first_alert.to_dict(),
        "attack_tx_hash": first_rec["tx_hash"],
    }

    if not anchor:
        return result

    print("[4/4] Anchoring first alert on Mantle mainnet SentinelAlertRegistry...")
    mw3 = _w3(MAINNET_RPC)
    tag = ALERT_TYPE_TAG.get(first_alert.alert_type, b"ALRT")
    window_id = int(first_alert.block)
    drift_score = int(round(min(float(first_alert.drift), 1.0) * 1_000_000))
    payload = abi_encode(["uint256", "uint32", "bytes4"], [window_id, drift_score, tag])
    log_data = SEL_LOG_ALERT + payload.hex()
    [anchor_hash] = _send_calls(mw3, acct, MAINNET_REGISTRY, [log_data], gas=200_000)
    arcpt = mw3.eth.wait_for_transaction_receipt(anchor_hash, timeout=180)
    first_alert.onchain_tx = anchor_hash
    result["first_alert"] = first_alert.to_dict()
    count = int(
        mw3.eth.call({"to": mw3.to_checksum_address(MAINNET_REGISTRY), "data": SEL_GET_ALERT_COUNT}).hex(),
        16,
    )
    result.update({
        "anchor_tx": anchor_hash,
        "anchor_block": int(arcpt["blockNumber"]),
        "anchor_status": int(arcpt["status"]),
        "registry": MAINNET_REGISTRY,
        "registry_alert_count": count,
        "window_id": window_id,
        "drift_score": drift_score,
        "alert_type_tag": "0x" + tag.hex(),
        "explorer_url": f"https://explorer.mantle.xyz/tx/{anchor_hash}",
    })
    print(f"      ✅ anchored: {anchor_hash} (status {int(arcpt['status'])}, "
          f"registry count now {count})")
    print(f"      🔗 https://explorer.mantle.xyz/tx/{anchor_hash}")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="T-13c: Self-attack demo")
    ap.add_argument("--victim", help="Victim contract address")
    ap.add_argument("--rpc", default="https://rpc.sepolia.mantle.xyz", help="RPC URL")
    ap.add_argument("--dry-run", action="store_true", help="Use synthetic txs, no RPC calls")
    ap.add_argument("--quiet", action="store_true", help="Suppress per-alert output")
    ap.add_argument("--warmup", type=int, default=30, help="live: # warm-up txs")
    ap.add_argument("--attack", type=int, default=8, help="live: # attack txs")
    ap.add_argument("--no-anchor", action="store_true", help="live: skip mainnet logAlert")
    args = ap.parse_args()

    # Default victim from deployments.json
    if not args.victim:
        deploys = _load_deployments()
        if "victim_testnet" in deploys:
            args.victim = deploys["victim_testnet"]["address"]
        else:
            args.victim = "0x1f88f063C00893642Ca4a74FE4d25Bf20c468E64"

    if args.dry_run:
        result = run_dry_run(args.victim, verbose=not args.quiet)
    else:
        import os

        pk = os.getenv("MANTLE_PRIVATE_KEY")
        if not pk:
            print("ERROR: set MANTLE_PRIVATE_KEY in the environment for live mode.")
            return 1
        result = run_live(
            args.victim, args.rpc, pk,
            n_warmup=args.warmup, n_attack=args.attack, anchor=not args.no_anchor,
        )
        out = Path("bench/runs/self_attack_live.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2))
        print(f"\nResult written to {out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
