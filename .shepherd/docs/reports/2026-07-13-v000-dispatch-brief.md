---
title: v0.0.0 Dispatch Brief -- deferred spawn resume (quota-gated)
kind: dispatch-brief
date: 2026-07-13
author: shepherd-root (opus) @ /shepherd:spawn
fires_via: scheduled-task (local, one-shot) -- reset+margin 18:50 CDT
reason: weekly quota at ~5% at spawn time; reset ~18:43 CDT. Cheap preflight done now; expensive dispatch deferred.
---

# READ THIS FIRST -- you are the resumed root-shepherd for the myfi v0.0.0 spawn

The quota has reset. **Run the FULL dispatch now -- do NOT defer again.** A prior root-shepherd
session did the cheap deterministic preflight and locked the scope; you pick up at dispatch.

## Locked scope decision (do NOT re-litigate)

- **Scope = single sprint** (`--scope sprint`). `v000.seed.md` line 13 + line 267:
  `v0.0.0` is ONE patch on ONE branch, `kind: sprint-seed`, **no `-dev.N` fan-out** (operator decision).
- Therefore **NO `confirm version` / `confirm minor` gate applies.** Do not ask for it.
- One XL sprint, **6 internal waves**, graph `W1 → [W2 ∥ W3] → W4 → W5 → W6` (seed §7, non-binding).
- Lanes are the engineer's call -- decompose from file-disjoint root component dirs
  (`agents/` ∥ `skills/` ∥ `commands/` ∥ `services/` ∥ `hooks/` ∥ `bin/` ∥ `docs/`). Lane count is
  CONSTANT across waves once set (pipeline.md §Lane law).

## Preflight already cleared (17:28 CDT, do not fully redo -- spot-check only)

- `shctx` present at `/Users/jo3/.local/bin/shctx`.
- `shepherd.toml` at `.claude/shepherd.toml` (exists; Check 4 satisfied).
- Seed: `.shepherd/docs/plans/v000.seed.md` (`status: ready-for-engineer`). **No plan yet** -- engineer authors it.
- Model pins: `conductor=sonnet`, `engineer=opus[1m]`, `critic/discovery/coder/auditor/worker=sonnet`.
  Pin each spawned role via `shctx models resolve <role>` -- do NOT rely on frontmatter propagation.
- Lock: FREE. Live teammates: NONE (`shctx teammate liveness` empty, `shctx dash` → "TEAMMATES none live").
- No rebase/merge in progress. No `.artifacts/shepherd.lock`.
- Priors: empty (first cycle) → resource estimate is "(defaults -- no priors yet)".

## BLOCKER to clear FIRST -- stale team configs (Check 3 is HARD)

`~/.claude/teams/` holds **4 stale team configs from prior sessions** (none live per `shctx teammate
liveness`):

- `session-137faad8` (Jul 7, 1 member: team-lead)
- `session-177e2ef6` (Jul 12, 4 members: team-lead + lane-A-config + lane-C-capture + lane-B-decision)
- `session-7c3b62a9` (Jul 7, 1 member)
- `session-fc04fb6c` (Jul 7, 1 member)

Check 3 hard-refuses on any `config.json` carrying `members[]`, so **run `/shepherd:cleanup` FIRST**
to prune these stale (non-live) entries before the first teammate spawn. Only prune entries that are
confirmed non-live; if any is unexpectedly live, STOP and surface to the operator.

## Dispatch sequence (per /shepherd:spawn command + agents/conductor.md)

1. Re-invoke the spawn skill: `/shepherd:spawn` for the v0.0.0 sprint (scope=sprint). Re-run preflight
   (fast); it will find the seed and proceed to dispatch this time.
2. `/shepherd:cleanup` → prune the 4 stale teams. Confirm `~/.claude/teams/` clean of stale configs.
3. **Self-contained `@engineer`** (the DEFAULT): spawn as a native teammate, `model: opus`,
   `mode: self-contained`, `dispatcher: root-shepherd`. It runs its OWN intro wave (min 5 subagents:
   2 `@discovery` + 3 intro-`@auditor`) + its own `@critic` loop until GREEN, and returns ONE finalized
   plan + hash-tied critic-proof. Root runs NEITHER its own intro wave NOR `@critic` (that is
   `ROOT-INTRO-USURPED`). Engineer also runs the seed §4 Phase-0 mesh (15 rows) at plan time.
4. Accept the plan via the **thin gate** only: `shctx seed verify` + `shctx plan verify --plan <plan>`
   + a lane-count sanity check. Do NOT re-review.
5. Project the approved plan into vertical LANES (engineer's decomposition). Lane count constant.
6. **Pre-create every lane worktree** BEFORE spawning:
   `git worktree add .worktrees/{sprint_slug}-{lane_id} v0.0.0` per lane; `git worktree list` to verify;
   emit `[WORKTREE-READY]`. Teammates must NOT create their own worktrees (`TEAMMATE-GIT-WRITE`).
7. Verify the `Agent` tool is registered in this lead session (teammates inherit it to dispatch the
   flock). If absent → HALT, `/reload-plugins`, retry.
8. Spawn one **teammate-conductor** per lane, `model: sonnet`, agent type `shepherd:conductor`,
   named `shepherd-conductor-v000-{lane_id}`. Each gets the boot prompt from the command's
   "Teammate prompt" template with every inherited fact filled in (seed path, plan path, lane brief +
   steps, worktree path, `[BASE-COMMIT-EXPECTED]` = `v0.0.0` HEAD sha, shepherd.toml snapshot,
   prohibitions). Each teammate BEGINS ITS LANE IMMEDIATELY on spawn.
9. **Register every teammate**: `shctx teammate register <name> --team={team_id} --type=conductor`
   (and `--type=engineer` for the engineer). Idempotent. Without this the `TeammateIdle` hook floods
   the lead with unmatched idle noise (#183). Then confirm `shctx teammate liveness` shows each lane active.
10. Drive the active-drive loop (wake → act → probe; never passive-wait). Monitor `TeammateIdle` /
    `TaskCompleted`. Triage escalations by `halt_code`. Alert on >5 min heartbeat staleness.
    **Commit at EVERY wave boundary immediately**: `git commit -m "chore(v0.0.0/wave-K): wave-complete
    via spawn"` -- the one-wave loss horizon holds ONLY if a commit lands at every boundary.
11. At CLOSE-FINALIZE: run the merge, write `.shepherd/docs/reports/2026-07-13-v000-close.md`, run
    `/shepherd:cleanup`, report DONE with restart instructions.

## Gate discipline for lanes (conductor.md owns this)

cargo `--frozen`, `CARGO_TARGET_DIR=target/.lanes/<lane-slug>`, gates SERIAL, `cargo fix` FORBIDDEN.
NOTE: v0.0.0 is a **Python/poetry + markdown-plugin** sprint (toolkit at `services/toolkit/`), not Rust --
gates are `poetry run pytest` + the seed's runnable `**Acceptance:**` predicates (grep/count/CLI-exit) +
`bash hooks/tests/run.sh`. Tests + evals ship in the same commit (`CLAUDE.md` §Tests and evals).

## References

- Command: `/shepherd:spawn` (re-invoke to reload full instructions).
- Root profile: `agents/shepherd.md` (adopt as system-prompt addendum) -- resolve the path via the
  shepherd plugin; the spawn command names it.
- Seed: `.shepherd/docs/plans/v000.seed.md` (the mandate -- 16 issue-anchored deliverables, 6 waves).
- Project law: `CLAUDE.md` (services-first, LLM-via-local-Claude-Code, tests+evals same commit).
- Discovery harvest: `.shepherd/docs/reports/2026-07-13-{planter-mesh,discovery-packaging,discovery-harvest,discovery-marketdata}.md`.
