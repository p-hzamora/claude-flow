# jira-dev-workflow

End-to-end Jira ticket workflow: read ticket via Atlassian MCP, create compliant git
branch, scope with `/grill-with-context`, hand off to `sdd-python-orchestrator`, commit/push via
`jira-git-committer`, close out in Jira. Also ships `jira-tech-lead-reviewer` for
read-only branch review.

**Version:** 0.3.2
**Dependencies:** `skills`, `python-suite` (both auto-enabled on install)

## Agents

| Agent | Path |
|---|---|
| `jira-dev-workflow` | `agents/jira-dev-workflow.md` |
| `jira-git-committer` | `agents/jira-git-committer.md` |
| `jira-tech-lead-reviewer` | `agents/jira-tech-lead-reviewer.md` — read-only branch review for tech leads: resolves the ticket from the branch name, delegates DDD/SOLID/CQRS compliance to `ddd-reviewer` (and `fastapi-reviewer` when the API layer changed), checks lint (`ruff check .` only, never `format`/`--fix`) and tests, then reconciles the diff against the Jira ticket — any code-vs-ticket discrepancy is asked back to the user, never assumed |

## Skills

| Skill | Path |
|---|---|
| `git-devops-conventions` | `skills/git-devops-conventions/SKILL.md` |
| `atlassian-jira-mcp` | `skills/atlassian-jira-mcp/SKILL.md` |

## Scripts

| Script | Path |
|---|---|
| `md2pdf.sh` | `scripts/md2pdf.sh` — converts a Markdown file to PDF via `pandoc`+`weasyprint` (self-installs both on first run). Mandatory in `jira-dev-workflow`'s Phase 6 for the ticket summary PDF — the agent must call it via `${CLAUDE_PLUGIN_ROOT}/scripts/md2pdf.sh <in>.md <out>.pdf`, never a hand-rolled `pandoc`/`weasyprint`/`wkhtmltopdf`/`cupsfilter` invocation in its place. The source `.md` must follow the C4 model structure (Context/Container/Component/Code sections, text only — no diagrams) mandated in Phase 6 of `agents/jira-dev-workflow.md`. |

Both agents above invoke these — the branch-name/author-email regexes and Atlassian MCP
gotchas live here once, not duplicated per agent. The commit-message regex is **not**
one of them: it's owned by `commit-message-generator` in the base `skills` plugin
(`plugins/skills/skills/commit-message-generator/SKILL.md`), which `jira-git-committer`
already invokes to generate titles — `git-devops-conventions` deliberately doesn't carry
a second copy of that pattern.

## Requires

- Atlassian MCP server, configured and authenticated by each user. Not bundled by this
  marketplace — see root [README](../README.md#not-bundled).

## Install

```
/plugin install jira-dev-workflow
```
