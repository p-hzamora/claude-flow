---
name: obsidian-vault-conventions
description: How this team creates, reads, and updates a repository's folder or a learning topic in the shared Obsidian vault through the Obsidian MCP: where it lives, the check that Obsidian is running and the repo is set up, the creation steps, the note schema, the admission rule that keeps it small, and the retrieval protocol. Use before any read from or write to the vault.
---

# Obsidian vault conventions

One vault, `~/Documents/brain/` (override: `$BRAIN_VAULT`), holds everything. Each
repository owns one folder, `repos/<repo>/`, and other areas of know-how live in their
own top-level folders. Notes link across folders. Reach the vault only through the
Obsidian MCP (`mcp__obsidian__*`); never write the vault directory with Bash or file
tools. `<repo>` is the repository's directory name (`basename $(git rev-parse --show-toplevel)`).

## Scope of writes

The writer writes only inside `repos/<repo>/` (repo mode) or `learning/<topic>/`
(learning mode, see below). It may read anywhere, and may link to notes elsewhere
(`[[know-how/area/note|label]]`) when a search finds a real match. It never edits notes
outside those two areas.

## Reaching the vault

The Obsidian MCP serves whichever vault is open in Obsidian, and only while the app is
running. Before every read or write, call `vault_read` on `repos/<repo>/brain.config.json`:

1. If the call cannot connect, stop and tell the user: "Obsidian is not running or its
   MCP is unreachable. Start Obsidian with the vault `~/Documents/brain` open, then retry."
2. If the file is missing, stop and tell the user: "No `repos/<repo>/` setup found. Open
   `~/Documents/brain` as the vault in Obsidian; if it is already open, run the
   `vault-push-sync` skill's `on` command in the repo first."
3. If its `repo` field is not `<repo>`, stop and report the mismatch. Write nothing.

Learning mode has no repo, so the check is `vault_list` on the vault root: a connection
failure gets message 1. If the listing shows neither `repos/` nor `learning/`, ask the
user to confirm the open vault is `~/Documents/brain` before the first write.

## Setting up a repo folder

Run once per repository, in this order:

1. The user runs `vault-push-sync on` in the repo. It creates
   `~/Documents/brain/repos/<repo>/brain.config.json` (schema below).
2. The user has `~/Documents/brain` open as a vault in Obsidian. Obsidian owns
   `.obsidian/`; never write it.
3. The writer passes the check above, then creates, through the MCP,
   `repos/<repo>/index.md`: a map of content, one line per note, grouped by type.
   Type folders (`decisions/`, `gotchas/`, `runs/`, `glossary/`) appear with their first note.
4. Ask the user to confirm the structure before adding any note beyond `index.md`.

### `brain.config.json`

```json
{ "repo": "<repo>", "update_on_push": false, "last_pushed_sha": null }
```

`update_on_push` is flipped only by the `vault-push-sync` skill. The writer updates
`last_pushed_sha` after a successful run and preserves every other key.

## What belongs in the repo folder

In: decisions with rationale, non-obvious gotchas, run outcomes (one page, with links),
glossary terms.

Out: file or code descriptions, diffs, task logs, and anything the repository already
records (code, git history, `CLAUDE.md`, `CONTEXT.md`, ADRs). Test every candidate:
"could someone get this from the repo in under a minute?" If yes, reject it.

Update before create: search for an existing note on the topic and edit it in place,
setting `updated`, before creating a new one. No secrets, tokens, or personal data.

## Note schema

Every note starts with this frontmatter; the same keys everywhere keep notes searchable
across repos and ingestible by a later cross-repo index.

```yaml
---
type: decision | gotcha | run | glossary
repo: <repo>
id: <type>-<slug>
date: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [<type>, <repo>]
---
```

| type | folder under `repos/<repo>/` | body headings |
|---|---|---|
| `decision` | `decisions/` | Decision, Rationale, Consequences, Alternatives rejected |
| `gotcha` | `gotchas/` | Symptom, Cause, Fix or workaround |
| `run` | `runs/` | Outcome, Delivered, Remaining work (one page, links to decisions) |
| `glossary` | `glossary/` | Definition, Avoid |

File name is `<slug>.md` (letters, digits, `-`). Link notes with the full vault path,
`[[repos/<repo>/decisions/slug|label]]`, so links resolve from any folder.
Add or update one line in `repos/<repo>/index.md` for every note created.
Write `Not recorded` where a heading has no source; never fill gaps.

## Learning notes

Written by the `learn` skill through `vault-writer`, into `learning/<topic>/`
(`<topic>` is a slug: letters, digits, `-`). One topic is self-contained so a skill can
later be generated from it: `index.md` plus one note per concept, `<slug>.md`.

```yaml
---
type: learning
topic: <topic>
id: learning-<topic>-<slug>
status: draft | done
sources: [<url>, ...]
date: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [learning, <topic>]
---
```

`index.md` has the same keys (`id: learning-<topic>`), a two-line summary, and one
`[[learning/<topic>/<slug>|label]]` line per concept. New notes are `draft`; set `done`
only when the user says the topic is finished. Concept notes use the headings
Explanation, Example, Pitfalls, Sources.

Admission rule for learning notes: the user's understanding in distilled, own words,
with every claim traceable to a cited source. Reject raw page copies, long quotes,
and anything the user did not take part in settling. Update an existing concept note in
place before creating one. No `repo` key and no `brain.config.json`.

## Retrieval protocol

1. Run the check above, then `search_simple` with the topic terms. Search the whole
   vault: related know-how outside `repos/<repo>/` counts.
2. Read `repos/<repo>/index.md` only if search is empty or too broad.
3. Use `vault_get_document_map` and read only the relevant sections of matching notes.
4. Return a distilled answer with the note paths as citations, never raw note bodies.
   If nothing matches, say `Not recorded` instead of guessing.

## Safety

Never call `vault_delete`, `vault_move`, `vault_copy`, or `command_execute`. Do not
write outside `repos/<repo>/` or `learning/<topic>/`.

## Review Checklist

- [ ] The check passed before any read or write, or the user was told what to start or open.
- [ ] Every note written passes the admission rule and has the full frontmatter.
- [ ] An existing note was updated instead of duplicated when one covered the topic.
- [ ] `repos/<repo>/index.md` lists every note created.
- [ ] Learning notes cite sources, are in the user's distilled words, and sit in `learning/<topic>/` with `index.md` updated.
- [ ] No secrets, no deletes, no writes outside `repos/<repo>/` or `learning/<topic>/`.
