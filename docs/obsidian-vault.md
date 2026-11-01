# obsidian-vault

One shared Obsidian vault with a folder per repository (`repos/<repo>/`), reached only
through the Obsidian MCP. Other know-how areas live in their own top-level folders and
link freely with the repo folders.

**Version:** 1.0.0
**Dependencies:** none (the user configures the Obsidian MCP server; it is not bundled)

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the skills are packaged through `../plugins/obsidian-vault/.codex-plugin/plugin.json`
and the role adapters live in [`../.codex/agents/`](../.codex/agents/).

**Automatic capture** (notes written after commits, without asking) is not part of this
plugin since 1.0.0: the `git push` hook and `vault-push-sync` skill were removed. Use
[noesis](https://github.com/p-hzamora/noesis) (`noesis capture on`) instead; it writes into
the same vault.

## Agents

| Agent | Responsibility | Codex routing phrases |
|---|---|---|
| `vault-writer` | The only writer of the vault: `repos/<repo>/` (repo mode) and `learning/<topic>/` (learning mode). Applies the admission rule, updates a note before creating one, keeps `index.md` current, and reports when Obsidian is not running. Uses `obsidian-vault-conventions`. | `update the vault`; `record project context` |
| `vault-reader` | Read-only lookup. Returns a distilled answer with note paths instead of raw notes. | `look up vault context`; `recall project knowledge` |

## Skills

| Skill | Path |
|---|---|
| `obsidian-vault-conventions` | `skills/obsidian-vault-conventions/SKILL.md`: vault location, reachability check, repo setup steps, note schema, admission rule, retrieval protocol. |
| `learn` | `skills/learn/SKILL.md`: user-invoked `/learn <topic>`. Researches and teaches a topic, then at each settled concept saves approved own-words notes to `learning/<topic>/` through `vault-writer`. Checks Obsidian before researching; falls back to chat-only notes if it stays down. |

## Vault location

`$BRAIN_VAULT`, default `~/brain/`, must be the vault open in Obsidian (the MCP
serves only the open vault). Each repo owns `repos/<repo>/`; `vault-writer` writes only
there, and reads or links to notes anywhere in the vault. Agents read
`repos/<repo>/brain.config.json` first and stop with a clear message if Obsidian is not
running or the repo is not set up; on first use, `vault-writer` creates that file and
`index.md` after the user confirms.
