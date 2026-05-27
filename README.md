# heywtf

AI-powered terminal assistant for macOS. Ask how to do things in the terminal, or diagnose the last failed command.

<img width="1352" height="686" alt="heywtf" src="https://github.com/user-attachments/assets/48b3cded-faf4-44cd-885d-580a31cbf8e6" />


> **Platform:** macOS with zsh. Linux works for `hey` queries but `hey wtf` shell integration is zsh-only.

**Backends:**
- **Ollama** — local, private, no API key (default)
- **OpenAI** — GPT-4o, GPT-4o-mini (API key required)
- **Gemini** — Google Gemini (API key required)

## Install

```bash
uv tool install heywtf
```

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it (`brew install uv` on macOS).

### Manual

```bash
git clone https://github.com/litlig/heywtf.git
cd heywtf
pip install -e .
```

## First-time setup

Run the interactive setup wizard:

```bash
hey config
```

It will ask you to choose a backend, set an API key if needed, and optionally add shell integration to your `~/.zshrc` so `hey wtf` works.

## Usage

### Ask a question

```bash
hey how to count words in a file
hey find all python files modified in the last 24 hours
hey compress a directory with tar
```

### Diagnose a failed command

After any failed command, run:

```bash
hey wtf
```

Example:

```
$ chmod 777 /etc/hosts
chmod: changing permissions of '/etc/hosts': Operation not permitted

$ hey wtf

  heywtf • powered by ollama (qwen2.5-coder:0.5b)
  ❌ Command failed: chmod 777 /etc/hosts
  ──────────────────────────────────────────────────

  Permission denied — use sudo for system files:
  sudo chmod 777 /etc/hosts
```

Requires shell integration (set up via `hey config`). To temporarily pause capture:

```bash
buddy-off   # pause (e.g. before an interactive session)
buddy-on    # resume
```

### One-off backend override

```bash
hey o explain async/await in Python    # use OpenAI for this query
hey g what is the difference between TCP and UDP  # use Gemini for this query
```

### Configure

```bash
hey config           # interactive setup wizard
hey config show      # view current config
hey config set backend openai          # set default backend
hey config set openai_api_key sk-...   # set API key
hey config set ollama_model qwen3-coder:3b
```

API keys can also be set via environment variables: `OPENAI_API_KEY`, `GOOGLE_API_KEY`.

## Ollama setup

Ollama is the default backend — local, private, no API key needed.

```bash
brew install ollama
ollama serve
ollama pull qwen2.5-coder:0.5b
```

## How `hey wtf` works

1. A `preexec` zsh hook captures each command and its stderr
2. A `precmd` hook checks the exit code — if non-zero, saves the command + error
3. `hey wtf` reads that saved context and asks the AI to diagnose it
4. Interactive commands (vim, ssh, top, etc.) are skipped to avoid breaking them


## Development

```bash
git clone https://github.com/litlig/heywtf.git
cd heywtf
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Test changes immediately:

```bash
hey how to list files
hey wtf
hey config
```

To test shell hooks in your current session:

```bash
source heywtf/shell/buddy.zsh
```

## License

MIT
