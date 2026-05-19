"""Configuration management for Terminal Buddy.

Priority: env vars > config file > defaults.
"""

import os
import json
from pathlib import Path

# Defaults
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5-coder:0.5b"
CONFIG_DIR = Path.home() / ".config" / "terminal-buddy"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _load_config_file() -> dict:
    """Load config from ~/.config/terminal-buddy/config.json if it exists."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def get_config() -> dict:
    """Get merged configuration with priority: env vars > config file > defaults."""
    file_config = _load_config_file()

    return {
        "ollama_url": os.environ.get(
            "BUDDY_OLLAMA_URL",
            file_config.get("ollama_url", DEFAULT_OLLAMA_URL),
        ),
        "model": os.environ.get(
            "BUDDY_MODEL",
            file_config.get("model", DEFAULT_MODEL),
        ),
    }


def save_default_config():
    """Create a default config file if none exists."""
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        default = {
            "ollama_url": DEFAULT_OLLAMA_URL,
            "model": DEFAULT_MODEL,
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default, f, indent=2)
