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

## Quality gates (before advancing a phase)

- Spec is unambiguous and complete for the current scope.
- Every acceptance criterion is testable.
- Test coverage aligns with spec requirements - no more, no less.
- Generated code passes all tests.
- Integration points are documented and verified, not assumed.

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

## Plan & spec persistence

Every time a plan is produced, before invoking any downstream implementation
agent, write the finalized plan (and the specs it was derived from) to the
location the calling agent specifies (e.g. a per-ticket `specs/` subdirectory) -
never invent a different location, and don't overwrite unrelated existing
planning files. If resuming after a context reset or interruption, check that
location for an existing plan before drafting a new one from scratch.
