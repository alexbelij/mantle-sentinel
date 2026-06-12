# Mantle Sentinel — Benchmark Protocol v1

**File:** `docs/BENCHMARK_PROTOCOL.md`
**Status:** Proposed (Principal Scientist & Strategic Reviewer)
**Scope:** Evaluation only. No architecture changes. The pipeline under test is the frozen Tier 1–6 system, exercised through the **same code path as live mode**.

**Purpose:** Replace "we produced a real alert" with three defensible numbers:

> **Detection delay (blocks) · False positives per contract-day · Lift over a naive baseline on identical features**

These three numbers are what judges can score. Everything below exists to produce them reproducibly.

---

## 0. Design Principles

1. **Same code path.** The benchmark feeds transactions into the exact entrypoint used by live ingestion. No "eval mode" forks. If judges ask "is the demo the real system?" the answer is yes, byte-for-byte.
2. **FP-budget-controlled comparison.** Never compare detectors at arbitrary thresholds. Fix a false-positive budget first, then compare detection delay and detection rate at that budget. This is the only fair comparison and it preempts the obvious judge objection ("you can always detect faster by alerting more").
3. **Deterministic and cheap.** Frozen dataset snapshot, pinned seeds, one command. Every experiment must run on a laptop in minutes, not hours.
4. **Honest labels.** Historical traffic is *presumed* benign, not *known* benign. We state this caveat ourselves before judges find it.

---

## 1. Historical Replay Methodology

### 1.1 Contract selection

Select **3–5 Mantle mainnet contracts** with sustained, diverse traffic. Selection criteria:

| Criterion | Threshold |
|---|---|
| Activity | ≥ 300 tx/day average over the capture window |
| Diversity | ≥ 4 distinct selectors in regular use |
| Caller mix | Mix of EOA-heavy and contract-caller-heavy |
| Category spread | At least one each of: DEX/router, token/stablecoin, bridge or lending pool |

Rationale: the FP profile of the system is dominated by traffic *shape* (caller churn, selector mix, burstiness). Three different shapes is the minimum to claim generality; one contract proves nothing.

### 1.2 Data capture

- **Window:** 14 consecutive days of history per contract (extend to 21 if any contract has < 300 tx/day).
- **Source:** Mantle RPC (`eth_getLogs` + block/tx fetch) or explorer API. Whichever is used, the output is normalized to one schema:

```
tx_record = {
  block_number, block_timestamp, tx_hash,
  contract, caller, selector, calldata,
  gas_used, value
}
```

- **Snapshot:** Capture once, write to `bench/data/{contract}/raw.jsonl`, compute SHA-256, commit the hash (not the data) to the repo. All experiments run from the snapshot — never from live RPC. This makes every number in the report reproducible.

### 1.3 Splits

Per contract, in strict time order (no shuffling — this is a streaming system):

| Split | Portion | Used for |
|---|---|---|
| **Warm-up** | Days 1–4 | Building DNA prototype, calibrating `normalize()` statistics. **No metrics recorded.** |
| **Calibration** | Days 5–7 | Tuning each detector's threshold to the FP budget (§4.3). |
| **Test** | Days 8–14 | All reported metrics. Touched exactly once per configuration. |

Cold-start is thereby measured implicitly: if the system still alerts on clean traffic in days 8–14, that is a real FP, not a warm-up artifact — and we can say so.

### 1.4 Replay harness

`bench/replay.py`:

- Reads the snapshot, emits records in `(block_number, tx_index)` order.
- Drives the pipeline's live entrypoint directly (function call, not network).
- Supports two clocks: **logical** (block timestamps; default, fast) and **scaled wall-clock** (for the demo recording only).
- Logs every pipeline output (drift values, run-length posterior / threshold state, alerts, interpreter output) to `bench/runs/{run_id}/events.jsonl`.
- Accepts `--inject <scenario> --onset <block> --seed <n>` (§2).

**Clean-traffic caveat (state it in the report):** we treat historical traffic as benign after a manual spot-check of alert candidates. If a clean-replay alert turns out to flag a genuinely odd historical event, that is reported as an anecdote, not silently relabeled.

---

## 2. Synthetic Attack Injection Methodology

### 2.1 Mechanics

Injection is a **transform over the replay stream**, applied at a randomized onset point. Two modes:

- **Insertion** — synthetic transactions added between real ones (e.g., a flood).
- **Mutation** — fields of real transactions rewritten from onset onward (e.g., gas shift).

Injected records carry a hidden `label=attack` field that the pipeline never sees; only the scorer reads it. Onset block is drawn uniformly from the test split, excluding the final 2 hours (so delay is measurable). Every trial is fully determined by `(scenario, contract, seed)`.

### 2.2 Scenario suite

Each scenario maps to a failure mode the system claims to catch — and one (S6) that probes the failure mode *we* identified. Parameters in brackets are the canonical setting; sweeps optional.

| ID | Scenario | Construction | Exercises |
|---|---|---|---|
| **S1** | New-selector flood | Insert calls with a never-seen selector at 3× the contract's median rate for 30 min | Tier 2 selector channel |
| **S2** | Caller takeover | One new EOA grows to ≥ 60% of traffic over 20 min | Tier 2 caller channel; FP-vs-novelty tradeoff |
| **S3** | Gas regime shift | Mutate gas_used by a sustained +3 buckets on all txs after onset | Tier 2 gas channel, Hamming path |
| **S4** | Value spike | Insert burst of top-bucket value transfers (10 tx in 5 min) | Tier 2 value channel |
| **S5** | Timing burst | Compress inter-tx intervals to p5 of historical distribution for 15 min | Timing deviation path |
| **S6** | **Slow drift** | Linearly interpolate selector/gas distribution from normal to S1+S3 profile over **6 hours** | Sub-threshold evasion; Dream Mode self-poisoning |
| **S7** | Payload mutation | Replace calldata bodies with high-entropy random bytes, valid selector kept | Tier 1 entropy filter (bypasses BOCPD) |
| **S8** *(stretch)* | Real exploit replay | Map a published EVM exploit transaction sequence (selector/gas/value/timing profile) onto the target contract's schema | End-to-end realism; strongest judge evidence |

**Trials:** 10 per (scenario × contract), seeds 1–10. With 3 contracts and S1–S7 that is 210 cheap replay runs — minutes of compute from the snapshot.

**S6 dual protocol:** run once with Dream Mode consolidation active across the simulated nights and once without. If the active run *absorbs* the drift (no alert, prototype migrated), that quantifies the self-poisoning risk and demonstrates we measured our own weakness — judges reward that.

### 2.3 What injection does *not* claim

Synthetic scenarios validate *sensitivity to behavioral change*, not *exploit detection* per se. Say this sentence in the report verbatim. S8 is what bridges the gap; if S8 is cut for time, the claim stays scoped to behavioral drift.

---

## 3. Metrics

### 3.1 Detection delay (primary)

For each attack trial:

```
delay_blocks = first_alert_block − onset_block      (alert must be a true positive)
```

- **True positive** = alert raised at or after onset, within the scenario window + 30 min grace.
- Also record `delay_tx` (transactions since onset) and `delay_wallclock` (from block timestamps). Blocks are the headline unit — chain-native and unambiguous on an L2 with ~2 s blocks.
- **Censoring:** no alert before scenario end ⇒ trial is a **miss**; it contributes to detection rate, not to the delay distribution (never average misses into delay).
- **Report:** median and p90 over trials, per scenario; plus **detection rate** = detected/10.

### 3.2 False positives per contract-day (primary)

On **clean** test-split replay (no injection):

```
FP/day = (# alerts on clean traffic) / (contract-days replayed)
```

- Count **alert episodes**, not raw alert events: consecutive alerts within 10 minutes collapse into one episode (matches how an on-call human experiences them).
- Report per contract and pooled. Tier 1 (entropy) and Tier 3–4 (drift) alerts are reported as separate lines — they are independent sensors by design and judges should see which one is noisy.

### 3.3 Secondary metrics (cheap, report if time permits)

- **Delay-vs-FP curve:** sweep the final threshold, plot median delay against FP/day. One plot says more than any table.
- **Interpreter accuracy:** for each detected synthetic attack, does Tier 5 name the injected feature channel? Report % correct over trials. This validates the explanation chain end-to-end (and constrains what Z.ai is allowed to narrate).
- **Warm-up requirement:** transactions until prototype self-similarity stabilizes (rolling Hamming to own prototype plateaus). One number per contract; answers the judge question "how long until this works on a new contract?"

---

## 4. Baseline Detector

### 4.1 Specification — `FreqBase`

A deliberately strong-but-simple detector on **identical inputs**: same 5 features, same bucket boundaries, same warm-up data, same alert-episode definition.

Per feature *f*, over a sliding window of the last *W* transactions (same *W* as the HDC comparison window):

- **Categorical features (caller, selector):** novelty rate = fraction of window items unseen in warm-up + calibration history.
- **Ordinal features (gas, value, timing buckets):** robust z-score of the window's bucket histogram shift = total-variation distance to the warm-up histogram, normalized by its calibration-split median/MAD.

```
score(t) = max over features f of z_f(t)
alert if score(t) > θ_base
```

~100 lines of Python, no dependencies beyond the existing bucketing code. The `max` aggregation deliberately mirrors Tier 3's fusion so the comparison isolates **representation** (HDC vs frequency tables), not fusion strategy.

### 4.2 Why this baseline and not a strawman

Judges discount victories over weak baselines. `FreqBase` is roughly what a competent engineer would build in an afternoon — beating it on delay or FP/day at matched budget is *exactly* the evidence that HDC earns its place. If `FreqBase` wins on some scenario, we report it and explain what HDC buys instead (fixed memory independent of cardinality, single-pass updates, one unified similarity space, graceful degradation) — measured honesty beats hidden losses.

### 4.3 Matched-budget comparison procedure

1. Fix the FP budget: **≤ 2 alert episodes per contract-day** (adjust once, before test runs, never after).
2. On the **calibration split**, tune each detector's final threshold (Sentinel: static threshold / BOCPD alert probability; FreqBase: θ_base) to the largest sensitivity that respects the budget.
3. Freeze thresholds. Run the **test split** once per configuration.
4. Compare: detection rate and median delay per scenario, FP/day on clean traffic.

This procedure is the single most judge-convincing element of the protocol. Do not skip it.

---

## 5. Ablation Study Plan

All ablations are **evaluation configurations** — components toggled or swept in the benchmark harness. Nothing is added to or removed from the frozen architecture.

| ID | Ablation | Configurations | Question answered | Priority |
|---|---|---|---|---|
| **AB1** | Drift fusion inputs | Hamming-only / timing-only / frozen `max()` | Does fusion beat either signal alone? Which signal owns the FP rate? | **P0** |
| **AB2** | Tier 4 detector | BOCPD vs `StaticThresholdDetector` | Is BOCPD worth its complexity, or is the MVP fallback the honest choice for the demo? | **P0** |
| **AB3** | Representation | Full Sentinel vs `FreqBase` (matched budget, §4.3) | Does HDC add measurable value? **The novelty slide.** | **P0** |
| **AB4** | Dream Mode | On / off, across multi-day test split + S6 | Does consolidation reduce FP drift over days? Does it absorb slow attacks? | **P1** |
| **AB5** | HDC dimensionality | D ∈ {1,024, 4,096, 10,000} | Robustness claim: results stable across D ⇒ not a tuning artifact | **P2** |
| **AB6** | Comparison window | W ∈ {25, 50, 100, 200} | Delay/stability tradeoff; documents the chosen W instead of leaving it magic | **P2** |

Each ablation reuses the same snapshot, scenarios, and scoring — incremental cost is one config flag and compute minutes.

**Reading guide for results:**
- AB1 tells us which signal to trust when triaging a live alert.
- AB2 protects the demo: if BOCPD's run-length posterior is unstable on our drift signal, we demo on the static fallback *and present that as a measured decision*, with BOCPD as the adaptive upgrade path.
- AB3 is the centerpiece. If we win: lead with it. If we tie: lead with HDC's systems properties (memory, single-pass, unified space) + the tie. If we lose: we found it before the judges did, and the pitch adjusts.

---

## 6. Reporting & Judge Artifacts

**`bench/REPORT.md`** (one page) containing:

1. **Headline box** — three numbers, pooled over contracts at the fixed FP budget:
   - Median detection delay: `X blocks (~Y s)`
   - False positives: `Z episodes / contract-day`
   - vs baseline: `ΔX blocks faster / ΔZ fewer FP at matched budget`
2. **Scenario table** — detection rate + median/p90 delay per scenario, Sentinel vs FreqBase.
3. **One plot** — delay-vs-FP curve, both detectors.
4. **Caveats (3 lines, ours before theirs):** presumed-benign clean traffic; synthetic scenarios measure behavioral drift, not exploits (modulo S8); results from 3–5 contracts on a 14-day window.

**Demo asset:** one recorded replay run (clean day + one S1 or S8 incident) with the full alert → interpreter → Z.ai chain, generated by `bench/replay.py --demo`. The live Mantle feed is shown as a bonus; the recording is the critical path.

---

## 7. Execution Plan (small-team budget)

One command — `make bench` — runs: snapshot integrity check → clean replays → scenario matrix → P0 ablations → report tables. Seeds pinned in `bench/config.yaml`.

| Step | Deliverable | Est. effort | Priority |
|---|---|---|---|
| 1 | Capture + snapshot 3 contracts | 0.5 day | P0 |
| 2 | Replay harness on live entrypoint | 0.5–1 day | P0 |
| 3 | Injector: S1, S3, S5, S7 | 0.5 day | P0 |
| 4 | Scorer (delay, FP/day, episodes) | 0.5 day | P0 |
| 5 | `FreqBase` + matched-budget procedure | 0.5 day | P0 |
| 6 | AB1–AB3 + REPORT.md | 0.5 day | P0 |
| 7 | S2, S4, S6 + AB4 | 0.5 day | P1 |
| 8 | S8 exploit replay, AB5–AB6, extra contracts | as time allows | P2 |

**Total P0: ≈ 3 person-days** — parallelizable across 2–3 people (capture/harness ∥ injector/scorer ∥ baseline).

**If time runs out, cut from the bottom — never cut:** clean-replay FP/day, S1 + S5 delay, and AB3. Those three are the minimum credible result.

---

## 8. Reproducibility Checklist

- [ ] Dataset snapshot SHA-256 committed
- [ ] All seeds pinned in `bench/config.yaml`
- [ ] Thresholds frozen after calibration split; test split touched once per configuration
- [ ] Benchmark drives the live pipeline entrypoint (no eval fork)
- [ ] Every reported number regenerable via `make bench`
- [ ] Caveats section present in REPORT.md
