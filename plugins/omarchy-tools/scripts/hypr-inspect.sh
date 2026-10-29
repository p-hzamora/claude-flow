#!/usr/bin/env bash
# Read-only Hyprland inspection and validation helper for Omarchy systems.
# Needs a running Hyprland session (hyprctl) and jq. It never edits any file.

set -o pipefail

usage() {
  cat <<'USAGE'
Usage:
  hypr-inspect.sh check                 reload the config, then print hyprctl configerrors
  hypr-inspect.sh monitors              one line per monitor: mode, position, scale, transform, workspace
  hypr-inspect.sh window                focused window: class, initialClass, title, workspace, floating
  hypr-inspect.sh clients               every window: workspace, class, title
  hypr-inspect.sh bind <MODS> <KEY>     who owns a key combo, e.g. bind SUPER SHIFT B

check exits 0 only when configerrors is empty. bind prints each owner with its
dispatcher and argument, so an existing Omarchy default can be unbound before it is
overridden. Exit codes: 0 ok, 1 errors or no match, 2 usage or missing dependency.
USAGE
}

need() {
  command -v "$1" >/dev/null 2>&1 || { printf 'Missing dependency: %s\n' "$1" >&2; exit 2; }
}

cmd_check() {
  hyprctl reload >/dev/null || { printf 'hyprctl reload failed. Is Hyprland running?\n' >&2; exit 1; }
  local errors
  errors=$(hyprctl configerrors)
  if [ -z "$errors" ]; then
    printf 'OK: reloaded, no config errors.\n'
  else
    printf 'CONFIG ERRORS:\n%s\n' "$errors"
    exit 1
  fi
}

cmd_monitors() {
  hyprctl monitors -j | jq -r '.[] |
    "\(.name)  \(.width)x\(.height)@\(.refreshRate | floor)  at \(.x)x\(.y)  scale \(.scale)  transform \(.transform)  workspace \(.activeWorkspace.name)\(if .disabled then "  DISABLED" else "" end)"'
}

cmd_window() {
  hyprctl activewindow -j | jq -r 'if .class == null then "No focused window." else
    "class: \(.class)\ninitialClass: \(.initialClass)\ntitle: \(.title)\nworkspace: \(.workspace.name)\nfloating: \(.floating)\nxwayland: \(.xwayland)" end'
}

cmd_clients() {
  hyprctl clients -j | jq -r 'sort_by(.workspace.id)[] | "ws \(.workspace.name)  \(.class)  \(.title)"'
}

# Modifier bits from Hyprland: SHIFT 1, CTRL 4, ALT 8, SUPER 64. CAPS (2) and NUM (16) are ignored.
cmd_bind() {
  [ $# -ge 2 ] || { usage >&2; exit 2; }
  local key=${!#} mask=0 mod i=1
  while [ "$i" -lt $# ]; do
    mod=$(printf '%s' "${!i}" | tr '[:lower:]' '[:upper:]')
    case $mod in
      SHIFT) mask=$((mask + 1)) ;;
      CTRL | CONTROL) mask=$((mask + 4)) ;;
      ALT) mask=$((mask + 8)) ;;
      SUPER | MOD4 | WIN) mask=$((mask + 64)) ;;
      *) printf "Unknown modifier '%s'. Use SHIFT, CTRL, ALT, SUPER.\n" "${!i}" >&2; exit 2 ;;
    esac
    i=$((i + 1))
  done
  local found
  found=$(hyprctl binds -j | jq -r --argjson mask "$mask" --arg key "$(printf '%s' "$key" | tr '[:lower:]' '[:upper:]')" '
    def strip($m; $bit): if (($m / $bit | floor) % 2) == 1 then $m - $bit else $m end;
    .[]
    | select((.key | ascii_upcase) == $key and strip(strip(.modmask; 2); 16) == $mask)
    | "\(.dispatcher) \(.arg)  [\(if .description == "" then "no description" else .description end)]\(if .submap != "" then "  submap=" + .submap else "" end)"')
  if [ -z "$found" ]; then
    printf 'Free: nothing is bound to this combination.\n'
    exit 1
  fi
  printf 'Bound to:\n%s\n' "$found"
}

[ $# -ge 1 ] || { usage >&2; exit 2; }
need hyprctl
need jq
subcommand=$1
shift
case $subcommand in
  check) cmd_check ;;
  monitors) cmd_monitors ;;
  window) cmd_window ;;
  clients) cmd_clients ;;
  bind) cmd_bind "$@" ;;
  -h | --help | help) usage ;;
  *) usage >&2; exit 2 ;;
esac
