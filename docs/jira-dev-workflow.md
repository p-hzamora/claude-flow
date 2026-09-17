# jira-dev-workflow

End-to-end Jira ticket workflow: read ticket via Atlassian MCP, create compliant git
branch, scope with `/grill-with-context`, hand off to `sdd-python-orchestrator`, commit/push via
`jira-git-committer`, close out in Jira. Also ships `jira-tech-lead-reviewer` for
read-only branch review.

**Language:** all Jira-bound content (new issue/subtask title+description, the Phase 6
summary.md/PDF, Jira comments) is written in plain Spanish for the Spanish-speaking Jira
team. Everything else — chat with the user, halt/failure reports, task labels — stays in
English.

**Version:** 0.6.0
**Dependencies:** `skills`, `python-suite`, `latex-tools` (all auto-enabled on install)

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the Jira and Git guidance skills are packaged through
`../plugins/jira-dev-workflow/.codex-plugin/plugin.json` and reuse the same files.
Matching project-scoped Codex profiles live in
[`../.codex/agents/`](../.codex/agents/) and rely on those skills rather than a
second workflow copy. Codex users still need a compatible, authenticated Atlassian MCP
connection for live Jira actions; see [`../.codex/README.md`](../.codex/README.md)
for profile setup in another project.

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

Both agents above invoke these — the branch-name/author-email regexes and Atlassian MCP
gotchas live here once, not duplicated per agent. The commit-message regex is **not**
one of them: it's owned by `commit-message-generator` in the base `skills` plugin
(`plugins/skills/skills/commit-message-generator/SKILL.md`), which `jira-git-committer`
already invokes to generate titles — `git-devops-conventions` deliberately doesn't carry
a second copy of that pattern.

Phase 6 writes the C4-structured Spanish Markdown summary as its canonical editorial
source, then delegates to `latex-tools`: `markdown-to-latex-author` turns it into an
organized root `.tex` document with the approved bundled report template, and
`latex-2-pdf-exporter` produces the verified PDF attached to Jira.

## Requires

- Atlassian MCP server, configured and authenticated by each user. Not bundled by this
  marketplace — see root [README](../README.md#not-bundled).

## Install

```
/plugin install jira-dev-workflow
```
