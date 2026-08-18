# jira-dev-workflow

End-to-end Jira ticket workflow: read ticket via Atlassian MCP, create compliant git
branch, scope with `/grill-me`, hand off to `sdd-python-orchestrator`, commit/push via
`jira-git-committer`, close out in Jira.

**Version:** 0.1.0
**Dependencies:** `skills`, `python-suite` (both auto-enabled on install)

## Agents

| Agent | Path |
|---|---|
| `jira-dev-workflow` | `agents/jira-dev-workflow.md` |
| `jira-git-committer` | `agents/jira-git-committer.md` |

## Requires

- Atlassian MCP server, configured and authenticated by each user. Not bundled by this
  marketplace — see root [README](../README.md#not-bundled).

## Install

```
/plugin install jira-dev-workflow
```
