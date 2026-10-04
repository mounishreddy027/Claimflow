import json
import tempfile
from pathlib import Path

import pytest

from claimflow.config_loaders.fraud_rules_loader import (
    FraudRulesLoader,
)
from claimflow.types.enums import LOB
from claimflow.types.exceptions import ConfigurationError


class TestFraudRulesLoader:
    def test_load_motor_fraud_rules_contains_version_and_effective_date(self):
        loader = FraudRulesLoader()
        rules = loader.load_rules(LOB.MOTOR)
        assert rules.version_number is not None
        assert rules.effective_date is not None
        assert rules.lob == LOB.MOTOR

    def test_load_health_fraud_rules_has_threshold(self):
        loader = FraudRulesLoader()
        rules = loader.load_rules(LOB.HEALTH)
        assert rules.threshold > 0
        assert len(rules.rules) > 0

    def test_load_life_fraud_rules_has_threshold(self):
        loader = FraudRulesLoader()
        rules = loader.load_rules(LOB.LIFE)
        assert rules.threshold > 0
        assert len(rules.rules) > 0

    def test_configuration_error_when_fraud_rules_json_missing(self):
        loader = FraudRulesLoader()
        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_rules_from_file("/nonexistent/path/fraud_rules.json", LOB.MOTOR)
        assert "not found" in str(exc_info.value).lower()

    def test_configuration_error_when_fraud_rules_json_malformed(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{ invalid json")
            temp_path = f.name
        try:
            loader = FraudRulesLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_rules_from_file(temp_path, LOB.MOTOR)
            assert "malformed" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_configuration_error_when_lob_missing_threshold(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({
                "version": "1.0",
                "effective_date": "2026-01-01",
                "rules_by_lob": {
                    "Motor": {
                        "rules": []
                    }
                }
            }, f)
            temp_path = f.name
        try:
            loader = FraudRulesLoader()
            with pytest.raises(ConfigurationError) as exc_info:
                loader.load_rules_from_file(temp_path, LOB.MOTOR)
            assert "threshold" in str(exc_info.value).lower()
        finally:
            Path(temp_path).unlink()

    def test_configuration_immutability_after_loading(self):
        loader = FraudRulesLoader()
        rules = loader.load_rules(LOB.MOTOR)
        with pytest.raises((TypeError, AttributeError, ValueError)):
            rules.threshold = 100
