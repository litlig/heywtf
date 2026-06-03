# heywtf

AI-powered terminal assistant for macOS. Ask how to do things in the terminal, or diagnose the last failed command.

<img width="1352" height="686" alt="heywtf" src="https://github.com/user-attachments/assets/48b3cded-faf4-44cd-885d-580a31cbf8e6" />

> **Platform:** macOS with zsh. Linux works for `hey` queries, but `hey wtf` shell integration is zsh-only.

## Quick start

```bash
uv tool install heywtf   # don't have uv? brew install uv
hey config               # pick a backend, set an API key, enable shell integration
hey how to check my ip   # ask away
```

`hey config` is a guided wizard — the only setup you need. Default backend is **Ollama** (local, private, no API key); **OpenAI** and **Gemini** are also supported.

## What you can do

**Ask a question** — get the command, instantly:

```bash
hey how to count words in a file
hey find all python files modified in the last 24 hours
```

**Diagnose a failure** — run `hey wtf` right after any command fails:

```
$ chmod 777 /etc/hosts
chmod: changing permissions of '/etc/hosts': Operation not permitted

$ hey wtf

  heywtf • powered by ollama (qwen2.5-coder:0.5b)
  💥 Command failed: chmod 777 /etc/hosts
  ──────────────────────────────────────────────────

  💡 Buddy: Permission denied — use sudo for system files:
  sudo chmod 777 /etc/hosts
```

The suggested command is **auto-copied to your clipboard** — just paste and run.

> `hey wtf` needs shell integration (enabled by `hey config`). Pause/resume capture with `buddy-off` / `buddy-on` before an interactive session.

**Switch backend for one query:**

```bash
hey o explain async/await in Python    # OpenAI
hey g difference between TCP and UDP    # Gemini
hey l how to tail a log file            # Ollama (local)
```

## Configuration

```bash
hey config                               # re-run the setup wizard
hey config show                          # view current config
hey config set backend openai            # change default backend
hey config set openai_api_key sk-...     # set an API key
hey config set ollama_model qwen3-coder:3b
hey config set copy_to_clipboard false   # disable clipboard auto-copy
```

API keys can also come from the `OPENAI_API_KEY` / `GOOGLE_API_KEY` environment variables.

**Using Ollama (the default):** install and pull a model first —

```bash
brew install ollama && ollama serve
ollama pull qwen2.5-coder:0.5b
```

## How `hey wtf` works

A zsh `preexec` hook captures each command and its stderr; a `precmd` hook saves the command and error when the exit code is non-zero. `hey wtf` reads that context and asks the AI to diagnose it. Interactive commands (vim, ssh, top, etc.) are skipped.

## Development

```bash
git clone https://github.com/litlig/heywtf.git && cd heywtf
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
source heywtf/shell/buddy.zsh    # load shell hooks in the current session
```

## License

MIT
