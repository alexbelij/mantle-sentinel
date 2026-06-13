# todo.md — Developer Viktor working plan (mantle-sentinel)

Deadline checkpoint: 2026-06-14 12:00 Minsk. Submission: June 15.
Work strictly top-down per docs/TASKS.md. Math defaults: docs/MVP_MATH_SPEC.md (MASTER_SEED=1337).

## Order of execution
- [ ] T-01 Scaffold + CI (package layout, make check = ruff+pytest, seed config, `python -m sentinel --version`)
- [ ] T-02 Data capture (Mantle RPC -> bench/data/{contract}/raw.jsonl, >=2000 tx, SHA-256 manifest, idempotent)
- [ ] T-03 Tier 2 HDC encoder (bipolar D=10000, role-filler bind, level encoding for ordinals, window bundling W=50)
- [ ] T-04 Tier 3 drift signal (hamming + timing, robust median/MAD normalize, drift=max)
- [ ] VIABILITY SPIKE (T-02->T-03->T-04 on 1 contract): clean p99<0.3 & 0 FP, injected S1 drift>0.7 within 2 windows; plot + numbers in LOG.md
- [ ] T-05 Tier 1 entropy filter (per (selector,len-bucket) Shannon baseline, 4 sigma)
- [ ] T-05b Tier 0 spam pre-filter (MIN_INTERVAL, k_spam=20)
- [ ] T-06 Tier 4 StaticThresholdDetector (theta=0.65, k=3 hysteresis, 10-min episode collapse)
- [ ] T-07 Tier 5 interpreter + Alert JSON (feature ablation, top-2, schema-valid)
- [ ] T-08 End-to-end replay (`python -m sentinel replay --snapshot ... [--inject ...]`)

## Notes
- Only deploy key (push) available; no PR API. Push branches `task/T-NN-*`, give Lead compare URLs.
- Determinism: every random vector seeded from MASTER_SEED=1337. CI golden-file test on 500-tx fixture.
- Per task: code + pytest acceptance test + `make check` green + LOG.md line + DECISIONS.md if spec gap.
