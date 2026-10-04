import re
from collections.abc import Mapping

REDACTED_MARKER: str = "[REDACTED]"

SENSITIVE_KEYS: set[str] = {
    "ssn",
    "social_security_number",
    "tax_id",
    "bank_account",
    "account_number",
    "medical_record",
    "medical_info",
    "health_info",
    "credit_card",
    "card_number",
    "cvv",
    "password",
    "file_content_stub",
    "document_url",
    "national_id",
    "recipient_account",
    "pin",
}

SSN_REGEX: re.Pattern[str] = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CC_REGEX: re.Pattern[str] = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")


def _redact_text(text: str) -> str:
    """Mask known sensitive patterns within free text."""
    redacted = SSN_REGEX.sub(REDACTED_MARKER, text)
    return CC_REGEX.sub(REDACTED_MARKER, redacted)


def redact_pii(data: object) -> object:
    """
    Recursively redact sensitive PII and confidential fields.

    Keys in SENSITIVE_KEYS and regex-matched text patterns are masked.
    """
    if isinstance(data, Mapping):
        result: dict[str, object] = {}
        for key, value in data.items():
            str_key = str(key).lower()
            if str_key in SENSITIVE_KEYS:
                result[str(key)] = REDACTED_MARKER
            else:
                result[str(key)] = redact_pii(value)
        return result

    if isinstance(data, list):
        return [redact_pii(item) for item in data]

    if isinstance(data, str):
        return _redact_text(data)

    return data
