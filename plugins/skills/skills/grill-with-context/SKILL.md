---
name: grill-with-context
description: Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree — grounded in the target repo's existing domain glossary and ADRs so the session never re-litigates settled ground. Use when the user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
---

# Grill With Context

Interview the user relentlessly about a plan or design until you reach a shared understanding. Map it as a **design tree**: every decision branches into the decisions that hang off it.

## Ground in existing context first

Before asking anything, check the target repo for prior state (soft dependency — proceed normally if none of this exists):

- root `CONTEXT.md`, or `CONTEXT-MAP.md` plus the per-context `CONTEXT.md`s it points to — the domain glossary already settled
- `docs/adr/` (root, or per-context alongside a `CONTEXT-MAP.md`) — architecture decisions already made

Read whatever is there before building the tree. Any frontier question already answered by the glossary or an ADR is pre-settled — cite it instead of asking it again ("your `CONTEXT.md` defines Order as X, using that"). If the discussion uses a term that conflicts with the glossary, surface the conflict as a question rather than silently picking a side. This is what keeps the session from starting stateless every time it runs in the same repo — later sessions build on earlier ones instead of re-deriving them.

## Work the tree in rounds

The **frontier** is every decision whose prerequisites are already settled: the questions you can ask *now* without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format each question:

```
❓ **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

➡️ <your recommended answer>
```

Each round's answers reshape the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a *later* round, not this one.

Finding *facts* is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, code, tools), dispatch a sub-agent to find it — don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait; ask the rest of the frontier now. The *decisions* are the user's — put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you've reached a shared understanding.

## Capture decisions as you go

As a term or decision resolves mid-session, record it immediately — don't batch this to the end.

**Glossary terms** go in `CONTEXT.md` (the right context's, if a `CONTEXT-MAP.md` is in play). Use the structure in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md). Create the file lazily — only once the first term resolves. `CONTEXT.md` is a glossary, never a spec or an implementation scratchpad.

**Architecture decisions** go in `docs/adr/NNNN-slug.md`, but only when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder why it was done this way
3. **The result of a real trade-off** — genuine alternatives existed and one was picked for specific reasons

Skip the ADR if any of the three is missing — most resolved questions don't warrant one. Use the structure in [ADR-FORMAT.md](./ADR-FORMAT.md). Create `docs/adr/` lazily — only once the first ADR is needed.
