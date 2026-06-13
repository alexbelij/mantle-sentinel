"""Attack injectors over a raw-tx stream (subset for T-08; full scenario set is T-09).

Each injector transforms benign test records into a labelled attack stream. Injected
records carry a hidden ``label="attack"`` the pipeline never reads (scorer-only).
"""
from __future__ import annotations

import copy
import hashlib

import numpy as np

NOVEL_SELECTOR = "0xdeadbeef"


def _onset_index(records: list[dict], onset_frac: float) -> int:
    return int(len(records) * onset_frac)


def inject_s1_selector_flood(
    records: list[dict], onset_frac: float = 0.5, n_inject: int = 80, seed: int = 0
) -> list[dict]:
    """S1: insert never-seen-selector calls at ~3x cadence starting at onset."""
    rng = np.random.default_rng(seed)
    out = [copy.deepcopy(r) for r in records]
    i = _onset_index(out, onset_frac)
    base = out[i]
    block = int(base["block_number"])
    ts = float(base["block_timestamp"])
    attacker = "0x" + rng.integers(0, 256, 20, dtype=np.uint8).tobytes().hex()
    injected = []
    for k in range(n_inject):
        ts += float(abs(rng.normal(4.0, 0.5))) + 0.05  # ~3x rate
        block += 1
        body = rng.integers(0, 256, 64, dtype=np.uint8).tobytes().hex()
        injected.append({
            "block_number": block,
            "block_timestamp": round(ts, 3),
            "tx_hash": "0x" + hashlib.sha256(f"inj-{seed}-{k}".encode()).hexdigest(),
            "contract": base["contract"],
            "caller": attacker,
            "calldata": NOVEL_SELECTOR + body,
            "gas_used": int(abs(rng.normal(95_000, 6_000))),
            "value": 0,
            "caller_is_contract": 1,
            "label": "attack",
        })
    return out[:i] + injected + out[i:]


INJECTORS = {"S1": inject_s1_selector_flood}
