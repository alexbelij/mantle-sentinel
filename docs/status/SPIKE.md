# Viability spike (D-08 go/no-go) — 2026-06-13

Pipeline T-02→T-03→T-04 (in fact the full T-01..T-08 stack) run on **real Mantle
mainnet data** captured via Etherscan V2 (chainid 5000). Deterministic; reproduce
with `uv run python -m bench.spike <snapshot>`.

## Datasets (real, direct calls to the contract)
| contract | type | txs | warmup | test windows |
|---|---|---|---|---|
| `0x013e…1E3a` Merchant Moe LB Router | swap router | 3618 | 1447 | 2122 |
| `0x09bc…0dF9` USDC.e | ERC-20 token | 3993 | 1597 | 2347 |

## Results
| metric | LB Router | USDC.e |
|---|---|---|
| clean drift median | 0.329 | 0.234 |
| clean drift p90 / p99 | 0.859 / 1.000 | 0.951 / 1.000 |
| clean regime episodes (unlabeled "FP") | 14 | 5 |
| injected (S1) max drift | 1.000 | 1.000 |
| injected detected episodes | 16 | 6 |
| separation (inj_max / clean_median) | 3.0× | 4.3× |

Plots: `docs/status/spike_lbrouter.png`, `docs/status/spike_usdce.png`.

## Reading
- **Mechanism works.** S1 selector floods drive drift to 1.0 and are detected on
  both contracts; the run is deterministic and every tier is exercised end-to-end
  on real data.
- **0-FP target is NOT met on real traffic** under the frozen θ=0.65 / k=3 detector.
  Real contract behaviour is non-stationary at the 50-tx window scale (heterogeneous
  selectors/callers; an early-test regime change pins drift at 1.0 for a sustained
  run — visible in both plots). The token (USDC.e) is markedly cleaner than the
  router (5 vs 14 episodes), confirming the method fits homogeneous contracts best.
- **Caveat:** the "FP" episodes are on *unlabeled* real data and some are likely
  *genuine* behavioural shifts between the warmup and test periods, not false alarms.

## Recommendation for the gate
Core HDC drift + interpreter is **viable** (clear injected separation, deterministic,
all tiers live on real data), but hitting low FP on real contracts needs one of:
per-selector / sub-prototypes, baseline adaptation (Dream Mode, currently deferred),
or θ recalibration (currently frozen). **Flagged to Lead** — recommend the demo use a
homogeneous (token-class) contract and/or per-selector prototypes. See D-10.
