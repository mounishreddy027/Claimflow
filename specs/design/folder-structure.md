# Folder Structure — ClaimFlow

Complete proposed directory tree for backend (Python), frontend (React), and supporting infrastructure.

```
cap3/
├── backend/                                    # Python backend application
│   ├── src/
│   │   └── claimflow/
│   │       ├── __init__.py
│   │       ├── main.py                         # FastAPI application entry point
│   │       ├── config.py                       # Configuration (env vars, settings)
│   │       ├── types/
│   │       │   ├── __init__.py
│   │       │   ├── claim.py                    # Claim type definitions
│   │       │   ├── policy.py                   # Policy type definitions
│   │       │   ├── document.py                 # Document type definitions
│   │       │   ├── assessment.py               # Assessment type definitions
│   │       │   ├── settlement.py               # Settlement type definitions
│   │       │   ├── fraud.py                    # Fraud screening type definitions
│   │       │   ├── audit.py                    # Audit log type definitions
│   │       │   ├── exceptions.py               # Custom exceptions (PolicyNotActiveException, etc.)
│   │       │   └── enums.py                    # Enums (ClaimState, ClaimType, etc.)
│   │       ├── config_loaders/
│   │       │   ├── __init__.py
│   │       │   ├── fraud_rules_loader.py       # Load fraud rule versions from JSON (E3-S2)
│   │       │   ├── document_checklist_loader.py # Load document checklists per LOB (E2-S1)
│   │       │   └── policy_loader.py             # Load policy definitions
│   │       ├── repositories/
│   │       │   ├── __init__.py
│   │       │   ├── base.py                     # Base repository class
│   │       │   ├── claim_repository.py         # Claim CRUD + state transitions
│   │       │   ├── policy_repository.py        # Policy lookups
│   │       │   ├── document_repository.py      # Document CRUD + immutability enforcement
│   │       │   ├── assessment_repository.py    # Assessment immutable recording
│   │       │   ├── fraud_repository.py         # Fraud screening result recording
│   │       │   ├── settlement_repository.py    # Settlement WORM ledger
│   │       │   ├── subclaim_repository.py      # Sub-claim creation and linking
│   │       │   ├── override_repository.py      # Override audit log (immutable)
│   │       │   ├── audit_repository.py         # Audit trail (append-only)
│   │       │   └── fraud_rule_repository.py    # Fraud rule version management
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── policy_service.py           # Policy active validation (E1-S1)
│   │       │   ├── fraud_service.py            # Fraud rule engine (E3-S1)
│   │       │   ├── assessment_service.py       # Coverage assessment (E4-S1)
│   │       │   ├── payout_service.py           # Payout calculation (E4-S2)
│   │       │   ├── settlement_service.py       # Settlement generation (E5-S2)
│   │       │   ├── document_service.py         # Document verification logic
│   │       │   ├── override_service.py         # Admin override implementation (E7-S1)
│   │       │   ├── dispute_service.py          # Dispute/sub-claim creation (E6-S1)
│   │       │   └── audit_service.py            # Audit trail recording
│   │       ├── api/
│   │       │   ├── __init__.py
│   │       │   ├── middleware.py               # Auth, correlation ID, request logging
│   │       │   ├── dependencies.py             # Dependency injection for services/repos
│   │       │   ├── routes/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── claims.py               # E1-S2: POST /api/claims/intake, GET /api/claims/{claim_id}
│   │       │   │   ├── documents.py            # E2-S2: POST /api/claims/{id}/documents, E2-S3: GET /api/document-verification-queue
│   │       │   │   ├── verification.py         # E2-S4: POST /api/claims/{id}/verify-documents
│   │       │   │   ├── fraud.py                # E3-S3: POST /api/claims/{id}/evaluate-fraud
│   │       │   │   ├── assessment.py           # E4-S3: POST /api/claims/{id}/assess
│   │       │   │   ├── settlement.py           # E5-S3: POST /api/claims/{id}/settle
│   │       │   │   ├── disputes.py             # E6-S1: POST /api/claims/{id}/dispute, E6-S2: GET /api/claims/{id}/linked-claims
│   │       │   │   ├── overrides.py            # E7-S3: POST /api/claims/{id}/override-decision
│   │       │   │   └── audit.py                # E7-S2: GET /api/audit-trail/{claim_id}
│   │       │   └── schemas.py                  # Request/response Pydantic models
│   │       ├── database/
│   │       │   ├── __init__.py
│   │       │   ├── models.py                   # SQLAlchemy ORM models
│   │       │   ├── engine.py                   # Database connection + session management
│   │       │   ├── migrations/
│   │       │   │   └── versions/                # Alembic migration scripts
│   │       │   │       ├── 001_initial_schema.py
│   │       │   │       ├── 002_immutability_triggers.py
│   │       │   │       └── 003_audit_trail_indexes.py
│   │       │   └── seed_data/
│   │       │       ├── policies.json            # Test policies
│   │       │       ├── fraud_rules.json         # Fraud rule definitions
│   │       │       └── checklists.json          # Document checklists per LOB
│   │       └── utils/
│   │           ├── __init__.py
│   │           ├── correlation_id.py           # Correlation ID generation/tracking
│   │           ├── immutability.py             # Immutability constraint enforcement
│   │           ├── financial.py                # Fixed-point arithmetic helpers
│   │           ├── pii_redaction.py            # PII redaction for audit logs
│   │           └── logging.py                  # Structured logging
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                         # Pytest fixtures and configuration
│   │   ├── unit/
│   │   │   ├── __init__.py
│   │   │   ├── test_policy_service.py           # Unit tests for policy validation (E1-S1)
│   │   │   ├── test_fraud_service.py            # Unit tests for fraud engine (E3-S1)
│   │   │   ├── test_assessment_service.py       # Unit tests for assessment (E4-S1)
│   │   │   ├── test_payout_service.py           # Unit tests for payout calc (E4-S2)
│   │   │   ├── test_settlement_service.py       # Unit tests for settlement (E5-S2)
│   │   │   └── test_override_service.py         # Unit tests for override (E7-S1)
│   │   ├── integration/
│   │   │   ├── __init__.py
│   │   │   ├── test_claim_intake_flow.py        # E1-S2 integration test
│   │   │   ├── test_document_workflow.py        # E2 document flow tests
│   │   │   ├── test_fraud_assessment_flow.py    # E3, E4 flow tests
│   │   │   ├── test_settlement_flow.py          # E5 settlement flow tests
│   │   │   ├── test_dispute_flow.py             # E6 dispute flow tests
│   │   │   └── test_override_flow.py            # E7 override flow tests
│   │   └── fixtures/
│   │       ├── __init__.py
│   │       ├── policies.py                     # Mock policy fixtures
│   │       ├── claims.py                       # Mock claim fixtures
│   │       └── users.py                        # Mock user fixtures
│   ├── pyproject.toml                          # Poetry/uv project config
│   ├── pytest.ini                              # Pytest configuration
│   ├── ruff.toml                               # Ruff linter configuration
│   ├── mypy.ini                                # MyPy type checker configuration
│   └── requirements.txt                        # Pin dependencies (generated from pyproject.toml)
│
├── frontend/                                   # React + TypeScript frontend
│   ├── src/
│   │   ├── index.tsx                           # React root
│   │   ├── App.tsx                             # Main app component
│   │   ├── types/
│   │   │   ├── claim.ts                        # Claim type definitions
│   │   │   ├── policy.ts                       # Policy type definitions
│   │   │   ├── api.ts                          # API request/response types
│   │   │   └── index.ts                        # Type barrel exports
│   │   ├── api/
│   │   │   ├── client.ts                       # Axios/fetch client with correlation ID
│   │   │   ├── claims.ts                       # Claim API methods
│   │   │   ├── documents.ts                    # Document API methods
│   │   │   ├── fraud.ts                        # Fraud evaluation API
│   │   │   ├── assessment.ts                   # Assessment API
│   │   │   ├── settlement.ts                   # Settlement API
│   │   │   ├── disputes.ts                     # Dispute/sub-claim API
│   │   │   ├── overrides.ts                    # Override API
│   │   │   └── audit.ts                        # Audit trail API
│   │   ├── pages/
│   │   │   ├── ClaimIntakePage.tsx             # FNOL filing page (E1-S2 UI)
│   │   │   ├── ClaimStatusPage.tsx             # Claim status query (E1-S3 UI)
│   │   │   ├── DocumentUploadPage.tsx          # Document upload (E2-S2 UI)
│   │   │   ├── VerificationQueuePage.tsx       # Verification queue (E2-S3 UI)
│   │   │   ├── FraudScreeningPage.tsx          # Fraud evaluation UI (E3-S3 UI)
│   │   │   ├── AssessmentPage.tsx              # Assessment decision UI (E4-S3 UI)
│   │   │   ├── SettlementPage.tsx              # Settlement confirmation UI (E5-S3 UI)
│   │   │   ├── DisputePage.tsx                 # Dispute filing UI (E6-S1 UI)
│   │   │   ├── OverridePage.tsx                # Admin override UI (E7-S3 UI)
│   │   │   └── AuditTrailPage.tsx              # Audit log viewer (E7-S2 UI)
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx                  # Reusable button component
│   │   │   │   ├── Card.tsx                    # Reusable card component
│   │   │   │   ├── Form.tsx                    # Form wrapper component
│   │   │   │   ├── Modal.tsx                   # Modal/dialog component
│   │   │   │   ├── CorrelationIdDisplay.tsx    # Display correlation ID
│   │   │   │   └── ErrorBanner.tsx             # Error message display
│   │   │   ├── claim/
│   │   │   │   ├── ClaimSummary.tsx            # Claim details display
│   │   │   │   ├── ClaimTimeline.tsx           # Claim state transition timeline
│   │   │   │   └── ClaimForm.tsx               # Claim data form
│   │   │   ├── document/
│   │   │   │   ├── DocumentUploader.tsx        # Multi-file upload component
│   │   │   │   ├── DocumentList.tsx            # Document list display
│   │   │   │   └── DocumentVerifier.tsx        # Document verification UI
│   │   │   ├── assessment/
│   │   │   │   ├── FraudScoreDisplay.tsx       # Fraud score visualization
│   │   │   │   ├── AssessmentDetails.tsx       # Assessment result display
│   │   │   │   └── PayoutCalculator.tsx        # Payout amount display
│   │   │   └── audit/
│   │   │       ├── AuditLogTable.tsx           # Audit trail table
│   │   │       └── AuditLogFilters.tsx         # Audit filter UI
│   │   ├── hooks/
│   │   │   ├── useClaimForm.ts                 # Claim form logic hook
│   │   │   ├── useDocumentUpload.ts            # Document upload hook
│   │   │   ├── useApi.ts                       # Generic API call hook
│   │   │   └── useAuth.ts                      # Authentication/role hook
│   │   ├── context/
│   │   │   ├── AuthContext.tsx                 # Authentication context (actor ID, role)
│   │   │   ├── ClaimContext.tsx                # Claim data context
│   │   │   └── NotificationContext.tsx         # Toast/notification context
│   │   ├── styles/
│   │   │   ├── globals.css                     # Global Tailwind styles
│   │   │   ├── components.css                  # Component-specific styles
│   │   │   └── theme.css                       # Theme variables
│   │   └── utils/
│   │       ├── formatters.ts                   # Date/currency/number formatting
│   │       ├── validators.ts                   # Form validation helpers
│   │       └── constants.ts                    # UI constants (claim states, etc.)
│   ├── public/
│   │   ├── index.html                          # HTML template
│   │   ├── favicon.ico                         # Favicon
│   │   └── manifest.json                       # PWA manifest
│   ├── tests/
│   │   ├── __mocks__/
│   │   │   └── api.ts                          # Mock API responses
│   │   ├── components/
│   │   │   ├── ClaimForm.test.tsx              # Component tests
│   │   │   └── DocumentUploader.test.tsx
│   │   ├── hooks/
│   │   │   └── useClaimForm.test.ts            # Hook tests
│   │   └── e2e/
│   │       ├── claim-intake.spec.ts            # E2E test: claim intake flow
│   │       ├── document-upload.spec.ts         # E2E test: document upload
│   │       ├── assessment.spec.ts              # E2E test: assessment flow
│   │       └── settlement.spec.ts              # E2E test: settlement flow
│   ├── playwright.config.ts                    # Playwright E2E configuration
│   ├── tsconfig.json                           # TypeScript configuration
│   ├── package.json                            # npm dependencies
│   ├── package-lock.json                       # Dependency lock file
│   └── tailwind.config.js                      # Tailwind CSS configuration
│
├── specs/
│   ├── stories/
│   │   ├── E1-S1.md                            # Policy Active Date Validation
│   │   ├── E1-S2.md                            # Claim Intake Endpoint (FNOL)
│   │   ├── E1-S3.md                            # Claim Status Query Endpoint
│   │   ├── E2-S1.md                            # Document Checklist Definition
│   │   ├── E2-S2.md                            # Document Upload Endpoint
│   │   ├── E2-S3.md                            # Document Verification Queue
│   │   ├── E2-S4.md                            # Verification Decision Endpoint
│   │   ├── E3-S1.md                            # Fraud Rule Engine
│   │   ├── E3-S2.md                            # Fraud Threshold Configuration
│   │   ├── E3-S3.md                            # Fraud Screening Endpoint
│   │   ├── E4-S1.md                            # Coverage Assessment Logic
│   │   ├── E4-S2.md                            # Payout Calculation
│   │   ├── E4-S3.md                            # Assessment Decision Endpoint
│   │   ├── E5-S1.md                            # Immutable Payout Ledger
│   │   ├── E5-S2.md                            # Settlement Payout Generation
│   │   ├── E5-S3.md                            # Settlement Confirmation Endpoint
│   │   ├── E6-S1.md                            # Dispute Intake & Sub-Claim
│   │   ├── E6-S2.md                            # Parent Claim State Management
│   │   ├── E7-S1.md                            # Decision Override Authority
│   │   ├── E7-S2.md                            # Audit Trail Recording
│   │   ├── E7-S3.md                            # Admin Override Endpoint
│   │   └── dependency-graph.md                 # Story dependencies and execution groups
│   └── design/
│       ├── system-design.md                    # High-level architecture overview
│       ├── api-contracts.md                    # REST API specification
│       ├── api-contracts.schema.json           # OpenAPI 3.0 schema
│       ├── data-models.md                      # Entity specifications
│       ├── data-models.schema.json             # JSON Schema for entities
│       ├── folder-structure.md                 # This file
│       ├── component-map.md                    # Story → file mapping
│       └── deployment.md                       # Deployment architecture
│
├── scripts/
│   ├── init.sh                                 # Initialize database, run migrations
│   ├── seed_test_data.sh                       # Load test policies and fraud rules
│   ├── run_backend.sh                          # Start backend dev server
│   ├── run_frontend.sh                         # Start frontend dev server
│   ├── run_tests.sh                            # Run all tests (backend + frontend)
│   └── docker_build.sh                         # Build Docker images
│
├── docker-compose.yml                          # Development environment orchestration
├── Dockerfile.backend                          # Python backend Dockerfile
├── Dockerfile.frontend                         # React frontend Dockerfile
├── .dockerignore
├── .gitignore
├── CLAUDE.md                                   # Project instructions and conventions
├── .claude/
│   ├── CLAUDE.md                               # Claude substrate governance rules
│   ├── agents/
│   │   ├── claim-intake-agent.md               # Domain agent for claims intake
│   │   ├── fraud-screening-agent.md            # Domain agent for fraud screening
│   │   ├── assessment-agent.md                 # Domain agent for assessment
│   │   ├── settlement-agent.md                 # Domain agent for settlement
│   │   ├── audit-tracer-agent.md               # Technical agent for audit verification
│   │   ├── archtest-author-agent.md            # Technical agent for architecture tests
│   │   └── state-machine-validator-agent.md    # Technical agent for state machine
│   ├── commands/
│   │   ├── brd.md                              # Generate BRD from conversation
│   │   ├── spec.md                             # Generate specs from BRD
│   │   ├── design.md                           # Generate architecture design
│   │   ├── build.md                            # Full 8-phase pipeline
│   │   ├── implement.md                        # Code generation with agent teams
│   │   ├── test.md                             # Test plan + Playwright E2E
│   │   ├── evaluate.md                         # Run app, verify contract
│   │   ├── review.md                           # Code review + security review
│   │   ├── auto.md                             # Autonomous ratcheting loop
│   │   ├── verify-ac.md                        # Verify acceptance criteria
│   │   ├── assess-claim.md                     # Assessment domain command
│   │   ├── audit-trace.md                      # Audit trail verification
│   │   └── validate-state-machine.md           # State machine validation
│   ├── skills/
│   │   ├── code-gen/
│   │   │   └── SKILL.md                        # Code generation quality guidelines
│   │   ├── testing/
│   │   │   └── SKILL.md                        # Testing patterns and practices
│   │   ├── evaluation/
│   │   │   ├── SKILL.md                        # Evaluation methodology
│   │   │   └── references/
│   │   │       ├── contract-schema.json        # Sprint contract format
│   │   │       └── playwright-patterns.md      # Playwright test patterns
│   │   ├── fraud-rule-evaluator/
│   │   │   └── SKILL.md                        # Fraud rule evaluation
│   │   ├── payout-calculator/
│   │   │   └── SKILL.md                        # Payout calculation skill
│   │   ├── document-checklist-generator/
│   │   │   └── SKILL.md                        # Document checklist generation
│   │   ├── state-machine-validator/
│   │   │   └── SKILL.md                        # State machine validation
│   │   ├── audit-tracer/
│   │   │   └── SKILL.md                        # Audit trail verification
│   │   └── archtest-author/
│   │       └── SKILL.md                        # Architecture test authoring
│   ├── hooks/
│   │   ├── README.md                           # Hook enforcement rules
│   │   ├── pre-commit.sh                       # Pre-commit validation
│   │   ├── post-write.sh                       # Post-write code checking
│   │   └── evaluation-gate.sh                  # Evaluation gate checks
│   ├── state/
│   │   ├── learned-rules.md                    # Rules learned during development
│   │   ├── architecture.md                     # Validated architecture decisions
│   │   └── progress.txt                        # Development progress tracking
│   └── settings.json                           # Claude Code harness configuration
│
├── docs/
│   ├── README.md                               # Project overview
│   ├── ARCHITECTURE.md                         # Detailed architecture documentation
│   ├── API.md                                  # API documentation (generated from schema)
│   ├── TESTING.md                              # Testing strategy and coverage
│   ├── COMPLIANCE.md                           # Compliance requirements (SOX, GDPR)
│   └── TROUBLESHOOTING.md                      # Debugging and troubleshooting guide
│
├── features.json                               # Feature flag definitions
├── calibration-profile.json                    # Agent calibration settings
├── project-manifest.json                       # Project metadata
├── init.sh                                     # Initialize entire project
├── README.md                                   # Project README
├── LICENSE                                     # License (Apache 2.0)
└── .gitignore                                  # Git ignore rules
```

## Directory Annotations

| Directory | Purpose |
|-----------|---------|
| `backend/src/claimflow/` | Python backend application source code |
| `backend/src/claimflow/types/` | Type definitions and exceptions |
| `backend/src/claimflow/config_loaders/` | Configuration loading (fraud rules, checklists) |
| `backend/src/claimflow/repositories/` | Data access layer with WORM enforcement |
| `backend/src/claimflow/services/` | Business logic layer (policy validation, fraud engine, payout calculation) |
| `backend/src/claimflow/api/routes/` | REST API endpoints |
| `backend/src/claimflow/database/` | ORM models, migrations, seed data |
| `backend/tests/` | Unit and integration tests |
| `frontend/src/types/` | TypeScript type definitions |
| `frontend/src/api/` | API client methods |
| `frontend/src/pages/` | Page-level components (one per major feature) |
| `frontend/src/components/` | Reusable component library |
| `frontend/src/hooks/` | Custom React hooks |
| `frontend/src/context/` | Context providers for global state |
| `frontend/tests/e2e/` | Playwright end-to-end tests |
| `specs/stories/` | Individual epic stories (E1-S1 through E7-S3) |
| `specs/design/` | Architecture and design documentation |
| `.claude/agents/` | Domain and technical agents for code generation |
| `.claude/commands/` | Slash commands for pipeline stages (/brd, /spec, /design, /build, etc.) |
| `.claude/skills/` | Reusable skills for code quality, testing, evaluation |
| `.claude/hooks/` | Validation hooks (pre-commit, post-write, evaluation gate) |
| `docs/` | User and developer documentation |
| `scripts/` | Automation scripts (init, test, deploy) |

## Layered Architecture in Folder Structure

The folder structure enforces one-way dependencies:

1. **Type Layer** (`backend/src/claimflow/types/`) — No dependencies, only definitions
2. **Config Layer** (`backend/src/claimflow/config_loaders/`) — Reads config files, uses types
3. **Repository Layer** (`backend/src/claimflow/repositories/`) — Accesses database, enforces immutability, uses types
4. **Service Layer** (`backend/src/claimflow/services/`) — Business logic, calls repositories, uses types
5. **API Layer** (`backend/src/claimflow/api/`) — REST handlers, calls services, uses types
6. **UI Layer** (`frontend/src/pages/`, `frontend/src/components/`) — React components, calls API

No layer imports from layers above it. All dependencies flow downward.

## Key Files by Story

| Story | Key Files |
|-------|-----------|
| E1-S1 (Policy Validation) | `services/policy_service.py`, `routes/claims.py` |
| E1-S2 (Claim Intake) | `routes/claims.py`, `repositories/claim_repository.py` |
| E1-S3 (Claim Status) | `routes/claims.py`, `repositories/claim_repository.py` |
| E2-S1 (Checklist Config) | `config_loaders/document_checklist_loader.py` |
| E2-S2 (Document Upload) | `routes/documents.py`, `repositories/document_repository.py` |
| E2-S3 (Verification Queue) | `routes/documents.py`, `repositories/document_repository.py` |
| E2-S4 (Verification Decision) | `routes/verification.py`, `repositories/claim_repository.py` |
| E3-S1 (Fraud Engine) | `services/fraud_service.py` |
| E3-S2 (Fraud Config) | `config_loaders/fraud_rules_loader.py` |
| E3-S3 (Fraud Screening) | `routes/fraud.py`, `services/fraud_service.py` |
| E4-S1 (Coverage Assessment) | `services/assessment_service.py` |
| E4-S2 (Payout Calculation) | `services/payout_service.py` |
| E4-S3 (Assessment Decision) | `routes/assessment.py`, `services/payout_service.py` |
| E5-S1 (Payout Ledger) | `repositories/settlement_repository.py` |
| E5-S2 (Settlement Generation) | `services/settlement_service.py` |
| E5-S3 (Settlement Confirmation) | `routes/settlement.py`, `services/settlement_service.py` |
| E6-S1 (Dispute Intake) | `services/dispute_service.py`, `routes/disputes.py` |
| E6-S2 (Parent State Mgmt) | `repositories/claim_repository.py`, `routes/disputes.py` |
| E7-S1 (Override Authority) | `services/override_service.py` |
| E7-S2 (Audit Trail) | `repositories/audit_repository.py`, `services/audit_service.py` |
| E7-S3 (Override Endpoint) | `routes/overrides.py`, `services/override_service.py` |

## Testing Directory Structure

```
backend/tests/
├── unit/                                       # Unit tests (mocked dependencies)
│   ├── test_policy_service.py                  # Policy validation tests
│   ├── test_fraud_service.py                   # Fraud engine tests
│   └── test_payout_service.py                  # Payout calculation tests
├── integration/                                # Integration tests (real DB)
│   ├── test_claim_intake_flow.py               # E1-S2 full flow test
│   ├── test_fraud_assessment_flow.py           # E3 → E4 flow test
│   └── test_settlement_flow.py                 # E5 flow test
└── fixtures/                                   # Shared test data
    ├── policies.py                             # Mock policies
    ├── claims.py                               # Mock claims
    └── users.py                                # Mock users
```

## Summary

The folder structure mirrors the layered architecture and story-based organization:
- Backend organized by layer (types → config → repository → service → API)
- Frontend organized by page (one major feature per page) + reusable components
- Specs organized by epic stories + design documentation
- Claude substrate organized by agents, commands, and skills
- Tests mirror source structure for easy navigation
