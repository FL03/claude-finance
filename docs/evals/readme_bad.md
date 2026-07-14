# myfi (golden: bad, engineering residue)

Shepherd is a Claude Code plugin for long-running engineering work: multi-hour sprints, full patch
arcs, parallel feature lanes, a structured pipeline with fixed roles, gated phases, read-only
audits, a per-project memory, and hooks that block the failure modes long sessions are prone to.

## A closed flock of six agents

| Agent | Job |
| :--- | :--- |
| `@engineer` | Audits ground truth, authors the sprint plan. |
| `@critic` | Adversarially reviews the plan before any code. |
| `@coder` | The only role writing production code, in parallel waves. |
| `@auditor` | Read-only reviewer; a swarm at sprint close. |
| `@worker` | Bounded catch-all: monitoring, ops, cleanup. |
| `@discovery` | Read-only orientation and research. |

## Install

```text
/plugin marketplace add FL03/shepherd
```

Read the docs for the full sprint lifecycle: plant a seed, spawn a conductor, run the pipeline.

## Quickstart

```bash
/shepherd:plant      # author a drift-resistant sprint seed
/shepherd:spawn      # run the sprint end to end
```

Everything here is oriented around getting a multi-hour engineering effort done: introduction mesh,
body waves, close report. Nothing about finance, a toolkit, market data, or a client-facing report
appears anywhere in this document.
