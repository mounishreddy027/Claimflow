from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from claimflow.api.routes import (
    assessment,
    audit,
    claims,
    disputes,
    documents,
    overrides,
    settlement,
)
from claimflow.types.exceptions import (
    ImmutabilityViolationError,
    InvalidClaimStateException,
    PayoutInvariantViolationException,
    PolicyNotActiveException,
    PolicyNotFoundError,
)

app = FastAPI(
    title="ClaimFlow Platform API",
    description="Enterprise Claims Management Platform for Horizon Insurance",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(claims.router)
app.include_router(documents.router)
app.include_router(assessment.router)
app.include_router(settlement.router)
app.include_router(overrides.router)
app.include_router(disputes.router)
app.include_router(audit.router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Health check endpoint complying with NFR-07 (< 1,000ms latency)."""
    return {"status": "ok", "service": "claimflow"}


@app.exception_handler(PolicyNotActiveException)
def policy_not_active_handler(request: Request, exc: PolicyNotActiveException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "PolicyNotActiveException",
            "code": "POLICY_NOT_ACTIVE_ON_INCIDENT_DATE",
            "message": str(exc),
            "policyNumber": exc.policy_number,
            "incidentDate": str(exc.incident_date),
            "policyStatus": exc.reason_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(PolicyNotFoundError)
def policy_not_found_handler(request: Request, exc: PolicyNotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "PolicyNotFound",
            "code": "POLICY_NOT_FOUND",
            "message": str(exc),
            "policyNumber": exc.policy_number,
        },
    )


@app.exception_handler(InvalidClaimStateException)
def invalid_state_handler(request: Request, exc: InvalidClaimStateException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "InvalidClaimStateException",
            "code": "ILLEGAL_STATE_TRANSITION",
            "message": str(exc),
            "claimId": exc.claim_id,
            "currentState": getattr(exc.current_state, "value", str(exc.current_state)),
            "attemptedTargetState": getattr(exc.attempted_target_state, "value", str(exc.attempted_target_state)),
            "permittedTargetStates": [getattr(s, "value", str(s)) for s in exc.allowed_target_states],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(PayoutInvariantViolationException)
def payout_invariant_handler(request: Request, exc: PayoutInvariantViolationException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "PayoutInvariantViolationException",
            "code": "PAYOUT_AMOUNT_MISMATCH",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(ImmutabilityViolationError)
def immutability_handler(request: Request, exc: ImmutabilityViolationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "ImmutabilityViolationError",
            "code": "MUTATION_FORBIDDEN",
            "message": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )
