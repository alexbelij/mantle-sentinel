"""Attack injectors over a raw-tx stream (T-08 + T-09 full scenario set).

Each injector transforms benign test records into a labelled attack stream. Injected
records carry a hidden ``label="attack"`` the pipeline never reads (scorer-only).

Scenarios:
    S1  selector_flood   — never-seen-selector calls at ~3× cadence
    S3  gas_shift        — gas values shifted 5× above normal distribution
    S5  timing_burst     — near-zero inter-transaction timing (burst pattern)
    S7  payload_mutation — randomized calldata bodies (random bytes replacing ABI args)
"""
from __future__ import annotations

import copy
import hashlib

import numpy as np

NOVEL_SELECTOR = "0xdeadbeef"


def _onset_index(records: list[dict], onset_frac: float) -> int:
    return int(len(records) * onset_frac)


# ── S1: selector flood ──────────────────────────────────────────────────

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


# ── S3: gas shift ───────────────────────────────────────────────────────

def inject_s3_gas_shift(
    records: list[dict], fraction: float = 0.3, seed: int = 42
) -> list[dict]:
    """S3: inject transactions with gas values shifted 5× above normal distribution.

    Replaces a ``fraction`` of records (starting at 50% onset) with copies whose
    ``gas_used`` is 5× the median gas of the original stream, plus noise.
    """
    rng = np.random.default_rng(seed)
    out = [copy.deepcopy(r) for r in records]
    if not out:
        return out

    # Compute median gas from original stream for the 5× multiplier
    gas_values = [float(r.get("gas_used", 95_000) or 95_000) for r in records]
    median_gas = float(np.median(gas_values))

    onset = _onset_index(out, 0.5)
    n_inject = max(1, int(len(out[onset:]) * fraction))
    indices = rng.choice(len(out) - onset, size=min(n_inject, len(out) - onset), replace=False) + onset

    for idx in indices:
        out[idx] = copy.deepcopy(out[idx])
        # 5× above normal, with some noise
        out[idx]["gas_used"] = int(median_gas * 5.0 + abs(rng.normal(0, median_gas * 0.3)))
        out[idx]["label"] = "attack"

    return out


# ── S5: timing burst ───────────────────────────────────────────────────

def inject_s5_timing_burst(
    records: list[dict], fraction: float = 0.3, seed: int = 42
) -> list[dict]:
    """S5: inject transactions with near-zero inter-transaction timing (burst).

    Creates a burst of transactions with timestamps compressed to near-zero
    intervals, simulating a rapid-fire attack pattern.
    """
    rng = np.random.default_rng(seed)
    out = [copy.deepcopy(r) for r in records]
    if not out:
        return out

    onset = _onset_index(out, 0.5)
    n_inject = max(1, int(len(out[onset:]) * fraction))

    base = out[onset]
    block = int(base["block_number"])
    ts = float(base["block_timestamp"])
    contract = base["contract"]
    attacker = "0x" + rng.integers(0, 256, 20, dtype=np.uint8).tobytes().hex()

    injected = []
    for k in range(n_inject):
        # Near-zero inter-tx interval: 0.01–0.5 seconds (vs normal ~12s)
        ts += float(rng.uniform(0.01, 0.5))
        block += 1
        # Use a normal selector but with burst timing
        sel = "0xa9059cbb"
        body = rng.integers(0, 256, 64, dtype=np.uint8).tobytes().hex()
        injected.append({
            "block_number": block,
            "block_timestamp": round(ts, 3),
            "tx_hash": "0x" + hashlib.sha256(f"s5-{seed}-{k}".encode()).hexdigest(),
            "contract": contract,
            "caller": attacker,
            "calldata": sel + body,
            "gas_used": int(abs(rng.normal(95_000, 6_000))),
            "value": 0,
            "caller_is_contract": 0,
            "label": "attack",
        })

    return out[:onset] + injected + out[onset:]


# ── S7: payload mutation ───────────────────────────────────────────────

def inject_s7_payload_mutation(
    records: list[dict], fraction: float = 0.3, seed: int = 42
) -> list[dict]:
    """S7: inject transactions with randomized calldata bodies.

    Replaces ABI-encoded arguments with random bytes while preserving the 4-byte
    selector prefix. Simulates calldata fuzzing / mutation attacks.
    """
    rng = np.random.default_rng(seed)
    out = [copy.deepcopy(r) for r in records]
    if not out:
        return out

    onset = _onset_index(out, 0.5)
    n_inject = max(1, int(len(out[onset:]) * fraction))
    indices = rng.choice(len(out) - onset, size=min(n_inject, len(out) - onset), replace=False) + onset

    for idx in indices:
        out[idx] = copy.deepcopy(out[idx])
        original_calldata = out[idx].get("calldata", "0x") or "0x"
        # Preserve the 4-byte selector (first 10 chars: "0x" + 8 hex)
        if len(original_calldata) >= 10:
            selector = original_calldata[:10]
        else:
            selector = "0xdeadbeef"
        # Replace the argument body with random bytes (64–256 bytes)
        body_len = int(rng.integers(64, 257))
        random_body = rng.integers(0, 256, body_len, dtype=np.uint8).tobytes().hex()
        out[idx]["calldata"] = selector + random_body
        out[idx]["label"] = "attack"

    return out


INJECTORS = {
    "S1": inject_s1_selector_flood,
    "S3": inject_s3_gas_shift,
    "S5": inject_s5_timing_burst,
    "S7": inject_s7_payload_mutation,
}
