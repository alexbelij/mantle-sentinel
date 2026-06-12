# MVP IMPLEMENTATION FREEZE

Status: FROZEN (restored + panel consensus 2026-06-13). Architecture: `docs/ARCHITECTURE_FREEZE.md`.

## P0 (pipeline core)
- Tier 0 Timing pre-filter
- Tier 1 Shannon Entropy
- Tier 2 HDC Encoder + Drift signal
- Tier 3 Static Threshold detector
- Tier 4 Interpreter (DNA Drift explainer)
- Alert JSON (`contracts/alert.schema.json`)

## MVP additions (panel consensus — after T-08 replay works)
- Z.ai GLM explanation, alert-only, strict template (T-19)
- Telegram alert delivery (T-21)
- On-chain alert anchor `SentinelAlertRegistry` on Mantle (T-13 — submission requirement)

## Deferred (full version / post-hackathon)
- BOCPD (pluggable behind the T-06 detector interface; fallback = static threshold)
- Dream Mode (nightly consolidation)
- Live Mantle stream (MVP = record-then-replay)
- Website / production integration

## Goal
End-to-end replay: transactions → Alert JSON (**T-08**) before any advanced feature work.
