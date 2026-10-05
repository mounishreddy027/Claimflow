from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any

from claimflow.domain.claim import Claim
from claimflow.types.enums import ClaimType, DocumentType
from claimflow.utils.financial import to_decimal


@dataclass(frozen=True)
class DocumentValidationFinding:
    """Individual verification finding on a supporting document."""

    code: str
    is_valid: bool
    message: str
    severity: str  # ERROR, WARNING, INFO


@dataclass(frozen=True)
class DocumentValidationReport:
    """Comprehensive validation outcome for a document."""

    document_id: str
    document_type: str
    is_acceptable: bool
    findings: list[DocumentValidationFinding] = field(default_factory=list)
    validated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentValidationService:
    """
    Intelligent validation engine verifying supporting document contents,
    temporal coherence with the incident date, and line-item integrity.
    """

    ALLOWED_FILE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}

    def validate_document(
        self,
        document_id: str,
        document_type: str,
        file_name: str,
        claim: Claim,
        extracted_metadata: dict[str, Any] | None = None,
    ) -> DocumentValidationReport:
        """Evaluate document against business rules and temporal constraints."""
        findings: list[DocumentValidationFinding] = []
        meta = extracted_metadata or {}

        # 1. Extension Check
        ext = ("." + file_name.rsplit(".", 1)[-1].lower()) if "." in file_name else ""
        if ext not in self.ALLOWED_FILE_EXTENSIONS:
            findings.append(
                DocumentValidationFinding(
                    code="DOC_INVALID_EXTENSION",
                    is_valid=False,
                    message=f"File extension '{ext}' not in allowed set: {self.ALLOWED_FILE_EXTENSIONS}",
                    severity="ERROR",
                )
            )

        # 2. Line of Business alignment check
        doc_type_enum = DocumentType(document_type) if document_type in DocumentType._value2member_map_ else None
        if doc_type_enum == DocumentType.POLICE_FIR and claim.claim_type != ClaimType.MOTOR:
            findings.append(
                DocumentValidationFinding(
                    code="DOC_LOB_MISMATCH",
                    is_valid=False,
                    message="Police FIR submitted for non-motor claim",
                    severity="WARNING",
                )
            )

        # 3. Temporal verification (document date vs incident date)
        doc_date_raw = meta.get("document_date")
        if isinstance(doc_date_raw, date):
            if doc_date_raw < claim.incident_date:
                findings.append(
                    DocumentValidationFinding(
                        code="DOC_PREDATES_INCIDENT",
                        is_valid=False,
                        message=f"Document date {doc_date_raw} precedes incident date {claim.incident_date}",
                        severity="ERROR",
                    )
                )

        # 4. Financial total verification for invoices
        invoice_total = meta.get("invoice_total")
        if invoice_total is not None:
            dec_total = to_decimal(Decimal(str(invoice_total)))
            if dec_total <= Decimal("0.00"):
                findings.append(
                    DocumentValidationFinding(
                        code="DOC_ZERO_INVOICE_TOTAL",
                        is_valid=False,
                        message="Invoice total must be strictly positive",
                        severity="ERROR",
                    )
                )

        is_acceptable = not any(f.severity == "ERROR" for f in findings)
        return DocumentValidationReport(
            document_id=document_id,
            document_type=document_type,
            is_acceptable=is_acceptable,
            findings=findings,
            validated_at=datetime.now(timezone.utc),
        )
