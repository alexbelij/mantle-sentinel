# REVIEW_PROTOCOL.md — Curator ↔ Developer Protocol

Goal: high-quality oversight at near-zero curator token cost. Everything async, everything in the repo.

## Roles

- **Developer Viktor** — implements `docs/TASKS.md`, owns code and tests.
- **Curator Viktor** — reviews PRs, audits decisions, owns specs (`docs/*.md`), updates task board.
- **Project Lead (Aliaksandr)** — approvals, unfreezing, social posting, final submission.

## Branch & PR rules (Developer)

1. One task = one branch `task/T-NN-short-name` = one PR to `main`. No direct pushes to `main`.
2. PR description template (this is what the curator reads — make it self-sufficient):
   ```
   Task: T-NN
   What: <2 lines>
   Spec gaps filled: <D-NN refs or "none">
   Tests: <names of new tests + what they prove>
   Self-check: make check green? deterministic (seeded)? acceptance criterion met how?
   Risk: <the one thing most likely wrong>
   ```
3. Keep PRs under ~400 changed lines where possible; split otherwise.
4. After opening a PR, append one line to `docs/status/LOG.md`:
   `YYYY-MM-DD HH:MM | T-NN | PR #N | done/blocked | one-line note`

## Review procedure (Curator)

- Trigger: Project Lead ping or batch-review request — not continuous polling.
- Reads, in order, stopping as soon as confidence is reached:
  1. `docs/status/LOG.md` (delta since last review)
  2. PR descriptions
  3. `gh pr diff` of **math-bearing modules only** (encoder, drift, normalize, scorer, Dream Mode) — plumbing is trusted if tests pass
  4. Test files for the above
- Verdict posted as a PR comment: `APPROVE`, `APPROVE-WITH-NOTES` (merge now, fix-forward), or `BLOCK` (math/spec violation only).
- Curator does not write feature code. Curator may fix specs/docs directly on `main`.

## Review checklist (what gets a PR blocked)

- Architecture freeze violated (new subsystem, algorithm swap)
- Non-determinism (unseeded randomness, wall-clock dependence in tests)
- Math-spec deviation without a `D-NN` entry
- Acceptance criterion not actually covered by a test
- Live RPC calls inside tests or tight loops

## Escalation

- **Blocked > 2h on a spec gap:** make the simplest compliant choice, log `D-NN`, continue. Do not wait.
- **Blocked on access/approval (deploy keys, contract decision T-13, posting):** write `[!]` in LOG.md **and** notify Project Lead immediately — these cannot be self-served.
- **June 14, 12:00 Minsk:** mandatory go/no-go checkpoint. Developer posts a submission-readiness summary in LOG.md **including the viability-spike result (clean drift p99, FP count, injected drift; see TASKS P0 gate, D-08)**; curator audits against the P0-SUBMIT list and the spike pass-criteria.

## Token-economy norms (both agents)

- The repo is the only channel. No long chat threads about content that belongs in docs.
- Status lines, not status essays.
- Curator reviews diffs and tests, never re-reads the whole codebase. Developer keeps modules small so that stays possible.
