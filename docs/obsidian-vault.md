# obsidian-vault

One shared Obsidian vault with a folder per repository (`repos/<repo>/`), reached only
through the Obsidian MCP. Other know-how areas live in their own top-level folders and
link freely with the repo folders.

**Version:** 0.1.0
**Dependencies:** none (the user configures the Obsidian MCP server; it is not bundled)

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the skills are packaged through `../plugins/obsidian-vault/.codex-plugin/plugin.json`
and the role adapters live in [`../.codex/agents/`](../.codex/agents/). The push hook is
Claude Code only.

## Agents

| Agent | Responsibility | Codex routing phrases |
|---|---|---|
| `vault-writer` | The only writer of the vault: `repos/<repo>/` (repo mode) and `learning/<topic>/` (learning mode). Applies the admission rule, updates a note before creating one, keeps `index.md` current, and reports when Obsidian is not running. Uses `obsidian-vault-conventions`. | `update the vault`; `record project context` |
| `vault-reader` | Read-only lookup. Returns a distilled answer with note paths instead of raw notes. | `look up vault context`; `recall project knowledge` |

## Skills

| Skill | Path |
|---|---|
| `obsidian-vault-conventions` | `skills/obsidian-vault-conventions/SKILL.md`: vault location, reachability check, repo setup steps, note schema, admission rule, retrieval protocol. |
| `vault-push-sync` | `skills/vault-push-sync/SKILL.md`: user-invoked on/off/status for the push hook in the current repo. |
| `learn` | `skills/learn/SKILL.md`: user-invoked `/learn <topic>`. Researches and teaches a topic, then at each settled concept saves approved own-words notes to `learning/<topic>/` through `vault-writer`. Checks Obsidian before researching; falls back to chat-only notes if it stays down. |

## Hook and script

| Component | Path |
|---|---|
| `PostToolUse` hook | `hooks/hooks.json`: matches `Bash(git push *)` and runs `scripts/vault-push-sync.py hook`. |
| `vault-push-sync.py` | `scripts/vault-push-sync.py`: the hook body plus `on`/`off`/`status`. |

The hook is inert unless `repos/<repo>/brain.config.json` has `update_on_push: true`
(enable with `vault-push-sync on`). When enabled and Obsidian's MCP port is closed, it tells
the user to start Obsidian and queues nothing; when open, it asks the main thread to
delegate to `vault-writer` with the commit range since `last_pushed_sha`. It only sees
pushes made through Claude's Bash tool. Hooks cannot launch agents, so delegation is a
request to the main thread, not a guarantee.

## Vault location

`$BRAIN_VAULT`, default `~/Documents/brain/`, must be the vault open in Obsidian (the MCP
serves only the open vault). Each repo owns `repos/<repo>/`; `vault-writer` writes only
there, and reads or links to notes anywhere in the vault. Agents read
`repos/<repo>/brain.config.json` first and stop with a clear message if Obsidian is not
running or the repo is not set up.
