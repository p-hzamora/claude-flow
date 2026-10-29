#!/usr/bin/env bash
# Add, remove, and list zsh aliases in one aliases file.
# Portable across macOS (bash 3.2), Linux, and WSL: no GNU-only flags, no arrays.

set -o pipefail

readonly DEFAULT_FILE="${ZSH_ALIASES_FILE:-$HOME/.config/zsh/aliases.zsh}"

usage() {
  cat <<'EOF'
Usage:
  zsh-alias.sh add [--file <path>] [--force] <name> <command>
  zsh-alias.sh remove [--file <path>] <name>
  zsh-alias.sh list [--file <path>]

The aliases file defaults to $ZSH_ALIASES_FILE, else ~/.config/zsh/aliases.zsh.
add refuses a name that already exists as an alias, function, command, or builtin
unless --force is passed; --force replaces an alias in the file and shadows anything
else. Exit codes: 0 done, 1 conflict or missing alias, 2 usage or invalid input.
EOF
}

die() {
  printf '%s\n' "$2" >&2
  exit "$1"
}

validate_name() {
  case $1 in
    '' | -* | *[!A-Za-z0-9_.-]*) die 2 "Invalid alias name '$1': use letters, digits, '_', '.', '-', and do not start with '-'." ;;
  esac
}

# Prints "<kind>" for a name as an interactive zsh sees it, or nothing if zsh is absent.
zsh_kind() {
  command -v zsh >/dev/null 2>&1 || return 0
  zsh -ic "whence -w -- '$1'" 2>/dev/null | sed -n 's/^.*: \([a-z]*\)$/\1/p' | tail -n 1
}

# Parses --file/--force flags; leaves the positional arguments in POSITIONAL.
parse_flags() {
  FILE=$DEFAULT_FILE
  FORCE=0
  POSITIONAL=()
  while [ $# -gt 0 ]; do
    case $1 in
      --file) [ $# -ge 2 ] || die 2 '--file needs a path.'; FILE=$2; shift 2 ;;
      --force) FORCE=1; shift ;;
      -h | --help) usage; exit 0 ;;
      --) shift; break ;;
      -*) die 2 "Unknown option '$1'." ;;
      *) break ;;
    esac
  done
  POSITIONAL=("$@")
}

has_alias() {
  [ -f "$FILE" ] && awk -v n="$1" 'index($0, "alias " n "=") == 1 { found = 1 } END { exit !found }' "$FILE"
}

check_syntax() {
  command -v zsh >/dev/null 2>&1 || { printf 'warning: zsh not found, syntax not checked.\n' >&2; return 0; }
  zsh -n "$1" 2>&1 || return 1
}

cmd_add() {
  parse_flags "$@"
  [ "${#POSITIONAL[@]}" -eq 2 ] || { usage >&2; exit 2; }
  local name=${POSITIONAL[0]} command=${POSITIONAL[1]}
  validate_name "$name"
  case $command in
    '') die 2 'The command must not be empty.' ;;
    *$'\n'*) die 2 'The command must be a single line; write a function by hand instead.' ;;
  esac

  if ! has_alias "$name" && [ "$FORCE" -eq 0 ]; then
    local kind
    kind=$(zsh_kind "$name")
    case $kind in
      '' | none) ;;
      *) die 1 "'$name' already exists in zsh as: $kind. Pick another name, or pass --force to shadow it." ;;
    esac
  elif has_alias "$name" && [ "$FORCE" -eq 0 ]; then
    die 1 "Alias '$name' is already defined in $FILE. Pass --force to replace it."
  fi

  local quoted line tmp
  quoted=$(printf '%s' "$command" | sed "s/'/'\\\\''/g")
  line="alias $name='$quoted'"

  mkdir -p "$(dirname "$FILE")" || die 2 "Cannot create the directory for $FILE."
  tmp=$(mktemp "${TMPDIR:-/tmp}/zsh-alias.XXXXXX") || die 2 'Cannot create a temporary file.'
  trap 'rm -f "$tmp"' EXIT
  if [ -f "$FILE" ]; then
    awk -v n="$name" 'index($0, "alias " n "=") != 1' "$FILE" > "$tmp"
  fi
  printf '%s\n' "$line" >> "$tmp"
  check_syntax "$tmp" || die 2 "The new line breaks the file's zsh syntax; $FILE was not changed."
  cat "$tmp" > "$FILE"
  printf 'added to %s: %s\nReload with: source ~/.zshrc\n' "$FILE" "$line"
}

cmd_remove() {
  parse_flags "$@"
  [ "${#POSITIONAL[@]}" -eq 1 ] || { usage >&2; exit 2; }
  local name=${POSITIONAL[0]} tmp
  validate_name "$name"
  has_alias "$name" || die 1 "Alias '$name' is not defined in $FILE."
  tmp=$(mktemp "${TMPDIR:-/tmp}/zsh-alias.XXXXXX") || die 2 'Cannot create a temporary file.'
  trap 'rm -f "$tmp"' EXIT
  awk -v n="$name" 'index($0, "alias " n "=") != 1' "$FILE" > "$tmp"
  cat "$tmp" > "$FILE"
  printf 'removed %s from %s\nReload with: source ~/.zshrc\n' "$name" "$FILE"
}

cmd_list() {
  parse_flags "$@"
  [ "${#POSITIONAL[@]}" -eq 0 ] || { usage >&2; exit 2; }
  [ -f "$FILE" ] || die 1 "No aliases file at $FILE."
  grep -E '^alias ' "$FILE" || true
}

[ $# -ge 1 ] || { usage >&2; exit 2; }
subcommand=$1
shift
case $subcommand in
  add) cmd_add "$@" ;;
  remove) cmd_remove "$@" ;;
  list) cmd_list "$@" ;;
  -h | --help | help) usage ;;
  *) usage >&2; exit 2 ;;
esac
