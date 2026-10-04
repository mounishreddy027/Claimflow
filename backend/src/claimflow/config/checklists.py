import json
from pathlib import Path

from claimflow.types.enums import ClaimType, DocumentType


class DocumentChecklistLoader:
    """Loader for document checklists per line of business."""

    class ConfigurationError(Exception):
        """Raised when configuration is invalid or incomplete."""

    def __init__(self, config_path: str) -> None:
        """Initialize loader with path to checklists.json."""
        self._config_path = Path(config_path)
        self._cache: dict[ClaimType, list[DocumentType]] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load and validate configuration file."""
        try:
            with open(self._config_path) as f:
                self._config = json.load(f)
        except json.JSONDecodeError as e:
            raise self.ConfigurationError(f"Invalid JSON in {self._config_path}") from e
        except FileNotFoundError as e:
            raise self.ConfigurationError(
                f"Configuration file not found: {self._config_path}"
            ) from e

    def load_checklist(self, claim_type: ClaimType) -> list[DocumentType]:
        """Load checklist for claim type, with caching."""
        if claim_type in self._cache:
            return self._cache[claim_type]

        claim_type_str = claim_type.value
        if claim_type_str not in self._config:
            raise self.ConfigurationError(
                f"Checklist not found for claim type: {claim_type_str}"
            )

        config_entry = self._config[claim_type_str]
        required = config_entry.get("required", [])

        checklist = [DocumentType(doc_type) for doc_type in required]
        self._cache[claim_type] = checklist

        return checklist

    def get_missing_documents(
        self, claim_type: ClaimType, uploaded_types: list[DocumentType]
    ) -> list[DocumentType]:
        """Identify missing required documents for a claim type."""
        required = self.load_checklist(claim_type)
        uploaded_set = set(uploaded_types)
        return [doc for doc in required if doc not in uploaded_set]
