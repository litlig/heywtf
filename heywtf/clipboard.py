"""Clipboard helpers — copy the suggested command so the user can paste it."""

from __future__ import annotations

import shutil
import subprocess

# Clipboard tools by platform, tried in order (macOS first, then Linux).
_CLIPBOARD_COMMANDS = [
    ["pbcopy"],
    ["wl-copy"],
    ["xclip", "-selection", "clipboard"],
    ["xsel", "--clipboard", "--input"],
]


def copy_to_clipboard(text: str) -> bool:
    """Copy text to the system clipboard. Returns True on success."""
    for cmd in _CLIPBOARD_COMMANDS:
        if shutil.which(cmd[0]):
            try:
                subprocess.run(cmd, input=text.encode(), check=True)
                return True
            except Exception:
                continue
    return False


def extract_command(response: str, is_fix: bool) -> str | None:
    """Pull the primary command out of a model response.

    The prompts put the command(s) first for questions, and after a one-line
    diagnosis for fixes — so we take the first command line accordingly.
    """
    lines = [line.strip() for line in response.strip().splitlines() if line.strip()]
    # Drop any markdown code-fence lines the model may have added anyway.
    lines = [line for line in lines if not line.startswith("```")]
    if not lines:
        return None

    idx = 1 if (is_fix and len(lines) > 1) else 0
    command = lines[idx].strip().strip("`").strip()
    return command or None
