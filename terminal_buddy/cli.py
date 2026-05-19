"""CLI entry points for Terminal Buddy.

hey            — Ask a shell question in natural language.
yolo           — Run a command; if it fails, get AI-powered help.
buddy-diagnose — Auto-diagnose a failed command (called by zsh hook).
"""

import sys
import subprocess
import shlex
from pathlib import Path

from terminal_buddy.config import get_config
from terminal_buddy.ollama_client import chat_stream, OllamaError
from terminal_buddy.prompts import build_ask_messages, build_fix_messages
from terminal_buddy.display import (
    console,
    print_error,
    print_thinking,
    stream_response,
    print_command_header,
    print_separator,
    print_banner,
)


def hey_main():
    """Entry point for the `hey` command.

    Usage:
        hey how to count words in a file
        hey "find files larger than 1GB"
    """
    if len(sys.argv) < 2:
        console.print()
        console.print("  [bold bright_cyan]hey[/] — ask your terminal buddy a question")
        console.print()
        console.print("  [dim]Usage:[/]  hey <question>")
        console.print("  [dim]Example:[/] hey how to count words in a file")
        console.print()
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    config = get_config()

    console.print()
    print_banner()
    print_command_header(question, failed=False)
    print_separator()

    messages = build_ask_messages(question)

    try:
        with print_thinking():
            # Start the stream — the first chunk will dismiss the spinner
            chunks = chat_stream(messages, config["model"], config["ollama_url"])
            # We need to get the first chunk inside the Live context,
            # then stream the rest outside
            first_chunk = next(chunks, None)

        if first_chunk is None:
            print_error("No response from model.")
            sys.exit(1)

        # Re-wrap the first chunk back into the generator
        def _rejoin():
            yield first_chunk
            yield from chunks

        stream_response(_rejoin())

    except OllamaError as e:
        console.print()
        print_error(str(e))
        console.print()
        sys.exit(1)


def yolo_main():
    """Entry point for the `yolo` command.

    Usage:
        yolo chmod 777 /etc/hosts
        yolo ls /nonexistent
    """
    if len(sys.argv) < 2:
        console.print()
        console.print("  [bold bright_cyan]yolo[/] — run a command, get help if it fails")
        console.print()
        console.print("  [dim]Usage:[/]  yolo <command>")
        console.print("  [dim]Example:[/] yolo chmod 777 /etc/hosts")
        console.print()
        sys.exit(1)

    # The command to run is everything after 'yolo'
    cmd_args = sys.argv[1:]
    cmd_string = " ".join(cmd_args)

    # Run the command, capturing output
    try:
        result = subprocess.run(
            cmd_string,
            shell=True,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        print_error(f"Failed to execute: {e}")
        sys.exit(1)

    # Always show stdout/stderr from the original command
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)

    # If command succeeded, we're done
    if result.returncode == 0:
        sys.exit(0)

    # Command failed — time to help
    config = get_config()

    console.print()
    print_banner()
    print_command_header(cmd_string, failed=True)
    print_separator()

    messages = build_fix_messages(
        command=cmd_string,
        exit_code=result.returncode,
        stderr=result.stderr,
        stdout=result.stdout,
    )

    try:
        with print_thinking():
            chunks = chat_stream(messages, config["model"], config["ollama_url"])
            first_chunk = next(chunks, None)

        if first_chunk is None:
            print_error("No response from model.")
            sys.exit(result.returncode)

        def _rejoin():
            yield first_chunk
            yield from chunks

        stream_response(_rejoin())

    except OllamaError as e:
        console.print()
        print_error(str(e))
        console.print()

    sys.exit(result.returncode)


def diagnose_main():
    """Entry point for `buddy-diagnose` — called by the zsh hook.

    Usage (from zsh hook, not typically called manually):
        buddy-diagnose <command> <exit_code> [stderr_output]
    """
    if len(sys.argv) < 3:
        console.print()
        console.print("  [bold bright_cyan]buddy-diagnose[/] — auto-diagnose a failed command")
        console.print()
        console.print("  [dim]Usage:[/]  buddy-diagnose <command> <exit_code> [stderr]")
        console.print("  [dim]Note:[/]  This is called automatically by the zsh hook.")
        console.print()
        sys.exit(1)

    command = sys.argv[1]
    exit_code = int(sys.argv[2])
    stderr_output = sys.argv[3] if len(sys.argv) > 3 else ""

    config = get_config()

    console.print()
    print_banner()
    print_command_header(command, failed=True)
    print_separator()

    messages = build_fix_messages(
        command=command,
        exit_code=exit_code,
        stderr=stderr_output,
        stdout="",
    )

    try:
        with print_thinking():
            chunks = chat_stream(messages, config["model"], config["ollama_url"])
            first_chunk = next(chunks, None)

        if first_chunk is None:
            print_error("No response from model.")
            return

        def _rejoin():
            yield first_chunk
            yield from chunks

        stream_response(_rejoin())

    except OllamaError as e:
        console.print()
        print_error(str(e))
        console.print()


def main():
    """Main entry point for `terminal-buddy` command.

    Usage:
        terminal-buddy --init-shell   Print shell integration script for eval.
    """
    if "--init-shell" in sys.argv:
        # Locate buddy.zsh relative to this package
        shell_script = Path(__file__).resolve().parent.parent / "shell" / "buddy.zsh"
        if not shell_script.exists():
            # Fallback: check common install locations
            import importlib.resources as pkg_resources
            print(f"# Error: Could not find buddy.zsh at {shell_script}", file=sys.stderr)
            print("# Try sourcing it manually from the terminal-buddy install directory.", file=sys.stderr)
            sys.exit(1)
        print(shell_script.read_text())
    else:
        console.print()
        console.print("  [bold bright_cyan]terminal-buddy[/] — AI-powered terminal assistant")
        console.print()
        console.print("  [dim]Commands:[/]")
        console.print("    [bright_cyan]hey[/]   <question>     Ask how to do something")
        console.print("    [bright_cyan]yolo[/]  <command>      Run a command with error diagnosis")
        console.print()
        console.print("  [dim]Shell setup:[/]")
        console.print("    Add to ~/.zshrc:  [green]eval \"$(terminal-buddy --init-shell)\"[/]")
        console.print()
        console.print("  [dim]Requires:[/] Ollama running locally (https://ollama.com)")
        console.print()
