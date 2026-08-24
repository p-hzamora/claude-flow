---
name: handoff
description: |
  Compact the current conversation into a portable handoff document: one markdown
  file, written to the OS temp directory (never the workspace), that a fresh agent
  can read to pick the work up. Use it when the work needs to travel somewhere this
  session can't reach — a different harness, a different directory/repo, a
  colleague, or a side task forked off mid-session while this session keeps going.

  Only invoke this when the user explicitly runs `/handoff` or asks to "hand off"
  the session. Never reach for this on your own — for the ordinary end-of-phase
  case (same harness, same directory, work continues here), staying in the
  session, a subagent, or /compact is the right move instead.
---

# Handoff

Compact this conversation into a single markdown handoff document a fresh agent can
read cold, without the original session open, and immediately continue from.

This is not a better `/compact`. `/compact` preserves intent and keeps you going in
this window. `/handoff` preserves the work's ability to *move* — to a new harness, a
new directory, a colleague, or a forked side task. If nothing is travelling, stop and
suggest `/compact` instead of writing a file.

## 1. Take the argument as the brief

The user passes a note about what the next session is for (e.g. "prototype whether X
approach works", "hand this to Codex to fix the failing test", "fork off: investigate
Y while I keep grilling"). That note determines what to keep. Without it, ask what the
next session needs to do before writing anything — a handoff aimed at nothing degrades
into a generic transcript dump.

## 2. Compact, don't copy

Carry forward:

- **The live thread** — what's in flight, why it's being done, what's left, and any
  open questions or blockers.
- **A suggested-skills section** — name the specific skill(s) (by name, from this
  marketplace or elsewhere) the next agent should reach for, and why.

Do **not** carry forward anything already written down elsewhere. Specs, plans, ADRs,
issues, commits, and diffs are referenced by file path or URL — never pasted in full.
If the same fact lives in two places, it will drift; the handoff document points at
the one place instead of becoming a second copy.

## 3. Say only what was verified

Flag confident-sounding claims the session never actually checked — "X isn't built",
"Y is already done", "the bug is in Z". The next agent treats this document as a
contract and will not re-verify it; an assumption written as a fact becomes a false
premise for everything downstream. Write verified facts as facts, and everything else
as "believed, not verified" or drop it.

## 4. Redact before writing

Strip any secret, token, key, or password from the document before it touches disk.
If a value looks like a credential and its presence isn't essential to the handoff,
leave it out and reference where it can be found instead (e.g. "token is in `.env`").

## 5. Write the file

- Location: the OS temp directory, never the project workspace. Use the platform
  temp dir (`$TMPDIR`/`os.tmpdir()`-equivalent — e.g. `/tmp` or `/private/tmp` on
  macOS/Linux, `%TEMP%` on Windows), not a path inside the repo.
- Format: single markdown file, one handoff per file.
- Filename: short and descriptive of the task, e.g. `handoff-<slug>.md`.

Structure the document as:

```markdown
# Handoff: <one-line title of the work>

## Why this exists
<what the next session is for — the argument passed in, expanded with any
relevant reasoning from this session>

## What's in flight
<the live thread: current state, what's been tried, what worked/didn't>

## What's next
<concrete next step(s) — the first thing the fresh agent should do>

## References
<specs/plans/ADRs/issues/commits/diffs as paths or URLs, not copied content>

## Verified vs. assumed
<anything stated as fact that was NOT independently checked this session,
called out explicitly>

## Suggested skills
<skill names the next agent should invoke, and why>
```

## 6. Hand it off

Report the full file path back to the user in plain text (not inside a shell
command). Tell them to point the fresh agent at it directly — "read this file, then
continue" — rather than pasting the summary into a command line: a summary containing
backticks or `$(...)` can get silently mangled when interpolated into something like
`claude "<summary>"`.

Remind them, if relevant:

- Temp is not durable. Some environments clear it between sessions, and `/tmp`
  doesn't survive a reboot. If the next session won't start soon, or runs under a
  different harness, copy the file somewhere durable now.
- If the handoff references other files that were also written to temp, those need
  to travel too, or the next agent can't follow the reference.

## 7. If it's a fork, not a handoff-and-leave

When the user is forking a side task while staying in this session: write the
document exactly the same way, but make clear in your reply that this session is
continuing unaffected — the fresh agent takes the fork, and its findings (once it
reports back) get referenced from here rather than re-explained.
