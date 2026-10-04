# Claude Harness Engine v1 — Design Reference

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User / CI                            │
└─────────────────────┬───────────────────────────────────────┘
                      │ slash commands
┌─────────────────────▼───────────────────────────────────────┐
│                   Orchestrator (Claude)                      │
│  /brd → /spec → /design → /build → /test → /evaluate        │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
Planner   Generator  Evaluator  Test Eng  Security Rev
   │          │          │          │          │
   └──────────┴──────────┴──────────┴──────────┘
                         │
              ┌──────────▼──────────┐
              │     State Layer      │
              │  features.json       │
              │  claude-progress.txt │
              │  learned-rules.md    │
              │  failures.md         │
              │  iteration-log.md    │
              └──────────────────────┘
```

## Karpathy Ratchet Loop

```
        ┌──────────────────────────────────┐
        │         Build Feature            │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────▼───────────────────┐
        │       Evaluate vs Design         │◄──────────┐
        └──────────────┬───────────────────┘           │
                       │                               │
              score ≥ threshold?                       │
                  /         \                          │
                Yes           No                       │
                 │             │                       │
        ┌────────▼──┐  ┌───────▼────────┐             │
        │  Proceed  │  │  Design Critic  │             │
        └───────────┘  │  suggests fix   │             │
                       └───────┬─────────┘             │
                               │                       │
                       ┌───────▼─────────┐             │
                       │  Generator      │─────────────┘
                       │  applies fix    │  (max 5 iterations)
                       └─────────────────┘
```

## Agent Roles

| Agent            | File                          | Responsibility                         |
|------------------|-------------------------------|----------------------------------------|
| Planner          | `.claude/agents/planner.md`   | Sprint planning, story breakdown       |
| Generator        | `.claude/agents/generator.md` | Feature implementation                 |
| Evaluator        | `.claude/agents/evaluator.md` | API + Playwright verification          |
| Design Critic    | `.claude/agents/design-critic.md` | Design scoring (Karpathy loop)     |
| UI Designer      | `.claude/agents/ui-designer.md`   | Mockups, design tokens             |
| Test Engineer    | `.claude/agents/test-engineer.md` | Test authoring and execution       |
| Security Reviewer| `.claude/agents/security-reviewer.md` | Vulnerability auditing         |

## ClaimFlow Domain Agents

| Agent                     | File                               | Responsibility                  |
|---------------------------|------------------------------------|---------------------------------|
| Claim Intake Agent        | `.claude/agents/claim-intake-agent.md` | FNOL validation, policy checks  |
| Fraud Screening Agent     | `.claude/agents/fraud-screening-agent.md` | Rule-based fraud detection  |
| Assessment Agent          | `.claude/agents/assessment-agent.md` | Claim amount calculation        |
| Settlement Agent          | `.claude/agents/settlement-agent.md` | Decisioning and payouts        |
| State Machine Validator   | `.claude/agents/state-machine-validator-agent.md` | Lifecycle validation |
| Audit Tracer              | `.claude/agents/audit-tracer-agent.md` | Compliance auditing        |
| Archtest Author           | `.claude/agents/archtest-author-agent.md` | Architecture testing       |

## Hook Execution Order

| # | Hook                  | File                               | Trigger                        |
|---|-----------------------|------------------------------------|--------------------------------|
| 1 | enforce-length-pre    | `hooks/enforce-length-pre.js`      | Pre-write/edit                 |
| 2 | scope-directory       | `hooks/scope-directory.js`         | File access                    |
| 3 | protect-env           | `hooks/protect-env.js`             | Any file write                 |
| 4 | detect-secrets        | `hooks/detect-secrets.js`          | Pre-commit                     |
| 5 | lint-on-save          | `hooks/lint-on-save.js`            | File save (.py, .ts)           |
| 6 | typecheck             | `hooks/typecheck.js`               | File save (.py, .ts)           |
| 7 | check-architecture    | `hooks/check-architecture.js`      | File save                      |
| 8 | check-function-length | `hooks/check-function-length.js`   | File save                      |
| 9 | check-file-length     | `hooks/check-file-length.js`       | File save                      |
| 10 | track-writes         | `hooks/track-writes.js`            | File save                      |
| 11 | pre-commit-gate      | `hooks/pre-commit-gate.js`         | Pre-commit                     |
| 12 | sprint-contract-gate | `hooks/sprint-contract-gate.js`    | Pre-build                      |

## State Files

| File                  | Purpose                                              |
|-----------------------|------------------------------------------------------|
| `features.json`       | Feature registry with status tracking                |
| `claude-progress.txt` | Session progress and current pipeline position       |
| `learned-rules.md`    | Accumulated rules from past failures (ratchet memory)|
| `failures.md`         | Failure log for pattern analysis                     |
| `iteration-log.md`    | Evaluator iteration history per feature              |
| `eval-scores.json`    | Design scores per component per iteration            |
| `coverage-baseline.txt` | Test coverage baseline for regression detection   |

## Sprint Contract Format

A sprint contract (sprint-contracts/{group-id}.json) defines a unit of work:

```json
{
  "contract_id": "group-01",
  "group_name": "FNOL Intake",
  "stories": ["intake-01", "intake-02", "intake-03"],
  "acceptance_criteria": [
    "All policy validation checks pass",
    "Document checklist generated correctly",
    "90% test coverage minimum"
  ],
  "dependencies": [],
  "estimated_complexity": "medium",
  "approved": false
}
```

The sprint-contract-gate hook blocks /build until approved: true.

## Quality Principles

1. Correctness first — all tests must pass before a feature is considered done
2. Type safety — strict typing enforced by hooks on every save
3. Layered architecture — one-way dependency boundaries enforced
4. Test coverage — coverage gate enforced at ≥ 80%; regressions block merges
5. Security by default — secrets detection runs on every commit
6. Iterative improvement — Karpathy ratchet ensures quality only moves forward

## Tech Stack

Backend: Python 3.12 + FastAPI + PostgreSQL + uv + pytest
Frontend: TypeScript + React 18 + Vite + npm + vitest
Deployment: Docker Compose (local dev), Cloud-ready configuration
