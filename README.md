# claude-flow

Private Claude Code plugin marketplace for the SDD/Jira/Python workflow agents.

## Plugins

- **skills** — cross-cutting, language-agnostic skills reused across plugins:
  `grill-me`, `commit-message-generator`, `claude-sdk-expert`, `graphify`,
  `api-rest-designer`.
- **python-suite** — reusable Python/DDD/FastAPI/SQLAlchemy agents and skills, each
  independently usable (not only reachable through an orchestrator):
  - Agents: `sdd-orchestrator`, `ddd-reviewer`, `ddd-implementer`, `ddd-entity-generator`,
    `fastapi-endpoint-builder`, `fastapi-reviewer`, `orm-model-inspector`,
    `sqlalchemy-expert-fixer`, `test-writer`
  - Skills: `clean-ddd-hexagonal-python`, `fastapi-async-patterns`, `sqlalchemy-orm`,
    `python-syntax`, `pytest`, `pytest-coverage`
  - No Jira coupling. Depends on `skills`.
- **jira-dev-workflow** — `jira-dev-workflow` + `jira-git-committer`. Depends on
  `skills` and `python-suite`.

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

Duplicated in both `jira-dev-workflow.md` and `jira-git-committer.md` (same plugin).
If DevOps changes these, update both files in the same commit:

- Branch name: `(develop|test|staging|main)|((feature|bugfix|hotfix)\/[A-Z][A-Z]{1,32}-\d+([-_].*)?)`
- Commit message: `(build|chore|docs|feat|fix|perf|refactor|style|test|update)(\(([a-zA-Z]+|([A-Z][A-Z]{1,32}-\d+))\))?: .*(.*\n*)*`
- Commit author email: `@(stidea\.com|grupo-st\.es|stanalytics\.es|noreply\.gitlab\.com)$`

## Install (teammates)

```
/plugin marketplace add git@github-personal:p-hzamora/claude-flow.git
/plugin install jira-dev-workflow
```
Installing `jira-dev-workflow` auto-enables `skills` and `python-suite` transitively.

Want just the Python suite, no Jira? `/plugin install python-suite` on its own — e.g. to
run `test-writer` standalone on a repo without going through any planning/ticket flow.

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
