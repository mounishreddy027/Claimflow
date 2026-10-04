import pytest
from fastapi.testclient import TestClient

from claimflow.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.AC_01
def test_intake_motor_claim_happy_path(client: TestClient) -> None:
    payload = {
        "policyNumber": "POL-MTR-1001",
        "incidentDate": "2026-09-15",
        "claimType": "MOTOR",
        "claimAmount": 3500.00,
        "incidentDescription": "Front bumper collision at intersection",
        "supportingDocuments": [
            {
                "documentType": "POLICE_FIR",
                "fileName": "fir_copy_2026.pdf",
                "fileContentStub": "data:application/pdf;base64,stubbed_payload==",
            },
            {
                "documentType": "REPAIR_INVOICE",
                "fileName": "auto_body_estimate.pdf",
                "fileContentStub": "data:application/pdf;base64,stubbed_payload==",
            },
        ],
    }

    response = client.post("/api/v1/claims/intake", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["policyNumber"] == "POL-MTR-1001"
    assert data["claimType"] == "MOTOR"
    assert data["status"] == "FILED"
    assert float(data["claimAmount"]) == 3500.00
    assert len(data["documentReceipts"]) == 2
    assert data["documentReceipts"][0]["status"] == "PENDING"

    claim_id = data["claimId"]
    get_res = client.get(f"/api/v1/claims/{claim_id}")
    assert get_res.status_code == 200
    assert get_res.json()["claimId"] == claim_id


@pytest.mark.AC_02
def test_intake_expired_policy_rejected(client: TestClient) -> None:
    payload = {
        "policyNumber": "POL-MTR-9999",
        "incidentDate": "2026-02-10",
        "claimType": "MOTOR",
        "claimAmount": 2000.00,
        "incidentDescription": "Expired policy crash",
        "supportingDocuments": [],
    }

    response = client.post("/api/v1/claims/intake", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "POLICY_NOT_ACTIVE_ON_INCIDENT_DATE"
    assert data["policyNumber"] == "POL-MTR-9999"


@pytest.mark.AC_02
def test_intake_lapsed_policy_rejected(client: TestClient) -> None:
    payload = {
        "policyNumber": "POL-HLT-5555",
        "incidentDate": "2026-03-01",
        "claimType": "HEALTH",
        "claimAmount": 1500.00,
        "incidentDescription": "Lapsed policy claim",
        "supportingDocuments": [],
    }

    response = client.post("/api/v1/claims/intake", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "POLICY_NOT_ACTIVE_ON_INCIDENT_DATE"


@pytest.mark.AC_02
def test_intake_nonexistent_policy_not_found(client: TestClient) -> None:
    payload = {
        "policyNumber": "POL-NONEXISTENT",
        "incidentDate": "2026-03-01",
        "claimType": "MOTOR",
        "claimAmount": 1000.00,
        "incidentDescription": "Nonexistent policy claim",
        "supportingDocuments": [],
    }

    response = client.post("/api/v1/claims/intake", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "POLICY_NOT_FOUND"


@pytest.mark.AC_03
def test_document_verification_flow(client: TestClient) -> None:
    # 1. Intake Motor claim
    payload = {
        "policyNumber": "POL-MTR-1001",
        "incidentDate": "2026-09-15",
        "claimType": "MOTOR",
        "claimAmount": 4000.00,
        "incidentDescription": "Accident",
        "supportingDocuments": [
            {"documentType": "POLICE_FIR", "fileName": "fir.pdf"},
            {"documentType": "REPAIR_INVOICE", "fileName": "invoice.pdf"},
        ],
    }
    intake_res = client.post("/api/v1/claims/intake", json=payload)
    claim_id = intake_res.json()["claimId"]

    # 2. Check documents
    doc_res = client.get(f"/api/v1/claims/{claim_id}/documents")
    assert doc_res.status_code == 200
    docs = doc_res.json()["documents"]
    assert len(docs) == 2
    fir_doc_id = docs[0]["documentId"]
    inv_doc_id = docs[1]["documentId"]

    # 3. Verify documents
    v1 = client.post(
        f"/api/v1/claims/{claim_id}/documents/{fir_doc_id}/verify",
        json={"action": "VERIFY", "notes": "Legible FIR"},
        headers={"X-Actor-Role": "ROLE_ASSESSOR"},
    )
    assert v1.status_code == 200
    assert v1.json()["status"] == "VERIFIED"

    v2 = client.post(
        f"/api/v1/claims/{claim_id}/documents/{inv_doc_id}/verify",
        json={"action": "VERIFY", "notes": "Legible Invoice"},
        headers={"X-Actor-Role": "ROLE_ASSESSOR"},
    )
    assert v2.status_code == 200

    # 4. Check that checklist is complete and claim transitioned to UNDER_REVIEW
    updated_doc_res = client.get(f"/api/v1/claims/{claim_id}/documents")
    assert updated_doc_res.json()["checklistStatus"] == "COMPLETE"

    claim_res = client.get(f"/api/v1/claims/{claim_id}")
    assert claim_res.json()["status"] == "UNDER_REVIEW"


@pytest.mark.AC_05
@pytest.mark.AC_06
@pytest.mark.AC_07
@pytest.mark.AC_08
def test_assessment_settlement_and_reopen_flow(client: TestClient) -> None:
    # 1. Create claim and advance to UNDER_REVIEW
    intake = client.post(
        "/api/v1/claims/intake",
        json={
            "policyNumber": "POL-MTR-1001",
            "incidentDate": "2026-09-15",
            "claimType": "MOTOR",
            "claimAmount": 4000.00,
            "incidentDescription": "Collision",
            "supportingDocuments": [
                {"documentType": "POLICE_FIR", "fileName": "fir.pdf"},
                {"documentType": "REPAIR_INVOICE", "fileName": "invoice.pdf"},
            ],
        },
    )
    claim_id = intake.json()["claimId"]
    doc_res = client.get(f"/api/v1/claims/{claim_id}/documents")
    for doc in doc_res.json()["documents"]:
        client.post(
            f"/api/v1/claims/{claim_id}/documents/{doc['documentId']}/verify",
            json={"action": "VERIFY"},
            headers={"X-Actor-Role": "ROLE_ASSESSOR"},
        )

    # 2. Assess claim
    assess_res = client.post(
        f"/api/v1/claims/{claim_id}/assess",
        json={"additionalDeductible": 0.00, "assessorNotes": "Standard repair confirmed."},
        headers={"X-Actor-Role": "ROLE_ASSESSOR"},
    )
    assert assess_res.status_code == 200
    assess_data = assess_res.json()
    assert float(assess_data["payableAmount"]) == 3500.00  # 4000 - 500 deductible

    # Claim should be APPROVED
    assert client.get(f"/api/v1/claims/{claim_id}").json()["status"] == "APPROVED"

    # 3. Settle claim
    settle_res = client.post(
        f"/api/v1/claims/{claim_id}/settle",
        headers={"X-Actor-Role": "ROLE_ASSESSOR"},
    )
    assert settle_res.status_code == 200
    settle_data = settle_res.json()
    assert settle_data["status"] == "DISBURSED"
    assert float(settle_data["payoutAmount"]) == 3500.00

    # Claim should be SETTLED
    assert client.get(f"/api/v1/claims/{claim_id}").json()["status"] == "SETTLED"

    # 4. Reopen claim
    reopen_res = client.post(
        f"/api/v1/claims/{claim_id}/reopen",
        json={
            "disputeReason": "Hidden transmission damage discovered",
            "supplementalAmount": 850.00,
            "disputeCategory": "SUPPLEMENTAL_DAMAGE",
        },
        headers={"X-Actor-Role": "ROLE_CUSTOMER"},
    )
    assert reopen_res.status_code == 201
    reopen_data = reopen_res.json()
    assert reopen_data["parentClaimStatus"] == "REOPENED"
    assert reopen_data["subClaimStatus"] == "UNDER_REVIEW"
    assert float(reopen_data["disputedAmount"]) == 850.00

    # 5. Check audit trail
    audit_res = client.get(f"/api/v1/audit-trail/{claim_id}")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert len(audit_data) >= 5


@pytest.mark.AC_09
def test_admin_override_endpoint(client: TestClient) -> None:
    # Create claim, reject it or auto-approve, then admin overrides
    intake = client.post(
        "/api/v1/claims/intake",
        json={
            "policyNumber": "POL-MTR-1001",
            "incidentDate": "2026-09-15",
            "claimType": "MOTOR",
            "claimAmount": 1000.00,
            "incidentDescription": "Collision",
            "supportingDocuments": [
                {"documentType": "POLICE_FIR", "fileName": "fir.pdf"},
                {"documentType": "REPAIR_INVOICE", "fileName": "invoice.pdf"},
            ],
        },
    )
    claim_id = intake.json()["claimId"]
    for doc in client.get(f"/api/v1/claims/{claim_id}/documents").json()["documents"]:
        client.post(
            f"/api/v1/claims/{claim_id}/documents/{doc['documentId']}/verify",
            json={"action": "VERIFY"},
            headers={"X-Actor-Role": "ROLE_ASSESSOR"},
        )
    client.post(f"/api/v1/claims/{claim_id}/assess", headers={"X-Actor-Role": "ROLE_ASSESSOR"})

    # Non-admin attempt -> 403 Forbidden
    non_admin_res = client.post(
        f"/api/v1/admin/claims/{claim_id}/override",
        json={
            "newDecision": "REJECT",
            "reasonCode": "ADM_OVR_FRAUD_FLAG_02",
            "comment": "Collusion suspected",
        },
        headers={"X-Actor-Role": "ROLE_ASSESSOR"},
    )
    assert non_admin_res.status_code == 403

    # Admin attempt -> 200 OK
    admin_res = client.post(
        f"/api/v1/admin/claims/{claim_id}/override",
        json={
            "newDecision": "REJECT",
            "reasonCode": "ADM_OVR_FRAUD_FLAG_02",
            "comment": "Collusion suspected by security audit",
        },
        headers={"X-Actor-Role": "ROLE_ADMIN"},
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["newDecision"] == "REJECT"

    # Status should now be REJECTED
    assert client.get(f"/api/v1/claims/{claim_id}").json()["status"] == "REJECTED"
