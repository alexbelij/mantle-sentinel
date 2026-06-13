"""Replay harness — drives the live Pipeline over a snapshot (BENCHMARK_PROTOCOL §0).

Deterministic: same snapshot + same options ⇒ byte-identical alert stream (§7).
"""
from __future__ import annotations

import json
from pathlib import Path

from sentinel.pipeline import build_pipeline, split_warmup


def _load(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def run_replay(
    records: list[dict],
    inject: str | None = None,
    onset_frac: float = 0.5,
    seed: int = 0,
) -> list[dict]:
    """Return the ordered list of alert dicts produced over the test split."""
    records = sorted(records, key=lambda r: (int(r["block_number"]), r.get("tx_hash", "")))
    warmup, test = split_warmup(records)

    if inject:
        from bench.injector import INJECTORS

        if inject not in INJECTORS:
            raise ValueError(f"unknown injector {inject!r}; have {sorted(INJECTORS)}")
        test = INJECTORS[inject](test, onset_frac=onset_frac, seed=seed)

    contract = records[0].get("contract", "0x") if records else "0x"
    pipe = build_pipeline(contract, warmup)
    alerts: list[dict] = []
    for r in test:
        for a in pipe.process_tx(r):
            alerts.append(a.to_dict())
    return alerts


def run_replay_file(path: str | Path, inject: str | None = None, out: str | Path | None = None,
                    onset_frac: float = 0.5, seed: int = 0) -> list[dict]:
    alerts = run_replay(_load(path), inject=inject, onset_frac=onset_frac, seed=seed)
    if out:
        Path(out).write_text(json.dumps(alerts, indent=2, sort_keys=True) + "\n")
    return alerts
