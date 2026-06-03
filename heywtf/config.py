"""Configuration management for heywtf."""

import json
from pathlib import Path

from heywtf.providers import Backend

DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODELS = {
    Backend.OLLAMA: "qwen2.5-coder:0.5b",
    Backend.OPENAI: "gpt-4o-mini",
    Backend.GEMINI: "gemini-2.0-flash",
}
CONFIG_DIR = Path.home() / ".config" / "heywtf"
CONFIG_FILE = CONFIG_DIR / "config.json"
STATE_FILE = CONFIG_DIR / "state.json"

VALID_CONFIG_KEYS = [
    "backend",
    "ollama_model",
    "ollama_url",
    "openai_model",
    "openai_api_key",
    "gemini_model",
    "gemini_api_key",
    "copy_to_clipboard",
]

SENSITIVE_KEYS = {"openai_api_key", "gemini_api_key"}


def _load_config_file() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def get_default_backend() -> Backend:
    """Return the configured default backend, falling back to OLLAMA."""
    cfg = _load_config_file()
    val = cfg.get("backend", "ollama")
    try:
        return Backend(val)
    except ValueError:
        return Backend.OLLAMA


def get_config(backend: Backend) -> dict:
    file_config = _load_config_file()
    model_key = f"{backend.value}_model"
    return {
        "backend": backend,
        "ollama_url": file_config.get("ollama_url", DEFAULT_OLLAMA_URL),
        "model": file_config.get(model_key) or DEFAULT_MODELS.get(backend),
        "openai_api_key": file_config.get("openai_api_key"),
        "gemini_api_key": file_config.get("gemini_api_key"),
        "copy_to_clipboard": _as_bool(file_config.get("copy_to_clipboard", True)),
    }


def _as_bool(value) -> bool:
    """Coerce a config value (bool or string) to a boolean. Defaults to True."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in ("false", "0", "no", "off")


def write_config(key: str, value: str) -> None:
    """Write a single key-value pair to the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load_config_file()
    existing[key] = value
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(existing, f, indent=2)
    except OSError as e:
        raise OSError(f"Could not write config: {e}")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(command: str, error: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_command": command, "last_error": error}, f)
    except OSError:
        pass
