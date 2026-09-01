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

When adding or changing a reusable procedure, update its shared `SKILL.md` once and
have both hosts refer to it. Run `python3 scripts/validate_multihost.py` before
handing off marketplace changes.
