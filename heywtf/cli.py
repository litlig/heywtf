"""CLI entry points for heywtf."""

import os
import sys
from pathlib import Path

from heywtf.config import (
    get_config,
    get_default_backend,
    load_state,
    save_state,
    write_config,
    CONFIG_FILE,
    DEFAULT_MODELS,
    VALID_CONFIG_KEYS,
    SENSITIVE_KEYS,
)
from heywtf.provider_factory import create_provider
from heywtf.providers import Backend, ProviderError
from heywtf.prompts import build_ask_messages, build_fix_messages
from heywtf.display import (
    console,
    print_error,
    print_thinking,
    stream_response,
    print_command_header,
    print_separator,
    print_banner,
    print_clipboard_note,
)
from heywtf.clipboard import copy_to_clipboard, extract_command

_INIT_LINE = 'eval "$(heywtf --init-shell)"'


def _get_version() -> str:
    from importlib.metadata import version, PackageNotFoundError

    try:
        return version("heywtf")
    except PackageNotFoundError:
        return "unknown"


def _show_version():
    console.print(f"  [bold bright_cyan]heywtf[/] [dim]v{_get_version()}[/]")


def _show_hey_help():
    console.print()
    console.print("  [bold bright_cyan]hey[/] — ask your terminal buddy a question")
    console.print()
    console.print("  [dim]Usage:[/]")
    console.print("    [green]hey[/] <question>       Ask using the configured backend")
    console.print("    [green]hey o[/] <question>     Ask using OpenAI (one-off override)")
    console.print("    [green]hey g[/] <question>     Ask using Gemini (one-off override)")
    console.print("    [green]hey l[/] <question>     Ask using Ollama (one-off override)")
    console.print("    [green]hey wtf[/]               Diagnose last failed command")
    console.print("    [green]hey config[/]            Interactive setup")
    console.print("    [green]hey config show[/]       Show current config")
    console.print("    [green]hey version[/]           Show the installed version")
    console.print()
    console.print("  [dim]Examples:[/]")
    console.print("    hey how to count words in a file")
    console.print("    hey o explain async/await in Python")
    console.print("    hey wtf")
    console.print()
    console.print("  [dim]First time?[/] Run [green]hey config[/] to choose a backend and set up.")
    console.print()
    console.file.flush()


def _parse_hey_arguments() -> tuple[Backend, bool, str]:
    """Parse hey arguments, returning (backend, is_wtf, query)."""
    if len(sys.argv) < 2:
        _show_hey_help()
        sys.exit(1)

    args = sys.argv[1:]

    backend = get_default_backend()
    if args[0] in ("o", "openai"):
        backend = Backend.OPENAI
        args = args[1:]
    elif args[0] in ("g", "gemini"):
        backend = Backend.GEMINI
        args = args[1:]
    elif args[0] in ("l", "ollama"):
        backend = Backend.OLLAMA
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


# ── hey config ────────────────────────────────────────────────────────────────

def _handle_config(args: list[str]):
    if not args:
        _run_config_wizard()
        return

    if args[0] == "show":
        _show_config()
        return

    if args[0] == "set":
        if len(args) < 3:
            console.print()
            print_error("Usage: hey config set <key> <value>")
            console.print(f"  Valid keys: {', '.join(VALID_CONFIG_KEYS)}")
            console.print()
            sys.exit(1)
        _set_config(args[1], args[2])
        return

    console.print()
    print_error(f"Unknown config subcommand: {args[0]!r}")
    console.print("  Usage: hey config  |  hey config show  |  hey config set <key> <value>")
    console.print()
    sys.exit(1)


def _run_config_wizard():
    from rich.prompt import Prompt, Confirm
    from heywtf.config import _load_config_file

    file_config = _load_config_file()
    current_backend = file_config.get("backend", "ollama")

    console.print()
    console.print("  [bold bright_cyan]heywtf setup[/]")
    console.print()
    console.print("  [dim]Choose a backend:[/]")
    console.print("    [bold]1[/]  ollama  — local, private, no API key needed")
    console.print("    [bold]2[/]  openai  — GPT-4o / GPT-4o-mini (API key required)")
    console.print("    [bold]3[/]  gemini  — Google Gemini (API key required)")
    console.print()

    default_choice = {"ollama": "1", "openai": "2", "gemini": "3"}.get(current_backend, "1")
    choice = Prompt.ask(
        f"  Backend [dim](current: {current_backend})[/]",
        choices=["1", "2", "3"],
        default=default_choice,
    )
    backend = {"1": "ollama", "2": "openai", "3": "gemini"}[choice]
    write_config("backend", backend)

    console.print()

    if backend == "openai":
        _wizard_openai(file_config)
    elif backend == "gemini":
        _wizard_gemini(file_config)
    else:
        _wizard_ollama(file_config)

    console.print()
    _wizard_shell_integration(file_config)

    console.print()
    console.print(f"  [green]✓[/] All set — using [bold]{backend}[/]. Run: [bold]hey <question>[/]")
    console.print()


def _wizard_openai(file_config: dict):
    from rich.prompt import Prompt

    current_key = file_config.get("openai_api_key", "")
    current_model = file_config.get("openai_model") or DEFAULT_MODELS[Backend.OPENAI]

    if current_key:
        masked = f"{current_key[:4]}...{current_key[-4:]}" if len(current_key) > 10 else "****"
        console.print(f"  [dim]OpenAI API key: {masked} (press Enter to keep)[/]")
        new_key = Prompt.ask("  New API key", default="", password=True)
        if new_key:
            write_config("openai_api_key", new_key)
    else:
        api_key = Prompt.ask("  OpenAI API key (sk-...)", password=True)
        if api_key:
            write_config("openai_api_key", api_key)

    model = Prompt.ask("  Model", default=current_model)
    if model != current_model:
        write_config("openai_model", model)


def _wizard_gemini(file_config: dict):
    from rich.prompt import Prompt

    current_key = file_config.get("gemini_api_key", "")
    current_model = file_config.get("gemini_model") or DEFAULT_MODELS[Backend.GEMINI]

    if current_key:
        masked = f"{current_key[:4]}...{current_key[-4:]}" if len(current_key) > 10 else "****"
        console.print(f"  [dim]Google API key: {masked} (press Enter to keep)[/]")
        new_key = Prompt.ask("  New API key", default="", password=True)
        if new_key:
            write_config("gemini_api_key", new_key)
    else:
        api_key = Prompt.ask("  Google API key (AIza...)", password=True)
        if api_key:
            write_config("gemini_api_key", api_key)

    model = Prompt.ask("  Model", default=current_model)
    if model != current_model:
        write_config("gemini_model", model)


def _wizard_ollama(file_config: dict):
    from rich.prompt import Prompt
    import requests as _requests

    current_model = file_config.get("ollama_model") or DEFAULT_MODELS[Backend.OLLAMA]
    ollama_url = file_config.get("ollama_url", "http://localhost:11434")

    try:
        _requests.get(ollama_url, timeout=2)
        console.print("  [green]✓[/] Ollama is running.")
    except Exception:
        console.print("  [yellow]![/] Ollama not detected at " + ollama_url)
        console.print()
        console.print("    Install:  [bold]https://ollama.com[/]  or  [bold]brew install ollama[/]")
        console.print("    Then run: [bold]ollama serve[/]")
        console.print("              [bold]ollama pull " + current_model + "[/]")

    console.print()
    model = Prompt.ask("  Model", default=current_model)
    if model != current_model:
        write_config("ollama_model", model)


def _wizard_shell_integration(file_config: dict):
    from rich.prompt import Confirm

    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        profile = Path.home() / ".zshrc"
    elif "bash" in shell:
        profile = Path.home() / ".bash_profile"
        if not profile.exists():
            profile = Path.home() / ".bashrc"
    else:
        profile = None

    # Already installed
    if profile and profile.exists() and _INIT_LINE in profile.read_text():
        console.print("  [green]✓[/] Shell integration ([bright_cyan]hey wtf[/]) already active.")
        return

    console.print("  [dim]Shell integration enables [/][bright_cyan]hey wtf[/][dim] — auto-diagnose failed commands.[/]")
    console.print()

    if profile:
        enable = Confirm.ask(f"  Add to ~/{profile.name}", default=True)
        if enable:
            with open(profile, "a") as f:
                f.write(f"\n# heywtf shell integration\n{_INIT_LINE}\n")
            console.print(f"  [green]✓[/] Added. Run: [bold]source ~/{profile.name}[/]")
        else:
            console.print("  [dim]Skipped. Add manually:[/]")
            console.print(f"    [green]{_INIT_LINE}[/]")
    else:
        console.print("  [dim]Add this to your shell profile to enable[/] [bright_cyan]hey wtf[/][dim]:[/]")
        console.print(f"    [green]{_INIT_LINE}[/]")


def _show_config():
    from heywtf.config import _load_config_file

    file_config = _load_config_file()
    backend_val = file_config.get("backend", "ollama")

    console.print()
    console.print(f"  [bold bright_cyan]heywtf config[/]  [dim]── {CONFIG_FILE}[/]")
    console.print()
    console.print(f"  [dim]{'backend':<20}[/] {backend_val}")
    console.print()

    for key in ["ollama_model", "ollama_url", "openai_model", "openai_api_key", "gemini_model", "gemini_api_key", "copy_to_clipboard"]:
        val = file_config.get(key)
        if val is None:
            display = "[dim](not set)[/]"
        elif key in SENSITIVE_KEYS:
            display = f"{val[:4]}...{val[-4:]}" if len(val) > 10 else "****"
        else:
            display = val
        console.print(f"  [dim]{key:<20}[/] {display}")

    console.print()
    console.print("  [dim]To change:[/]  [green]hey config[/]  or  [green]hey config set <key> <value>[/]")
    console.print()


def _set_config(key: str, value: str):
    if key not in VALID_CONFIG_KEYS:
        console.print()
        print_error(f"Unknown config key: {key!r}")
        console.print(f"  Valid keys: {', '.join(VALID_CONFIG_KEYS)}")
        console.print()
        sys.exit(1)

    if key == "backend":
        valid = [b.value for b in Backend]
        if value not in valid:
            console.print()
            print_error(f"Invalid backend: {value!r}")
            console.print(f"  Valid values: {', '.join(valid)}")
            console.print()
            sys.exit(1)

    try:
        write_config(key, value)
    except OSError as e:
        console.print()
        print_error(str(e))
        console.print()
        sys.exit(1)

    masked = f"{value[:4]}...{value[-4:]}" if key in SENSITIVE_KEYS and len(value) > 10 else (
        "****" if key in SENSITIVE_KEYS else value
    )
    console.print()
    console.print(f"  [green]✓[/] [bold]{key}[/] = [bold]{masked}[/]")
    console.print()


# ── Entry points ──────────────────────────────────────────────────────────────

def hey_main():
    """Entry point for the `hey` command."""
    if len(sys.argv) < 2:
        _show_hey_help()
        sys.exit(1)

    if sys.argv[1] in ("version", "--version", "-v"):
        console.print()
        _show_version()
        console.print()
        return

    if sys.argv[1] == "config":
        console.print()
        _handle_config(sys.argv[2:])
        return

    backend_to_use, is_wtf, query = _parse_hey_arguments()
    config = get_config(backend_to_use)

    console.print()
    print_banner(backend_to_use.value, config["model"])

    if is_wtf:
        state = load_state()
        if not state or not state.get("last_command"):
            console.print()
            print_error("No previous failed command to diagnose.")
            console.print("  Try running a command first, then: hey wtf")
            console.print()
            sys.exit(1)

        command = state["last_command"]
        error = state.get("last_error", "")
        print_command_header(command, failed=True)
        print_separator()
        messages = build_fix_messages(command=command, exit_code=1, stderr=error, stdout="")
    else:
        print_command_header(query, failed=False)
        print_separator()
        messages = build_ask_messages(query)

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

        def _rejoin():
            yield first_chunk
            yield from chunks

        full_response = stream_response(_rejoin())

        if config.get("copy_to_clipboard"):
            command = extract_command(full_response, is_fix=is_wtf)
            if command and copy_to_clipboard(command):
                print_clipboard_note(command)

    except ProviderError as e:
        console.print()
        print_error(str(e))
        console.print()
        sys.exit(1)


def buddy_diagnose_main():
    """Entry point for the `buddy-diagnose` command (called by the shell hook)."""
    if len(sys.argv) < 4:
        sys.exit(1)
    save_state(command=sys.argv[1], error=sys.argv[3])


def main():
    """Entry point for the `heywtf` command."""
    if "--init-shell" in sys.argv:
        try:
            from importlib.resources import files
            shell_text = files("heywtf.shell").joinpath("buddy.zsh").read_text()
            print(shell_text)
        except Exception as e:
            print(f"# Error: Could not load shell integration: {e}", file=sys.stderr)
            sys.exit(1)
    elif any(a in ("version", "--version", "-v") for a in sys.argv[1:]):
        console.print()
        _show_version()
        console.print()
    else:
        console.print()
        console.print("  [bold bright_cyan]heywtf[/] — AI-powered terminal assistant")
        console.print()
        console.print("  [dim]Commands:[/]")
        console.print("    [bright_cyan]hey[/] <question>      Ask anything")
        console.print("    [bright_cyan]hey wtf[/]             Diagnose last failed command")
        console.print("    [bright_cyan]hey config[/]          Setup: choose backend, API keys, shell integration")
        console.print()
        console.print("  [dim]First time?[/]  Run [green]hey config[/] to get started.")
        console.print()
