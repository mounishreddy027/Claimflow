# ClaimFlow Test Coverage & Quality Gate Report

> **Generated:** 2026-10-05 08:12:39 UTC | **Quality Gate 3:** `PASS`

## 1. Executive Summary & Quality Gates

| Metric | Target | Actual | Evaluation Status |
|---|:---:|:---:|:---:|
| **Overall Coverage** | $\ge 85\%$ | **92.9%** | **PASS** |
| **Domain Layer (`domain/`)** | $\ge 85\%$ | **100.0%** | **PASS** |
| **Total Statements** | - | **1568** | - |
| **Covered Statements** | - | **1457** | - |
| **Missing Lines** | - | **111** | - |

---

## 2. Coverage by Subsystem & Module

| Module / Component | Stmts | Miss | Cover % | Visual Progress |
|---|:---:|:---:|:---:|:---:|
| `claimflow/api/dependencies.py` | 44 | 2 | **95.5%** | `[###########.]` |
| `claimflow/api/routes/assessment.py` | 29 | 2 | **93.1%** | `[###########.]` |
| `claimflow/api/routes/audit.py` | 10 | 0 | **100.0%** | `[############]` |
| `claimflow/api/routes/claims.py` | 50 | 1 | **98.0%** | `[############]` |
| `claimflow/api/routes/disputes.py` | 25 | 4 | **84.0%** | `[##########..]` |
| `claimflow/api/routes/documents.py` | 34 | 4 | **88.2%** | `[###########.]` |
| `claimflow/api/routes/fraud.py` | 22 | 3 | **86.4%** | `[##########..]` |
| `claimflow/api/routes/overrides.py` | 31 | 7 | **77.4%** | `[#########...]` |
| `claimflow/api/routes/policies.py` | 14 | 0 | **100.0%** | `[############]` |
| `claimflow/api/routes/settlement.py` | 29 | 5 | **82.8%** | `[##########..]` |
| `claimflow/api/schemas.py` | 164 | 0 | **100.0%** | `[############]` |
| `claimflow/config/checklists.py` | 32 | 0 | **100.0%** | `[############]` |
| `claimflow/config/env.py` | 39 | 9 | **76.9%** | `[#########...]` |
| `claimflow/config_loaders/fraud_rules_loader.py` | 63 | 8 | **87.3%** | `[##########..]` |
| `claimflow/database/models.py` | 18 | 1 | **94.4%** | `[###########.]` |
| `claimflow/domain/claim.py` | 30 | 0 | **100.0%** | `[############]` |
| `claimflow/domain/state_machine.py` | 27 | 0 | **100.0%** | `[############]` |
| `claimflow/main.py` | 57 | 13 | **77.2%** | `[#########...]` |
| `claimflow/repositories/audit_repository.py` | 63 | 7 | **88.9%** | `[###########.]` |
| `claimflow/repositories/claim_repository.py` | 43 | 1 | **97.7%** | `[############]` |
| `claimflow/repositories/document_repository.py` | 45 | 4 | **91.1%** | `[###########.]` |
| `claimflow/repositories/policy_repository.py` | 13 | 2 | **84.6%** | `[##########..]` |
| `claimflow/repositories/settlement_repository.py` | 33 | 5 | **84.8%** | `[##########..]` |
| `claimflow/repositories/subclaim_repository.py` | 22 | 2 | **90.9%** | `[###########.]` |
| `claimflow/services/assessment_engine.py` | 28 | 0 | **100.0%** | `[############]` |
| `claimflow/services/audit_service.py` | 29 | 0 | **100.0%** | `[############]` |
| `claimflow/services/audit_verifier.py` | 34 | 1 | **97.1%** | `[############]` |
| `claimflow/services/compliance_service.py` | 54 | 1 | **98.1%** | `[############]` |
| `claimflow/services/coverage_assessment_service.py` | 25 | 1 | **96.0%** | `[############]` |
| `claimflow/services/disbursement_gateway.py` | 53 | 3 | **94.3%** | `[###########.]` |
| `claimflow/services/document_validation_service.py` | 42 | 3 | **92.9%** | `[###########.]` |
| `claimflow/services/fraud_service.py` | 119 | 16 | **86.6%** | `[##########..]` |
| `claimflow/services/override_governance_service.py` | 27 | 2 | **92.6%** | `[###########.]` |
| `claimflow/services/policy_service.py` | 15 | 0 | **100.0%** | `[############]` |
| `claimflow/services/settlement_service.py` | 46 | 2 | **95.7%** | `[###########.]` |
| `claimflow/types/audit.py` | 26 | 0 | **100.0%** | `[############]` |
| `claimflow/types/enums.py` | 60 | 0 | **100.0%** | `[############]` |
| `claimflow/types/exceptions.py` | 34 | 0 | **100.0%** | `[############]` |
| `claimflow/utils/financial.py` | 16 | 0 | **100.0%** | `[############]` |
| `claimflow/utils/pii_redaction.py` | 23 | 2 | **91.3%** | `[###########.]` |

---

## 3. Coverage Report Artifacts
- **Interactive HTML Report:** [`htmlcov/index.html`](file:///./htmlcov/index.html)
- **Machine-readable XML:** [`coverage.xml`](file:///./backend/coverage.xml)
- **Machine-readable JSON:** [`backend/coverage.json`](file:///./backend/coverage.json)
