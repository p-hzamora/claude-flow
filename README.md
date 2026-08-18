# claude-flow

Private Claude Code plugin marketplace for the SDD/Jira/Python workflow agents.

## Plugins

- **skills** — cross-cutting, language-agnostic skills reused across plugins:
  `grill-with-context`, `commit-message-generator`, `claude-sdk-expert`, `graphify`,
  `api-rest-designer`, `sdd-workflow` (stack-agnostic SDD orchestration methodology —
  any stack orchestrator, e.g. `sdd-python-orchestrator` below or a future
  `sdd-docker-orchestrator`, invokes this first, then layers its own stack context
  on top).
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

## Adding more later

- New stack suite (e.g. `go-suite`): add a folder under `plugins/`, add one entry to
  `.claude-plugin/marketplace.json`'s `plugins[]`, commit, push.
- New agent/skill in an existing plugin: drop the file in that plugin's `agents/` or
  `skills/` folder, commit, push. No marketplace.json change needed.
- Teammates pick up changes with `/plugin marketplace update` then `/plugin update <name>`.

## Update

```
/plugin marketplace update
/plugin update jira-dev-workflow
```
