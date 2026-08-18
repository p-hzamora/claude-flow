---
name: git-devops-conventions
description: DevOps-mandated regex validation for branch names and commit author email used across this team's git workflow. Use before creating a branch, or whenever git identity needs validating against company policy. For the commit-message format itself, see the `commit-message-generator` skill instead.
---

# Non-negotiable regexes (this skill's scope)

These come from DevOps and are enforced elsewhere in CI. Validate against them locally, verbatim, before any git side effect (branch creation, push):

- Branch name: `(develop|test|staging|main)|((feature|bugfix|hotfix)\/[A-Z][A-Z]{1,32}-\d+([-_].*)?)`
- Commit author email: `@(stidea\.com|grupo-st\.es|stanalytics\.es|noreply\.gitlab\.com)$`

## Commit-message format lives elsewhere

The commit-message regex is **not** duplicated here. It's owned by the `commit-message-generator` skill (`plugins/skills/skills/commit-message-generator/SKILL.md`, in the base `skills` plugin) — that skill already generates titles against it and documents the pattern with a full breakdown and examples. Read/invoke it for the pattern itself; use the validation method below to check a candidate title against whatever it documents.

Putting the commit-message pattern in the `skills` plugin rather than here is deliberate: `skills` is the shared base every other plugin already depends on, so anything that isn't Jira/DevOps-specific belongs there, not duplicated into a plugin-specific skill.

## How to validate

Validate a branch name (against the branch regex above) or a commit-message title (against whatever `commit-message-generator` documents) with Python `re.fullmatch` against the exact pattern string. The commit-author-email pattern is a domain-suffix check (leading `@`, trailing `$`, no leading `.*`) and is unsatisfiable under `fullmatch` — validate it with `re.search` instead, keeping `fullmatch` for the other two. Do this via a heredoc `python3` one-liner in Bash, to avoid shell-escaping mistakes. Never hand-roll a looser check beyond this documented exception, and never normalize, truncate, or auto-correct a string that fails — report the exact regex, the exact string, and why, then stop.

## Single source of truth

Branch-name and author-email patterns live only here. `jira-dev-workflow` and `jira-git-committer` both invoke this skill for those two — if DevOps changes either, edit it here once. Because a skill is read fresh via the Skill tool on each invocation (unlike an agent's own frontmatter/body, which is snapshotted at session start), both agents pick up the change on their very next call — no session restart needed, and nothing to keep in sync by hand across agent files.
