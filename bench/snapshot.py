"""Synthetic raw-tx snapshot (BENCHMARK_PROTOCOL §1.2 schema) for tests and the
viability-spike fallback. Deterministic. Emulates a token-like contract: transfer()
dominates, recurring callers, near-constant block cadence, structured ABI calldata.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

NORMAL_SELECTORS = ("0xa9059cbb", "0x23b872dd", "0x095ea7b3", "0x2e1a7d4d")
SELECTOR_WEIGHTS = (0.80, 0.10, 0.07, 0.03)


def _addr(rng: np.random.Generator) -> str:
    return "0x" + rng.integers(0, 256, 20, dtype=np.uint8).tobytes().hex()


def synth_records(
    n: int, seed: int = 0, start_block: int = 96_000_000, start_ts: int = 1_781_000_000
) -> list[dict]:
    rng = np.random.default_rng(seed)
    contract = "0x013e138ef6008ae5fdfde29700e3f2bc61d21e3a"
    pool = [_addr(rng) for _ in range(40)]
    pool_is_contract = [int(rng.random() < 0.15) for _ in pool]
    recipients = [_addr(rng) for _ in range(50)]

    block = start_block
    ts = float(start_ts)
    out: list[dict] = []
    for i in range(n):
        sel = NORMAL_SELECTORS[rng.choice(len(NORMAL_SELECTORS), p=SELECTOR_WEIGHTS)]
        ci = int(rng.integers(0, len(pool)))
        recipient = recipients[int(rng.integers(0, len(recipients)))]
        amount = int(rng.integers(1, 10**6))
        body = bytes.fromhex(recipient[2:]).rjust(32, b"\x00").hex() + amount.to_bytes(32, "big").hex()
        gas = int(abs(rng.normal(95_000, 6_000)))
        value = 0
        dt = float(abs(rng.normal(12.0, 0.6))) + 0.1
        ts += dt
        block += max(1, round(dt / 2))
        out.append({
            "block_number": block,
            "block_timestamp": round(ts, 3),
            "tx_hash": "0x" + hashlib.sha256(f"{seed}-{i}".encode()).hexdigest(),
            "contract": contract,
            "caller": pool[ci],
            "calldata": sel + body,
            "gas_used": gas,
            "value": value,
            "caller_is_contract": pool_is_contract[ci],
        })
    return out


def write_snapshot(records: list[dict], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        for r in records:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    path.with_suffix(path.suffix + ".sha256").write_text(digest + "\n")
    return path


def load_snapshot(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
