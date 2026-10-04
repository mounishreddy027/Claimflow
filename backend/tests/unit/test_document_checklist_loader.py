import json
import tempfile
from pathlib import Path

import pytest

from claimflow.config.checklists import DocumentChecklistLoader
from claimflow.types.enums import ClaimType, DocumentType


class TestDocumentChecklistLoader:
    """Test document checklist loading, caching, and validation."""

    @pytest.fixture
    def checklist_json(self) -> dict:
        """Return test checklist configuration."""
        return {
            "MOTOR": {
                "required": ["POLICE_FIR", "REPAIR_INVOICE"],
                "optional": ["REPAIR_ESTIMATE"],
            },
            "HEALTH": {
                "required": ["HOSPITAL_BILL", "DISCHARGE_SUMMARY"],
                "optional": [],
            },
            "LIFE": {
                "required": ["DEATH_CERTIFICATE"],
                "optional": ["AUTOPSY_REPORT"],
            },
        }

    @pytest.fixture
    def temp_config_file(self, checklist_json) -> Path:
        """Create temporary checklists.json file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            json.dump(checklist_json, f)
            return Path(f.name)

    def test_load_motor_checklist_contains_required_documents(
        self, temp_config_file: Path
    ) -> None:
        """AC1: Motor checklist includes POLICE_FIR and REPAIR_INVOICE."""
        loader = DocumentChecklistLoader(str(temp_config_file))
        checklist = loader.load_checklist(ClaimType.MOTOR)

        assert DocumentType.POLICE_FIR in checklist
        assert DocumentType.REPAIR_INVOICE in checklist

    def test_load_health_checklist_contains_required_documents(
        self, temp_config_file: Path
    ) -> None:
        """AC2: Health checklist includes HOSPITAL_BILL and DISCHARGE_SUMMARY."""
        loader = DocumentChecklistLoader(str(temp_config_file))
        checklist = loader.load_checklist(ClaimType.HEALTH)

        assert DocumentType.HOSPITAL_BILL in checklist
        assert DocumentType.DISCHARGE_SUMMARY in checklist

    def test_load_life_checklist_contains_required_documents(
        self, temp_config_file: Path
    ) -> None:
        """AC3: Life checklist includes DEATH_CERTIFICATE."""
        loader = DocumentChecklistLoader(str(temp_config_file))
        checklist = loader.load_checklist(ClaimType.LIFE)

        assert DocumentType.DEATH_CERTIFICATE in checklist

    def test_checklist_cached_returns_same_object(
        self, temp_config_file: Path
    ) -> None:
        """AC4: Checklists cached in memory - second load returns same object."""
        loader = DocumentChecklistLoader(str(temp_config_file))

        checklist1 = loader.load_checklist(ClaimType.MOTOR)
        checklist2 = loader.load_checklist(ClaimType.MOTOR)

        assert checklist1 is checklist2

    def test_malformed_json_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        """AC5: ConfigurationError raised if checklists.json malformed."""
        bad_json_file = tmp_path / "bad.json"
        bad_json_file.write_text("{invalid json")

        with pytest.raises(DocumentChecklistLoader.ConfigurationError):
            loader = DocumentChecklistLoader(str(bad_json_file))
            loader.load_checklist(ClaimType.MOTOR)

    def test_missing_lob_raises_configuration_error(
        self, tmp_path: Path
    ) -> None:
        """AC6: ConfigurationError raised if required LOB missing."""
        minimal_json = tmp_path / "minimal.json"
        minimal_json.write_text(json.dumps({"MOTOR": {"required": [], "optional": []}}))

        loader = DocumentChecklistLoader(str(minimal_json))
        with pytest.raises(DocumentChecklistLoader.ConfigurationError):
            loader.load_checklist(ClaimType.HEALTH)

    def test_missing_file_raises_configuration_error(self) -> None:
        """ConfigurationError raised if configuration file not found."""
        nonexistent_path = "/nonexistent/path/checklists.json"

        with pytest.raises(DocumentChecklistLoader.ConfigurationError):
            DocumentChecklistLoader(nonexistent_path)

    def test_get_missing_documents_identifies_gaps(
        self, temp_config_file: Path
    ) -> None:
        """AC7: Validation identifies missing required documents."""
        loader = DocumentChecklistLoader(str(temp_config_file))

        uploaded = [DocumentType.POLICE_FIR]
        missing = loader.get_missing_documents(ClaimType.MOTOR, uploaded)

        assert DocumentType.REPAIR_INVOICE in missing
        assert len(missing) == 1
