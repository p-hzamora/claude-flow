#!/usr/bin/env bash
# Safe, deterministic Git worktree lifecycle helper.
# It deliberately never runs reset, clean, forced deletion, or force checkout.

set -o pipefail

readonly RESULT_HEADER='WORKTREE_RESULT'

usage() {
  cat <<'EOF'
Usage:
  git-worktree-management.sh inspect [--repo <directory>] [--path <directory>]
  git-worktree-management.sh create-new --branch <branch> --base <base-ref> [--repo <directory>] [--path <directory>]
  git-worktree-management.sh create-existing --branch <branch> [--repo <directory>] [--path <directory>]
  git-worktree-management.sh create-remote --remote <remote> --branch <remote-branch> [--local-branch <branch>] [--repo <directory>] [--path <directory>]
  git-worktree-management.sh remove --path <directory> [--repo <directory>] [--force]
  git-worktree-management.sh prune [--repo <directory>]

--force is accepted only by remove and must represent the caller's explicit
authorization to remove a dirty worktree. It is never implied by this script.
EOF
}

result() {
  local operation=$1 status=$2 repository=$3 branch=$4 base_ref=$5 path=$6 clean=$7 message=$8 next_action=$9
  printf '%s\noperation: %s\nstatus: %s\nrepository: %s\nbranch: %s\nbase_ref: %s\npath: %s\nclean: %s\nmessage: %s\nnext_action: %s\n' \
    "$RESULT_HEADER" "$operation" "$status" "$repository" "$branch" "$base_ref" "$path" "$clean" "$message" "$next_action"
}

fail() {
  local operation=$1 repository=$2 message=$3
  result "$operation" failed "$repository" null null null unknown "$message" "Correct the input and retry."
  return 1
}

block() {
  local operation=$1 repository=$2 branch=$3 base_ref=$4 path=$5 clean=$6 message=$7 next_action=$8
  result "$operation" blocked "$repository" "$branch" "$base_ref" "$path" "$clean" "$message" "$next_action"
  return 2
}

absolute_path() {
  local input=$1
  if command -v realpath >/dev/null 2>&1 && realpath -m -- "$PWD" >/dev/null 2>&1; then
    realpath -m -- "$input"
  else
    case "$input" in
      /*) printf '%s\n' "$input" ;;
      *) printf '%s/%s\n' "$(pwd -P)" "$input" ;;
    esac
  fi
}

load_repository() {
  local operation=$1 anchor=$2 anchor_root primary_path
  if ! anchor_root=$(git -C "$anchor" rev-parse --show-toplevel 2>/dev/null); then
    fail "$operation" null "'$anchor' is not inside a Git worktree."
    return 1
  fi
  anchor_root=$(absolute_path "$anchor_root")
  if ! WORKTREE_LIST=$(git -C "$anchor_root" worktree list --porcelain 2>/dev/null); then
    fail "$operation" "$anchor_root" "Unable to inspect registered worktrees."
    return 1
  fi
  primary_path=$(first_registered_worktree)
  if [[ -z $primary_path ]]; then
    fail "$operation" "$anchor_root" "Git reported no registered worktree."
    return 1
  fi
  REPOSITORY=$(absolute_path "$primary_path")
}

first_registered_worktree() {
  local line
  while IFS= read -r line || [[ -n $line ]]; do
    if [[ $line == 'worktree '* ]]; then
      printf '%s\n' "${line#worktree }"
      return 0
    fi
  done <<< "$WORKTREE_LIST"
  return 1
}

valid_branch_name() {
  git check-ref-format --branch "$1" >/dev/null 2>&1
}

sanitize_branch_name() {
  local value=$1 sanitized
  sanitized=$(printf '%s' "$value" | LC_ALL=C sed -E 's/[^A-Za-z0-9._-]+/-/g; s/-+/-/g; s/^-+//; s/-+$//')
  printf '%s\n' "${sanitized:-branch}"
}

default_path() {
  local branch=$1 repo_name repo_parent
  repo_name=$(basename "$REPOSITORY")
  repo_parent=$(dirname "$REPOSITORY")
  printf '%s/%s-wt/%s\n' "$repo_parent" "$repo_name" "$(sanitize_branch_name "$branch")"
}

registered_branch_at() {
  local wanted_path=$1 line current_path= target_seen=false
  while IFS= read -r line || [[ -n $line ]]; do
    case "$line" in
      'worktree '*)
        if [[ $target_seen == true ]]; then
          printf 'DETACHED\n'
          return 0
        fi
        current_path=${line#worktree }
        [[ $(absolute_path "$current_path") == "$wanted_path" ]] && target_seen=true
        ;;
      'branch '*)
        if [[ $target_seen == true ]]; then
          printf '%s\n' "${line#branch }"
          return 0
        fi
        ;;
    esac
  done <<< "$WORKTREE_LIST"
  if [[ $target_seen == true ]]; then
    printf 'DETACHED\n'
    return 0
  fi
  return 1
}

attached_path_for_branch() {
  local wanted_branch=$1 wanted_ref="refs/heads/$1" line current_path=
  while IFS= read -r line || [[ -n $line ]]; do
    case "$line" in
      'worktree '*) current_path=${line#worktree } ;;
      'branch '*)
        if [[ ${line#branch } == "$wanted_ref" ]]; then
          absolute_path "$current_path"
          return 0
        fi
        ;;
    esac
  done <<< "$WORKTREE_LIST"
  return 1
}

worktree_clean() {
  local path=$1 status
  if ! status=$(git -C "$path" status --porcelain=v1 --untracked-files=all 2>/dev/null); then
    printf 'unknown\n'
  elif [[ -z $status ]]; then
    printf 'true\n'
  else
    printf 'false\n'
  fi
}

prepare_path() {
  local operation=$1 branch=$2 base_ref=$3 requested_path=$4
  TARGET_PATH=$(absolute_path "${requested_path:-$(default_path "$branch")}")
  local registered_branch
  if registered_branch=$(registered_branch_at "$TARGET_PATH"); then
    if [[ $registered_branch == "refs/heads/$branch" ]]; then
      result "$operation" exists "$REPOSITORY" "$branch" "$base_ref" "$TARGET_PATH" "$(worktree_clean "$TARGET_PATH")" "The requested worktree already exists with the requested branch." null
      return 10
    fi
    block "$operation" "$REPOSITORY" "$branch" "$base_ref" "$TARGET_PATH" "$(worktree_clean "$TARGET_PATH")" "The path is already registered to '${registered_branch#refs/heads/}'." "Choose another path or use the registered worktree."
    return $?
  fi
  if [[ -e $TARGET_PATH ]]; then
    block "$operation" "$REPOSITORY" "$branch" "$base_ref" "$TARGET_PATH" unknown "The requested directory exists but is not a registered worktree." "Choose an empty new path; do not overwrite this directory."
    return $?
  fi
  return 0
}

ensure_branch_unattached() {
  local operation=$1 branch=$2 base_ref=$3 path=$4 attached_path
  if attached_path=$(attached_path_for_branch "$branch"); then
    if [[ $attached_path != "$path" ]]; then
      block "$operation" "$REPOSITORY" "$branch" "$base_ref" "$path" unknown "Branch '$branch' is already checked out at '$attached_path'." "Use that worktree, select another branch, or obtain explicit authorization for a force checkout."
      return 2
    fi
  fi
  return 0
}

create_worktree() {
  local operation=$1 branch=$2 base_ref=$3 mode=$4
  if ! mkdir -p -- "$(dirname "$TARGET_PATH")"; then
    fail "$operation" "$REPOSITORY" "Cannot create the worktree parent directory."
    return 1
  fi
  local git_output
  case "$mode" in
    new) git_output=$(git -C "$REPOSITORY" worktree add -b "$branch" "$TARGET_PATH" "$base_ref" 2>&1) ;;
    existing) git_output=$(git -C "$REPOSITORY" worktree add "$TARGET_PATH" "$branch" 2>&1) ;;
    remote) git_output=$(git -C "$REPOSITORY" worktree add --track -b "$branch" "$TARGET_PATH" "$base_ref" 2>&1) ;;
    *) fail "$operation" "$REPOSITORY" "Unsupported creation mode."; return 1 ;;
  esac
  if [[ $? -ne 0 ]]; then
    fail "$operation" "$REPOSITORY" "Git could not create the worktree; no force option was used."
    return 1
  fi
  result "$operation" created "$REPOSITORY" "$branch" "$base_ref" "$TARGET_PATH" "$(worktree_clean "$TARGET_PATH")" "Worktree created and assigned to '$branch'." "Change to '$TARGET_PATH'."
}

inspect() {
  local repo_arg=$PWD path_arg= line count=0 current_branch=null target_path
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo) [[ $# -ge 2 ]] || { usage >&2; return 64; }; repo_arg=$2; shift 2 ;;
      --path) [[ $# -ge 2 ]] || { usage >&2; return 64; }; path_arg=$2; shift 2 ;;
      *) usage >&2; return 64 ;;
    esac
  done
  load_repository inspect "$repo_arg" || return $?
  while IFS= read -r line || [[ -n $line ]]; do [[ $line == 'worktree '* ]] && ((count++)); done <<< "$WORKTREE_LIST"
  target_path=$(absolute_path "${path_arg:-$REPOSITORY}")
  if [[ ! -d $target_path ]]; then
    block inspect "$REPOSITORY" null null "$target_path" unknown "The requested worktree directory does not exist; $count worktree(s) are registered." "Run 'git worktree list --porcelain' to inspect registered paths."
    return $?
  fi
  if ! git -C "$target_path" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    block inspect "$REPOSITORY" null null "$target_path" unknown "The requested directory is not a Git worktree; $count worktree(s) are registered." "Select a path reported by 'git worktree list'."
    return $?
  fi
  current_branch=$(git -C "$target_path" symbolic-ref --quiet --short HEAD 2>/dev/null || printf 'DETACHED')
  result inspect success "$REPOSITORY" "$current_branch" null "$target_path" "$(worktree_clean "$target_path")" "Inspected '$target_path'; $count worktree(s) are registered." "Use 'git worktree list --porcelain' for the complete registration list."
}

create_new() {
  local repo_arg=$PWD path_arg= branch= base_ref=
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo) [[ $# -ge 2 ]] || { usage >&2; return 64; }; repo_arg=$2; shift 2 ;;
      --path) [[ $# -ge 2 ]] || { usage >&2; return 64; }; path_arg=$2; shift 2 ;;
      --branch) [[ $# -ge 2 ]] || { usage >&2; return 64; }; branch=$2; shift 2 ;;
      --base) [[ $# -ge 2 ]] || { usage >&2; return 64; }; base_ref=$2; shift 2 ;;
      *) usage >&2; return 64 ;;
    esac
  done
  [[ -n $branch && -n $base_ref ]] || { usage >&2; return 64; }
  load_repository create "$repo_arg" || return $?
  valid_branch_name "$branch" || { block create "$REPOSITORY" "$branch" "$base_ref" null unknown "'$branch' is not a valid Git branch name." "Provide a valid branch name."; return $?; }
  git -C "$REPOSITORY" rev-parse --verify --quiet --end-of-options "${base_ref}^{commit}" >/dev/null || { block create "$REPOSITORY" "$branch" "$base_ref" null unknown "Base ref '$base_ref' does not resolve to a commit." "Select an existing explicit base branch, tag, or commit."; return $?; }
  prepare_path create "$branch" "$base_ref" "$path_arg"; local prepared=$?
  [[ $prepared -eq 10 ]] && return 0
  [[ $prepared -eq 0 ]] || return $prepared
  if git -C "$REPOSITORY" show-ref --verify --quiet "refs/heads/$branch"; then
    local attached_path
    if attached_path=$(attached_path_for_branch "$branch"); then
      block create "$REPOSITORY" "$branch" "$base_ref" "$TARGET_PATH" unknown "Branch '$branch' already exists and is checked out at '$attached_path'." "Use that worktree, select another branch, or obtain explicit authorization for a force checkout."
      return $?
    fi
    block create "$REPOSITORY" "$branch" "$base_ref" "$TARGET_PATH" unknown "Local branch '$branch' already exists." "Use create-existing for that branch, or choose a new branch name."
    return $?
  fi
  ensure_branch_unattached create "$branch" "$base_ref" "$TARGET_PATH" || return $?
  create_worktree create "$branch" "$base_ref" new
}

create_existing() {
  local repo_arg=$PWD path_arg= branch=
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo) [[ $# -ge 2 ]] || { usage >&2; return 64; }; repo_arg=$2; shift 2 ;;
      --path) [[ $# -ge 2 ]] || { usage >&2; return 64; }; path_arg=$2; shift 2 ;;
      --branch) [[ $# -ge 2 ]] || { usage >&2; return 64; }; branch=$2; shift 2 ;;
      *) usage >&2; return 64 ;;
    esac
  done
  [[ -n $branch ]] || { usage >&2; return 64; }
  load_repository create "$repo_arg" || return $?
  valid_branch_name "$branch" || { block create "$REPOSITORY" "$branch" null null unknown "'$branch' is not a valid Git branch name." "Provide a valid branch name."; return $?; }
  git -C "$REPOSITORY" show-ref --verify --quiet "refs/heads/$branch" || { block create "$REPOSITORY" "$branch" null null unknown "Local branch '$branch' does not exist." "Create it from an explicit base, or use create-remote."; return $?; }
  prepare_path create "$branch" null "$path_arg"; local prepared=$?
  [[ $prepared -eq 10 ]] && return 0
  [[ $prepared -eq 0 ]] || return $prepared
  ensure_branch_unattached create "$branch" null "$TARGET_PATH" || return $?
  create_worktree create "$branch" null existing
}

create_remote() {
  local repo_arg=$PWD path_arg= remote= branch= local_branch= remote_ref upstream
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo) [[ $# -ge 2 ]] || { usage >&2; return 64; }; repo_arg=$2; shift 2 ;;
      --path) [[ $# -ge 2 ]] || { usage >&2; return 64; }; path_arg=$2; shift 2 ;;
      --remote) [[ $# -ge 2 ]] || { usage >&2; return 64; }; remote=$2; shift 2 ;;
      --branch) [[ $# -ge 2 ]] || { usage >&2; return 64; }; branch=$2; shift 2 ;;
      --local-branch) [[ $# -ge 2 ]] || { usage >&2; return 64; }; local_branch=$2; shift 2 ;;
      *) usage >&2; return 64 ;;
    esac
  done
  [[ -n $remote && -n $branch ]] || { usage >&2; return 64; }
  local_branch=${local_branch:-$branch}
  load_repository create "$repo_arg" || return $?
  valid_branch_name "$branch" && valid_branch_name "$local_branch" || { block create "$REPOSITORY" "$local_branch" "$remote/$branch" null unknown "The requested local or remote branch name is invalid." "Provide valid branch names without a remote prefix."; return $?; }
  git -C "$REPOSITORY" remote get-url "$remote" >/dev/null 2>&1 || { block create "$REPOSITORY" "$local_branch" "$remote/$branch" null unknown "Remote '$remote' is not configured." "Select a configured remote or add it explicitly before retrying."; return $?; }
  remote_ref="refs/remotes/$remote/$branch"
  if ! git -C "$REPOSITORY" show-ref --verify --quiet "$remote_ref"; then
    if ! git -C "$REPOSITORY" fetch --no-tags "$remote" "refs/heads/$branch:$remote_ref" >/dev/null 2>&1; then
      fail create "$REPOSITORY" "Unable to fetch '$remote/$branch'."
      return 1
    fi
  fi
  git -C "$REPOSITORY" show-ref --verify --quiet "$remote_ref" || { block create "$REPOSITORY" "$local_branch" "$remote/$branch" null unknown "Remote-tracking branch '$remote/$branch' does not exist." "Verify the remote branch name and fetch permissions."; return $?; }
  if git -C "$REPOSITORY" show-ref --verify --quiet "refs/heads/$local_branch"; then
    upstream=$(git -C "$REPOSITORY" for-each-ref --format='%(upstream:short)' "refs/heads/$local_branch")
    if [[ $upstream != "$remote/$branch" ]]; then
      TARGET_PATH=$(absolute_path "${path_arg:-$(default_path "$local_branch")}")
      block create "$REPOSITORY" "$local_branch" "$remote/$branch" "$TARGET_PATH" unknown "Local branch '$local_branch' already exists but does not track '$remote/$branch'." "Choose --local-branch explicitly or inspect the existing branch."
      return $?
    fi
  fi
  prepare_path create "$local_branch" "$remote/$branch" "$path_arg"; local prepared=$?
  [[ $prepared -eq 10 ]] && return 0
  [[ $prepared -eq 0 ]] || return $prepared
  ensure_branch_unattached create "$local_branch" "$remote/$branch" "$TARGET_PATH" || return $?
  if git -C "$REPOSITORY" show-ref --verify --quiet "refs/heads/$local_branch"; then
    create_worktree create "$local_branch" "$remote/$branch" existing
  else
    create_worktree create "$local_branch" "$remote/$branch" remote
  fi
}

remove_worktree() {
  local repo_arg=$PWD path_arg= force=false registered_branch clean
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo) [[ $# -ge 2 ]] || { usage >&2; return 64; }; repo_arg=$2; shift 2 ;;
      --path) [[ $# -ge 2 ]] || { usage >&2; return 64; }; path_arg=$2; shift 2 ;;
      --force) force=true; shift ;;
      *) usage >&2; return 64 ;;
    esac
  done
  [[ -n $path_arg ]] || { usage >&2; return 64; }
  load_repository remove "$repo_arg" || return $?
  TARGET_PATH=$(absolute_path "$path_arg")
  if ! registered_branch=$(registered_branch_at "$TARGET_PATH"); then
    block remove "$REPOSITORY" null null "$TARGET_PATH" unknown "The path is not a registered worktree." "Inspect with 'git worktree list'; use prune only for stale metadata."
    return $?
  fi
  local branch=${registered_branch#refs/heads/}
  [[ -d $TARGET_PATH ]] || { block remove "$REPOSITORY" "$branch" null "$TARGET_PATH" unknown "The directory is missing; its registration may be stale." "Run prune to remove stale metadata after inspection."; return $?; }
  clean=$(worktree_clean "$TARGET_PATH")
  if [[ $clean != true && $force != true ]]; then
    block remove "$REPOSITORY" "$branch" null "$TARGET_PATH" "$clean" "The worktree has uncommitted changes or cannot be inspected." "Preserve or commit the changes; pass --force only with explicit authorization."
    return $?
  fi
  local git_output
  if [[ $force == true ]]; then
    git_output=$(git -C "$REPOSITORY" worktree remove --force "$TARGET_PATH" 2>&1)
  else
    git_output=$(git -C "$REPOSITORY" worktree remove "$TARGET_PATH" 2>&1)
  fi
  if [[ $? -ne 0 ]]; then
    fail remove "$REPOSITORY" "Git could not remove the worktree."
    return 1
  fi
  result remove removed "$REPOSITORY" "$branch" null "$TARGET_PATH" "$clean" "Worktree removed; its local branch was preserved." null
}

prune_worktrees() {
  local repo_arg=$PWD dry_run
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --repo) [[ $# -ge 2 ]] || { usage >&2; return 64; }; repo_arg=$2; shift 2 ;;
      *) usage >&2; return 64 ;;
    esac
  done
  load_repository prune "$repo_arg" || return $?
  if ! dry_run=$(git -C "$REPOSITORY" worktree prune --dry-run --verbose 2>&1); then
    fail prune "$REPOSITORY" "Unable to check for stale worktree metadata."
    return 1
  fi
  if [[ -z $dry_run ]]; then
    result prune success "$REPOSITORY" null null null unknown "No stale worktree metadata exists; nothing was pruned." null
    return 0
  fi
  if ! git -C "$REPOSITORY" worktree prune >/dev/null 2>&1; then
    fail prune "$REPOSITORY" "Git could not prune stale worktree metadata."
    return 1
  fi
  result prune success "$REPOSITORY" null null null unknown "Pruned stale worktree administrative metadata." "Run 'git worktree list --porcelain' to confirm the remaining registrations."
}

main() {
  [[ $# -ge 1 ]] || { usage >&2; return 64; }
  local operation=$1
  shift
  case "$operation" in
    inspect) inspect "$@" ;;
    create-new) create_new "$@" ;;
    create-existing) create_existing "$@" ;;
    create-remote) create_remote "$@" ;;
    remove) remove_worktree "$@" ;;
    prune) prune_worktrees "$@" ;;
    --help|-h|help) usage ;;
    *) usage >&2; return 64 ;;
  esac
}

main "$@"
