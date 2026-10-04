# src/controllers/CLAUDE.md — Controller & Web API Guidelines

This document governs the HTTP and REST controller layer (`src/controllers/`).

---

## 1. Controller Responsibilities

1. **Protocol Translation:** Convert incoming HTTP JSON payloads into validated command objects and delegate to services.
2. **Security & Role Boundaries (NFR-04):**
   - Assessor endpoints (`/api/v1/assessor/**`) require `ROLE_ASSESSOR` or `ROLE_ADMIN`.
   - Admin override endpoints (`/api/v1/admin/**`) strictly mandate `ROLE_ADMIN`. Calls without `ROLE_ADMIN` must return HTTP `403 Forbidden`.
   - Customer endpoints (`/api/v1/claims/intake`, `/api/v1/claims/{id}/status`, `/api/v1/claims/{id}/reopen`) allow authenticated policyholders or anonymous intake.
3. **Correlation ID Propagation (NFR-06):**
   - Intercept `X-Correlation-ID` header; if absent, generate a UUID.
   - Inject into MDC context for structured JSON logging.
   - Echo `X-Correlation-ID` in all HTTP response headers.
4. **PII Sanitization in Web Logs (NFR-03):**
   - Intercept and redact request/response bodies prior to logging.
   - Never log claimant SSN, medical diagnoses, police FIR full text, or banking credentials.
5. **Health Endpoint (NFR-07):**
   - Expose `GET /health` responding with HTTP 200 in ≤ 1,000ms from startup.

---

## 2. Standard Exception Mappings

| Domain Exception | HTTP Status Code | Response Code String |
|---|---|---|
| `PolicyNotActiveException` (AC-02) | `422 Unprocessable Entity` | `POLICY_NOT_ACTIVE_ON_INCIDENT_DATE` |
| `InvalidClaimStateException` (AC-10) | `409 Conflict` | `ILLEGAL_STATE_TRANSITION` |
| `IncompleteDocumentChecklistException` (AC-03) | `400 Bad Request` | `INCOMPLETE_DOCUMENT_CHECKLIST` |
| `PayoutInvariantViolationException` (AC-07) | `500 Internal Server Error` | `PAYOUT_INVARIANT_VIOLATION` |
| `AccessDeniedException` (NFR-04) | `403 Forbidden` | `FORBIDDEN_INSUFFICIENT_ROLE` |
| `EntityNotFoundException` | `404 Not Found` | `RESOURCE_NOT_FOUND` |
