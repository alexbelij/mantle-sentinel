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
import sys
import time
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Synthetic transaction generators (for --dry-run and on-chain warmup/attack)
# ---------------------------------------------------------------------------

# VictimCounter ABI selectors
SEL_INCREMENT = "0xd09de08a"        # increment()
SEL_RESET = "0xd826f88f"            # reset()
SEL_INCREMENT_BY = "0x30f3f0db"     # incrementBy(uint256)


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

    print(f"=== Self-Attack Demo (dry-run) ===")
    print(f"Victim contract: {victim_addr}")

    records, inject_start_block = _generate_dry_run_stream(victim_addr)
    print(f"Generated {len(records)} synthetic transactions")
    print(f"  Warmup: 100 normal increment() calls")
    print(f"  Attack: 50 anomalous calls (S1+S7 hybrid)")
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

    print(f"\n=== Results ===")
    print(f"Total alerts: {len(all_alerts)}")
    episodes = {a.episode_id for a in all_alerts}
    print(f"Unique episodes: {len(episodes)}")

    regime_alerts = [a for a in all_alerts if a.alert_type == "regime_shift"]
    print(f"Regime shift alerts: {len(regime_alerts)}")

    if regime_alerts:
        first = regime_alerts[0]
        delay = first.block - inject_start_block
        print(f"First regime alert delay: {delay} blocks after injection start")
        print(f"\nFirst alert JSON:")
        print(json.dumps(first.to_dict(), indent=2))
    else:
        print("⚠️  No regime shift alerts detected (may need more attack txs)")

    # In dry-run, skip on-chain alert logging
    print(f"\n(dry-run: skipped on-chain alert logging to SentinelAlertRegistry)")
    print(f"In live mode, would call logAlert() on mainnet registry")
    print(f"Registry: 0x593C9a4dd6806510e379e30481eaCd27d2016FbE (Mantle mainnet)")

    return {
        "alerts": [a.to_dict() for a in all_alerts],
        "inject_start_block": inject_start_block,
        "total_alerts": len(all_alerts),
        "regime_alerts": len(regime_alerts),
        "episodes": len(episodes),
    }


def run_live(victim_addr: str, rpc_url: str, pk: str) -> dict:
    """Execute the self-attack demo with real RPC calls.

    1. Send 100 normal increment() txs to VictimCounter (warmup)
    2. Send 50 anomalous txs (attack)
    3. Feed each tx to Sentinel pipeline
    4. Log alerts to SentinelAlertRegistry on mainnet
    """
    print(f"=== Self-Attack Demo (LIVE) ===")
    print(f"Victim: {victim_addr}")
    print(f"RPC: {rpc_url}")
    print("⚠️  Live mode sends real transactions. Use --dry-run to test first.")
    print("Live mode implementation requires funded account and gas.")
    print("Use --dry-run for testing.")
    return {"status": "live_mode_placeholder"}


def main() -> int:
    ap = argparse.ArgumentParser(description="T-13c: Self-attack demo")
    ap.add_argument("--victim", help="Victim contract address")
    ap.add_argument("--rpc", default="https://rpc.sepolia.mantle.xyz", help="RPC URL")
    ap.add_argument("--dry-run", action="store_true", help="Use synthetic txs, no RPC calls")
    ap.add_argument("--quiet", action="store_true", help="Suppress per-alert output")
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
        pk = "0x3946db779fcc0b64c5e0134947842fd2c67b165db14d4bd37aa4386de0ceaa23"
        result = run_live(args.victim, args.rpc, pk)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
