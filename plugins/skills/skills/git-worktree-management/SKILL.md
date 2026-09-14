---
name: git-worktree-management
description: Safely inspect, create, reuse, remove, and prune Git worktrees for software repositories. Use when a task involves Git worktrees, branch-to-worktree assignment, remote-tracking branches, or isolated parallel working directories; not for ordinary single-worktree Git operations.
---

# Git Worktree Management

Manage the complete Git worktree lifecycle safely and predictably. A Git worktree is **not** a manually copied repository: it is another working directory connected to the same Git repository metadata and object database. Do not copy a repository to create one.

## Terms and invariants

- **Repository**: the Git repository and its shared object database/metadata. In results, `repository` is the absolute path of the primary registered worktree (the first entry from `git worktree list --porcelain`); this makes directory naming stable even when the command starts inside a linked worktree.
- **Worktree**: one checked-out working tree registered with that repository. The main checkout is also a worktree.
- **Worktree directory**: the filesystem path containing a particular worktree.
- **Branch**: a local ref such as `feature/foo`, which can be checked out in at most one worktree without explicit force authorization.
- **Remote-tracking branch**: a locally stored ref such as `origin/feature/foo` that records a remote branch. It is not itself a local branch that can be assigned to a worktree.

Always preserve user changes. Never run `git reset --hard`, `git clean -fd`, a forced branch deletion, `git worktree remove --force`, or `git worktree add --force` unless the caller has explicitly requested that exact destructive/force operation. Never delete a local branch unless explicitly asked, and never delete a remote branch unless explicitly asked.

Before any change, determine the repository root and run `git worktree list` (prefer `--porcelain` for parsing). Inspect the registered paths and their checked-out branches; do not assume the current directory is the main worktree.

## Helper

Use the shipped helper when available:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh --help
```

It validates inputs, lists worktrees before every mutating operation, avoids all force modes unless `remove --force` is explicitly passed, and emits the result format below. In Codex, resolve the plugin installation directory first and run its `scripts/git-worktree-management.sh`; do not replace it with a manual repository copy. If the helper is unavailable, follow the canonical commands and validations in this skill.

## Predictable directory naming

Unless the caller gives an explicit directory, derive it as:

```text
<repo-parent>/<repo-name>-wt/<sanitized-branch-name>
```

For repository `~/projects/atlantis` and branch `bugfix/ABC-1234`, use:

```text
~/projects/atlantis-wt/bugfix-ABC-1234
```

Sanitize only the directory component: replace path separators and other non-filesystem-safe characters with `-`, collapse repeated separators, and retain letters, digits, `.`, `_`, and `-`. Do not change the actual Git branch name. If two branches sanitize to the same directory name, block and require an explicit directory rather than guessing a suffix.

## Canonical operations

### Inspect

Start from any directory inside the selected repository:

```bash
git rev-parse --show-toplevel
git worktree list --porcelain
git branch --show-current
git status --short
```

For a specific worktree, run `git -C <absolute-worktree-path> branch --show-current` and `git -C <absolute-worktree-path> status --short --untracked-files=all`. A detached worktree has no checked-out branch and must be reported as detached, not inferred as a branch.

The helper form is:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh inspect --repo <directory> [--path <worktree-directory>]
```

### Create a new branch and worktree

Require both an exact new branch name and an explicit base ref. Validate the branch with `git check-ref-format --branch <branch>`, and validate the base resolves to a commit with `git rev-parse --verify <base-ref>^{commit}`. Do not silently select `main`, `master`, `develop`, HEAD, or any other base: an omitted base can change history.

Then verify all of the following before creating anything:

1. `git worktree list --porcelain` has been inspected.
2. The local branch does not already exist (unless the requested directory is already registered to that same branch, which is an idempotent `exists` result).
3. The target directory does not exist unless it is that already-correct worktree.
4. The branch is not attached to another registered worktree.

The canonical command, only after those checks, is equivalent to:

```bash
git worktree add -b <branch> <absolute-path> <base-ref>
```

Use the helper for the validation and operation:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh create-new \
  --repo <repository-or-worktree> --branch <branch> --base <base-ref> [--path <absolute-path>]
```

### Add an existing local branch

First confirm `refs/heads/<branch>` exists and use `git worktree list --porcelain` to ensure no other worktree has `branch refs/heads/<branch>`. If it is already attached elsewhere, report that path and stop. Do not use `git worktree add --force` without explicit authorization.

After validation, the canonical command is:

```bash
git worktree add <absolute-path> <branch>
```

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh create-existing \
  --repo <repository-or-worktree> --branch <branch> [--path <absolute-path>]
```

### Add a remote branch

Require the remote name and remote branch name separately (for example, `origin` and `feature/foo`), and choose the local branch name explicitly when it differs. Verify the remote exists with `git remote get-url <remote>`. If `refs/remotes/<remote>/<branch>` is absent, fetch that specific branch; do not assume stale remote information is current.

If the local branch does not exist, create it with upstream tracking and add it to the worktree. If it already exists, reuse it only when it tracks the requested remote-tracking branch and is not attached to another worktree; otherwise block rather than modifying its upstream silently.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh create-remote \
  --repo <repository-or-worktree> --remote origin --branch feature/foo \
  [--local-branch feature/foo] [--path <absolute-path>]
```

### Remove

Resolve the target to an absolute path, confirm it is registered by `git worktree list --porcelain`, and inspect it first:

```bash
git -C <absolute-path> status --porcelain=v1 --untracked-files=all
```

If output is non-empty—or status cannot be inspected—refuse removal and report `clean: false` or `unknown`. The caller must preserve/commit the changes or explicitly authorize force removal. For a clean worktree, run:

```bash
git worktree remove <absolute-path>
```

The helper keeps the local branch by default:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh remove --repo <repository-or-worktree> --path <absolute-path>
```

Only when the caller explicitly authorizes destructive removal of that dirty worktree may you use `remove --force`, which maps to `git worktree remove --force`. This is not permission to delete its local branch, remote branch, or unrelated paths.

### Prune stale metadata

Use `git worktree prune` only after a dry-run finds stale administrative metadata, or when cleanup was explicitly requested. It is for registrations whose directories have already disappeared; it is not a replacement for removing a live worktree.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh prune --repo <repository-or-worktree>
```

The helper runs `git worktree prune --dry-run --verbose` first and does nothing when no stale metadata exists.

## Delegation request contract

When another agent delegates lifecycle work to `git-worktree-expert`, it sends one
line-oriented request. For an SDD planning run, `planning_id` and `planning_path`
are mandatory and identify the planning record that owns the worktree. They are
coordination metadata, not Git arguments.

```text
WORKTREE_REQUEST
operation: <create|inspect|remove|prune>
repository: <absolute repository root or worktree path>
planning_id: <planning folder name, or null outside SDD>
planning_path: <absolute {root}/{id} path, or null outside SDD>
branch: <local branch name or null>
base_ref: <explicit ref for a new branch, otherwise null>
path: <explicit absolute worktree path, or null to use the standard derived path>
task: <bounded task the worktree will isolate>
authorization: <"none" or the exact user-authorized destructive action>
```

For `create`, the caller must supply a branch and—when that branch is new—an
explicit `base_ref`. Do not infer either from a planning id. For `remove`, the
caller must explicitly state the user's authorization; ordinary post-commit
cleanup is `authorization: none` and succeeds only for a clean worktree. The
expert validates the operation through this skill and responds with the exact
`WORKTREE_RESULT` block below.

## Idempotence and result reporting

If the requested directory is already registered to the requested branch (and, for remote setup, its upstream is correct), return `exists` rather than recreate it. Always report the absolute path and assigned branch for a newly created or reused worktree.

Emit this exact, line-oriented block once for the completed operation. Use `null` where a field does not apply.

```text
WORKTREE_RESULT
operation: <create|inspect|remove|prune|other>
status: <created|exists|removed|blocked|failed|success>
repository: <absolute repository root>
branch: <branch name or null>
base_ref: <base ref or null>
path: <absolute worktree path or null>
clean: <true|false|unknown>
message: <concise explanation>
next_action: <recommended next action or null>
```

## Examples

1. Create `feature/foo` from `main`:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh create-new \
     --repo ~/projects/atlantis --branch feature/foo --base main
   # creates ~/projects/atlantis-wt/feature-foo
   ```

## Review Checklist

- [ ] The repository, branch, base ref, and requested lifecycle operation were resolved before mutation.
- [ ] The returned worktree path, branch assignment, and cleanliness status were verified.
- [ ] Development occurs only in the assigned worktree, never an assumed or ambiguous path.
- [ ] Cleanup or pruning targets only the explicitly confirmed worktree and reports its result.

2. Create `bugfix/ABC-1234` from `develop`:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh create-new \
     --repo ~/projects/atlantis --branch bugfix/ABC-1234 --base develop
   # creates ~/projects/atlantis-wt/bugfix-ABC-1234
   ```

3. Open an existing branch in a worktree:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh create-existing \
     --repo ~/projects/atlantis --branch release/2.4
   ```

4. A branch already attached elsewhere is blocked, with its existing path reported:

   ```text
   WORKTREE_RESULT
   operation: create
   status: blocked
   repository: /home/me/projects/atlantis
   branch: release/2.4
   base_ref: null
   path: /home/me/projects/atlantis-wt/release-2.4
   clean: unknown
   message: Branch 'release/2.4' is already checked out at '/home/me/projects/atlantis-release'.
   next_action: Use that worktree, select another branch, or obtain explicit authorization for a force checkout.
   ```

5. Remove a clean worktree:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh remove \
     --repo ~/projects/atlantis --path ~/projects/atlantis-wt/feature-foo
   ```

6. A dirty worktree is refused without force authorization:

   ```text
   WORKTREE_RESULT
   operation: remove
   status: blocked
   repository: /home/me/projects/atlantis
   branch: feature/foo
   base_ref: null
   path: /home/me/projects/atlantis-wt/feature-foo
   clean: false
   message: The worktree has uncommitted changes or cannot be inspected.
   next_action: Preserve or commit the changes; pass --force only with explicit authorization.
   ```

7. Prune stale registrations after inspection:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh prune --repo ~/projects/atlantis
   ```

8. Fetch and open a remote branch with a tracking local branch:

   ```bash
   ${CLAUDE_PLUGIN_ROOT}/scripts/git-worktree-management.sh create-remote \
     --repo ~/projects/atlantis --remote origin --branch feature/foo
   ```

9. Reuse a correctly configured worktree:

   ```text
   WORKTREE_RESULT
   operation: create
   status: exists
   repository: /home/me/projects/atlantis
   branch: feature/foo
   base_ref: main
   path: /home/me/projects/atlantis-wt/feature-foo
   clean: true
   message: The requested worktree already exists with the requested branch.
   next_action: null
   ```
