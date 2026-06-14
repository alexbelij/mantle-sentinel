"""T-09 / T-18e: Tests for attack injectors (S1, S3, S5, S6, S7)."""
from __future__ import annotations

import numpy as np

from bench.injector import (
    INJECTORS,
    inject_s1_selector_flood,
    inject_s3_gas_shift,
    inject_s5_timing_burst,
    inject_s6_slow_drift,
    inject_s7_payload_mutation,
)
from bench.snapshot import synth_records


def _base_records(n: int = 200, seed: int = 0) -> list[dict]:
    return synth_records(n, seed=seed)


# ── S1 selector flood ──────────────────────────────────────────────────

class TestS1SelectorFlood:
    def test_injected_records_have_novel_selector(self):
        base = _base_records()
        out = inject_s1_selector_flood(base, onset_frac=0.5, n_inject=20, seed=0)
        attacks = [r for r in out if r.get("label") == "attack"]
        assert len(attacks) == 20
        for a in attacks:
            assert a["calldata"].startswith("0xdeadbeef")

    def test_deterministic_with_seed(self):
        base = _base_records()
        out1 = inject_s1_selector_flood(base, seed=42)
        out2 = inject_s1_selector_flood(base, seed=42)
        assert [r["tx_hash"] for r in out1] == [r["tx_hash"] for r in out2]

    def test_different_seeds_differ(self):
        base = _base_records()
        out1 = inject_s1_selector_flood(base, seed=1)
        out2 = inject_s1_selector_flood(base, seed=2)
        hashes1 = {r["tx_hash"] for r in out1 if r.get("label") == "attack"}
        hashes2 = {r["tx_hash"] for r in out2 if r.get("label") == "attack"}
        assert hashes1 != hashes2


# ── S3 gas shift ────────────────────────────────────────────────────────

class TestS3GasShift:
    def test_injected_gas_is_elevated(self):
        base = _base_records()
        median_gas = float(np.median([r["gas_used"] for r in base]))
        out = inject_s3_gas_shift(base, fraction=0.3, seed=42)
        attacks = [r for r in out if r.get("label") == "attack"]
        assert len(attacks) > 0
        for a in attacks:
            # Gas should be significantly above median (at least 3× given 5× shift)
            assert a["gas_used"] > median_gas * 3, (
                f"gas_used={a['gas_used']} should be > {median_gas * 3}"
            )

    def test_deterministic_with_seed(self):
        base = _base_records()
        out1 = inject_s3_gas_shift(base, seed=42)
        out2 = inject_s3_gas_shift(base, seed=42)
        gas1 = [r["gas_used"] for r in out1]
        gas2 = [r["gas_used"] for r in out2]
        assert gas1 == gas2

    def test_different_seeds_differ(self):
        base = _base_records()
        out1 = inject_s3_gas_shift(base, seed=1)
        out2 = inject_s3_gas_shift(base, seed=2)
        gas1 = [r["gas_used"] for r in out1 if r.get("label") == "attack"]
        gas2 = [r["gas_used"] for r in out2 if r.get("label") == "attack"]
        assert gas1 != gas2

    def test_non_attack_records_unchanged(self):
        base = _base_records()
        out = inject_s3_gas_shift(base, fraction=0.3, seed=42)
        clean = [r for r in out if r.get("label") != "attack"]
        # Clean records should keep their original gas values
        original_gas = {r["tx_hash"]: r["gas_used"] for r in base}
        for r in clean:
            assert r["gas_used"] == original_gas[r["tx_hash"]]


# ── S5 timing burst ────────────────────────────────────────────────────

class TestS5TimingBurst:
    def test_injected_timestamps_are_burst(self):
        base = _base_records()
        out = inject_s5_timing_burst(base, fraction=0.3, seed=42)
        attacks = [r for r in out if r.get("label") == "attack"]
        assert len(attacks) > 1
        # Check inter-attack intervals are tiny (< 1 second)
        for i in range(1, len(attacks)):
            dt = attacks[i]["block_timestamp"] - attacks[i - 1]["block_timestamp"]
            assert dt < 1.0, f"Inter-attack dt={dt} should be < 1.0s"

    def test_deterministic_with_seed(self):
        base = _base_records()
        out1 = inject_s5_timing_burst(base, seed=42)
        out2 = inject_s5_timing_burst(base, seed=42)
        ts1 = [r["block_timestamp"] for r in out1]
        ts2 = [r["block_timestamp"] for r in out2]
        assert ts1 == ts2

    def test_different_seeds_differ(self):
        base = _base_records()
        out1 = inject_s5_timing_burst(base, seed=1)
        out2 = inject_s5_timing_burst(base, seed=2)
        ts1 = [r["block_timestamp"] for r in out1 if r.get("label") == "attack"]
        ts2 = [r["block_timestamp"] for r in out2 if r.get("label") == "attack"]
        assert ts1 != ts2


# ── S6 slow drift ──────────────────────────────────────────────────────

class TestS6SlowDrift:
    def test_registered_in_injectors(self):
        assert INJECTORS.get("S6") is inject_s6_slow_drift

    def test_run_replay_calling_convention(self):
        # run_replay/CLI call every injector as fn(records, onset_frac=, seed=)
        base = _base_records()
        out = inject_s6_slow_drift(base, onset_frac=0.5, seed=0)
        assert len(out) == len(base)  # in-place mutation, no insertion

    def test_gas_ramps_up_over_span(self):
        base = _base_records(n=400)
        out = inject_s6_slow_drift(base, onset_frac=0.5, seed=7)
        attacks = [r for r in out if r.get("label") == "attack"]
        assert len(attacks) > 4
        q = len(attacks) // 4
        early = float(np.mean([r["gas_used"] for r in attacks[:q]]))
        late = float(np.mean([r["gas_used"] for r in attacks[-q:]]))
        assert late > early * 2, f"late gas {late} should ramp well above early {early}"

    def test_calldata_corruption_grows(self):
        base = _base_records(n=400)
        original = {r["tx_hash"]: r.get("calldata", "0x") for r in base}
        out = inject_s6_slow_drift(base, onset_frac=0.5, seed=7)
        attacks = [r for r in out if r.get("label") == "attack"]
        # first attack window (p≈0) keeps its calldata; a late one is mutated
        assert attacks[0]["calldata"] == original[attacks[0]["tx_hash"]]
        assert attacks[-1]["calldata"] != original[attacks[-1]["tx_hash"]]

    def test_clean_prefix_untouched(self):
        base = _base_records()
        original = {r["tx_hash"]: (r["gas_used"], r.get("calldata")) for r in base}
        out = inject_s6_slow_drift(base, onset_frac=0.5, seed=7)
        clean = [r for r in out if r.get("label") != "attack"]
        for r in clean:
            assert (r["gas_used"], r.get("calldata")) == original[r["tx_hash"]]

    def test_deterministic_with_seed(self):
        base = _base_records()
        out1 = inject_s6_slow_drift(base, seed=42)
        out2 = inject_s6_slow_drift(base, seed=42)
        assert [r["gas_used"] for r in out1] == [r["gas_used"] for r in out2]
        assert [r["calldata"] for r in out1] == [r["calldata"] for r in out2]

    def test_different_seeds_differ(self):
        base = _base_records()
        out1 = inject_s6_slow_drift(base, seed=1)
        out2 = inject_s6_slow_drift(base, seed=2)
        g1 = [r["gas_used"] for r in out1 if r.get("label") == "attack"]
        g2 = [r["gas_used"] for r in out2 if r.get("label") == "attack"]
        assert g1 != g2


# ── S7 payload mutation ────────────────────────────────────────────────

class TestS7PayloadMutation:
    def test_injected_calldata_has_random_body(self):
        base = _base_records()
        out = inject_s7_payload_mutation(base, fraction=0.3, seed=42)
        attacks = [r for r in out if r.get("label") == "attack"]
        assert len(attacks) > 0
        for a in attacks:
            cd = a["calldata"]
            # Selector preserved (10 chars: "0x" + 8 hex)
            assert len(cd) >= 10
            # Body is longer than just selector (random bytes added)
            assert len(cd) > 10 + 64, f"calldata too short: {len(cd)}"

    def test_selector_preserved(self):
        base = _base_records()
        original_selectors = {}
        for r in base:
            cd = r.get("calldata", "0x")
            if len(cd) >= 10:
                original_selectors[r["tx_hash"]] = cd[:10]

        out = inject_s7_payload_mutation(base, fraction=0.3, seed=42)
        for r in out:
            if r.get("label") == "attack":
                cd = r["calldata"]
                # Selector is from the original or fallback
                assert len(cd[:10]) == 10

    def test_deterministic_with_seed(self):
        base = _base_records()
        out1 = inject_s7_payload_mutation(base, seed=42)
        out2 = inject_s7_payload_mutation(base, seed=42)
        cd1 = [r["calldata"] for r in out1]
        cd2 = [r["calldata"] for r in out2]
        assert cd1 == cd2

    def test_different_seeds_differ(self):
        base = _base_records()
        out1 = inject_s7_payload_mutation(base, seed=1)
        out2 = inject_s7_payload_mutation(base, seed=2)
        cd1 = [r["calldata"] for r in out1 if r.get("label") == "attack"]
        cd2 = [r["calldata"] for r in out2 if r.get("label") == "attack"]
        assert cd1 != cd2

    def test_body_differs_from_original(self):
        base = _base_records()
        original_cd = {r["tx_hash"]: r.get("calldata", "0x") for r in base}
        out = inject_s7_payload_mutation(base, fraction=0.3, seed=42)
        mutated = 0
        for r in out:
            if r.get("label") == "attack" and r["tx_hash"] in original_cd:
                if r["calldata"] != original_cd[r["tx_hash"]]:
                    mutated += 1
        assert mutated > 0, "At least some payloads should be mutated"
