"""CLI entrypoint for the sentinel package.

Usage:
    python -m sentinel --version
    python -m sentinel replay --snapshot bench/data/<contract>/raw.jsonl [--inject S1]
    python -m sentinel scan 0x09bc4e0d864854c6afb6eb9a9cdf58ac190d0df9
    python -m sentinel scan 0x09bc4e... --explain
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sentinel import __version__


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sentinel", description="Mantle Sentinel CLI")
    parser.add_argument("--version", action="store_true", help="print version and exit")
    sub = parser.add_subparsers(dest="command")

    replay = sub.add_parser("replay", help="replay a snapshot through the pipeline")
    replay.add_argument("--snapshot", required=True, help="path to raw.jsonl snapshot")
    replay.add_argument("--inject", default=None, help="scenario id (e.g. S1)")
    replay.add_argument("--onset", type=float, default=0.5, help="injection onset fraction [0,1]")
    replay.add_argument("--seed", type=int, default=1, help="injection seed")
    replay.add_argument("--out", default=None, help="path to write alerts JSON")
    replay.add_argument(
        "--detector", default=None, choices=["static", "bocpd"],
        help="Tier-4 detector; overrides SENTINEL_DETECTOR env (default: static)",
    )
    replay.add_argument(
        "--dream-mode", action="store_true",
        help="enable Dream-Mode prototype consolidation (every N=100 safe windows)",
    )

    scan = sub.add_parser("scan", help="behavioral audit of any Mantle contract")
    scan.add_argument("address", help="contract address (0x...)")
    scan.add_argument("--n", type=int, default=2000, help="max transactions to fetch")
    scan.add_argument("--explain", action="store_true", help="include Z.ai behavioral profile")
    scan.add_argument("--out", default=None, help="write JSON report to path (default: bench/reports/<addr>.json)")
    scan.add_argument("--json", action="store_true", help="output JSON instead of human-readable")
    scan.add_argument("--min-health", type=int, default=None, metavar="N",
                      help="exit 1 if health score < N (CI gate mode)")

    watch = sub.add_parser("watch", help="live behavioral monitoring of a Mantle contract")
    watch.add_argument("address", help="contract address (0x...)")
    watch.add_argument("--interval", type=int, default=30, help="polling interval in seconds")
    watch.add_argument("--warmup", type=int, default=500, help="number of txs for warmup phase")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version or args.command is None:
        print(f"mantle-sentinel {__version__}")
        return 0

    if args.command == "watch":
        from sentinel.watch import watch

        watch(args.address, interval=args.interval, warmup_n=args.warmup)
        return 0

    if args.command == "scan":
        from sentinel.scan import print_report, scan_contract

        report = scan_contract(args.address, n_txs=args.n, explain=args.explain)
        out_path = args.out or f"bench/reports/{args.address.lower()}.json"
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(json.dumps(report, indent=2) + "\n")
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print_report(report)
            print(f"Report saved: {out_path}")

        # CI gate: exit 1 if health score below threshold
        if args.min_health is not None:
            score = report["health_score"]
            if score < args.min_health:
                print(
                    f"FAIL: health {score} < threshold {args.min_health}",
                    file=sys.stderr,
                )
                return 1
        return 0

    if args.command == "replay":
        # Imported lazily so `--version` works before heavy modules exist.
        from sentinel.replay import run_replay_file

        alerts = run_replay_file(
            args.snapshot,
            inject=args.inject,
            out=args.out,
            onset_frac=args.onset,
            seed=args.seed,
            detector=args.detector,
            dream_mode=args.dream_mode,
        )
        print(f"{len(alerts)} alert(s)")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
