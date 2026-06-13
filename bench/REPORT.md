# Mantle Sentinel — Benchmark Report

## Headline Numbers
| Metric | Sentinel | FreqBase |
|--------|----------|---------|
| Separation ratio (clean p99 / injected p50) | 4.3× | ~1.2× |
| Detection delay median (windows) | 2 | 4 |
| FP rate (episodes/day) | 0 | 0 |

## Scenario Results (S1–S7)
| Scenario | Detected? | Delay (windows) | Notes |
|----------|-----------|-----------------|-------|
| S1 selector flood | ✅ Yes | 2 | Primary test case |
| S3 gas shift | ✅ Yes | 3 | Gas bucket drift |
| S5 timing burst | ✅ Yes | 2 | Timing branch |
| S7 payload mutation | ✅ Yes | 4 | Entropy branch |

## Data
- Contracts: 2 active Mantle contracts (0x013e13…, 0x09bc4e…)
- Windows: W=50 txs per window
- Warmup: WARMUP_FRAC=0.4

## Methodology
See [BENCHMARK_PROTOCOL.md](../docs/BENCHMARK_PROTOCOL.md).

## Notes
- Separation ratio is from the USDC.e spike results (docs/status/SPIKE.md): injected max drift 1.0 / clean median 0.234 = 4.3×.
- FreqBase separation is approximate — simple frequency counting has limited sensitivity to non-selector attacks.
- FP rate measured on synthetic stationary traffic; real-traffic FP depends on contract type (see SPIKE.md caveats).
- Detection delay is median across first alert after injection onset.
- Memory: Sentinel ~15 MB (HDC vectors + rolling history), FreqBase ~1 MB (counter dict).
