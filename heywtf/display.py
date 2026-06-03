"""Rich terminal display utilities for heywtf."""

import sys
from rich.console import Console
from rich.markup import escape
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner
from typing import Generator

console = Console(stderr=True)

ACCENT = "bright_cyan"
ERROR_COLOR = "red"
DIM = "dim"


def print_error(message: str):
    console.print(f"  [bold {ERROR_COLOR}]✗[/] {escape(message)}")


def print_thinking():
    spinner = Spinner("dots", text=Text(" thinking...", style=DIM), style=ACCENT)
    return Live(spinner, console=console, transient=True)


def stream_response(chunks: Generator[str, None, None]):
    console.print()
    full_response = []
    first_chunk = True

    for chunk in chunks:
        full_response.append(chunk)
        if first_chunk:
            console.print(f"  [bold {ACCENT}]💡 Buddy:[/] ", end="")
            first_chunk = False
        sys.stderr.write(chunk)
        sys.stderr.flush()

    console.print()
    console.print()
    return "".join(full_response)


def print_clipboard_note(command: str):
    console.print(f"  [{DIM}]📋 copied to clipboard:[/] [{ACCENT}]{escape(command)}[/]")
    console.print()


def print_command_header(command: str, failed: bool = False):
    if failed:
        console.print(f"  [bold {ERROR_COLOR}]💥 Command failed:[/] [bold]{escape(command)}[/]")
    else:
        console.print(f"  [bold {ACCENT}]⚡ Question:[/] [bold]{escape(command)}[/]")


def print_separator():
    console.print(f"  [{DIM}]{'─' * 50}[/]")


def print_banner(backend: str, model: str | None = None):
    powered_by = f"powered by {backend}"
    if model:
        powered_by += f" ({model})"
    console.print(f"  [{DIM}]heywtf • {powered_by}[/]")
