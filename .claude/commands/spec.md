---
name: spec
description: Translates an approved Business Requirements Document into vertical epics, granular user stories, an acyclic dependency graph, and features.json for session tracking.
argument-hint: "[path-to-BRD]"
agent: planner
---

# /spec — Story Decomposition & Feature Specification Command

When this command is invoked, the `planner` agent decomposes the approved Business Requirements Document (BRD) into vertical epics, granular user stories with testable acceptance criteria, an acyclic dependency graph, and a machine-readable `features.json` registry.

---

## Overview & Execution Context

- **Assigned Agent:** `planner` (`.claude/agents/planner.md`)
- **SDLC Gate:** Gate 2 (Story Decomposition & Dependency Modeling)
- **Input Artifact:** `specs/brd/brd.md` (or path passed as argument)
- **Output Artifacts:**
  - `specs/stories/dependency-graph.md`
  - `specs/stories/E{n}-S{n}.md` (individual story definitions)
  - `features.json` (root feature tracking registry)
- **Required Gate:** Human review and signoff before proceeding to `/design`

---

## Execution Steps

### Step 1 — Ingest & Validate BRD
1. Resolve the BRD path: Use the argument passed to `/spec [path]` or default to `specs/brd/brd.md`.
2. Verify that the file exists and has been approved. If missing, halt execution immediately:
   > "Error: BRD file not found at `{path}`. Please run `/brd` first to gather business requirements."
3. Extract core requirements, domain invariants, and non-functional requirements (NFRs).

### Step 2 — Decompose into Vertical Epics
Organize functional areas into coherent vertical slices (`E1`, `E2`, `E3`...):
- Each epic must represent an end-to-end capability (e.g., Claim Intake, Fraud Screening, Financial Assessment, Settlement & Payout).
- Maintain 3–5 stories per epic. Never allow fewer than 2 or more than 5 stories per epic.
- If an epic exceeds 5 stories, split it into two focused epics.

### Step 3 — Author User Stories with Testable Acceptance Criteria
For each story within an epic, generate a specification adhering to the following structure:
- **Story Identifier:** `E{n}-S{n}` (e.g., `E1-S1`, `E1-S2`).
- **Title:** Concise imperative description (e.g., `Submit FNOL with incident details and documents`).
- **Narrative:** Persona format (`As a claimant, I want to submit FNOL so that Horizon can process my loss`).
- **Acceptance Criteria (3–6 per story):**
  - Must be objectively testable and observable (concrete status codes, JSON payload keys, error messages).
  - Explicitly tag canonical acceptance criterion IDs (e.g., `AC-01`, `AC-02`) and non-functional requirement IDs (`NFR-01`, `NFR-02`).
  - Vague phrasing such as "works properly" or "fast loading" is strictly prohibited.
- **Layer Assignment:** Exactly one of: `Types` | `Config` | `Repository` | `Service` | `API` | `UI`.
- **Dependency Group:** Letter assignment (`A`, `B`, `C`...) for parallel scheduling.
- **Upstream Dependencies:** List of blocking story IDs (`depends_on: []` if Group A).

### Step 4 — Construct the Acyclic Dependency Graph
Generate `specs/stories/dependency-graph.md`:
1. Group stories into execution tiers:
   - **Group A:** Zero dependencies (foundations, base domain types, data models). Executed in parallel.
   - **Group B:** Depends exclusively on Group A outputs (repositories, base services).
   - **Group C:** Depends on Group B/A (orchestration services, controllers, business rules).
   - **Group D+:** Higher-level API integrations, UI views, end-to-end workflows.
2. Validate that **zero circular dependencies** exist. Any cycle must be resolved before proceeding.
3. Render a Mermaid `graph TD` visualizing the dependency flow across groups.

### Step 5 — Write Individual Story Files
Write each individual story definition to `specs/stories/E{n}-S{n}.md`. Include:
```markdown
# Story E{n}-S{n}: {Title}

**Epic:** {Epic Name}  
**Layer:** {Layer}  
**Group:** {Group}  
**Depends On:** [{Dependencies}]

## Description
{Narrative and business context}

## Acceptance Criteria
- [ ] AC-01: {Specific observable criterion}
- [ ] AC-02: {Specific observable criterion}
- [ ] AC-03: {Specific observable criterion}
```

### Step 6 — Generate `features.json` Registry
Transform every acceptance criterion into machine-readable feature entries and write to `features.json` (and `specs/features.json`):

```json
[
  {
    "id": "F001",
    "category": "functional",
    "story": "E1-S1",
    "group": "A",
    "description": "FNOL submission endpoint returns 201 Created with claim reference ID on valid payload",
    "steps": [
      "POST /api/v1/claims with valid policy_number and incident_date",
      "Assert HTTP response status is 201",
      "Assert response JSON contains non-null claim_id and state equals FILED"
    ],
    "passes": false,
    "last_evaluated": null,
    "failure_reason": null,
    "failure_layer": null
  }
]
```

**Registry Schema Requirements:**
- `id`: Sequential zero-padded identifier (`F001`, `F002`...).
- `category`: `functional` | `integration` | `ui` | `security` | `performance`.
- `passes`: Set strictly to `false` at creation.
- `last_evaluated`: Set strictly to `null` until evaluated.
- Every story criterion must map to at least one entry.

---

## Step 7 — Human Gate & Review Checklist

Present the summary to the user:
1. Total Epics, Stories, and Generated Features count.
2. Parallel execution groups table (Group, Stories, Layers).
3. Pre-approval verification checklist:
   - [ ] Every story contains 3–6 testable acceptance criteria.
   - [ ] Every story has an explicit layer and group assignment.
   - [ ] Dependency graph is strictly acyclic.
   - [ ] All features initialized with `passes: false`.

> **Gate 2 Approval Check:**
> "Story decomposition and `features.json` generation complete.
> Approve this specification to proceed to `/design`, or provide corrections."
