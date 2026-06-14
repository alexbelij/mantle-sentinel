"""T-18e: Dream-Mode A/B benchmark on the S6 slow-drift scenario.

Runs the live pipeline over a deterministic synthetic snapshot in four conditions
(CLEAN / S6 × dream-mode OFF / ON) and prints a Markdown table. The point is an
apples-to-apples comparison: does opt-in Dream-Mode consolidation change detection
of a slow "boil-the-frog" attack, or inflate false positives on clean traffic?

Deterministic (fixed seed) — same snapshot ⇒ byte-identical metrics. The committed
evidence is the table pasted into bench/REPORT.md; bench/runs/* stays gitignored.

Run:  .venv/bin/python -m bench.dream_bench
"""
from __future__ import annotations

from bench.injector import INJECTORS
from bench.scorer import _BLOCKS_PER_WINDOW
from bench.snapshot import synth_records
from sentinel.pipeline import build_pipeline, split_warmup

SEED = 7
N_TXS = 8000
ONSET_FRAC = 0.5


def _run(records: list[dict], inject: str | None, dream: bool) -> dict:
    records = sorted(records, key=lambda r: (int(r["block_number"]), r.get("tx_hash", "")))
    warmup, test = split_warmup(records)

    start_block = None
    if inject:
        onset = int(len(test) * ONSET_FRAC)
        start_block = int(test[onset]["block_number"])
        test = INJECTORS[inject](test, onset_frac=ONSET_FRAC, seed=SEED)

    pipe = build_pipeline(records[0]["contract"], warmup, dream_mode=dream)
    alerts = [a for r in test for a in pipe.process_tx(r)]

    episodes = {a.episode_id for a in alerts if a.episode_id is not None}
    delay_windows = float("inf")
    if start_block is not None:
        post = [a.block - start_block for a in alerts if a.block >= start_block]
        if post:
            delay_windows = min(post) / _BLOCKS_PER_WINDOW

    return {
        "alerts": len(alerts),
        "episodes": len(episodes),
        "delay_windows": delay_windows,
        "dream_count": pipe.dream_count,
        "detected": len(alerts) > 0 if inject else None,
    }


def main() -> int:
    recs = synth_records(N_TXS, seed=SEED)
    rows = []
    for label, inject in (("CLEAN", None), ("S6 slow-drift", "S6")):
        for dream in (False, True):
            r = _run(recs, inject, dream)
            rows.append((label, dream, r))

    print(f"# Dream-Mode A/B — snapshot n={N_TXS} txs, seed={SEED}, onset={ONSET_FRAC}\n")
    print("| Scenario | Dream | Alerts | Episodes | Det. delay (win) | Consolidations | Detected |")
    print("|----------|-------|--------|----------|------------------|----------------|----------|")
    for label, dream, r in rows:
        delay = "—" if r["delay_windows"] == float("inf") else f"{r['delay_windows']:.0f}"
        det = "—" if r["detected"] is None else ("✅" if r["detected"] else "❌")
        print(
            f"| {label} | {'ON' if dream else 'OFF'} | {r['alerts']} | {r['episodes']} "
            f"| {delay} | {r['dream_count']} | {det} |"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
