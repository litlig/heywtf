# heywtf

AI-powered terminal assistant for macOS. Ask how to do things in the terminal, or diagnose the last failed command.

<img width="1352" height="686" alt="heywtf" src="https://github.com/user-attachments/assets/48b3cded-faf4-44cd-885d-580a31cbf8e6" />

> **Platform:** macOS with zsh. Linux works for `hey` queries, but `hey wtf` shell integration is zsh-only.

**Backends:** Ollama (local, no API key, default) · OpenAI · Gemini (both need an API key).

## Install

```bash
uv tool install heywtf
```

[Install uv](https://docs.astral.sh/uv/getting-started/installation/) first if needed (`brew install uv`). Then run the setup wizard:

```bash
hey config
```

It walks you through picking a backend, setting an API key, and adding shell integration to `~/.zshrc` so `hey wtf` works.

## Usage

**Ask a question:**

```bash
hey how to count words in a file
hey find all python files modified in the last 24 hours
```

**Diagnose a failed command** — just run `hey wtf` after it fails:

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

This needs shell integration (set up via `hey config`). Pause/resume capture with `buddy-off` / `buddy-on` — e.g. before an interactive session.

**Override the backend for one query:**

```bash
hey o explain async/await in Python                  # OpenAI
hey g difference between TCP and UDP                  # Gemini
```

## Configure

```bash
hey config show                          # view current config
hey config set backend openai            # default backend
hey config set openai_api_key sk-...     # API key
hey config set ollama_model qwen3-coder:3b
```

API keys can also come from `OPENAI_API_KEY` / `GOOGLE_API_KEY`. For the default Ollama backend:

```bash
brew install ollama && ollama serve
ollama pull qwen2.5-coder:0.5b
```

## How `hey wtf` works

A zsh `preexec` hook captures each command and its stderr; a `precmd` hook saves the command and error if the exit code is non-zero. `hey wtf` then reads that context and asks the AI to diagnose it. Interactive commands (vim, ssh, top, etc.) are skipped.

## Development

```bash
git clone https://github.com/litlig/heywtf.git && cd heywtf
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
source heywtf/shell/buddy.zsh    # load shell hooks in the current session
```

## License

MIT
