from claimflow.repositories.audit_repository import AuditRepository
from claimflow.repositories.claim_repository import ClaimRepository
from claimflow.repositories.document_repository import DocumentRepository
from claimflow.repositories.policy_repository import PolicyRepository
from claimflow.repositories.settlement_repository import SettlementRepository
from claimflow.repositories.subclaim_repository import SubClaimRepository
from claimflow.services.assessment_engine import AssessmentEngine
from claimflow.services.audit_service import AuditService
from claimflow.services.fraud_service import FraudService
from claimflow.services.policy_service import PolicyService
from claimflow.services.settlement_service import SettlementService

# Module-level singletons for in-memory persistence across routes
_audit_repo = AuditRepository()
_audit_service = AuditService(repository=_audit_repo)
_claim_repo = ClaimRepository(audit_service=_audit_service)
_policy_repo = PolicyRepository()
_policy_service = PolicyService()
_doc_repo = DocumentRepository()
_assessment_engine = AssessmentEngine()
_fraud_service = FraudService()
_settlement_repo = SettlementRepository()
_settlement_service = SettlementService(
    claim_repository=_claim_repo,
    settlement_repository=_settlement_repo,
    assessment_engine=_assessment_engine,
    fraud_service=_fraud_service,
    audit_service=_audit_service,
)
_subclaim_repo = SubClaimRepository()


def get_audit_repository() -> AuditRepository:
    return _audit_repo


def get_audit_service() -> AuditService:
    return _audit_service


def get_claim_repository() -> ClaimRepository:
    return _claim_repo


def get_policy_repository() -> PolicyRepository:
    return _policy_repo


def get_policy_service() -> PolicyService:
    return _policy_service


def get_document_repository() -> DocumentRepository:
    return _doc_repo


def get_assessment_engine() -> AssessmentEngine:
    return _assessment_engine


def get_fraud_service() -> FraudService:
    return _fraud_service


def get_settlement_repository() -> SettlementRepository:
    return _settlement_repo


def get_settlement_service() -> SettlementService:
    return _settlement_service


def get_subclaim_repository() -> SubClaimRepository:
    return _subclaim_repo
