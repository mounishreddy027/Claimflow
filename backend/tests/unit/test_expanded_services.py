from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from claimflow.domain.claim import Claim
from claimflow.services.audit_verifier import AuditVerifier
from claimflow.services.compliance_service import ComplianceService
from claimflow.services.disbursement_gateway import DisbursementGateway, PaymentRail, PaymentStatus
from claimflow.services.document_validation_service import DocumentValidationService
from claimflow.services.fraud_service import FraudScreeningResult
from claimflow.services.override_governance_service import OverrideGovernanceService
from claimflow.types.audit import AuditLogEntry
from claimflow.types.enums import ActorRole, ClaimState, ClaimType


@pytest.fixture
def motor_claim() -> Claim:
    return Claim(
        claim_id="CLM-TEST-900",
        policy_number="POL-MTR-1001",
        claim_type=ClaimType.MOTOR,
        claim_amount=Decimal("12000.00"),
        incident_date=date(2026, 6, 15),
        incident_description="Multi-car collision on freeway",
        current_state=ClaimState.APPROVED,
    )


# --- 1. ComplianceService Tests ---

def test_compliance_sar_generation_when_fraud_exceeds_threshold(motor_claim: Claim) -> None:
    compliance = ComplianceService()
    fraud_high = FraudScreeningResult(
        report_id="FRD-01",
        claim_id=motor_claim.claim_id,
        policy_version=1,
        fraud_score=75,
        policy_threshold=50,
        is_flagged=True,
    )
    sar = compliance.generate_sar(motor_claim, fraud_high)
    assert sar is not None
    assert sar.risk_level == "CRITICAL"
    assert "Statutory referral" in sar.narrative_summary
    assert sar.statutory_deadline > sar.filing_date


def test_compliance_sar_not_triggered_for_clean_claim(motor_claim: Claim) -> None:
    compliance = ComplianceService()
    fraud_clean = FraudScreeningResult(
        report_id="FRD-02",
        claim_id=motor_claim.claim_id,
        policy_version=1,
        fraud_score=15,
        policy_threshold=50,
        is_flagged=False,
    )
    sar = compliance.generate_sar(motor_claim, fraud_clean)
    assert sar is None


def test_compliance_loss_ratio_calculation(motor_claim: Claim) -> None:
    compliance = ComplianceService()
    report = compliance.calculate_loss_ratio(
        lob=ClaimType.MOTOR,
        claims=[motor_claim],
        earned_premium=Decimal("20000.00"),
        period_start=date(2026, 1, 1),
        period_end=date(2026, 12, 31),
    )
    assert report.loss_ratio_percent == Decimal("60.00")
    assert report.is_favorable is True


# --- 2. DisbursementGateway Tests ---

def test_aba_routing_validation() -> None:
    gateway = DisbursementGateway()
    # Chase Manhattan Bank ABA 021000021 -> 3*0 + 7*2 + 1*1 + 3*0 + 7*0 + 1*0 + 3*0 + 7*2 + 1*1 = 14 + 1 + 14 + 1 = 30 % 10 == 0
    assert gateway.validate_aba_routing("021000021") is True
    assert gateway.validate_aba_routing("123456789") is False
    assert gateway.validate_aba_routing("short") is False


def test_disbursement_execution() -> None:
    gateway = DisbursementGateway()
    txn = gateway.disburse(
        payout_id="PAY-100",
        claim_id="CLM-100",
        amount=Decimal("3500.00"),
        rail=PaymentRail.ACH_SAME_DAY,
        account_number="123456789012",
        routing_number="021000021",
    )
    assert txn.status == PaymentStatus.CLEARED
    assert txn.recipient_masked == "****-****-9012"
    assert txn.amount == Decimal("3500.00")


# --- 3. AuditVerifier Tests ---

def test_audit_verifier_empty_ledger() -> None:
    verifier = AuditVerifier()
    rep = verifier.verify_ledger([])
    assert rep.is_valid is True
    assert rep.total_blocks_verified == 0


def test_audit_verifier_valid_chain() -> None:
    import hashlib
    import json

    verifier = AuditVerifier()
    prev_hash = "0" * 64

    # Entry 1
    d1 = {"action": "create"}
    c1 = json.dumps(d1, sort_keys=True, separators=(",", ":"))
    h1 = hashlib.sha256(f"{prev_hash}:AUD-1:CLM-1:CLAIM_CREATED:{c1}".encode("utf-8")).hexdigest()
    entry1 = AuditLogEntry(
        audit_id="AUD-1",
        correlation_id="COR-1",
        timestamp=datetime.now(timezone.utc),
        actor_id="usr1",
        actor_role="ROLE_CLAIMANT",
        operation_type="CLAIM_CREATED",
        claim_id="CLM-1",
        previous_hash=prev_hash,
        entry_hash=h1,
        detail_json=d1,
    )

    # Entry 2
    d2 = {"action": "assess"}
    c2 = json.dumps(d2, sort_keys=True, separators=(",", ":"))
    h2 = hashlib.sha256(f"{h1}:AUD-2:CLM-1:ASSESSMENT_SUBMITTED:{c2}".encode("utf-8")).hexdigest()
    entry2 = AuditLogEntry(
        audit_id="AUD-2",
        correlation_id="COR-2",
        timestamp=datetime.now(timezone.utc),
        actor_id="usr2",
        actor_role="ROLE_ASSESSOR",
        operation_type="ASSESSMENT_SUBMITTED",
        claim_id="CLM-1",
        previous_hash=h1,
        entry_hash=h2,
        detail_json=d2,
    )

    rep = verifier.verify_ledger([entry1, entry2])
    assert rep.is_valid is True
    assert rep.total_blocks_verified == 2


def test_audit_verifier_detects_tampered_payload() -> None:
    verifier = AuditVerifier()
    prev_hash = "0" * 64
    fake_entry = AuditLogEntry(
        audit_id="AUD-TAMPER",
        correlation_id="COR-1",
        timestamp=datetime.now(timezone.utc),
        actor_id="usr1",
        actor_role="ROLE_CLAIMANT",
        operation_type="CLAIM_CREATED",
        claim_id="CLM-1",
        previous_hash=prev_hash,
        entry_hash="bad_hash_12345",
        detail_json={"foo": "bar"},
    )
    rep = verifier.verify_ledger([fake_entry])
    assert rep.is_valid is False
    assert rep.tampered_entry_id == "AUD-TAMPER"


# --- 4. DocumentValidationService Tests ---

def test_document_validation_rules(motor_claim: Claim) -> None:
    service = DocumentValidationService()
    rep = service.validate_document(
        document_id="DOC-01",
        document_type="POLICE_FIR",
        file_name="fir_police.pdf",
        claim=motor_claim,
        extracted_metadata={"document_date": date(2026, 6, 16), "invoice_total": "1200.00"},
    )
    assert rep.is_acceptable is True
    assert len(rep.findings) == 0

    bad_rep = service.validate_document(
        document_id="DOC-02",
        document_type="POLICE_FIR",
        file_name="fir_police.exe",
        claim=motor_claim,
    )
    assert bad_rep.is_acceptable is False
    assert any(f.code == "DOC_INVALID_EXTENSION" for f in bad_rep.findings)


# --- 5. OverrideGovernanceService Tests ---

def test_override_governance_rbac_and_sod(motor_claim: Claim) -> None:
    gov = OverrideGovernanceService()

    # Non-admin rejected
    check_assessor = gov.evaluate_override_eligibility(
        claim=motor_claim,
        actor_role=ActorRole.ASSESSOR,
        reason_code="ADM_OVR_FRAUD_CLEARED_01",
        comment="Legitimate customer loss verified by adjuster",
    )
    assert check_assessor.is_permitted is False
    assert "lacks administrative override privilege" in (check_assessor.rejection_reason or "")

    # Admin with high value ($12,000 >= $10,000 threshold) -> requires dual approval
    check_admin = gov.evaluate_override_eligibility(
        claim=motor_claim,
        actor_role="ROLE_ADMIN",
        reason_code="ADM_OVR_FRAUD_CLEARED_01",
        comment="Executive review confirms exceptional catastrophic weather event",
    )
    assert check_admin.is_permitted is True
    assert check_admin.requires_dual_approval is True
