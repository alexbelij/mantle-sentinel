"""T-05 acceptance tests (MVP_MATH_SPEC §3)."""
from __future__ import annotations

import numpy as np

from sentinel.entropy import (
    EntropyFilter,
    body_of,
    byte_entropy,
    length_bucket,
    selector_of,
)

SELECTOR = "0xa9059cbb"  # transfer(address,uint256)


# A token's transfers hit a recurring set of recipients (CEX, market makers, users),
# so normal calldata entropy is concentrated. Fixed pool ⇒ realistic low variance.
_ADDR_POOL = [
    bytes(12) + np.random.default_rng(1000 + i).integers(0, 256, 20, dtype=np.uint8).tobytes()
    for i in range(50)
]


def _normal_calldata(rng: np.random.Generator) -> str:
    """Structured ABI calldata: transfer(address, amount) — 2 zero-padded words.
    Address drawn from a recurring pool; amount a small int. Low, stable entropy."""
    addr = _ADDR_POOL[int(rng.integers(0, len(_ADDR_POOL)))]
    amount = int(rng.integers(1, 10**6)).to_bytes(32, "big")
    return SELECTOR + addr.hex() + amount.hex()


def _random_body_calldata(rng: np.random.Generator) -> str:
    """S7: valid selector kept, body replaced with high-entropy random bytes."""
    body = rng.integers(0, 256, 64, dtype=np.uint8).tobytes()
    return SELECTOR + body.hex()


def test_byte_entropy_bounds():
    assert byte_entropy(b"") == 0.0
    assert byte_entropy(b"\x00" * 32) == 0.0  # single symbol ⇒ 0
    rnd = np.random.default_rng(0).integers(0, 256, 4096, dtype=np.uint8).tobytes()
    assert byte_entropy(rnd) > 7.5  # near-uniform ⇒ ~8 bits


def test_helpers():
    cd = _normal_calldata(np.random.default_rng(1))
    assert selector_of(cd) == SELECTOR
    assert len(body_of(cd)) == 64
    assert length_bucket(64) == 2  # 37..100 bucket


def test_normal_calldata_zero_alerts():
    rng = np.random.default_rng(7)
    warm = [_normal_calldata(rng) for _ in range(400)]
    filt = EntropyFilter().fit(warm)
    test = [_normal_calldata(rng) for _ in range(400)]
    alerts = sum(filt.check(cd) for cd in test)
    assert alerts == 0, f"normal ABI calldata produced {alerts} false entropy alerts"


def test_randomized_body_alerts():
    rng = np.random.default_rng(7)
    warm = [_normal_calldata(rng) for _ in range(400)]
    filt = EntropyFilter().fit(warm)
    # randomized bodies are the same length bucket (64 bytes) but high entropy
    attacks = [_random_body_calldata(rng) for _ in range(20)]
    detected = sum(filt.check(cd) for cd in attacks)
    assert detected == len(attacks), f"only {detected}/{len(attacks)} random bodies flagged"


def test_abstain_on_unpopulated_cell():
    filt = EntropyFilter().fit([_normal_calldata(np.random.default_rng(0)) for _ in range(5)])
    # only 5 samples (< 20) ⇒ must abstain even on a wild body
    rng = np.random.default_rng(3)
    assert filt.check(_random_body_calldata(rng)) is False
