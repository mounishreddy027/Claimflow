from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar
from uuid import uuid4

from claimflow.types.enums import ClaimType


@dataclass
class DocumentRecord:
    """Document metadata entity."""

    document_id: str
    claim_id: str
    document_type: str
    file_name: str
    status: str = "PENDING"
    rejection_reason: str | None = None
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    verified_at: datetime | None = None
    verified_by: str | None = None


class DocumentRepository:
    """Repository managing document storage, verification, and checklist completeness."""

    MANDATORY_CHECKLISTS: ClassVar[dict[str, list[str]]] = {
        ClaimType.MOTOR.value: ["POLICE_FIR", "REPAIR_INVOICE"],
        ClaimType.HEALTH.value: ["HOSPITAL_BILL", "DISCHARGE_SUMMARY"],
        ClaimType.LIFE.value: ["DEATH_CERTIFICATE"],
    }

    def __init__(self) -> None:
        self._documents: dict[str, DocumentRecord] = {}

    def add_document(
        self,
        claim_id: str,
        document_type: str,
        file_name: str,
        status: str = "PENDING",
    ) -> DocumentRecord:
        """Store a new supporting document receipt."""
        doc_id = f"DOC-{uuid4().hex[:8].upper()}"
        record = DocumentRecord(
            document_id=doc_id,
            claim_id=claim_id,
            document_type=document_type,
            file_name=file_name,
            status=status,
            uploaded_at=datetime.now(timezone.utc),
        )
        self._documents[doc_id] = record
        return record

    def get_documents_by_claim_id(self, claim_id: str) -> list[DocumentRecord]:
        """Fetch all documents associated with a claim."""
        return [d for d in self._documents.values() if d.claim_id == claim_id]

    def get_document_by_id(self, doc_id: str) -> DocumentRecord | None:
        """Fetch document by unique document ID."""
        return self._documents.get(doc_id)

    def verify_document(
        self,
        doc_id: str,
        verified_by: str,
        action: str = "VERIFY",
        rejection_reason: str | None = None,
    ) -> DocumentRecord:
        """Update verification status for an uploaded document."""
        doc = self._documents.get(doc_id)
        if doc is None:
            raise KeyError(f"Document not found: {doc_id}")

        if action.upper() == "REJECT":
            doc.status = "REJECTED"
            doc.rejection_reason = rejection_reason or "Rejected by verifier"
        else:
            doc.status = "VERIFIED"

        doc.verified_at = datetime.now(timezone.utc)
        doc.verified_by = verified_by
        return doc

    def is_checklist_complete(self, claim_id: str, claim_type: ClaimType) -> bool:
        """Check whether all mandatory checklist items are present and verified."""
        mandatory = self.MANDATORY_CHECKLISTS.get(claim_type.value, [])
        claim_docs = self.get_documents_by_claim_id(claim_id)
        verified_types = {d.document_type for d in claim_docs if d.status == "VERIFIED"}
        return all(m in verified_types for m in mandatory)
