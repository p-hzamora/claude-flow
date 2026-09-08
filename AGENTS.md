# Codex instructions for claude-flow

`claude-flow` is a multi-host plugin marketplace. Reusable procedures and reference
knowledge have one source of truth: `plugins/*/skills/*/SKILL.md`. Do not make a
Codex-specific copy of a skill.

Read [`CLAUDE.md`](./CLAUDE.md) before changing a plugin, its version, manifests, or
documentation. It contains the repository's full maintenance and release rules.

Codex-specific agent profiles live in [`.codex/agents/`](./.codex/agents/). They are
thin role adapters: they select a role, permissions, and the relevant shared skills;
they must not reimplement those skills' procedures. The matching Claude Code profiles
remain in `plugins/*/agents/` because Claude Code and Codex use different agent
configuration formats and tool models.

When delegation is useful, use the named Codex profile for an independent, bounded
workstream. Prefer direct work for small or sequential changes. Review profiles are
read-only; do not override their sandbox to make edits.

## Git worktree ownership

All Git worktree lifecycle operations MUST be delegated to `git-worktree-expert`.
Do not directly create, remove, prune, relocate, or otherwise manage Git worktrees
when `git-worktree-expert` is available.

### Agent delegation architecture

`git-worktree-expert` is the sole lifecycle owner. It uses the
`git-worktree-management` skill as its authoritative procedure; development agents
must send a `WORKTREE_REQUEST` and act only after receiving `WORKTREE_RESULT`.

```text
Development Agent
      │
      │ WORKTREE_REQUEST
      ▼
git-worktree-expert
      │
      │ uses
      ▼
git-worktree-management skill
      │
      ▼
Git worktree
      │
      │ WORKTREE_RESULT
      ▼
Development Agent
```

When isolated work is required:

1. Ask `git-worktree-expert` for a worktree.
2. Provide the desired branch/task and base ref when known.
3. Wait for its `WORKTREE_RESULT`.
4. Perform the development task inside the returned `path`.
5. Delegate worktree cleanup back to `git-worktree-expert` when needed.

Normal Git operations within the assigned worktree remain the responsibility of the
current development agent.

When adding or changing a reusable procedure, update its shared `SKILL.md` once and
have both hosts refer to it. Run `python3 scripts/validate_multihost.py` before
handing off marketplace changes.
