# heywtf — zsh error capture
# Enable with:
#   eval "$(heywtf --init-shell)"
#
# How it works:
#   - preexec: saves the command string, redirects stderr through tee to capture it
#   - precmd: checks exit code; if non-zero, saves command + error so you can
#     diagnose it later by running: hey wtf
#
# Set BUDDY_DISABLED=1 to temporarily disable error capture.
# Set BUDDY_VERBOSE=1 to see debug info.

# --- Configuration ---

# Interactive commands that should NOT have their stderr captured
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
  local cmd_base="${1%% *}"
  cmd_base="${cmd_base##*/}"
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
  __buddy_stderr_file=""

  if __buddy_is_blacklisted "$1"; then
    [[ -n "$BUDDY_VERBOSE" ]] && echo "[buddy] skipping capture for: $1" >&2
    return
  fi

  __buddy_stderr_file=$(mktemp /tmp/buddy_stderr.XXXXXX)
  exec {__buddy_saved_fd}>&2
  exec 2> >(tee -a "$__buddy_stderr_file" >&$__buddy_saved_fd)
  __buddy_capturing=1
}

__buddy_precmd() {
  local rc=$?

  if (( __buddy_capturing )); then
    exec 2>&$__buddy_saved_fd
    exec {__buddy_saved_fd}>&-
    __buddy_capturing=0
    sleep 0.05
  fi

  if [[ $rc -ne 0 && -n "$__buddy_cmd" && "$__buddy_cmd" != buddy-diagnose* ]]; then
    local stderr_content=""
    if [[ -f "$__buddy_stderr_file" ]]; then
      stderr_content=$(cat "$__buddy_stderr_file" 2>/dev/null)
    fi
    buddy-diagnose "$__buddy_cmd" "$rc" "$stderr_content"
  fi

  [[ -f "$__buddy_stderr_file" ]] && rm -f "$__buddy_stderr_file"
  __buddy_cmd=""
  __buddy_stderr_file=""
  __buddy_saved_fd=""
}

# --- Register hooks ---
autoload -Uz add-zsh-hook
add-zsh-hook preexec __buddy_preexec
add-zsh-hook precmd __buddy_precmd

# --- Manual commands ---

buddy-off() {
  export BUDDY_DISABLED=1
  echo "heywtf error capture disabled. Run buddy-on to re-enable."
}

buddy-on() {
  unset BUDDY_DISABLED
  echo "heywtf error capture enabled."
}
