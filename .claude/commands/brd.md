---
name: brd
description: Direct invocation of the Socratic interview and business requirements gathering workflow across five dimensions to synthesize a comprehensive Business Requirements Document.
argument-hint: "[optional-project-or-feature-name]"
agent: planner
---

# /brd — Business Requirements Document Gathering Command

When this command is invoked, the `planner` agent executes an interactive Socratic interview to elicit requirements, explore architectural alternatives, and synthesize a structured Business Requirements Document (BRD).

---

## Overview & Execution Context

- **Assigned Agent:** `planner` (`.claude/agents/planner.md`)
- **SDLC Gate:** Gate 1 (Requirements Discovery & Approval)
- **Output Target:** `specs/brd/brd.md` (or `specs/brd/feature-{name}.md`)
- **Required Gate:** Explicit human approval before advancing to `/spec`

---

## Execution Steps

### Step 0 — Pre-flight Exploration & Brainstorming
1. Before beginning the structured interview, initiate a brainstorming pass to explore the user's intent, core value proposition, and design space.
2. Uncover implicit domain requirements (e.g., insurance claim lifecycles, regulatory audit constraints, payout invariants).
3. Feed initial brainstorming findings into the interview prompt without bypassing human verification.

### Step 1 — Codebase & Substrate Analysis
Scan the project workspace to detect existing infrastructure and avoid contradictory proposals:
- Check existing directories: `src/`, `specs/`, `backend/`, `frontend/`.
- Identify runtime languages, database technologies, and configuration files.
- Inspect `.claude/program.md` and `.claude/state/learned-rules.md` for project-specific constraints.
- Note existing domain rules, policies, and entity models already in place.

### Step 2 — The Five-Dimension Socratic Interview
Conduct the interview sequentially. Ask 2–4 targeted questions per dimension, summarize responses, and obtain confirmation before advancing:

#### Dimension 1 — Why (Problem & Goals)
- What specific business problem does this solve, and who are the primary users?
- What does quantifiable success look like in 30, 60, and 90 days?
- What is the operational cost or risk of not solving this problem?
- *Confirm:* "Here is the problem and success criteria as understood: [summary]. Does this accurately reflect your vision?"

#### Dimension 2 — What (Scope & MVP)
- What are the mandatory core operations the system must perform?
- What features are explicitly out of scope for the initial release?
- What is the minimum viable product (MVP) — the smallest deployable slice delivering real value?
- What external systems, registries, or third-party APIs must be integrated?
- *Confirm:* "Here is the agreed core scope and MVP boundary: [summary]. Anything to add, adjust, or exclude?"

#### Dimension 2.5 — Alternatives Considered
Propose 2–3 concrete implementation approaches with explicit trade-offs:
- Approach description and architectural pattern.
- Advantages, disadvantages, technical risks, and maintenance footprint.
- Recommendation with justification.
- *Confirm:* Record the user's chosen direction and the rationale for discarding alternative approaches.

#### Dimension 3 — How (Technical Architecture)
- What is the target technology stack (backend, frontend, database, test frameworks)?
- What are the core data entities, schemas, and persistence requirements?
- What are the non-functional requirements (throughput, response latency, fixed-point precision)?
- *Confirm:* "Here is the captured technical architecture: [summary]. Does this match your architectural standards?"

#### Dimension 4 — Edge Cases & Operational Constraints
- What happens when critical operations fail (e.g., transaction failure, external service downtime)?
- What compliance, regulatory, or data handling standards apply (e.g., PII masking, immutable audit trails)?
- What are the known edge cases or boundary conditions in business logic?
- *Confirm:* "Here are the operational constraints and failure scenarios: [summary]. Are any constraints missing?"

#### Dimension 5 — UI Context & User Experience
- Does the system include a user interface? What are the primary screens, journeys, and states?
- What responsive breakpoints and viewports must be supported (desktop, tablet, mobile)?
- What design system, color tokens, and accessibility (WCAG AA) standards must be satisfied?
- *Confirm:* "Here is the captured UI context: [summary]. Is this design scope complete?"

---

## Step 3 — Synthesize into Structured BRD

Upon confirming all dimensions, compile the final document into exactly 13 standard sections:
1. **Executive Summary**
2. **Problem Statement & Business Objectives**
3. **Target Users & Personas**
4. **Success Metrics & KPIs**
5. **Functional Scope (In-Scope vs. Out-of-Scope)**
6. **MVP Definition & Vertical Slices**
7. **Alternatives Considered & Architectural Trade-offs**
8. **Technical Architecture & Stack Specifications**
9. **Data Model Overview & Core Entities**
10. **External Integrations & Third-Party Boundaries**
11. **Edge Cases, Security & Non-Functional Requirements**
12. **UI/UX Context & Responsive Wireframes**
13. **Open Questions & Future Considerations**

---

## Step 4 — Output Artifact Generation

- Write the synthesized document:
  - For full projects: `specs/brd/brd.md`
  - For feature additions: `specs/brd/feature-{name}.md`
- Ensure the parent directory `specs/brd/` is created if not already present.

---

## Step 5 — Human Gate & Review

Present the generated BRD to the user with the following verification prompt:
> **Gate 1 Approval Check:**
> "The Business Requirements Document has been written to `specs/brd/brd.md`.
> Does this BRD accurately capture your requirements?
> Reply **Approved** to proceed to `/spec`, or provide specific amendments."

> [!CAUTION]
> **Strict Gate Enforcement:** Never advance automatically to `/spec` without explicit user confirmation.
