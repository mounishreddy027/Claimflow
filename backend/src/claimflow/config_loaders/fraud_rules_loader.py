import json
from dataclasses import dataclass
from pathlib import Path

from claimflow.types.enums import LOB
from claimflow.types.exceptions import ConfigurationError


@dataclass(frozen=True)
class FraudRule:
    name: str
    predicate: str
    weight: int
    description: str


@dataclass(frozen=True)
class FraudRuleSet:
    lob: LOB
    threshold: int
    rules: tuple
    version_number: str
    effective_date: str

    def version(self) -> str:
        return self.version_number


class FraudRulesLoader:
    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = str(
                Path(__file__).parent.parent / "database" / "seed_data" / "fraud_rules.json"
            )
        self.config_path = config_path
        self._cache: dict[LOB, FraudRuleSet] = {}

    def load_rules(self, lob: LOB) -> FraudRuleSet:
        if lob in self._cache:
            return self._cache[lob]
        rules = self.load_rules_from_file(self.config_path, lob)
        self._cache[lob] = rules
        return rules

    def load_rules_from_file(self, file_path: str, lob: LOB) -> FraudRuleSet:
        try:
            config_file = Path(file_path)
            if not config_file.exists():
                raise ConfigurationError(f"Configuration file not found: {file_path}")

            with open(config_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Malformed JSON in configuration file: {e}")
        except FileNotFoundError as e:
            raise ConfigurationError(f"Configuration file not found: {file_path}") from e

        try:
            version = data.get("version")
            effective_date = data.get("effective_date")
            rules_by_lob = data.get("rules_by_lob", {})

            lob_config = rules_by_lob.get(lob.value)
            if not lob_config:
                raise ConfigurationError(
                    f"No configuration found for LOB: {lob.value}"
                )

            threshold = lob_config.get("threshold")
            if threshold is None:
                raise ConfigurationError(
                    f"Threshold not defined for LOB: {lob.value}"
                )

            rule_list = lob_config.get("rules", [])
            rules = tuple(
                FraudRule(
                    name=rule["name"],
                    predicate=rule["predicate"],
                    weight=rule["weight"],
                    description=rule["description"],
                )
                for rule in rule_list
            )

            return FraudRuleSet(
                lob=lob,
                threshold=int(threshold),
                rules=rules,
                version_number=str(version),
                effective_date=str(effective_date),
            )
        except KeyError as e:
            raise ConfigurationError(
                f"Missing required configuration key: {e}"
            ) from e
        except (ValueError, TypeError) as e:
            raise ConfigurationError(
                f"Invalid configuration value: {e}"
            ) from e

    def get_threshold(self, lob: LOB) -> int:
        rules = self.load_rules(lob)
        return rules.threshold
