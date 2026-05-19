# Terminal Buddy 🤖

AI-powered terminal assistant that runs **100% locally** using [Ollama](https://ollama.com). No cloud, no API keys, no data leaves your machine.

## Features

- **`hey`** — Ask how to do something in the terminal
- **Auto error detection** — Automatically diagnoses failed commands (via zsh hook)
- **`yolo`** — Manually run a command with error diagnosis
- **`wtf`** — Re-diagnose the last failed command
- **`buddy-off` / `buddy-on`** — Toggle auto-detection

## Install

### Homebrew (recommended)

```bash
brew install xiaofeihu/tap/terminal-buddy
```

### pipx

```bash
pipx install terminal-buddy
```

### pip

```bash
pip install terminal-buddy
```

### Shell Setup

After installing, add this to your `~/.zshrc` to enable auto-error detection:

```bash
eval "$(terminal-buddy --init-shell)"
```

Then reload your shell:

```bash
source ~/.zshrc
```

## Prerequisites

- [Ollama](https://ollama.com) running locally
- A model pulled (default: `qwen3-coder:1.5b`)

```bash
ollama pull qwen3-coder:1.5b
```

## Usage

### Ask a question

```bash
hey how to count words in a file
hey "find all python files modified in the last 24 hours"
hey "compress a directory with tar"
```

### Auto error detection (just use your terminal normally!)

```bash
$ chmod 777 /etc/hosts
chmod: changing permissions of '/etc/hosts': Operation not permitted

  🤖 terminal-buddy • powered by ollama
  ❌ Command failed: chmod 777 /etc/hosts
  ──────────────────────────────────────────────────

  💡 Buddy: Permission denied — you need elevated privileges.
  sudo chmod 777 /etc/hosts
```

### Manual run with `yolo`

```bash
yolo chmod 777 /etc/hosts
yolo ls /nonexistent_directory
```

### Re-diagnose with `wtf`

After any failed command, type `wtf` to get help.

### Toggle auto-detection

```bash
buddy-off   # disable auto-detection (e.g. before running vim)
buddy-on    # re-enable
```

## How Auto-Detection Works

1. **`preexec` hook** — Before each command, captures the command string and redirects stderr through `tee` to a temp file (so you still see errors in real-time)
2. **`precmd` hook** — After each command, checks the exit code. If non-zero, sends the command + captured stderr to Ollama for diagnosis
3. **Blacklist** — Interactive programs (vim, ssh, less, top, etc.) skip stderr capture to avoid breaking them

## Configuration

### Environment Variables

```bash
export BUDDY_MODEL="qwen3-coder:3b"         # change model
export BUDDY_OLLAMA_URL="http://localhost:11434"  # change Ollama URL
export BUDDY_DISABLED=1                      # disable auto-detection
export BUDDY_VERBOSE=1                       # debug output
```

### Config File

`~/.config/terminal-buddy/config.json`:

```json
{
  "model": "qwen3-coder:1.5b",
  "ollama_url": "http://localhost:11434"
}
```

Priority: env vars > config file > defaults.

## Development

```bash
git clone https://github.com/xiaofeihu/terminal-buddy.git
cd terminal-buddy
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

The `-e` (editable) install means changes to the source code take effect immediately — no reinstall needed. Just edit and test:

```bash
hey how to list files          # test your changes instantly
terminal-buddy --init-shell    # test shell integration output
```

To test the shell hooks in your current session:

```bash
source shell/buddy.zsh
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT
