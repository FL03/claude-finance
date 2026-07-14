---
name: taxes
description: Tax-workflow pipeline — gathers account activity, classifies income/gains, routes each item to its IRS form, computes an estimate, flags the filing deadline, clears the @auditor compliance gate, and emits a filing-actionable summary. Loads skills/taxes/SKILL.md first, then @auditor before anything ships.
argument-hint: "[tax_year] [--account taxable|ira|401k|hsa] [--dry-run]"
allowed-tools: Read, Grep, Glob, Bash, Skill, Agent, Write, mcp__plugin_myfi_myfi-toolkit__quote, mcp__plugin_myfi_myfi-toolkit__db_init, mcp__plugin_myfi_myfi-toolkit__db_migrate, mcp__plugin_myfi_myfi-toolkit__db_version
---

# /myfi:taxes — Tax-Workflow Pipeline

Runs the client's raw account activity for `tax_year` (default: the current calendar year) all
the way to a filing-actionable summary: which forms apply, which 1099s to pull, the estimated
short-term/long-term gain split, one or two concrete optimization moves with their deadline, and
the filing deadline stated plainly. This command is the pipeline; `skills/taxes/SKILL.md` is the
form map and workflow it implements — never improvise a rule this skill does not name.

## Step 0 — Load skills

1. `skills/myfi/SKILL.md` first — orientation: toolkit surface, flock table, LLM law.
2. `skills/taxes/SKILL.md` — mandatory. The seven-step workflow and IRS form map this pipeline
   walks below. Do not run Step 1 before this is loaded.

## Step 1 — Gather

Pull the client's account activity for `tax_year` via the toolkit
(`mcp__plugin_myfi_myfi-toolkit__quote` for current pricing context on any still-open position;
account/transaction data comes from what the client supplies or has on file — this pipeline never
fetches live brokerage data, no such tool is wired here). Identify every account type touched
(`--account` narrows to one; default scans all: taxable brokerage, traditional/Roth IRA, 401(k),
HSA) — each has a different tax treatment for the same underlying transaction.

## Step 2 — Classify

Sort activity per `skills/taxes/SKILL.md` §2: realized capital gains/losses (short-term vs
long-term by holding period), ordinary vs qualified dividends, interest income, wash sales,
retirement contributions/distributions.

## Step 3 — Route to forms

Map each classified item to its documented home (Form 8949 → Schedule D for gains, Schedule B for
dividends/interest above threshold, Publication 550 for wash-sale/cost-basis mechanics,
Publication 590-A/590-B for retirement contributions/distributions). Anything outside the skill's
named baseline (multi-state filings, foreign accounts/FBAR, business income, AMT edge cases) is
flagged out-of-scope and routed to a human preparer, never guessed.

## Step 4 — Compute

Net short-term and long-term gains/losses separately, apply the $3,000/year capital-loss deduction
cap against ordinary income (remainder carried forward), and sum an estimated taxable-income
delta. This is an estimate for a workflow, not a filed number.

## Step 5 — Identify optimizations

Surface tax-loss harvesting (respecting the 30-day wash-sale window), asset-location moves,
holding-period timing near the one-year mark, and retirement-contribution timing — each grounded
in the mechanism it relies on, each with the deadline it is actionable by.

## Step 6 — Flag filing deadlines

State the individual filing deadline (April 15, next business day if a weekend/holiday) and any
applicable quarterly estimated-tax deadlines. Name explicitly that Form 4868 moves the *filing*
deadline, never the *payment* deadline.

## Step 7 — Compliance gate

Dispatch `@auditor` (loads `compliance` alongside `skills/taxes/SKILL.md`) with the Steps 1-6
draft before anything reaches the client. `@auditor` runs its Hypothesis+Falsification+Confidence
triple against every numeric claim and form citation and returns PASS/REDO, capped at 3 REDO
cycles (`agents/auditor.md`'s contract). A REDO re-runs the failing step(s) with the auditor's
findings attached — never silently patch the draft yourself. Only a PASS clears Step 8.

## Step 8 — Report

Assemble the filing-actionable summary (form checklist, ST/LT gain split, 1-2 optimization moves
with deadlines, the filing deadline, and the professional-review caveat from
`skills/taxes/SKILL.md` §7 — this is a checklist for a preparer or filing software, not a
substitute for either). Write it to `.myfi/reports/taxes-<tax_year>-<timestamp>.md` and print the
path — this is the pipeline's deliverable artifact.

## `--dry-run`

Skips the toolkit/network calls and the `@auditor` dispatch, walking the same eight steps against
placeholder data so the pipeline shape can be verified structurally (the seam the integration
suite's mock-LLM lane exercises). Never used for a real filing-actionable output.

## Non-goals

No live trade execution, no filed submission — this command produces a checklist a human acts on;
it never files, transmits, or submits anything on the client's behalf.
