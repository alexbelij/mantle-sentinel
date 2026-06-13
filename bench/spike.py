"""Viability spike (D-08 go/no-go gate) — runs T-02→T-03→T-04 on one real contract.

Reports clean-traffic drift distribution + false-positive episodes (Tier-4 detector)
and injected (S1) drift + detection. Writes a PNG if matplotlib is available and
prints a one-line LOG-ready summary.

    uv run python -m bench.spike <snapshot> [--png docs/status/spike_drift.png]
"""
from __future__ import annotations

import argparse

import numpy as np

from bench.injector import inject_s1_selector_flood
from bench.snapshot import load_snapshot
from sentinel.pipeline import build_pipeline, split_warmup


def _run(test_records: list[dict], warmup: list[dict], contract: str):
    pipe = build_pipeline(contract, warmup)
    drifts: list[float] = []
    alerts: list[dict] = []
    for r in test_records:
        for a in pipe.process_tx(r):
            alerts.append(a.to_dict())
        if pipe.last_drift is not None:
            drifts.append(pipe.last_drift)
            pipe.last_drift = None
    return np.asarray(drifts), alerts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot")
    ap.add_argument("--png", default="docs/status/spike_drift.png")
    args = ap.parse_args()

    records = sorted(load_snapshot(args.snapshot), key=lambda r: (int(r["block_number"]), r["tx_hash"]))
    contract = records[0]["contract"]
    warmup, test = split_warmup(records)

    clean_d, clean_alerts = _run(test, warmup, contract)
    inj_d, inj_alerts = _run(inject_s1_selector_flood(test, onset_frac=0.5, seed=7), warmup, contract)

    clean_regime = [a for a in clean_alerts if a["alert_type"] == "regime_shift"]
    inj_regime = [a for a in inj_alerts if a["alert_type"] == "regime_shift"]
    clean_eps = {a.get("episode_id") for a in clean_regime}
    inj_eps = {a.get("episode_id") for a in inj_regime}

    print(f"contract={contract}")
    print(f"warmup={len(warmup)} test={len(test)} windows={len(clean_d)}")
    print(f"CLEAN drift  median={np.median(clean_d):.3f} p90={np.quantile(clean_d,.9):.3f} "
          f"p99={np.quantile(clean_d,.99):.3f} max={clean_d.max():.3f}")
    print(f"CLEAN false-positive regime episodes = {len(clean_eps)}  (alerts={len(clean_regime)})")
    print(f"INJECTED max drift={inj_d.max():.3f}  detected regime episodes={len(inj_eps)}")
    sep = (inj_d.max() / max(np.median(clean_d), 1e-6))
    print(f"separation (injected_max / clean_median) = {sep:.1f}x")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(clean_d, lw=0.7, color="#2a7", label="clean drift")
        ax.plot(inj_d, lw=0.7, color="#c33", alpha=0.7, label="S1-injected drift")
        ax.axhline(0.65, ls="--", color="#555", label="θ=0.65")
        ax.set_xlabel("window (test stream)")
        ax.set_ylabel("drift")
        ax.set_title(f"Viability spike — {contract[:10]}… (clean FP episodes={len(clean_eps)})")
        ax.legend(loc="upper left", fontsize=8)
        fig.tight_layout()
        from pathlib import Path
        Path(args.png).parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.png, dpi=110)
        print(f"plot -> {args.png}")
    except Exception as e:  # noqa: BLE001
        print(f"(plot skipped: {e})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
