# claude-flow

Private multi-host plugin marketplace: `skills` (cross-cutting), `python-suite`
(Python/DDD/FastAPI/SQLAlchemy), `jira-dev-workflow` (end-to-end Jira ticket workflow).
Claude Code and Codex share the plugin directories; reusable behavior belongs in
`skills/`, while host-specific manifests live beside each other.
Domain vocabulary — what "Plugin", "Agent", "Skill" mean here, and resolved naming
ambiguities — lives in [`CONTEXT.md`](./CONTEXT.md). Read it before naming a new concept
or introducing a new structural term.

## Repo shape

```
plugins/<name>/
  .claude-plugin/plugin.json   # this plugin's own metadata + version
  .codex-plugin/plugin.json    # Codex metadata + the shared skills entry point
  agents/*.md                  # Claude Code subagent definitions (persona, tools, model)
  skills/<name>/SKILL.md       # instructions loaded into the calling thread, no persona
  scripts/*.sh                 # plain executables invoked via Bash, referenced by agents/skills as ${CLAUDE_PLUGIN_ROOT}/scripts/<name>, never a bare relative path
.codex/agents/*.toml           # Codex-native, project-scoped role adapters; refer to shared skills, never copy them
.agents/plugins/marketplace.json # Codex marketplace catalog for the plugin folders
.claude-plugin/marketplace.json  # shared/legacy-compatible marketplace catalog
docs/<plugin>.md                 # human-facing reference per plugin, tables of contents
README.md                        # top-level overview, dependency graph, install commands
```

## When you touch a plugin, update all of these in the same commit

**Add or change an agent/skill inside an existing plugin** (no new plugin):

1. Bump that plugin's `version` in its own `plugins/<name>/.claude-plugin/plugin.json`
   — patch for a fix, minor for a new agent/skill, major for a breaking rename/removal.
2. Mirror the same version in `plugins/<name>/.codex-plugin/plugin.json` and in
   `.claude-plugin/marketplace.json`'s matching `plugins[]` entry. These must never
   drift.
3. Add/update the row in `docs/<plugin>.md`'s Agents or Skills table, and its
   `**Version:**` line.
4. Add/update the bullet in the root `README.md`'s plugin list.
5. Run `claude plugin validate . --strict` before committing.

**Add a brand-new plugin folder:**

- Everything above, plus one new entry in `.claude-plugin/marketplace.json`'s
  `plugins[]` and a new `docs/<plugin>.md` page.

The Codex manifest must point at the same `skills/` directory. Do not make a second
copy of a skill just to change its host or model name. Codex uses the model selected
by the user; plugin manifests do not select an OpenAI model. Codex custom-agent
configuration is project-scoped (`.codex/agents/*.toml`), rather than a plugin-manifest
component. Keep those adapters thin: select the role and relevant shared skills, but
do not duplicate the Claude agent body or a skill's procedure.

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

## Skill completion checklists

Every shared skill ends with a `## Review Checklist`. When a task uses a skill, treat
that checklist as a completion gate: before reporting the task complete, verify every
item that applies to the work. Record an item as not applicable only with a concrete
reason. If an applicable item fails or cannot be verified, continue the work or report
the task as incomplete/blocked; do not claim completion.

The checklist complements the user's request and repository instructions. It does not
authorize extra scope, external mutations, or a second review of unrelated work.

## Git worktree ownership

All Git worktree lifecycle operations MUST be delegated to `git-worktree-expert`.
Do not directly create, remove, prune, relocate, or otherwise manage Git worktrees
when `git-worktree-expert` is available.

### Agent delegation architecture

`git-worktree-expert` is the sole lifecycle owner. It uses the
`git-worktree-management` skill as its authoritative procedure; development agents
must send a `WORKTREE_REQUEST` and act only after receiving `WORKTREE_RESULT`.

```text
Development Agent
      │
      │ WORKTREE_REQUEST
      ▼
git-worktree-expert
      │
      │ uses
      ▼
git-worktree-management skill
      │
      ▼
Git worktree
      │
      │ WORKTREE_RESULT
      ▼
Development Agent
```

When isolated work is required:

1. Ask `git-worktree-expert` for a worktree.
2. Provide the desired branch/task and base ref when known.
3. Wait for its `WORKTREE_RESULT`.
4. Perform the development task inside the returned `path`.
5. Delegate worktree cleanup back to `git-worktree-expert` when needed.

Normal Git operations within the assigned worktree remain the responsibility of the
current development agent.

## Non-negotiable regexes

Enforced by DevOps in CI, used across `jira-dev-workflow`. Two owners:

- Branch name + commit author email — `git-devops-conventions` skill
  (`plugins/jira-dev-workflow/skills/git-devops-conventions/SKILL.md`).
- Commit message — `commit-message-generator` skill
  (`plugins/skills/skills/commit-message-generator/SKILL.md`, base `skills` plugin).

Don't inline a copy of either anywhere else — point at the owning skill.
