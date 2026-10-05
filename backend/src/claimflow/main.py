from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from claimflow.api.routes import (
    assessment,
    audit,
    claims,
    disputes,
    documents,
    fraud,
    overrides,
    policies,
    settlement,
)
from claimflow.config.env import get_ai_config
from claimflow.types.exceptions import (
    ImmutabilityViolationError,
    InvalidClaimStateException,
    PayoutInvariantViolationException,
    PolicyNotActiveException,
    PolicyNotFoundError,
)

app = FastAPI(
    title="ClaimFlow Platform API",
    description="Enterprise Claims Management Platform for Horizon Insurance with AI Decisioning & Deterministic Fallback",
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
app.include_router(fraud.router)
app.include_router(policies.router)
app.include_router(assessment.router)
app.include_router(settlement.router)
app.include_router(overrides.router)
app.include_router(disputes.router)
app.include_router(audit.router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Health check endpoint complying with NFR-07 (< 1,000ms latency)."""
    return {"status": "ok", "service": "claimflow"}


@app.get("/api/v1/system/config", tags=["system"])
def get_system_config() -> dict[str, object]:
    """System AI configuration and fallback engine status."""
    cfg = get_ai_config()
    return {
        "aiConfigured": bool(cfg.get("api_key")),
        "aiProvider": cfg.get("provider"),
        "aiModel": cfg.get("model"),
        "fallbackEngine": "DETERMINISTIC_RULES (FR-01 to FR-06)",
    }


# Frontend integration: serve frontend static files and root dashboard
frontend_dir = Path(__file__).resolve().parent.parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")

    @app.get("/", include_in_schema=False)
    def serve_frontend() -> FileResponse:
        index_file = frontend_dir / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return JSONResponse({"message": "ClaimFlow API active. Frontend index.html not yet built."})

    @app.get("/app.js", include_in_schema=False)
    def serve_app_js() -> FileResponse:
        js_file = frontend_dir / "app.js"
        if js_file.exists():
            return FileResponse(str(js_file), media_type="application/javascript")
        return JSONResponse({"error": "not found"}, status_code=404)


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
