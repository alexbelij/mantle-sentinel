"""sentinel scan — one-command behavioral audit for any Mantle contract.

Usage:
    python -m sentinel scan 0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9
    ZAI_API_KEY=... python -m sentinel scan 0x09bc4e... --explain
"""
from __future__ import annotations

import os
import sys
from collections import Counter

import numpy as np

from bench.capture_etherscan import fetch_txlist, to_raw
from sentinel.pipeline import build_pipeline, split_warmup


def compute_health_score(
    alert_details: list[dict],
    drift_median: float,
    drift_p99: float,
) -> int:
    """0-100 health score. 100 = perfectly stable, 0 = critical anomaly.

    Formula (deterministic — same data ⇒ same score):
        base = 100
        - min(30, num_episodes * 2)          # alert episodes
        - min(25, 50 * max(0, drift_p99 - 0.5))  # high drift spikes
        - min(15, 30 * max(0, drift_median - 0.3))  # sustained drift
    """
    # Count unique episodes
    episodes = {a.get("episode_id", a.get("alert_id", "")) for a in alert_details}
    n_episodes = len(episodes)

    penalty = 0.0
    penalty += min(30, n_episodes * 2)
    penalty += min(25, 50 * max(0.0, drift_p99 - 0.5))
    penalty += min(15, 30 * max(0.0, drift_median - 0.3))

    return max(0, int(round(100 - penalty)))


def analyze_records(
    records: list[dict],
    address: str,
    explain: bool = False,
) -> dict:
    """Run the pipeline on pre-fetched records and return a report dict.

    This is the testable core — no network calls.
    """
    warmup, test = split_warmup(records)

    if not warmup:
        return _empty_report(address, len(records), 0, 0)
    if not test:
        return _empty_report(address, len(records), len(warmup), 0)

    pipe = build_pipeline(address.lower(), warmup)
    alerts: list[dict] = []
    drifts: list[float] = []
    for r in test:
        for a in pipe.process_tx(r):
            alerts.append(_alert_to_dict(a))
        if pipe.last_drift is not None:
            drifts.append(pipe.last_drift)

    drift_arr = np.array(drifts) if drifts else np.array([0.0])
    drift_median = float(np.median(drift_arr))
    drift_p99 = float(np.percentile(drift_arr, 99))

    # Selector distribution
    selectors = Counter(
        r.get("selector", (r.get("calldata", "0x") or "0x")[:10]) for r in records
    )
    total_sel = sum(selectors.values()) or 1
    top_selectors = {k: round(v / total_sel, 4) for k, v in selectors.most_common(10)}

    # Gas stats
    gas_vals = [int(r.get("gas_used", 0)) for r in records if int(r.get("gas_used", 0)) > 0]
    gas_median = int(np.median(gas_vals)) if gas_vals else 0
    gas_p99 = int(np.percentile(gas_vals, 99)) if gas_vals else 0

    score = compute_health_score(alerts, drift_median, drift_p99)

    report = {
        "contract": address.lower(),
        "chain": "mantle",
        "chain_id": 5000,
        "txs_fetched": len(records),
        "txs_warmup": len(warmup),
        "txs_analyzed": len(test),
        "health_score": score,
        "drift_median": round(drift_median, 4),
        "drift_p99": round(drift_p99, 4),
        "unique_selectors": len(selectors),
        "top_selectors": top_selectors,
        "gas_median": gas_median,
        "gas_p99": gas_p99,
        "alerts": len(alerts),
        "alert_details": alerts,
    }

    if explain:
        from sentinel.explain_zai import profile_contract

        report["zai_profile"] = profile_contract(report)

    return report


def _empty_report(address: str, fetched: int, warmup: int, analyzed: int) -> dict:
    return {
        "contract": address.lower(),
        "chain": "mantle",
        "chain_id": 5000,
        "txs_fetched": fetched,
        "txs_warmup": warmup,
        "txs_analyzed": analyzed,
        "health_score": 100,
        "drift_median": 0.0,
        "drift_p99": 0.0,
        "unique_selectors": 0,
        "top_selectors": {},
        "gas_median": 0,
        "gas_p99": 0,
        "alerts": 0,
        "alert_details": [],
    }


def _alert_to_dict(a) -> dict:
    """Convert an Alert object to a plain dict."""
    return {
        "alert_id": a.alert_id,
        "ts": a.ts,
        "block": a.block,
        "contract": a.contract,
        "alert_type": a.alert_type,
        "drift": a.drift,
        "branch": a.branch,
        "episode_id": a.episode_id,
    }


def scan_contract(
    address: str,
    n_txs: int = 2000,
    explain: bool = False,
) -> dict:
    """Fetch txs from Etherscan (or Routescan fallback), run pipeline, return report dict."""
    key = os.environ.get("ETHERSCAN_KEY", "")
    if key:
        txs = fetch_txlist(address, n_txs, key)
    else:
        # Routescan fallback (no API key needed)
        from sentinel.watch import fetch_txlist_from_block

        txs = fetch_txlist_from_block(address, start_block=0, n=n_txs)
    raw = to_raw(txs, address)
    if len(raw) < 100:
        print(
            f"WARNING: only {len(raw)} txs found — need ≥100 for meaningful analysis",
            file=sys.stderr,
        )
        if len(raw) < 20:
            print("ERROR: too few transactions for analysis", file=sys.stderr)
            sys.exit(1)

    return analyze_records(raw, address, explain=explain)


def print_report(report: dict) -> None:
    """Pretty-print report to stdout."""
    score = report["health_score"]
    icon = "✅" if score >= 80 else "⚠️" if score >= 50 else "🔴"

    sel_str = ", ".join(
        f"{k} ({v:.0%})" for k, v in list(report["top_selectors"].items())[:5]
    )

    print(f"""
Mantle Sentinel — Behavioral Scan
══════════════════════════════════
Contract:     {report['contract']}
Chain:        Mantle ({report['chain_id']})
Transactions: {report['txs_fetched']} fetched, {report['txs_warmup']} warmup, {report['txs_analyzed']} analyzed
──────────────────────────────────

Health Score: {score} / 100  {icon}

Drift (median):    {report['drift_median']:.3f}
Drift (p99):       {report['drift_p99']:.3f}
Unique selectors:  {report['unique_selectors']}
Top selectors:     {sel_str}
Gas (median):      {report['gas_median']:,}
Gas (p99):         {report['gas_p99']:,}
Alerts:            {report['alerts']}
""")
    if "zai_profile" in report:
        print(f'Z.ai Profile:\n  "{report["zai_profile"]}"\n')
