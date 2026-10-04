---
name: design
description: Generates system architecture, OpenAPI/JSON schemas, domain state machines, component mappings, and self-contained UI mockups by coordinating planner and ui-designer agents.
argument-hint: "[--force]"
agent: planner
---

# /design — System Architecture & UI Mockup Command

When this command is invoked, the `planner` agent coordinates with the `ui-designer` agent to produce system architecture blueprints, machine-readable schemas, domain state machine specifications, component routing tables, and self-contained UI mockups.

---

## Overview & Execution Context

- **Primary Agent:** `planner` (`.claude/agents/planner.md`)
- **Coordinated Agent:** `ui-designer` (`.claude/agents/ui-designer.md`)
- **SDLC Gate:** Gate 3 (Architectural Design & Contract Definition)
- **Input Dependencies:** `specs/stories/` and `features.json`
- **Output Artifacts:**
  - `specs/design/system-design.md`
  - `specs/design/api-contracts.md` & `specs/design/api-contracts.schema.json` (OpenAPI 3.0)
  - `specs/design/data-models.md` & `specs/design/data-models.schema.json` (JSON Schema)
  - `specs/design/state-machines.md` (Domain Lifecycle Transitions)
  - `specs/design/folder-structure.md`
  - `specs/design/component-map.md` (Story ID → Implementation File Ownership)
  - `specs/design/deployment.md`
  - `specs/design/mockups/E{n}-S{n}.html` (Standalone UI mockups per UI story)
- **Required Gate:** Human review and signoff before proceeding to `/build`

---

## Execution Steps

### Step 0 — Architectural Brainstorming & Direction
1. Analyze architectural trade-offs: data storage choices, relational vs document storage, synchronous vs event-driven state transitions, and fixed-point math guarantees.
2. Formulate explicit architectural decisions and document rationale prior to locking schema definitions.

### Step 1 — Concurrent Agent Spawning

Execute both agents concurrently within the design phase:

#### 1. Planner Agent Responsibilities
The `planner` agent reads all stories from `specs/stories/` and authors:
- **`system-design.md`:** Component topology, layered boundaries (`Types` → `Config` → `Repository` → `Service` → `API` → `UI`), security perimeters, and request flow.
- **`api-contracts.md` & `api-contracts.schema.json`:** Comprehensive specification of every HTTP endpoint: HTTP method, path, headers, request body, query parameters, response codes (200, 201, 400, 403, 404, 422, 500), and JSON schemas. Must produce a valid, parseable OpenAPI 3.0 document.
- **`data-models.md` & `data-models.schema.json`:** Relational entity definitions, primary keys, foreign keys, table indexes, immutability constraints (append-only ledger tables), and JSON Schema (draft-07+).
- **`state-machines.md`:** Formal domain state machine definition detailing states (e.g., `FILED`, `UNDER_REVIEW`, `APPROVED`, `REJECTED`, `SETTLED`, `REOPENED`), legal transitions, illegal transitions, guard conditions, and transition ledger logging.
- **`folder-structure.md`:** Complete annotated directory tree for both backend and frontend modules.
- **`component-map.md`:** Authoritative file ownership matrix mapping every story ID (`E{n}-S{n}`) to the exact source files, test files, and shared interfaces it owns.
- **`deployment.md`:** Container topology, `docker-compose.yml` service definitions, port mappings, volume mounts, environment configurations, and health check endpoints.

#### 2. UI Designer Agent Responsibilities
The `ui-designer` agent reads UI stories and generates self-contained HTML mockups:
- Location: `specs/design/mockups/E{n}-S{n}.html` (one per story where `layer: UI`).
- Must inline all styling (Tailwind CSS or modern CSS tokens) and interactive JavaScript without external unpkg/CDN runtime dependencies.
- Match exact field names, entity models, and enum values defined in `api-contracts.md`.
- Include empty, loading, error, and validation states alongside the happy path.
- Label interactive elements with their corresponding API contract calls.

---

## Step 2 — Post-Completion Cross-Validation Pass

Perform an automated consistency audit after both agents complete:
1. **Schema Syntax Validation:** Ensure `api-contracts.schema.json` and `data-models.schema.json` are valid, well-formed JSON.
2. **UI vs. API Shape Alignment:**
   - Scan all `.html` mockups in `specs/design/mockups/`.
   - Extract form inputs, payload fields, and table columns.
   - Verify every field name in the UI matches the property names in `api-contracts.schema.json`.
   - Report any discrepancies (e.g., `claimNumber` vs `claim_number`).
3. **Component Map Integrity:** Ensure every story in `specs/stories/` is mapped to at least one production file and one test file.

---

## Step 3 — Human Gate & Review

Present the architectural deliverables to the user:
- Architecture summary (layers, protocols, persistence).
- State machine transition rules.
- OpenAPI schema validation status.
- Mockup catalog with local links.

> **Gate 3 Approval Check:**
> "System architecture, schemas, and UI mockups generated and validated.
> Approve the design to proceed to autonomous implementation via `/build` or `/auto`, or specify amendments."
