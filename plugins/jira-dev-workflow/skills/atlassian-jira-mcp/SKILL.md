---
name: atlassian-jira-mcp
description: Operational knowledge for working with this team's Atlassian Jira via the Atlassian MCP server — site disambiguation, credentials, the no-attachment-tool REST fallback, ADF description format, and other gotchas. Use whenever reading, writing, transitioning, commenting on, attaching to, or creating a Jira issue.
---

# Site disambiguation

`mcp__atlassian__getAccessibleAtlassianResources` can return more than one accessible site. Use the one matching this team's real tracker (`stidea-atlantis.atlassian.net`). A near-empty `eva-project.atlassian.net` decoy sandbox can also appear and will 404 every real ticket with a "does not exist or you do not have permission" error that reads like a permissions problem. Never pick by name similarity to the project key — pick the real tracker explicitly.

# Credentials

Two separate things, both required, neither substitutable for the other:

- **Atlassian MCP session** — established externally, before the session starts; verified with `getAccessibleAtlassianResources`. If it errors or returns no site, the MCP connection needs (re)authenticating — this is not an env var problem.
- **`JIRA_EMAIL` + `JIRA_API_TOKEN`** — plain environment variables, needed because the Atlassian MCP server has **no attachment/upload tool**. Confirm both with `[ -n "$JIRA_EMAIL" ] && [ -n "$JIRA_API_TOKEN" ]`. If either is missing, report which one by exact name — never invent alternate variable names — and note they may need sourcing from the user's shell profile before the session was launched (an `export` typed in a different terminal never reaches an already-running session).

# Attaching a file (no MCP tool exists for this)

Raw REST call with basic auth:

```
curl -sS -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "X-Atlassian-Token: no-check" -F "file=@<path>" "<baseUrl>/rest/api/3/issue/<KEY>/attachments"
```

Resolve `<baseUrl>` via `mcp__atlassian__getAccessibleAtlassianResources`. **Never** ask the user to paste the token into chat, and never echo its value in command output or logs — pipe anything that might contain it through `sed -E 's/[A-Za-z0-9_-]{60,}/[REDACTED]/g'` before displaying (the token itself is ~192 chars). Non-2xx response: report the raw status/body, don't retry blindly.

# Creating an issue or subtask (no MCP tool exists for this either)

- Raw REST: `POST /rest/api/3/issue`, same basic-auth credentials as attachment, `Content-Type: application/json`.
- Discover current issue-type ids first — they differ per project and can change: `curl -sS -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "<baseUrl>/rest/api/3/issue/createmeta/<PROJECT>/issuetypes"`.
- The `description` field must be **ADF** (Atlassian Document Format) JSON, not a plain string — a string returns HTTP 400. Build the payload in a small Python script written to the scratchpad and post with `curl --data @payload.json`, rather than inlining JSON in the shell, to avoid quoting/escaping breakage.
- **Subtask parent trap**: a subtask's `parent` field points at its parent task/story (level 0). That same `parent` field on a level-0 issue instead points at its **Epic**. Don't confuse the two when asked to file "a subtask under X".
- **Verification**: never trust the POST response alone — re-read the created issue with `getJiraIssue` and confirm `issuetype.subtask`, `parent.key`, and the project before reporting the key back. A newly created subtask can land in a non-obvious initial status (e.g. Backlog rather than To Do) — report the actual status, don't assume.

# Transitions

Never guess a transition id. Call `mcp__atlassian__getTransitionsForJiraIssue` first, find the transition matching what you need (e.g. an "In Progress"-equivalent or "Done"-equivalent) from what's actually returned, then call `mcp__atlassian__transitionJiraIssue`. If the transition you need isn't in the list, stop and ask — list the exact transitions available.

# Comments

`mcp__atlassian__addCommentToJiraIssue`'s `contentFormat` defaults to markdown and will convert `*bold*` to `_italic_` and mangle nested `**bullets**` into literal `\*\*` — use only flat, single-level `*` bullets. To fix a wrong comment, pass `commentId` to the same tool rather than posting a second comment.

## Review Checklist

- [ ] The real tracker site was selected explicitly, not inferred from a similar name.
- [ ] The target issue, project, and requested operation were verified before mutation.
- [ ] Credentials, tokens, and REST output were handled without exposing secrets.
- [ ] Every create, transition, attachment, or comment mutation was re-read or otherwise verified.
