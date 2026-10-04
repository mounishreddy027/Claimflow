---
name: auto
description: Orchestrates the autonomous ratcheting loop with Karpathy ratcheting, sprint contract negotiation, agent teams, 6-layer ratchet gates, and self-healing.
argument-hint: "[--mode full|lean|solo|turbo] [--group GROUP_ID]"
agent: generator
---

# /auto — Autonomous Ratcheting Build Loop Command

When this command is invoked, the `generator` lead orchestrates the autonomous build loop implementing Andrej Karpathy's ratcheting pattern, GAN-style generator-evaluator separation, sprint contract negotiations, and failure-driven learning across dependency groups.

---

## Overview & Execution Context

- **Assigned Lead Agent:** `generator` (`.claude/agents/generator.md`)
- **Gatekeeper Agent:** `evaluator` (`.claude/agents/evaluator.md`)
- **Visual Critic Agent:** `design-critic` (`.claude/agents/design-critic.md`)
- **Orchestration Rule:** The lead orchestrates execution and spawns specialized worker teams; it does not write speculative code directly.
- **State Files Monitored:**
  - `.claude/program.md` (Human control knobs & constraints)
  - `.claude/state/learned-rules.md` (Monotonically accumulated rules)
  - `claude-progress.txt` (Session chaining & memory bridge)
  - `features.json` (Machine-readable feature pass/fail ledger)
  - `.claude/state/failures.md` (Failure categorization log)
  - `.claude/state/coverage-baseline.txt` (Ratchet coverage floor)
  - `.claude/state/iteration-log.md` (Iteration history)

---

## Execution Loop

### Section 1 — Context Recovery Protocol (Start of Every Iteration)
At the start of every iteration, read the following files in strict order:
1. **`.claude/program.md`:** Re-read project constraints and human instructions. Never cache.
2. **`.claude/state/learned-rules.md`:** Load accumulated rules. Inject verbatim into all agent prompts.
3. **`claude-progress.txt`:** Parse the final session block to determine `current_group`, `groups_completed`, and `next_action`.
4. **`features.json`:** Identify remaining unpassed features.
5. **`specs/stories/dependency-graph.md`:** Select the next unfinished dependency group whose upstream dependencies are 100% complete.

---

### Section 2 — Sprint Contract Negotiation
Before any code is generated for a group, establish immutable done-criteria:
1. **Generator Proposal:**
   - Ingest group stories from `specs/stories/`, `specs/design/api-contracts.md`, and `component-map.md`.
   - Draft a sprint contract using `.claude/templates/sprint-contract.json` containing `api_checks`, `playwright_checks`, `design_checks`, `architecture_checks`, and targeted feature IDs.
   - Write draft to `sprint-contracts/{group}.json`.
2. **Evaluator Review & Approval:**
   - Spawn `evaluator` (`.claude/agents/evaluator.md`) to audit the proposed contract against acceptance criteria.
   - The evaluator adds missing checks, trims untraceable checks, and finalizes the file.
   - Once approved, the contract is **immutable**.

---

### Section 3 — Agent Team Parallel Execution
Spawn a Claude Code agent team to execute the group's stories:
1. **Micro-DAG Handshake:**
   - Inspect `specs/design/component-map.md` to identify shared files and interface boundaries (`Produces:` / `Consumes:`).
   - Divide teammates into phases: Phase 1 (independent interface contracts), Phase 2 (consumers), Phase 3 (integrators).
2. **Teammate Spawning:**
   - Up to 5 concurrent teammates per phase.
   - Every teammate receives story acceptance criteria, exact file ownership, all learned rules, and quality principles from `.claude/skills/code-gen/SKILL.md`.
   - Mandatory Red-Green-Refactor: Teammates must write failing tests before implementing production logic.

---

### Section 4 — The 6-Layer Ratchet Gate
After the agent team finishes, execute the ratchet verification gates. Progress is monotonic — regressions are strictly blocked.

| Gate | Scope & Tooling | Condition for Passing |
|---|---|---|
| **1. Unit Tests** | `pytest -x -q` / `npm test` | 100% tests pass (0 failures) |
| **2. Lint & Types** | `ruff check`, `mypy`, `eslint`, `tsc` | 0 lint errors, 0 type errors |
| **3. Test Coverage** | `pytest --cov` / `vitest --coverage` | Coverage >= baseline AND >= 80% hard floor |
| **4. Architecture Checks** | Files exist check, schema validation | All contract files present on disk |
| **5. Evaluator Gate** | API + Playwright vs. running application | All `api_checks` and `playwright_checks` pass |
| **6. Design Critic** | Vision scoring vs. `calibration-profile.json` | Weighted score >= threshold (Full mode only) |

---

### Section 5 — PASS / FAIL & Self-Healing Loop

#### On PASS (All Gates Green):
1. Commit changes: `git add -A && git commit -m "feat: implement group {group}"`.
2. Update `features.json`: Set `passes: true` and record timestamp for all features in the group.
3. Update `claude-progress.txt`: Append new session block.
4. Update `.claude/state/coverage-baseline.txt`: Record new higher coverage baseline.
5. Advance to the next group.

#### On FAIL (Self-Healing — Maximum 3 Attempts):
1. **Classify Failure:** Categorize into one of 10 standardized categories (Lint/Format, Type Error, Test Failure, Import Error, Coverage Drop, API Failure, Playwright Failure, Design Score Low, Container Failure, Architecture Drift).
2. **Execute Targeted Fix:**
   - Spawn `generator` with failure JSON, category auto-fix strategy, accumulated `prior_attempts`, and all learned rules.
   - Apply surgical corrections strictly to failing components.
3. **Re-evaluate:** Re-run only the failed gate.
4. **Third Failure Escalation:**
   - Revert current group modifications: `git checkout -- {group_files}`.
   - Log incident details to `.claude/state/failures.md`.
   - Extract a new rule into `.claude/state/learned-rules.md` if the failure pattern occurred 2+ times.
   - Mark group as `BLOCKED` in `claude-progress.txt` and escalate to the human supervisor.

---

### Section 6 — Application Lifecycle Management
The orchestrator manages application state according to `verification.mode` in `project-manifest.json`:
- **Docker Mode:** Starts stack via `bash init.sh` or `docker compose up -d --build`. Executes health check retry loop before evaluator handoff. Tears down via `docker compose down -v` on completion.
- **Local Mode:** Spawns background service processes and verifies local health endpoints.
- **Stub Mode:** Spawns lightweight schema-valid mock servers based on `api-contracts.schema.json`.

---

### Section 7 — Session Chaining & Completion
Append session progress to `claude-progress.txt`:
```text
=== Session {N} ===
date: {ISO 8601 timestamp}
mode: {mode}
groups_completed: [A, B, ...]
groups_remaining: [C, D, ...]
current_group: {group}
features_passing: {pass_count} / {total_count}
coverage: {coverage_percent}%
learned_rules: {rule_count}
blocked_stories: {none | list}
next_action: {specific next task}
```

**Build Complete Criteria:**
When all features in `features.json` are `passes: true` and coverage >= 80%:
1. Print completion summary (features, coverage, iterations).
2. Generate developer `README.md` documenting architecture, API endpoints, setup, and test commands.
3. Commit and exit cleanly.
