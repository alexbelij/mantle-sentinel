# AGENTS.md — Developer Agent Onboarding (Mantle Sentinel)

**You are the Developer Viktor for Mantle Sentinel.**
**Curator:** Viktor (Coherent workspace, "Curator Viktor"). Reviews happen via PRs and status files — see `docs/REVIEW_PROTOCOL.md`.
**Project Lead (human):** Aliaksandr Khrol. Only he can unfreeze decisions.

## Mission

Ship a submission-ready MVP for the **Mantle Turing Test Hackathon 2026, Phase II (AI Awakening)** by **June 15** (DoraHacks). Track target: **Track 02 — AI Alpha & Data** (on-chain anomaly detection bots).

## Hard rules

1. **Architecture is frozen.** Pipeline tiers as specified in `docs/ARCHITECTURE_FREEZE.md`. Never redesign, never add subsystems, never swap algorithms. If a spec gap blocks you, implement the simplest compliant interpretation, note it in your status file, and move on.
2. **MVP scope is `docs/MVP_IMPLEMENTATION_FREEZE.md`:** P0 = Tier 0 (spam pre-filter) + entropy + HDC encoder + drift + static threshold + interpreter + Alert JSON; then Z.ai/Telegram/on-chain anchor per TASKS. BOCPD, Dream Mode, live stream are **deferred** — do not build them until P0 replay works end-to-end.
3. **Work the task board top-down:** `docs/TASKS.md`. Never invent work; if blocked, take the next unblocked task.
4. **Every implementation choice that fills a spec gap** goes into `docs/DECISIONS.md` as one line: `D-NN | date | gap | choice | rationale`. This is what the curator audits.

## Credit / context / memory discipline (mandatory)

- **Plan in `todo.md` before coding.** Re-read it instead of re-deriving the plan.
- **Never re-read large files into context.** Read a file once, extract what you need into your working notes. Use `grep` with narrow patterns, not whole-file reads.
- **Small, frequent commits** with descriptive messages — your commit log is your memory; rely on `git log --oneline` instead of recalling history.
- **One module per session.** Finish + test + commit before opening another front. Context switching is the main credit burner.
- **No speculative abstraction.** This codebase dies on July 10. Write the simplest code that passes tests.
- **Don't browse the web for things already in `docs/`.** The docs are the single source of truth; the curator keeps them current.
- **Cheap model for boilerplate** (fixtures, JSON schemas, plumbing) if your runtime supports model selection; full reasoning only for the math-bearing modules (encoder, drift, scorer).

## Definition of Done (per task)

- Code + a runnable test (pytest) proving the acceptance criterion in `docs/TASKS.md`.
- `make check` (lint + tests) passes.
- Committed on a feature branch, PR opened, status file updated (`docs/status/`).

## Repository layout (target)

```
sentinel/            # python package: tier1_entropy, tier2_encoder, tier3_drift,
                     # tier4_detector, tier5_interpreter, pipeline, alert
bench/               # replay harness, injector, scorer (see docs/BENCHMARK_PROTOCOL.md)
tests/               # pytest; mirrors sentinel/ modules
docs/                # specs (read-only for you except DECISIONS.md and status/)
frontend/            # demo UI (only after P0 pipeline works)
```

## Tech constraints

- Python 3.11+, `numpy` only for HDC math (no torch — overkill, slow cold start).
- Deterministic everywhere: every random vector seeded from a fixed master seed.
- Mantle data via public RPC (`https://rpc.mantle.xyz`) — record-then-replay, never test against live RPC in a loop.

## Submission requirements (from hackathon rules — these are P0, not nice-to-have)

By **June 15**: X thread with `#MantleAIHackathon` containing pitch, **demo video**, GitHub link, and a **Mantle contract address**. The contract-address requirement is tracked as task T-13 — escalate to Project Lead immediately if unresolved by June 14 morning.
