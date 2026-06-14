"""CLI entrypoint for the sentinel package.

Usage:
    python -m sentinel --version
    python -m sentinel replay --snapshot bench/data/<contract>/raw.jsonl [--inject S1]
"""
from __future__ import annotations

import argparse
import sys

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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version or args.command is None:
        print(f"mantle-sentinel {__version__}")
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
        )
        print(f"{len(alerts)} alert(s)")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
