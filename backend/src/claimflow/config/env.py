import os
from pathlib import Path
from typing import TypedDict


class AIConfig(TypedDict):
    provider: str | None
    api_key: str | None
    model: str | None


def load_env_file() -> None:
    """Load key-value pairs from .env into os.environ if not already defined."""
    # Strictly scoped to Cap3 project root and backend directory
    project_root = Path(__file__).resolve().parents[4]  # Cap3
    candidate_paths = [
        project_root / ".env",
        project_root / "backend" / ".env",
    ]

    for p in candidate_paths:
        if p.exists() and p.is_file():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = val
            except Exception:
                pass
            break


# Load .env upon import
load_env_file()


def get_ai_config() -> AIConfig:
    """Detect available AI LLM provider and API key."""
    # Ensure environment is fresh from file if any changes occurred
    load_env_file()

    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        return {
            "provider": "gemini",
            "api_key": gemini_key,
            "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        }

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return {
            "provider": "openai",
            "api_key": openai_key,
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        }

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        return {
            "provider": "anthropic",
            "api_key": anthropic_key,
            "model": os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
        }

    return {
        "provider": None,
        "api_key": None,
        "model": None,
    }
