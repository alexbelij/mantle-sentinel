# Benchmark

## Headline Numbers

| Metric | Sentinel | FreqBase |
|--------|----------|---------|
| Separation ratio (clean p99 / injected p50) | **4.3×** | ~1.2× |
| Detection delay — S1 hi-entropy | **≤ 2 windows** | N/A |
| False positives on clean stream (8000 windows) | 0 real FP¹ | — |
| Test suite | 109 deterministic tests | — |

¹ FP rate ≈ 0.2% of windows; static θ=0.65 on baseline noise; real USDC.e stream = 0 false episodes.

## Dream Mode A/B (S6 slow-drift, n=8000, seed=7)

| Scenario | Dream | Episodes | Delay (win) | Consolidations |
|----------|-------|----------|-------------|----------------|
| CLEAN | OFF | 16 | — | 0 |
| CLEAN | ON | 15 | — | 23 |
| S6 slow-drift | OFF | 12 | 102 | 0 |
| S6 slow-drift | ON | 11 | 99 | 19 |

Dream Mode: FP 16→15 (−6%), delay 102→99 (−3%). S6 detected in both modes.  
Consolidations 23 (clean) vs 19 (S6): rolling-median gate correctly excludes rising-drift windows from baseline update.

## Attack Scenarios

| Scenario | Description | Detected |
|----------|-------------|---------|
| S1 | Hi-entropy selector spray | ✅ ≤ 2 windows |
| S2 | Gas spike | ✅ |
| S3 | Calldata pattern shift | ✅ |
| S4 | Timing flood | ✅ |
| S5 | Combined (S1+S4) | ✅ |
| S6 | Slow drift ("boil the frog"): gas 1×→5×, calldata corruption post-onset | ✅ delay ~100 win |

## Running the Benchmark

```bash
# Full benchmark suite
uv run python bench/dream_bench.py

# Individual scenario
uv run python -m sentinel replay --snapshot ... --inject S6 --dream-mode
```

Full results: `bench/REPORT.md`
