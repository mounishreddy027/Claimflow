---
name: implement
description: Generates production code and tests for a story group following strict TDD (red-green-refactor), quality principles, and agent team parallel execution.
argument-hint: "[group-id]"
agent: generator
---

# /implement — TDD Code Generation & Agent Implementation Command

When this command is invoked, the `generator` agent implements all stories within a specified dependency group using Claude Code agent teams, enforcing strict Test-Driven Development (TDD) and architectural boundaries.

---

## Overview & Execution Context

- **Assigned Agent:** `generator` (`.claude/agents/generator.md`)
- **SDLC Gate:** Implementation & Unit Verification
- **Input Dependencies:**
  - `specs/stories/dependency-graph.md` (Target group and upstream dependencies)
  - `specs/design/component-map.md` (Authoritative file ownership mapping)
  - `specs/stories/E{n}-S{n}.md` (Acceptance criteria per story)
  - `.claude/state/learned-rules.md` (Accumulated architectural rules)
- **Output Artifacts:** Production source code, comprehensive unit and integration tests

---

## Execution Steps

### Step 0 — Implementation Planning
1. Before writing code or launching teammates, formulate an explicit implementation plan detailing:
   - Specific files to create or modify according to `specs/design/component-map.md`.
   - Domain models, service interfaces, and dependency injections.
   - Verification test strategies for happy, boundary, and error scenarios.
2. Present the plan and confirm task boundaries prior to execution.

### Step 1 — Ingest Six Quality Principles
Inject the six foundational quality principles from `.claude/skills/code-gen/SKILL.md` into all implementation tasks:
1. **Small Modules:** One file, one responsibility. Warning at 200 lines; hard block at 300 lines. Decompose large files.
2. **Static Typing:** Annotate every variable, parameter, and return value. Zero `any` (TypeScript) or untyped signatures (Python).
3. **Functions Under 50 Lines:** Decompose long functions into named, isolated sub-functions.
4. **Single Owner for State Mutations:** Every database write, status change, or event publish has exactly one call site. Pass entity IDs rather than duplicating creations.
5. **Explicit Error Handling:** Define domain-specific error classes (e.g., `PolicyNotActiveException`, `InvalidClaimStateException`). Never swallow exceptions or use bare catch-all blocks.
6. **No Dead Code:** Every line must trace to a specified acceptance criterion. No speculative code or commented-out blocks.
7. **Self-Documenting:** Expressive naming over redundant comments. Comments reserved for non-obvious business invariants and regulatory logic.

### Step 2 — Verify Upstream Dependencies
Read `specs/stories/dependency-graph.md`:
- Identify all stories within the requested group.
- Assert that all upstream groups have been fully implemented and verified.
- If upstream groups have pending failures, halt execution and report the dependency blocker.

### Step 3 — Load File Ownership Boundaries
Read `specs/design/component-map.md`:
- Extract the list of files owned by each story.
- Identify shared type definitions and interfaces.
- Enforce strict boundaries: No teammate may modify a file assigned to another story without coordination.

### Step 4 — Inject Monotonic Learned Rules
Read `.claude/state/learned-rules.md`:
- Inject all accumulated rules and code examples verbatim into teammate prompts.
- Ensure past failure patterns (e.g., missing invariant checks, unmocked environment variables) are proactively mitigated.

### Step 5 — Agent Team Spawning (Multi-Story Groups)
If the group contains 2 or more stories, launch an agent team:
- Create **1 teammate per story** (maximum 5 concurrent teammates).
- If the group contains more than 5 stories, execute in sequential batches of 5.
- Teammate Prompts must include:
  - Full acceptance criteria for the assigned story.
  - Dedicated file ownership list.
  - All learned rules and quality principles.
  - Mandatory TDD instructions: Write failing unit/integration tests before writing implementation logic.
- Coordinate shared files: If two stories touch a shared interface, Phase 1 establishes the interface contract before Phase 2 consumers implement logic.

### Step 6 — Direct Execution (Single-Story Groups)
If the group contains exactly 1 story, execute directly via the `generator` agent:
- Present the planned file changes and test design.
- Write failing tests asserting all acceptance criteria.
- Implement production code to satisfy the tests.
- Refactor for clarity, ensuring compliance with function length and typing rules.

---

## Step 7 — Validation Gate

After all teammates or direct tasks complete, execute the validation gate:
```bash
# 1. Run full test suite
pytest -x -q              # or: npm test

# 2. Run linter
ruff check .              # or: npm run lint

# 3. Run static typechecker
mypy src/                 # or: npm run typecheck
```
All checks must exit with code 0. If any command fails, assign the failure output to the responsible teammate for immediate remediation.

---

## Step 8 — Automated Code Review & Self-Healing

Spawn the code reviewer against modified files:
- Evaluate findings across three severities:
  - **BLOCK:** Architectural violations, type mismatches, missing tests, or security risks. Must be resolved before merge (maximum 3 self-healing retry cycles).
  - **WARN:** Advisory improvements or non-critical formatting notes.
  - **INFO:** Optional stylistic observations.
- If BLOCK findings persist after 3 remediation cycles, halt and escalate to the human supervisor with a detailed issue log.
