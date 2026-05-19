"""Rich terminal display utilities for Terminal Buddy."""

import sys
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.live import Live
from rich.spinner import Spinner
from typing import Generator

console = Console(stderr=True)

# Theme colors
ACCENT = "bright_cyan"
ERROR_COLOR = "red"
SUGGESTION_COLOR = "bright_green"
DIM = "dim"


def print_error(message: str):
    """Print an error message."""
    console.print(f"  [bold {ERROR_COLOR}]✗[/] {message}")


def print_thinking():
    """Show a thinking spinner. Returns a Live context manager."""
    spinner = Spinner("dots", text=Text(" thinking...", style=DIM), style=ACCENT)
    return Live(spinner, console=console, transient=True)


def stream_response(chunks: Generator[str, None, None]):
    """Stream LLM response chunks to the terminal with formatting."""
    console.print()

    # Collect the full response while streaming
    full_response = []
    first_chunk = True

    for chunk in chunks:
        full_response.append(chunk)
        if first_chunk:
            console.print(f"  [bold {ACCENT}]💡 Buddy:[/] ", end="")
            first_chunk = False
        # Print each chunk as it arrives
        sys.stderr.write(chunk)
        sys.stderr.flush()

    # Final newline
    console.print()
    console.print()

    return "".join(full_response)


def print_command_header(command: str, failed: bool = False):
    """Print the command being analyzed."""
    if failed:
        console.print(f"  [bold {ERROR_COLOR}]❌ Command failed:[/] [bold]{command}[/]")
    else:
        console.print(f"  [bold {ACCENT}]⚡ Question:[/] [bold]{command}[/]")


def print_separator():
    """Print a thin separator line."""
    console.print(f"  [{DIM}]{'─' * 50}[/]")


def print_banner():
    """Print a small banner/branding."""
    console.print(f"  [{DIM}]terminal-buddy • powered by ollama[/]")
