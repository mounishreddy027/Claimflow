# specs/CLAUDE.md — Specifications Governance & Authoring Rules

This document governs the maintenance, modification, and structure of all specification files in `specs/`.

---

## 1. The Spec-Is-Truth Non-Negotiable Rule

Whenever code implementation and specification diverge:
- **The specification wins.**
- Developers and agents must NEVER modify a specification merely to accommodate a flawed or shortcut code implementation.
- If a business requirement legitimately changes, update the relevant `specs/*_spec.md` deliberately first, review the diff, and then prompt the `generator` agent to re-implement code and tests to conform to the updated spec.

---

## 2. Specification Structure Standard

Every feature specification in `specs/` must include:
1. **Header Metadata:** Feature Title, Feature ID (`SPEC-NN`), Domain (`Insurance — Claims Operations BC-AINE-005`).
2. **Feature Description & Scope:** High-level narrative and business boundaries.
3. **Explicit Acceptance Criteria:**
   - Clearly mapped to canonical IDs (`AC-01` through `AC-10`).
   - Formatted in testable **Given-When-Then** scenarios.
   - Exhaustive coverage of happy path, boundary edge cases, and failure modes.
4. **Data Contracts / API Specifications:**
   - Request and response JSON schemas.
   - HTTP status codes (e.g., 201 Created, 400 Bad Request, 403 Forbidden, 422 Unprocessable Entity).
5. **Non-Functional Requirements Mapping:**
   - Specific citations of `NFR-01` through `NFR-08`.

---

## 3. Mandatory AC Traceability

No specification may be committed without explicit reference to its assigned Acceptance Criteria:
- `intake_spec.md` -> `AC-01`, `AC-02`
- `document_verification_spec.md` -> `AC-03`
- `fraud_screening_spec.md` -> `AC-04`
- `assessment_spec.md` -> `AC-05`, `NFR-01`
- `settlement_spec.md` -> `AC-06`, `AC-07`
- `reopen_spec.md` -> `AC-08`
- `admin_override_spec.md` -> `AC-09`, `NFR-04`
- `state_machine_spec.md` -> `AC-10`
