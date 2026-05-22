# heywtf 🤖

AI-powered terminal assistant with **multiple AI backends** and flexible usage modes:

**Backends:**
- 🔒 **Ollama** — Local, private, 100% offline (default)
- 🚀 **ChatGPT Web** — Powerful AI without API keys (browser automation)
- 🔓 **OpenAI** — GPT-4o, GPT-4o-mini, etc. (bring your API key)
- 🔓 **Gemini** — Google's models (bring your API key)

Choose what works best for you — switch anytime!

## Features

- **`hey`** — Ask how to do something (uses default model)
- **`hey o <query>`** — Use OpenAI (requires API key)
- **`hey g <query>`** — Use Gemini (requires API key)
- **`hey web <query>`** — Use ChatGPT Web (browser automation, no API key)
- **`hey wtf`** — Diagnose the last failed command
- **Error capture** — Automatically remembers failed commands so `hey wtf` can diagnose them (via zsh hook)
- **`buddy-off` / `buddy-on`** — Toggle error capture

## Install

### Homebrew (recommended)

```bash
brew install litlig/tap/heywtf
```

### pipx

```bash
pipx install heywtf
```

### pip

```bash
pip install heywtf
```

### Shell Setup

After installing, add this to your `~/.zshrc` to enable auto-error detection:

```bash
eval "$(heywtf --init-shell)"
```

Then reload your shell:

```bash
source ~/.zshrc
```

## Prerequisites

**Choose at least one backend:**

### Option 1: Ollama (Default - Recommended)
- [Ollama](https://ollama.com) running locally
- A model pulled (default: `qwen2.5-coder:0.5b`)

```bash
ollama serve     # in one terminal
ollama pull qwen2.5-coder:0.5b
```

### Option 2: ChatGPT Web
- Logged into [ChatGPT](https://chat.openai.com)
- No API key needed, uses browser automation
- Install the browser dependency:

```bash
pip install 'heywtf[chatgpt-web]'
playwright install chromium
```

### Option 3: OpenAI (with `hey o`)
- [OpenAI API key](https://platform.openai.com/api-keys)
- Add `"openai_api_key": "sk-..."` to `~/.config/heywtf/config.json`

### Option 4: Gemini (with `hey g`)
- [Google API key](https://aistudio.google.com/apikey)
- Add `"gemini_api_key": "AIza..."` to `~/.config/heywtf/config.json`

See [BACKENDS.md](BACKENDS.md) for detailed setup instructions and comparison.

## Usage

### Ask a question with default model

```bash
hey how to count words in a file
hey "find all python files modified in the last 24 hours"
hey "compress a directory with tar"
```

### Use OpenAI (requires API key)

```bash
hey o "explain async/await in Python"
hey o "write a dockerfile for a node app"
```

### Use Gemini (requires API key)

```bash
hey g "what's the best way to structure a REST API?"
hey g "debug this regex: ^\\d{3}-\\d{3}-\\d{4}$"
```

### Use ChatGPT Web (no API key needed)

```bash
hey web "search for best practices on docker networking"
```

> **Note:** Requires being logged into ChatGPT and the `heywtf[chatgpt-web]` extra installed.

### Re-diagnose previous error

After any command fails:

```bash
$ chmod 777 /etc/hosts
chmod: changing permissions of '/etc/hosts': Operation not permitted

$ hey wtf

  heywtf • powered by ollama (qwen2.5-coder:0.5b)
  ❌ Command failed: chmod 777 /etc/hosts
  ──────────────────────────────────────────────────

  Permission denied — use sudo for system files:
  sudo chmod 777 /etc/hosts
```

### Error capture

When a command fails, heywtf silently remembers it. Run `hey wtf` whenever you
want the diagnosis:

```bash
$ chmod 777 /etc/hosts
chmod: changing permissions of '/etc/hosts': Operation not permitted

$ hey wtf

  heywtf • powered by ollama (qwen2.5-coder:0.5b)
  ❌ Command failed: chmod 777 /etc/hosts
  ──────────────────────────────────────────────────

  Permission denied — you need elevated privileges:
  sudo chmod 777 /etc/hosts
```

### Toggle error capture

```bash
buddy-off   # disable error capture (e.g. before running vim)
buddy-on    # re-enable
```

## How Error Capture Works

1. **`preexec` hook** — Before each command, captures the command string and tees its stderr
2. **`precmd` hook** — After each command, checks the exit code. If non-zero, saves the command + stderr so `hey wtf` can diagnose it later
3. **Blacklist** — Interactive programs (vim, ssh, less, top, etc.) skip capture to avoid breaking them

## Configuration

### Models

Each backend has its own model. Set per-backend models in `~/.config/heywtf/config.json`:

```json
{
  "ollama_model": "qwen3-coder:3b",
  "openai_model": "gpt-4o",
  "gemini_model": "gemini-1.5-pro"
}
```

Each backend uses its own model — settings never leak across backends. If unset, each falls back to a sensible built-in default (Ollama → `qwen2.5-coder:0.5b`, OpenAI → `gpt-4o-mini`, Gemini → `gemini-2.0-flash`).

### API Keys

Save API keys in `~/.config/heywtf/config.json`:

```json
{
  "openai_api_key": "sk-...",
  "gemini_api_key": "..."
}
```

See [config.example.json](config.example.json) for a full template with all options.

**Priority:** config file > defaults

## Code Architecture

heywtf uses a **provider abstraction** for extensibility:

- **`providers.py`** — Abstract base `Provider` class
- **`ollama_client.py`** — `OllamaProvider` (local inference)
- **`chatgpt_client.py`** — `ChatGPTProvider` (browser automation)
- **`openai_provider.py`** — `OpenAIProvider` (API-based)
- **`gemini_provider.py`** — `GeminiProvider` (API-based)
- **`provider_factory.py`** — Factory to instantiate providers by name

Adding new providers is straightforward: inherit from `Provider` and implement `chat_stream()`.

## Development

```bash
git clone https://github.com/litlig/heywtf.git
cd heywtf
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

The `-e` (editable) install means changes to the source code take effect immediately — no reinstall needed:

```bash
hey how to list files          # test your changes instantly
hey o explain recursion        # test with OpenAI (if API key set)
hey wtf                        # test wtf command
```

To test the shell hooks in your current session:

```bash
source shell/buddy.zsh
```

## Contributing

Contributions are welcome! To add a new provider:

1. Create `<provider>_provider.py` inheriting from `Provider`
2. Implement `chat_stream(messages: list[dict])`
3. Update `provider_factory.py` to register it
4. Add config support in `config.py`
5. Update README with usage examples

## License

MIT

