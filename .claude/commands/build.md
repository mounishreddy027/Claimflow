---
name: build
description: Executes the complete end-to-end SDLC pipeline across 8 sequential phases with human approval gates on phases 1-3 and autonomous execution in phases 5-8.
argument-hint: "[path-to-BRD] [--mode full|lean|solo|turbo]"
agent: planner
---

# /build — Full SDLC Pipeline Execution Command

When this command is invoked, the `planner` agent orchestrates the end-to-end software development lifecycle across 8 structured phases, enforcing human approval gates at requirements, specification, and architecture stages before launching the autonomous build ratchet.

---

## Overview & Execution Context

- **Orchestrating Agent:** `planner` (`.claude/agents/planner.md`)
- **Downstream Agents:** `generator` (`.claude/agents/generator.md`), `evaluator` (`.claude/agents/evaluator.md`), `ui-designer` (`.claude/agents/ui-designer.md`), `design-critic` (`.claude/agents/design-critic.md`)
- **Execution Modes:**
  - `full`: All ratchet gates enforced, including Playwright UI automation and Design Critic vision scoring (default).
  - `lean`: Skips Design Critic vision scoring; retains API and Playwright browser checks.
  - `solo`: Generator works sequentially without team spawning, evaluator, or Docker stack checks.
  - `turbo`: Single-pass execution for advanced models with per-commit lint/test gates and single final evaluation.

---

## The 8-Phase Pipeline Execution

### Phase 1 — Business Requirements Gathering [HUMAN APPROVAL GATE]
1. Execute `/brd` workflow using the provided requirements document or prompt.
2. Produce structured `specs/brd/brd.md`.
3. **Mandatory Gate:** Halt execution and present summary to the user:
   > "Approve BRD to proceed to Phase 2 (Story Specification)?"
4. Do NOT proceed without explicit user consent.

### Phase 2 — Story Specification & Feature Generation [HUMAN APPROVAL GATE]
1. Execute `/spec` using the approved BRD.
2. Generate user stories (`specs/stories/E{n}-S{n}.md`), acyclic dependency graph (`specs/stories/dependency-graph.md`), and `features.json`.
3. **Mandatory Gate:** Halt execution and present story count, parallel groups, and feature list:
   > "Approve stories and dependency graph to proceed to Phase 3 (Architecture Design)?"
4. Do NOT proceed without explicit user consent.

### Phase 3 — Architecture & Interface Design [HUMAN APPROVAL GATE]
1. Execute `/design` using approved stories.
2. Produce `system-design.md`, `api-contracts.md`, `api-contracts.schema.json`, `data-models.md`, `data-models.schema.json`, `component-map.md`, and HTML mockups.
3. Validate schema syntax and verify UI field name alignment.
4. **Mandatory Gate:** Halt execution and present architecture summary:
   > "Approve architecture and component mapping to enter autonomous implementation?"
5. Do NOT proceed without explicit user consent.

### Phase 4 — State Layer Initialization
Before entering the autonomous loop, initialize all repository state tracking files:
1. `.claude/state/coverage-baseline.txt`: Initialize to `0` (or current baseline).
2. `.claude/state/iteration-log.md`: Write header `# Iteration Log\n\nTracking autonomous build cycles.\n`.
3. `.claude/state/failures.md`: Ensure file exists for recording failure classifications.
4. `.claude/state/learned-rules.md`: Ensure file exists to store extracted ratchet rules.
5. `claude-progress.txt`: Write Session 0 block:
   ```text
   === Session 0 ===
   date: {ISO 8601 current timestamp}
   mode: {mode}
   groups_completed: []
   groups_remaining: [A, B, C, ...]
   current_group: none
   features_passing: 0 / {total features}
   coverage: 0%
   learned_rules: 0
   next_action: Begin autonomous build with /auto
   ```

### Phases 5–8 — Autonomous Execution Loop
Invoke the `/auto` execution loop with the selected mode:
```bash
/auto --mode {mode}
```
The `/auto` command assumes control of:
- **Phase 5:** Sprint contract negotiation per dependency group (`sprint-contracts/{group}.json`).
- **Phase 6:** Agent team execution using `generator` teammates adhering to red-green-refactor TDD.
- **Phase 7:** Ratchet gate verification (unit tests, type checking, coverage >= baseline, evaluator checks).
- **Phase 8:** Self-healing and session chaining across context windows.

### Phase 9 — Application Documentation & README Generation
Upon successful completion of all feature groups:
1. Ingest `specs/brd/brd.md`, `specs/design/system-design.md`, `specs/design/api-contracts.md`, `component-map.md`, and `project-manifest.json`.
2. Generate a comprehensive, developer-facing `README.md` for the generated application containing:
   - Project Title & Business Overview.
   - Architectural Layering & Service Diagram.
   - Technology Stack Table (Framework, Database, Testing, CI).
   - Local Setup & Quick Start (`bash init.sh`, Docker Compose).
   - Complete API Endpoint Catalog.
   - Test Execution Instructions (Unit, Integration, E2E).
   - Environment Configuration Table.
3. Commit documentation: `git add README.md && git commit -m "docs: add application README"`.
