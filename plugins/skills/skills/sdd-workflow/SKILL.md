---
name: sdd-workflow
description: Stack-agnostic Spec-Driven Development orchestration methodology - specification analysis, phase sequence, agent coordination, quality gates, escalation, plus simplicity/surgical-change discipline. Any stack-specific SDD orchestrator (sdd-python-orchestrator, sdd-docker-orchestrator, ...) invokes this first for the process, then applies its own stack context on top. Use when coordinating a multi-agent implementation workflow from a specification.
---

# SDD Workflow (stack-agnostic)

The process any Spec-Driven Development orchestrator follows, regardless of target
stack. A stack-specific orchestrator agent invokes this skill for *how to run the
workflow*, then layers its own frontmatter (language, architecture, tooling
conventions) on top for *what the stack requires*.

## Core discipline (apply through every phase)

- **Think before coding.** State assumptions explicitly. If the spec has multiple
  valid interpretations, present them - don't pick silently. If something is
  unclear, stop and ask rather than guessing forward.
- **Simplicity first.** Minimum implementation that satisfies the spec. No
  speculative abstractions, no configurability nobody asked for, no error handling
  for scenarios the spec doesn't describe. If a downstream agent's diff could be
  half the size and still meet the spec, say so before accepting its output.
- **Surgical changes.** Downstream agents should touch only what the spec
  requires. Treat "also refactored X while I was in there" in an implementation
  report as scope creep to flag, not something to accept silently.
- **Goal-driven execution.** Every phase needs a verifiable success criterion, not
  a vague one - "add validation" becomes "write tests for invalid inputs, then
  make them pass." Loop on a phase until its criterion is actually met; don't
  advance on an assumption.

## Specification analysis

- Identify functional and non-functional requirements.
- Detect ambiguities, gaps, or conflicts - flag them for clarification before
  implementation starts; never fill a gap with a silent assumption.
- Classify requirements by complexity, dependencies, and testing needs.
- Extract acceptance criteria and edge cases explicitly.
- Map requirements to implementation domains (API, database, security, testing,
  etc.) - the stack-specific agent applies its own layer mapping on top of this.

## Phase sequence

1. **Specification refinement** - validate and tighten the spec; loop back here
   if a later phase surfaces a gap.
2. **Test design** - tests come from the specification, before implementation
   (tests-first within SDD, not tests-after-code).
3. **Code generation** - implementation follows validated specs and tests; code
   never drives the spec, the spec drives the code.
4. **Validation** - run generated tests, verify spec compliance.
5. **Integration** - confirm new code integrates with existing architecture.
6. **User review and closeout** - present the verified implementation for the
   user's review; commit and release its worktree only after explicit approval.

Feedback loops are not failures: if tests fail or a spec gap emerges mid-phase,
route back to refinement rather than patching around it.

## Agent coordination

- Give each invoked agent complete context: the relevant spec slice, current
  workflow state, prior results, and a specific, bounded task.
- Define a clear, checkable success criterion per agent before invoking it.
- Track workflow state explicitly: what's analyzed/tested/implemented,
  dependencies between tasks, blockers, which agents ran and what they returned.
- One agent's output becomes the next agent's input - make handoffs explicit,
  don't let an agent re-derive context it should have been given.
- Detect conflicts (e.g. test requirements vs. implementation constraints) and
  resolve them at the orchestration level, not by letting one agent silently
  override another's contract.

### Mandatory worktree isolation

Every planning run that will change source code, tests, configuration, or other
versioned artifacts owns one isolated Git worktree. Treat a planning run as one
bounded implementation task: do not assign two independently implemented tasks
to the same run or worktree. Parallel work requires a separate `{root}/{id}/`
planning record and a separate worktree for each task.

Before delegating the first source-changing task, send a `WORKTREE_REQUEST` to
the `git-worktree-expert` agent and wait for a successful `WORKTREE_RESULT`.
`git-worktree-expert` is the sole owner of inspection, branch assignment,
creation, removal, and pruning; the SDD orchestrator never performs lifecycle
commands itself. Follow the request contract in
[`git-worktree-management`](../git-worktree-management/SKILL.md#delegation-request-contract).

Bind the two records with the planning folder name:

- `planning_id` is exactly `{id}` and `planning_path` is the absolute
  `{root}/{id}` path.
- Request an explicit worktree directory ending in `{id}`, normally
  `<repo-parent>/<repo-name>-wt/{id}`. The worktree remains outside the planning
  folder: the latter is the audit record, not a source checkout.
- Supply the task's approved branch and, for a new branch, its explicit base
  ref. A planning id is not a license to guess branch or history.
- Persist the returned absolute `path`, `branch`, and `base_ref` in `state.json`.
  Do not send implementation agents to any other checkout.

If the worktree request is blocked or fails, set the run to `blocked` with the
reported reason and do not start source-changing work on a shared checkout.

At closeout, keep the run in `reviewing` until the user has checked the
implementation and explicitly approves a commit. Then invoke
`commit-message-generator` to propose the staged-file grouping and title(s),
obtain the required review of those proposals, commit within the assigned
worktree, and delegate removal to `git-worktree-expert`. Removal is ordinary,
non-force cleanup only after the expert reports the worktree clean. Do not
delete the branch unless the user separately requests it. Mark the run `done`
only after the commit and worktree removal both succeed; otherwise retain the
exact pending cleanup reason in `state.json`.

## Quality gates (before advancing a phase)

- Spec is unambiguous and complete for the current scope.
- Every acceptance criterion is testable.
- Test coverage aligns with spec requirements - no more, no less.
- Generated code passes all tests.
- Integration points are documented and verified, not assumed.
- The user has explicitly approved commit/cleanup, and the associated worktree
  has been safely released before a run is marked `done`.

## Communication style

- State clearly what's being orchestrated and why.
- Explain phase dependencies ("tests before code, because they validate spec
  interpretation").
- Flag uncertainties or ambiguities that need human input - don't bury them in a
  wall of status text.
- Present workflow state in digestible, structured chunks.

## Escalation

- Spec too vague for agents to work effectively -> halt, request clarification.
  Don't invoke implementation agents on a guess.
- Generated code conflicts with existing architecture -> route through an
  integration-verification step, then back to refinement.
- Tests fail on a spec-interpretation disagreement -> propose a spec amendment,
  don't silently reinterpret the spec to make tests pass.
- Task falls outside any available agent's capability -> escalate to the human
  with exact context, don't attempt it improvised.

## State tracking & persistence

Every workflow run is identified by a single id (a ticket key, feature slug, or
other caller-supplied identifier) and gets one folder, not scattered files:

```
{root}/{id}/
  request.md     - the original request/spec as given, captured verbatim (or a
                    faithful summary) before any refinement - so a later resume
                    or audit can see what was actually asked, not just what got
                    built
  specs/         - the refined SDD specs derived from the request (one file per
                    concern is fine - api, data-model, etc.)
  summary.md     - written only once the workflow reaches a terminal state
                    (done or blocked) - what was implemented, key decisions,
                    outcome
  state.json     - machine-readable status, updated at every phase transition
```

`{root}` is whatever the calling agent specifies; a stack orchestrator's own
default (e.g. `.claude/planning/`) applies only when the caller doesn't say
otherwise - see that orchestrator's own file for its default. Never invent a
different root, and never overwrite an unrelated existing id's folder.

### Planning-record and spec conventions

Use the canonical planning-record layout in
[`references/PLANNING-FOLDER-STRUCTURE.md`](references/PLANNING-FOLDER-STRUCTURE.md).
It defines the purpose, lifecycle, and required content of every file in a run
folder. In particular, `request.md` is immutable evidence of the starting
request, `state.json` is the current machine-readable checkpoint, and
`summary.md` is a terminal-only handoff.

Use [`references/SPECS.md`](references/SPECS.md) when creating or refining
`specs/`. It defines the required file set, naming scheme, requirement IDs, and
the exact common section order for every concern specification. Do not create
an unstructured collection of notes: every requirement must be catalogued once,
each concern spec must trace back to that catalogue, and verification must map
acceptance criteria to observable evidence.

### state.json shape

```json
{
  "id": "<caller-supplied id>",
  "status": "draft | refining | testing | implementing | validating | integrating | reviewing | done | blocked",
  "phase": "<current phase name from the Phase sequence above>",
  "summary": "one-line current status, human-readable",
  "specs": ["specs/<file>.md", "..."],
  "worktree": {
    "planning_id": "<same value as id>",
    "branch": "<assigned local branch, null before assignment>",
    "base_ref": "<base ref for a new branch, or null>",
    "path": "<absolute assigned worktree path, or null>",
    "status": "unassigned | assigned | cleanup-pending | released"
  },
  "blockers": ["<any open blocker, empty when not blocked>"],
  "updated": "<ISO 8601 timestamp from the `date -u +%Y-%m-%dT%H:%M:%SZ` shell command, never guessed>"
}
```

### Discipline

- Write `request.md` and create `state.json` (status `draft`) before starting
  Specification Refinement - don't do the refinement work first and document it
  after.
- Update `state.json`'s `status`, `phase`, and `updated` at every phase
  transition defined in the Phase sequence above, not just at the start and
  end. A stale `state.json` is worse than none, because a resuming session will
  trust it.
- Before the first source-changing delegation, create or reuse the run's
  exclusive worktree through `git-worktree-expert`, then record its result in
  `state.json`. A read-only refinement or design activity may happen before
  assignment; no source changes may.
- On `blocked` (see Escalation above), set `status: "blocked"` and fill
  `blockers` with the exact reason - don't leave a workflow silently stuck with
  no machine-readable trace of why.
- Write `summary.md` only on a terminal state (`done` or `blocked`), never as a
  running log - it's the answer to "what happened here", not a diary.
- Resuming a workflow: read `state.json` first. If `status` isn't a fresh
  `draft`, read `request.md` and existing `specs/` before doing anything else -
  never restart refinement from scratch when state already exists.

## Review Checklist

- [ ] Requirements, ambiguities, acceptance criteria, and edge cases are captured in the planning record and specifications.
- [ ] Each phase has observable success evidence; no phase advanced on an assumption.
- [ ] Source-changing work used the assigned worktree and recorded its lifecycle state.
- [ ] Validation, integration, review, and terminal `state.json` status accurately reflect the actual outcome.
