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
    replay.add_argument("--inject", default=None, help="scenario id (S1, S3, S5, S7)")
    replay.add_argument("--onset", type=int, default=None, help="injection onset block")
    replay.add_argument("--seed", type=int, default=1, help="injection seed")
    replay.add_argument("--out", default=None, help="path to write alerts JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.version or args.command is None:
        print(f"mantle-sentinel {__version__}")
        return 0

    if args.command == "replay":
        # Imported lazily so `--version` works before heavy modules exist.
        from sentinel.replay import run_replay

        alerts = run_replay(
            snapshot=args.snapshot,
            inject=args.inject,
            onset=args.onset,
            seed=args.seed,
            out=args.out,
        )
        print(f"{len(alerts)} alert(s)")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
