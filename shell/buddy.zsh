# heywtf — zsh error capture
# Add this to your ~/.zshrc:
#   source /path/to/heywtf/shell/buddy.zsh
#
# How it works:
#   - preexec: saves the command string, redirects stderr through tee to capture it
#   - precmd: checks exit code, if non-zero, saves the command + error so you can
#     diagnose it later by running: hey wtf
#
# Set BUDDY_DISABLED=1 to temporarily disable error capture.
# Set BUDDY_VERBOSE=1 to see debug info.

# --- Configuration ---

# Interactive commands that should NOT have their stderr captured
# (they break when stderr is redirected through a pipe)
__buddy_blacklist=(
  vim nvim vi nano emacs
  less more man
  ssh scp sftp
  top htop btop
  tmux screen
  fzf
  python3 python ipython node
  docker-compose
  watch
  gdb lldb
)

# --- State ---
__buddy_cmd=""
__buddy_stderr_file=""
__buddy_saved_fd=""
__buddy_capturing=0

# --- Helpers ---

__buddy_is_blacklisted() {
  local cmd_base="${1%% *}"  # first word of the command
  cmd_base="${cmd_base##*/}" # strip path (e.g. /usr/bin/vim -> vim)
  local bl
  for bl in "${__buddy_blacklist[@]}"; do
    [[ "$cmd_base" == "$bl" ]] && return 0
  done
  return 1
}

# --- Hooks ---

__buddy_preexec() {
  [[ -n "$BUDDY_DISABLED" ]] && return

  __buddy_cmd="$1"
  __buddy_capturing=0
  __buddy_stderr_file=""  # clear so precmd can't read a prior command's stderr

  # Skip stderr capture for blacklisted (interactive) commands
  if __buddy_is_blacklisted "$1"; then
    [[ -n "$BUDDY_VERBOSE" ]] && echo "[buddy] skipping capture for: $1" >&2
    return
  fi

  # Create temp file and tee stderr to capture it while still displaying
  __buddy_stderr_file=$(mktemp /tmp/buddy_stderr.XXXXXX)
  exec {__buddy_saved_fd}>&2
  exec 2> >(tee -a "$__buddy_stderr_file" >&$__buddy_saved_fd)
  __buddy_capturing=1
}

__buddy_precmd() {
  local rc=$?

  # Restore stderr if we were capturing
  if (( __buddy_capturing )); then
    exec 2>&$__buddy_saved_fd
    exec {__buddy_saved_fd}>&-
    __buddy_capturing=0

    # Small delay to let tee finish writing
    sleep 0.05
  fi

  # If the command failed, save it + its error so `hey wtf` can diagnose later
  if [[ $rc -ne 0 && -n "$__buddy_cmd" && "$__buddy_cmd" != buddy-diagnose* ]]; then
    local stderr_content=""
    if [[ -f "$__buddy_stderr_file" ]]; then
      stderr_content=$(cat "$__buddy_stderr_file" 2>/dev/null)
    fi

    # Persist the failed command + error (the Python CLI entry point)
    buddy-diagnose "$__buddy_cmd" "$rc" "$stderr_content"
  fi

  # Cleanup
  [[ -f "$__buddy_stderr_file" ]] && rm -f "$__buddy_stderr_file"
  __buddy_cmd=""
  __buddy_stderr_file=""
  __buddy_saved_fd=""
}

# --- Register hooks ---
# Append to existing hooks instead of overwriting
autoload -Uz add-zsh-hook
add-zsh-hook preexec __buddy_preexec
add-zsh-hook precmd __buddy_precmd

# --- Manual commands ---

# `buddy-off` / `buddy-on` — toggle error capture
buddy-off() {
  export BUDDY_DISABLED=1
  echo "🔇 heywtf error capture disabled."
}

buddy-on() {
  unset BUDDY_DISABLED
  echo "🔊 heywtf error capture enabled."
}

echo "🤖 heywtf loaded. When a command fails, run 'hey wtf' to diagnose it."
echo "   Use 'buddy-off' to disable, 'buddy-on' to re-enable."
