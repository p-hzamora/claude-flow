---
name: prototype
description: |
  Build a throwaway prototype to answer a design question that can only be settled
  by looking at running code — an "unknown unknown" no amount of talking it through
  will resolve. Covers both UI prototypes (several radically different variations
  behind a floating toggle, so a human can walk the design tree and apply taste) and
  business-logic prototypes (a tiny interactive terminal app that drives a state
  machine/entity through edge cases that are hard to reason about on paper).

  Use when the user says "prototype this", "let's spike this", "build a throwaway to
  test X", "I need to see this before I decide", or when a design conversation
  (e.g. mid `grill-with-context`) hits a question that talking it through cannot
  settle. The prototype is disposable: it lives in its own directory, is never
  merged into the real codebase, and exists only to produce a decision. Pair with
  `handoff` to carry that decision back to the session that needed it.
---

# Prototype

Answer a design question with running code instead of more discussion. The
prototype itself is not the deliverable — the **decision it produces** is. Nothing
here gets merged.

## 1. Isolate it

Put the prototype in its own directory, never inside the real project tree:

- A sibling directory (`../<project>-proto-<slug>/`) or a scratch location, not a
  branch or folder inside the working repo.
- `git init` it only if the prototype itself benefits from version control (e.g.
  comparing UI variations over time). It never becomes a branch of the real repo and
  is never the target of a merge.
- Keep it minimal: whatever stack answers the question fastest, not the project's
  actual stack unless that's the variable under test.

If the user is mid-conversation elsewhere (a `grill-with-context` session that hit a
question only code can answer, or any other in-flight thread), that session keeps
running — this is a fork, not an interruption. See §5.

## 2. Frontend vs backend

The two shapes below map onto frontend and backend questions, and each has its own
reference point outside this skill:

- **Frontend** — visual/interaction questions. If the user is explicitly talking
  about frontend and the question is purely about look/feel/interaction with no
  throwaway-variation comparison needed, reach for Claude Code's native `/design`
  skill instead of this one — it's the dedicated frontend-design tool and doesn't
  need the prototype machinery below. Come back to the UI-prototype shape in §3 when
  the question specifically needs several radically different builds compared
  side by side (`/design` produces one direction at a time, not a toggleable set).
- **Backend** — business-logic, state-machine, and entity questions live in DDD
  territory. If this repo also has `python-suite` installed, ground the prototype's
  vocabulary in the `clean-ddd-hexagonal-python` skill (Entity/Value Object/Aggregate
  semantics) so the REPL models the same concepts the real implementation will use,
  and route the eventual real implementation through `ddd-entity-generator` /
  `ddd-implementer` rather than free-hand code. Without `python-suite` installed,
  proceed with the business-logic shape in §3 on its own — it doesn't require DDD.

## 3. Pick the shape: UI or business-logic

**UI prototype** — when the open question is about look, feel, or interaction, and
the answer needs a human's taste to resolve, not a spec:

- Generate several **radically different** variations, not incremental tweaks of one
  idea. If all the variations look like nudges of the same layout, throw two out and
  start further apart — the value is in covering distant regions of the design
  space, not refining one.
- Wire a floating toggle button into the page that cycles between variations without
  a reload, so the human can flip back and forth to compare.
- Present it, then walk the **design tree** with the user: which elements from which
  variation survive, which get discarded, which get combined. This is manual —
  the whole reason this is a UI prototype and not a generated mock is that the human
  applies taste the model can't see for itself. AFK/unattended agents cannot close
  this loop alone; a human has to look at it.
- Iterate the toggle set as the tree narrows, until one direction is left standing.

**Business-logic prototype** — when the open question is about a state machine,
aggregate, or entity whose behavior over time is hard to trace on paper:

- Build a small interactive terminal app (a REPL) around the entity/state machine in
  question — no framework, no persistence layer, no UI, just enough logic to
  reproduce the behavior under test.
- Give it commands that map onto the real transitions/events the entity can receive.
  After every command, print the full resulting state.
- Drive it through the specific edge cases the design conversation couldn't resolve
  by discussion: illegal transition ordering, boundary values, concurrent-looking
  event sequences, whatever was actually in question. Let the user drive it too —
  the point is to let them try inputs they're worried about, not just the ones you
  thought of.
- Stop once the ambiguous case(s) produce a clear, observed answer.

If the question spans both (a stateful UI), run the business-logic REPL first to
settle the state model, then build the UI variations on top of the settled model —
don't design UI atop a state machine that's still in question.

## 4. Extract the decision, not the code

Once the question is answered:

- Write down what was decided and why in one or two sentences — the artifact that
  matters is the decision, not the prototype's source.
- Do not copy prototype code into the real project. Reimplement the settled
  direction properly there, through the project's normal build path (its own
  agents/skills — e.g. `ddd-entity-generator`, `fastapi-endpoint-builder` — not by
  lifting throwaway code).
- Leave the prototype directory in place until the user confirms they're done with
  it; it's disposable but not yours to delete unasked.

## 5. Hand the answer back

This is the fork case `handoff` describes: use it to carry the settled decision back
to the session or directory that needed it, rather than re-explaining the whole
detour there. The handoff document should carry:

- What question sent you to the prototype in the first place.
- What was decided, and the one or two observations that settled it.
- A pointer to the prototype directory (path only — the code isn't going anywhere,
  and isn't the point).

The originating session resumes with the decision as a settled fact and doesn't
re-litigate it — same principle `grill-with-context` uses for anything already
resolved in `CONTEXT.md`/ADRs.
