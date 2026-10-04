# src/CLAUDE.md — Source Code Layering & Engineering Rules

This document establishes the architectural standards, layering conventions, and coding guardrails for the `src/` directory.

---

## 1. Clean Architecture Layering Rules

The application code strictly adheres to the 4-tier Clean Architecture model:

```
[ controllers ]  -->  [ services ]  -->  [ domain ]
       |                      |               ^
       v                      v               |
[ security / web ]     [ repositories ] -------+
```

### Dependency Invariants
1. **Domain Layer (`src/domain/`)** is the inner core. It must NOT import or depend on controllers, services, repositories, database drivers, or web frameworks.
2. **Services Layer (`src/services/`)** orchestrates domain use cases. It depends on `domain` and repository interfaces. It must NOT depend on HTTP request/response DTOs.
3. **Controllers Layer (`src/controllers/`)** handles HTTP REST translation, security context authentication, PII log filtering, and request validation. It depends on `services`.
4. **Repositories Layer (`src/repositories/`)** handles data persistence. It implements repository interfaces and interacts with storage tables.

---

## 2. Universal Code Constraints

1. **No Floating-Point Math (NFR-01):** Every monetary and financial field (`claimAmount`, `deductibles`, `coPay`, `payableAmount`, `payoutAmount`, `sumInsured`) must use fixed-point decimal objects (`BigDecimal`), never `float` or `double`.
2. **Append-Only Immutability (NFR-02):** Core records (claims, fraud reports, assessments, settlements, override audits) are immutable ledgers. In-place `UPDATE` or `DELETE` statements are forbidden.
3. **Zero-PII Logging (NFR-03):** No claimant names, addresses, identification numbers, medical diagnoses, or account credentials in log strings.
4. **Mandatory Correlation ID (NFR-06):** Every incoming request must capture or generate `X-Correlation-ID` and bind it to MDC/thread context.
5. **No Hand Coding:** All files in `src/` must be authored by Claude Code agents.
