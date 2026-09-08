# claude-flow

Private multi-host plugin marketplace for the SDD/Jira/Python workflows. Claude Code
and OpenAI Codex reuse the same skill files; each plugin has a host-specific manifest
only where the host requires one.

## Plugins

- **skills** — cross-cutting, language-agnostic skills reused across plugins:
  `grill-with-context`, `commit-message-generator`, `claude-sdk-expert`, `graphify`,
  `api-rest-designer`, `git-worktree-management` (safe, deterministic Git worktree
  lifecycle management), `sdd-workflow` (stack-agnostic SDD orchestration methodology —
  any stack orchestrator, e.g. `sdd-python-orchestrator` below or a future
  `sdd-docker-orchestrator`, invokes this first, then layers its own stack context
  on top), `handoff` (user-invoked only, via `/handoff` — compacts the conversation
  into a portable markdown handoff document in the OS temp dir for a fresh agent, a
  colleague, or a forked side task to pick up; not a `/compact` replacement),
  `prototype` (builds a throwaway UI-variations-behind-a-toggle or state-machine
  terminal REPL in its own directory to settle a design question code can answer
  and words can't; pairs with `handoff` to carry the decision back).
- **python-suite** — reusable Python/DDD/FastAPI/SQLAlchemy agents and skills, each
  independently usable (not only reachable through an orchestrator):
  - Agents: `sdd-python-orchestrator`, `ddd-reviewer`, `ddd-implementer`,
    `ddd-entity-generator`, `fastapi-endpoint-builder`, `fastapi-reviewer`,
    `orm-model-inspector`, `ruff-linter`, `sqlalchemy-expert-fixer`, `test-writer`
  - Skills: `clean-ddd-hexagonal-python`, `fastapi-async-patterns`, `sqlalchemy-orm`,
    `python-syntax`, `pytest`, `pytest-coverage`
  - No Jira coupling. Depends on `skills` (for `sdd-workflow` plus the general ones).
- **jira-dev-workflow** — `jira-dev-workflow` + `jira-git-committer` +
  `jira-tech-lead-reviewer` (read-only branch review: resolves the ticket from the
  branch name, delegates DDD/SOLID/CQRS compliance to `ddd-reviewer`/`fastapi-reviewer`,
  checks lint/tests, reconciles the diff against the ticket), plus two skills the agents
  invoke: `git-devops-conventions` (the branch-name/author-email regexes below)
  and `atlassian-jira-mcp` (site disambiguation, credentials, the REST fallbacks for
  attaching/creating issues, transitions, comments). The commit-message regex is owned
  by `skills`' `commit-message-generator`, not by `git-devops-conventions` — see below.
  Also ships `scripts/md2pdf.sh`, the mandatory (non-optional) Markdown-to-PDF converter
  `jira-dev-workflow` calls in Phase 6 — never a hand-rolled `pandoc`/`weasyprint` call.
  Phase 6's `.md` source must follow the C4 model structure (Context/Container/Component/
  Code, text sections only, no diagrams).
  Depends on `skills` and `python-suite`.

## Dependency graph

```
jira-dev-workflow  --depends on-->  skills
                   --depends on-->  python-suite  --depends on-->  skills
```

## Not bundled

- **Atlassian MCP server** — `jira-dev-workflow` calls `mcp__atlassian__*` tools directly.
  Each teammate must configure and authenticate their own Atlassian MCP connection;
  this marketplace does not install or configure it.

## Non-negotiable regexes

Two owners. Neither pattern is inlined here — read them at the source, so there's
exactly one copy of each in the whole repo:

- **Branch name** and **commit author email** — owned by the `git-devops-conventions`
  skill (`plugins/jira-dev-workflow/skills/git-devops-conventions/SKILL.md`).
  `jira-dev-workflow.md` and `jira-git-committer.md` both invoke it rather than each
  carrying their own copy.
- **Commit message** — owned by the `commit-message-generator` skill
  (`plugins/skills/skills/commit-message-generator/SKILL.md`, base `skills` plugin,
  used outside the Jira flow too). `jira-git-committer` invokes it both to generate
  and to validate titles.

If DevOps changes one, edit it at its owning skill only.

## Install (teammates)

```
/plugin marketplace add git@github-personal:p-hzamora/claude-flow.git
/plugin install jira-dev-workflow
```
Installing `jira-dev-workflow` auto-enables `skills` and `python-suite` transitively.

Want just the Python suite, no Jira? `/plugin install python-suite` on its own — e.g. to
run `test-writer` standalone on a repo without going through any planning/ticket flow.

Building a suite for another stack (e.g. `docker-suite` with an `sdd-docker-orchestrator`)?
Have it depend on `skills` and invoke the `sdd-workflow` skill the same way
`sdd-python-orchestrator` does — the orchestration process is shared, only the
stack-specific context in the agent's own file differs.

## Use with Codex / ChatGPT

The same marketplace is legacy-compatible with Codex. Each plugin also contains a
`.codex-plugin/plugin.json` manifest whose `skills` entry points at the existing
`skills/` directory, so no skill files are copied or renamed.

From the repository root, add the marketplace to Codex once:

```
codex plugin marketplace add /absolute/path/to/claude-flow
codex plugin list
codex plugin add skills@claude-flow
codex plugin add python-suite@claude-flow
# Add jira-dev-workflow@claude-flow after the two dependencies above when needed.
```

The native Codex catalog is [`.agents/plugins/marketplace.json`](./.agents/plugins/marketplace.json).
It lists the same three plugin folders as the Claude marketplace, with Codex-specific
availability metadata. Codex plugin manifests do not currently declare dependencies,
so install `skills` explicitly before `python-suite`, and both before
`jira-dev-workflow`.

Codex loads the shared skills with the selected OpenAI model. The Claude Code
`agents/` definitions are not advertised as Codex skills: the two hosts have different
agent configuration, tool, and permission models. Matching, thin Codex role adapters
are versioned in [`.codex/agents/`](./.codex/agents/) and reuse the installed shared
skills rather than copying a procedure. Codex discovers them automatically when this
repository is the project; to use them from another project, follow
[`.codex/README.md`](./.codex/README.md) to symlink the directory and retain one
source of truth.

Validate the dual-host layout with:

```
python3 scripts/validate_multihost.py
```

## Adding more later

- New plugin: add a folder under `plugins/`, add one entry to
  `.claude-plugin/marketplace.json`'s `plugins[]`, and add both
  `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` when it should work
  in both hosts.
- New agent/skill in an existing plugin: drop the file in that plugin's `agents/` or
  `skills/` folder, commit, push. For Codex portability, put reusable behavior in
  `skills/`; Claude-only orchestration can remain in `agents/`. No marketplace.json
  change is needed for a component-only change.
- Teammates pick up changes with `/plugin marketplace update` then `/plugin update <name>`.

## Update

```
/plugin marketplace update
/plugin update jira-dev-workflow
```
