# claude-flow

Private Claude Code plugin marketplace for the SDD/Jira workflow agents.

## Plugins

- **shared-skills** — skills reused across plugins (`grill-me`, `commit-message-generator`).
  Currently: `grill-me` used by `jira-dev-workflow`, `commit-message-generator` used by
  `jira-git-committer`. No dependents yet outside this repo, but this is the plugin new
  shared skills go into as the marketplace grows.
- **sdd-orchestrator-suite** — `sdd-orchestrator` plus its DDD/FastAPI/ORM/test specialist
  agents (`ddd-reviewer`, `ddd-implementer`, `ddd-entity-generator`, `fastapi-endpoint-builder`,
  `fastapi-reviewer`, `orm-model-inspector`, `sqlalchemy-expert-fixer`, `test-writer`).
  No Jira coupling — usable by any future workflow that needs SDD implementation
  (e.g. a non-Jira planning agent), not just `jira-dev-workflow`.
- **jira-dev-workflow** — `jira-dev-workflow` + `jira-git-committer`. Depends on
  `shared-skills` and `sdd-orchestrator-suite`.

## Dependency graph

```
jira-dev-workflow  --depends on-->  shared-skills
                   --depends on-->  sdd-orchestrator-suite
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
Installing `jira-dev-workflow` auto-enables its `shared-skills` and
`sdd-orchestrator-suite` dependencies transitively.

Want only the SDD suite without Jira? `/plugin install sdd-orchestrator-suite` on its own.

## Adding more later

- New plugin: add a folder under `plugins/`, add one entry to
  `.claude-plugin/marketplace.json`'s `plugins[]`, commit, push.
- New agent/skill in an existing plugin: drop the file in that plugin's `agents/` or
  `skills/` folder, commit, push. No marketplace.json change needed.
- Teammates pick up changes with `/plugin marketplace update` then `/plugin update <name>`.

## Update

```
/plugin marketplace update
/plugin update jira-dev-workflow
```
