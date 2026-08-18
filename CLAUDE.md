# claude-flow

Private Claude Code plugin marketplace: `skills` (cross-cutting), `python-suite`
(Python/DDD/FastAPI/SQLAlchemy), `jira-dev-workflow` (end-to-end Jira ticket workflow).
Domain vocabulary — what "Plugin", "Agent", "Skill" mean here, and resolved naming
ambiguities — lives in [`CONTEXT.md`](./CONTEXT.md). Read it before naming a new concept
or introducing a new structural term.

## Repo shape

```
plugins/<name>/
  .claude-plugin/plugin.json   # this plugin's own metadata + version
  agents/*.md                  # full subagent definitions (persona, tools, model)
  skills/<name>/SKILL.md       # instructions loaded into the calling thread, no persona
.claude-plugin/marketplace.json  # lists every plugin + mirrors each plugin's version
docs/<plugin>.md                 # human-facing reference per plugin, tables of contents
README.md                        # top-level overview, dependency graph, install commands
```

## When you touch a plugin, update all of these in the same commit

**Add or change an agent/skill inside an existing plugin** (no new plugin):

1. Bump that plugin's `version` in its own `plugins/<name>/.claude-plugin/plugin.json`
   — patch for a fix, minor for a new agent/skill, major for a breaking rename/removal.
2. Mirror the same version in `.claude-plugin/marketplace.json`'s matching `plugins[]`
   entry. The two must never drift.
3. Add/update the row in `docs/<plugin>.md`'s Agents or Skills table, and its
   `**Version:**` line.
4. Add/update the bullet in the root `README.md`'s plugin list.
5. Run `claude plugin validate . --strict` before committing.

**Add a brand-new plugin folder:**

- Everything above, plus one new entry in `.claude-plugin/marketplace.json`'s
  `plugins[]` and a new `docs/<plugin>.md` page.

**Extract knowledge shared by two or more agents into a skill** (the pattern
`git-devops-conventions` and `atlassian-jira-mcp` follow inside `jira-dev-workflow`):

- Put it in that plugin's `skills/<name>/SKILL.md`, have every consuming agent point at
  it by name instead of restating it — a skill is read fresh via the Skill tool on each
  invocation, so there's nothing to keep manually in sync across agent files the way
  duplicated inline text needs.
- If you find the same paragraph copy-pasted across two agent `.md` files, that's the
  signal to extract, not a thing to keep synced by hand.
- **Before extracting, `grep -r` the exact string across the whole repo, not just the
  plugin you're editing.** A pattern duplicated inside one plugin may already have a
  canonical home in another (e.g. the commit-message regex was duplicated in
  `jira-dev-workflow` *and* separately owned by `commit-message-generator` in the base
  `skills` plugin — a plugin-local extraction would have created a third copy instead of
  fixing the drift). If a canonical source already exists elsewhere, point at it instead
  of creating a new one — prefer the `skills` plugin as the owner when the knowledge
  isn't actually specific to the plugin you're in.

## Publishing / picking up changes

```
/plugin marketplace update
/plugin update <name>
```

No separate build step. A version bump only matters for humans reading `docs/`/README —
Claude Code re-reads plugin files from the marketplace source on update regardless.

## Non-negotiable regexes

Enforced by DevOps in CI, used across `jira-dev-workflow`. Two owners:

- Branch name + commit author email — `git-devops-conventions` skill
  (`plugins/jira-dev-workflow/skills/git-devops-conventions/SKILL.md`).
- Commit message — `commit-message-generator` skill
  (`plugins/skills/skills/commit-message-generator/SKILL.md`, base `skills` plugin).

Don't inline a copy of either anywhere else — point at the owning skill.
