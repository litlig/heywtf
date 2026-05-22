"""Configuration management for heywtf.

Priority: config file > defaults.
"""

import json
from pathlib import Path

from source.providers import Backend

DEFAULT_BACKEND = Backend.OLLAMA
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODELS = {
    Backend.OLLAMA: "qwen2.5-coder:0.5b",
    Backend.OPENAI: "gpt-4o-mini",
    Backend.GEMINI: "gemini-2.0-flash",
    Backend.CHATGPT_WEB: "gpt-4o-mini",
}
CONFIG_DIR = Path.home() / ".config" / "heywtf"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_FILE = CONFIG_DIR / "state.json"


def _load_config_file() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def get_config(backend: Backend) -> dict:
    file_config = _load_config_file()
    model_key = f"{backend.value}_model"
    return {
        "backend": backend,
        "ollama_url": file_config.get("ollama_url", DEFAULT_OLLAMA_URL),
        "model": file_config.get(model_key) or DEFAULT_MODELS.get(backend),
        "openai_api_key": file_config.get("openai_api_key"),
        "gemini_api_key": file_config.get("gemini_api_key"),
    }


def load_state() -> dict:
    """Load the last failed command and error.

    Returns:
        Dict with 'last_command' and 'last_error' keys, or empty dict if not found.
    """
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(command: str, error: str) -> None:
    """Persist the most recent failed command and its error output."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_command": command, "last_error": error}, f)
    except OSError:
        pass
