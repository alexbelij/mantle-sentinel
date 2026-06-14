# Status LOG — one line per event
# Format: YYYY-MM-DD HH:MM | T-NN | PR #N | done/blocked | note

2026-06-13 00:30 | setup | - | done | Curator kit committed: AGENTS.md, TASKS.md, REVIEW_PROTOCOL.md, MVP_MATH_SPEC.md, BENCHMARK_PROTOCOL.md, DECISIONS.md
2026-06-13 02:10 | setup | - | done | Docs reconciled to panel consensus: GPT drafts archived, MVP_MATH_SPEC restored (+Tier 0, D=10k), ARCHITECTURE_FREEZE/README/IMPL_FREEZE rewritten, T-05b/T-21 added, T-19 -> P1
2026-06-13 05:00 | T-13 | - | decided | Lead: SentinelAlertRegistry final deploy on Mantle MAINNET (manual, key not shared); self-attack demo on Sepolia testnet (T-13b/T-13c added). Viability spike added as Jun 14 go/no-go gate (D-07, D-08).

2026-06-13 06:00 | T-01 | branch task/T-01-scaffold | done | scaffold: pyproject, Makefile(make check), config.py (frozen consts), CLI (--version, replay), CI workflow, tests
2026-06-13 06:30 | T-03 | branch task/T-03-hdc-encoder | done | Tier 2 HDC encoder: bipolar D=10k, sha256 item memory, level-encoded ordinals, role-filler binding, sign-bundling, ablation; 5 tests
2026-06-13 07:00 | T-04 | branch task/T-04-drift | done | Tier 3 drift = max(norm(hamming), norm(timing)), robust median/MAD; D-09 MAD-degeneracy guard, D-10 squash-tail (FP control delegated to Tier-4 hysteresis); clean median 0.09, injected ~1.0, 0 false alerts via k=3; 2 tests
2026-06-13 07:20 | T-05 | branch task/T-05-entropy | done | Tier 1 Shannon entropy filter, per (selector,len-bucket) baseline, 4sigma, abstain <20; 5 tests
2026-06-13 07:30 | T-05b | branch task/T-05b-prefilter | done | Tier 0 spam pre-filter, MIN_INTERVAL=0.001-quantile, k_spam=20, spam excluded from baselines; 3 tests
2026-06-13 07:45 | T-06 | branch task/T-06-detector | done | Tier 4 StaticThresholdDetector theta=0.65 k=3 hysteresis + shared EpisodeTracker (10-min collapse); 6 tests
2026-06-13 08:00 | T-07 | branch task/T-07-interpreter | done | Tier 5 feature-ablation interpreter (top-2 attribution) + Alert JSON (jsonschema-validated against contracts/alert.schema.json); 7 tests
2026-06-13 08:20 | T-08 | branch task/T-08-replay | done | end-to-end pipeline (Tier0->5 single entrypoint) + FeatureExtractor (quantile buckets, streaming novelty) + replay harness + S1 injector + synthetic snapshot; determinism byte-identical; CLI `python -m sentinel replay`; 3 tests. Total 35 tests, ruff clean
2026-06-13 08:20 | T-02 | - | in-progress | Etherscan V2 key received (chainid 5000); capturing real snapshot next for viability spike

2026-06-13 09:10 | T-02 | branch task/T-02-data | done | Etherscan V2 capture script (urllib, chainid 5000) -> raw.jsonl + sha256; captured LB Router (3618 tx) + USDC.e (3993 tx)
2026-06-13 09:15 | spike | branch task/T-02-data | done | D-08 viability spike on REAL data: mechanism works (S1 -> drift 1.0, detected; deterministic), but 0-FP NOT met under frozen theta/k (router 14 / token 5 regime episodes; separation 3-4.3x). See docs/status/SPIKE.md + plots. FLAGGED to Lead: needs per-selector prototypes / Dream Mode / theta recalibration.
2026-06-13 11:xx | REVIEW | PR #1 | APPROVE-WITH-NOTES | Curator: viability spike CONDITIONAL PASS. Core HDC mechanism works (separation 3-4.3x, S1 always detected). FP gate revised per D-10: 14 clean regime episodes on LB Router (high), 5 on USDC.e (acceptable). D-11: demo uses USDC.e. Code quality HIGH. Next: T-09+T-10+T-13b+T-13c+T-19+T-21 on new branch, then merge to main.

2026-06-14 11:00 | T-17c | branch task/T-17c-bocpd-env | done | SENTINEL_DETECTOR env flag selects Tier-4 detector (static default | bocpd drop-in); build_pipeline(detector=)/replay/CLI --detector; tests/test_pipeline.py (6). Also chore: cleared pre-existing ruff debt (UP037/F401/I001 + bad noqa) -> make lint green. 97 tests pass.

2026-06-14 11:20 | T-18d | branch task/T-18d-dream-pipeline | done | Dream Mode in pipeline: opt-in dream_mode consolidates safe windows (detector silent + drift<running median over last W=100 windows) into the drift prototype every n_dream=100 via dream_update(alpha=0.5) (MVP_MATH_SPEC §6 / D-04 / D-12); replay/CLI --dream-mode. Off by default. tests/test_replay.py +4 (clean 0-FP + consolidation fires, no-FP regression, attack detected, determinism). make lint green.

2026-06-14 12:40 | T-18e | branch task/T-18e-s6-bench | done | S6 slow-drift injector ("boil-the-frog": gas 1x->5x + growing calldata-entropy ramp across post-onset span, in-place) added to bench/injector.py + INJECTORS; bench/dream_bench.py dual-run harness (CLEAN/S6 x dream OFF/ON, deterministic n=8000 seed=7); rows -> bench/REPORT.md. Result: Dream Mode did 19-23 consolidations yet added 0 clean FP (16->15 eps) and did NOT mask S6 (detected both modes, delay 102 vs 99 win) — rolling-median gate excludes rising-drift attack windows. tests/test_injector.py +7, tests/test_replay.py +1. 109 passed, make lint green.
