"""CLI entry points for heywtf.

hey            — Ask a shell question in natural language.
"""

import sys
from pathlib import Path

from source.config import get_config, load_state, save_state
from source.provider_factory import create_provider
from source.providers import Backend, ProviderError
from source.prompts import build_ask_messages, build_fix_messages
from source.display import (
    console,
    print_error,
    print_thinking,
    stream_response,
    print_command_header,
    print_separator,
    print_banner,
)


def _show_hey_help():
    """Display help for the hey command."""
    console.print()
    console.print("  [bold bright_cyan]hey[/] — ask your terminal buddy a question")
    console.print()
    console.print("  [dim]Usage:[/]")
    console.print("    [green]hey[/] <question>       Use default model")
    console.print("    [green]hey o[/] <question>     Use OpenAI (requires API key)")
    console.print("    [green]hey g[/] <question>     Use Gemini (requires API key)")
    console.print("    [green]hey web[/] <question>   Use ChatGPT web (browser)")
    console.print("    [green]hey wtf[/]               Re-diagnose previous failed command")
    console.print()
    console.print("  [dim]Examples:[/]")
    console.print("    hey how to count words in a file")
    console.print("    hey o show me async/await in Python")
    console.print("    hey g compress directory with tar")
    console.print("    hey web find nginx config")
    console.print("    hey wtf                 # (after a command failed)")
    console.print()


def _parse_hey_arguments() -> tuple[Backend, bool, str]:
    """Parse hey command arguments.

    Returns:
        (backend, is_wtf, query). backend is the prefix-selected backend, defaulting
        to Backend.OLLAMA when no prefix is given (there is no CLI prefix for ollama,
        so OLLAMA here always means "no explicit prefix").
    """
    if len(sys.argv) < 2:
        _show_hey_help()
        sys.exit(1)

    args = sys.argv[1:]

    backend = Backend.OLLAMA
    if args[0] in ("o", "openai"):
        backend = Backend.OPENAI
        args = args[1:]
    elif args[0] in ("g", "gemini"):
        backend = Backend.GEMINI
        args = args[1:]
    elif args[0] == "web":
        backend = Backend.CHATGPT_WEB
        args = args[1:]

    if not args:
        _show_hey_help()
        sys.exit(1)

    if args[0] == "wtf":
        return backend, True, ""
    if args[0] in ("help", "-h", "--help"):
        _show_hey_help()
        sys.exit(0)

    return backend, False, " ".join(args)


def hey_main():
    """Entry point for the `hey` command.

    Usage:
        hey how to count words in a file
        hey o show me async/await in Python
        hey g explain docker
        hey web search for nginx config
        hey wtf  (re-diagnose previous error)
    """
    backend_to_use, is_wtf, query = _parse_hey_arguments()
    config = get_config(backend_to_use)

    console.print()
    print_banner(backend_to_use.value, config["model"])

    if is_wtf:
        state = load_state()
        if not state or not state.get("last_command"):
            console.print()
            print_error("No previous failed command to diagnose.")
            console.print("  Try running a command first, then use: hey wtf")
            console.print()
            sys.exit(1)

        command = state["last_command"]
        error = state.get("last_error", "")

        print_command_header(command, failed=True)
        print_separator()

        messages = build_fix_messages(
            command=command,
            exit_code=1,
            stderr=error,
            stdout="",
        )
    else:
        print_command_header(query, failed=False)
        print_separator()
        messages = build_ask_messages(query)

    # Create and use provider
    try:
        provider = create_provider(backend_to_use, config)
    except ProviderError as e:
        console.print()
        print_error(str(e))
        console.print()
        sys.exit(1)

    try:
        with print_thinking():
            chunks = provider.chat_stream(messages)
            first_chunk = next(chunks, None)

        if first_chunk is None:
            print_error("No response from model.")
            sys.exit(1)

        # Re-wrap the first chunk back into the generator
        def _rejoin():
            yield first_chunk
            yield from chunks

        stream_response(_rejoin())

    except ProviderError as e:
        console.print()
        print_error(str(e))
        console.print()
        sys.exit(1)


def buddy_diagnose_main():
    """Entry point for the `buddy-diagnose` command (called by the shell hook).

    Usage: buddy-diagnose <command> <exit_code> <stderr>

    Saves the failed command and error to state for later use by `hey wtf`.
    """
    if len(sys.argv) < 4:
        sys.exit(1)

    save_state(command=sys.argv[1], error=sys.argv[3])


def main():
    """Main entry point for `heywtf` command.

    Usage:
        heywtf --init-shell   Print shell integration script for eval.
    """
    if "--init-shell" in sys.argv:
        # Locate buddy.zsh relative to this package
        shell_script = Path(__file__).resolve().parent.parent / "shell" / "buddy.zsh"
        if not shell_script.exists():
            print(f"# Error: Could not find buddy.zsh at {shell_script}", file=sys.stderr)
            print("# Try sourcing it manually from the heywtf install directory.", file=sys.stderr)
            sys.exit(1)
        print(shell_script.read_text())
    else:
        console.print()
        console.print("  [bold bright_cyan]heywtf[/] — AI-powered terminal assistant")
        console.print()
        console.print("  [dim]Commands:[/]")
        console.print("    [bright_cyan]hey[/]   <question>     Ask how to do something")
        console.print()
        console.print("  [dim]Shell setup:[/]")
        console.print("    Add to ~/.zshrc:  [green]eval \"$(heywtf --init-shell)\"[/]")
        console.print()
        console.print("  [dim]Requires:[/] Ollama running locally (https://ollama.com)")
        console.print()
