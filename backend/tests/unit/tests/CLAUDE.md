# tests/CLAUDE.md — Testing Conventions & Quality Gates

This document defines testing standards, tagging conventions, and quality gates for the `tests/` directory.

---

## 1. Mandatory Acceptance Criteria Tagging

**Every test class and test case MUST be explicitly tagged with its canonical AC identifier.**
Un-tagged tests will fail the evaluator quality ratchet.

### Canonical Tags:
- `AC-01`: Customer FNOL filing with policy, date, type, and documents
- `AC-02`: Policy inactive on incident date raises `PolicyNotActiveException`
- `AC-03`: Document checklist enforcement varies by claim type
- `AC-04`: Deterministic fraud scoring and policy threshold flagging
- `AC-05`: Assessment computation math and invariant `payable_amount >= 0`
- `AC-06`: Adjudication decision engine with policy reason codes
- `AC-07`: Immutable settlement payout record matching assessed amount
- `AC-08`: Reopen creates linked sub-claim; original moves to `REOPENED`
- `AC-09`: Admin overrides auto-approve/reject with audited comment/reason
- `AC-10`: Enforced claim state transitions and `InvalidClaimStateException`
- `NFR-01`: Fixed-point decimal arithmetic in financial calculations
- `NFR-02`: Append-only immutability of ledgers
- `NFR-03`: Zero PII in application logs
- `NFR-04`: Role-based access control separation (Assessor vs Admin)
- `NFR-06`: Structured JSON logging with request correlation IDs
- `NFR-07`: Health endpoint returns HTTP 200 within 1 second of startup
- `NFR-08`: Automated architectural tests and structural invariants

---

## 2. Test Suite Organization

```
tests/
├── CLAUDE.md                 <-- You are here
├── unit/
│   ├── domain/               <-- Pure business rules, math, invariants (AC-02, AC-03, AC-04, AC-05, AC-06)
│   └── state/                <-- State machine lifecycle transitions (AC-10)
├── integration/              <-- Database repository ledgers, append-only checks (AC-07, NFR-02)
├── api/                      <-- REST controller endpoints, RBAC, correlation IDs (AC-01, AC-08, AC-09, NFR-04, NFR-06, NFR-07)
├── security/                 <-- PII log redaction tests (NFR-03)
├── architecture/             <-- ArchUnit / structural tests (NFR-01, NFR-08)
└── e2e/                      <-- Playwright browser end-to-end tests (UI validation)
```

---

## 3. TDD Enforcement & Coverage Baselines

1. **Red-Green-Refactor:** Generator agents must write failing tests first, followed by minimal implementation, followed by clean refactoring.
2. **Coverage Floor:** The evaluator enforces a hard coverage floor of **80%**, with a target of **90%+** on `src/domain/`.
3. **Zero Tolerance for Flaky Tests:** Any test that fails intermittently must be isolated and fixed immediately.
