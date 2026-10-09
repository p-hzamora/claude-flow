---
name: learn
description: Research a topic, teach it to the user step by step, and at each settled concept save own-words notes to learning/<topic>/ in the Obsidian vault so they can become skills later. User-invoked with /learn <topic>.
---

# Learn

Teach the user one topic in depth and keep what they settle in the vault. The topic
comes from the command argument; if it is missing, ask for it. Derive `<topic>`, a slug
of letters, digits, and `-`.

## Procedure

1. **Check the vault first, before any research.** Delegate to `vault-reader` with the
   topic and no repository. It checks that Obsidian is reachable and returns what the
   vault already holds under `learning/<topic>/` and elsewhere.
   - If it reports Obsidian is down, tell the user to start Obsidian with
     `~/Documents/brain` open and wait for their reply. Write no drafts while waiting.
     Re-run the reader once when they say it is up.
   - If it still fails after that retry, or the user says to go on without it, run the
     rest in **chat-only mode**: teach as usual, and at each checkpoint present the
     notes in the conversation instead of writing the vault. Do not retry again unless asked.
2. **Research.** Use WebSearch and WebFetch. Prefer official docs and primary sources.
   Keep each source's URL and the date read. Never paste pages into the vault.
3. **Teach one concept at a time.** Short explanation, a runnable or concrete example,
   and the common pitfalls. Ask a question to check understanding, and adapt to the
   answers. Build on existing vault notes instead of repeating them.
4. **Checkpoint when a concept is settled** (the user confirms they understand it or
   says to move on). List the notes you propose, one line each with its path under
   `learning/<topic>/`, and ask for approval. On approval, delegate to `vault-writer`
   with `mode: learning`, the `topic`, and for each note its slug, a body in the user's
   words with the headings Explanation, Example, Pitfalls, Sources, and its sources.
   Relay the writer's `created|updated` lines. In chat-only mode, show the same notes in
   chat instead.
5. **Finish.** When the user says the topic is done, offer any unsaved concepts as a last
   checkpoint, then ask whether to set the topic's `status` to `done`.

## Rules

- Notes follow the "Learning notes" section of `obsidian-vault-conventions`; do not
  restate its schema or admission rule here.
- Own words with cited sources; no raw page dumps or long quotes. Write `Not recorded`
  rather than filling a gap.
- Nothing is written to the vault without the user's approval at a checkpoint.
- Keep notes terse. Every token written is one the user reads and pays for.

## Review Checklist

- [ ] The vault was checked before research, and Obsidian-down was handled as specified.
- [ ] Every note was approved at a checkpoint before being written.
- [ ] Every note cites sources and is in the user's distilled words.
- [ ] `learning/<topic>/index.md` lists every concept note.
- [ ] Chat-only mode was entered only after a failed retry or the user's say-so.
