# Specification set

`specs/` is the refined, testable contract for one SDD run. It is deliberately
small: split by concern only when that makes a contract easier to understand or
review. It must never become a duplicate of the codebase, a task diary, or a
generic implementation checklist.

## Required layout and naming

```text
specs/
  README.md
  00-overview.md
  10-<concern>.md          # zero or more, in increments of 10
  90-verification.md
```

`README.md`, `00-overview.md`, and `90-verification.md` are required for every
refined run. The concern files are optional and selected by the work, not by a
fixed technology list. Common examples are `10-api.md`, `20-domain.md`,
`30-data-model.md`, `40-security.md`, `50-ui.md`, and `60-migration.md`.
Choose a concise lowercase kebab-case concern name; leave numeric gaps so a new
concern can be inserted without renaming existing files. If a concern does not
exist, do not create an empty file.

The file list is an index, not a phase plan:

| File | Owns |
| --- | --- |
| `README.md` | navigation, status of each specification, and dependencies between specs |
| `00-overview.md` | problem, scope, canonical requirements, acceptance criteria, assumptions, and open questions |
| `NN-<concern>.md` | detailed contract for one bounded concern, traced to requirements |
| `90-verification.md` | test and validation design, mapping every acceptance criterion to evidence |

Use stable identifiers throughout the set:

- `FR-001`, `FR-002` — functional requirements.
- `NFR-001`, `NFR-002` — measurable non-functional requirements.
- `AC-001`, `AC-002` — observable acceptance criteria.
- `Q-001`, `Q-002` — unresolved questions or blockers.
- `D-001`, `D-002` — decisions that materially shape the solution.

The identifiers are assigned in `00-overview.md` and are never reused for a
different meaning. A concern file and the verification spec reference those IDs;
they do not restate a divergent version. When a requirement changes, amend the
catalogue and every affected concern or verification row in the same refinement
step.

## `README.md`: specification index

```markdown
# Specification index: `<id>`

## Reading order

1. [Overview](00-overview.md) — `approved | draft | needs-decision`
2. [API contract](10-api.md) — `approved | draft | needs-decision`
3. [Verification](90-verification.md) — `approved | draft | needs-decision`

## Dependency map

| Specification | Depends on | Why |
| --- | --- | --- |
| `10-api.md` | `00-overview.md` | exposes FR-001 and FR-002 |
| `90-verification.md` | `00-overview.md`, `10-api.md` | verifies AC-001 through AC-004 |

## Open decisions

| ID | Question | Owner / needed input | Blocks |
| --- | --- | --- | --- |
| Q-001 | `<question>` | `<person or source>` | `10-api.md` |
```

Keep the index aligned with the real files. A spec marked `needs-decision` cannot
be treated as an approved contract; surface its question in `state.json` if it
blocks phase progress.

## `00-overview.md`: canonical requirements catalogue

```markdown
# Overview: `<feature name>`

## Problem and intended outcome

<who has the problem, the current pain, and the observable result this work creates>

## Scope

### In scope

- <bounded outcome>

### Out of scope

- <explicit exclusion>

## Context and constraints

- <existing system fact, policy, compatibility boundary, or imposed constraint>

## Requirements

| ID | Requirement | Priority | Source |
| --- | --- | --- | --- |
| FR-001 | The system shall … | must | request / ticket section |
| NFR-001 | The system shall … within … | must | request / decision |

## Acceptance criteria

| ID | Given / When / Then | Covers |
| --- | --- | --- |
| AC-001 | Given …, when …, then … | FR-001 |

## Assumptions

- A-001: <explicit, non-blocking assumption and why it is safe>

## Open questions

| ID | Question | Needed input | Impact if unresolved |
| --- | --- | --- | --- |
| Q-001 | <question> | <who or what decides> | <what it blocks> |

## Decisions

| ID | Decision | Rationale | Consequences |
| --- | --- | --- | --- |
| D-001 | <decision> | <why> | <trade-off or affected spec> |
```

Requirements state externally observable behaviour or measurable qualities, not
implementation guesses. Each requirement uses “shall” (or another unambiguous
normative form), has a source, and is independently testable. Acceptance
criteria use concrete preconditions, action, and outcome; “works correctly” and
“is user-friendly” are not criteria. An unresolved requirement is a question,
not an assumption. An assumption is permitted only when it does not alter scope,
contract, security, or compatibility; otherwise halt for a decision.

## Concern-spec template: `NN-<concern>.md`

Every concern file uses these headings in this order. Write `Not applicable` in
a section that genuinely does not apply; do not silently omit a contract area.
Additional concern-specific sections may follow `Detailed contract` only when
they clarify behaviour.

```markdown
# <Concern> specification

**Status:** `draft | approved | needs-decision`

**Requirement coverage:** `FR-001, NFR-001, AC-001`

**Dependencies:** `<specifications, external systems, or none>`

## Purpose and scope

<what this concern owns; its explicit boundary>

## Detailed contract

<inputs, outputs, data shapes, events, state transitions, interfaces, or UX
behaviour appropriate to this concern. Use tables or examples where precision
matters. Define field meaning, optionality, defaults, and units.>

## Rules and invariants

- <rule that must always hold, including validation or authorization rules>

## Normal and alternate flows

1. <happy-path interaction or transition>
2. <alternate path>

## Failure and edge behaviour

| Condition | Required behaviour | User / caller-visible result |
| --- | --- | --- |
| <invalid or boundary condition> | <system response> | <contractual output> |

## Acceptance mapping

| Criterion | How this concern satisfies it |
| --- | --- |
| AC-001 | <specific behaviour or contract element> |

## Decisions, assumptions, and open questions

| Type | ID | Detail | Impact |
| --- | --- | --- |
| decision | D-001 | <detail> | <impact> |

## Delivery impact

<likely integration points, migrations, rollout/compatibility needs, and test
categories. This is a boundary map, not a file-by-file coding plan.>
```

For an API concern, `Detailed contract` includes operations, paths, request and
response schemas, status/error behaviour, auth, pagination/filtering where
relevant, and compatibility. For a data concern, include ownership, entities,
constraints, lifecycle, migration/backfill, and retention. For security, include
assets, trust boundaries, authorization, threats, and audit requirements. For a
UI concern, include user state, accessibility, loading/error/empty states, and
responsive behaviour. These additions refine the common template; they never
replace its requirement traceability or edge-case sections.

## `90-verification.md`: evidence plan

The verification specification is written before implementation and proves that
the refined contract can be evaluated. It is not merely a list of test files.

```markdown
# Verification specification

## Verification approach

<test levels and non-test evidence needed; explain notable boundaries or fakes>

## Acceptance-criteria matrix

| Criterion | Scenario / check | Level | Evidence | Status |
| --- | --- | --- | --- | --- |
| AC-001 | Given … when … then … | unit / integration / e2e / review | `<test name or command>` | planned |

## Requirement coverage

| Requirement | Verified by | Gap or rationale |
| --- | --- | --- |
| FR-001 | AC-001 | none |

## Edge and failure cases

| Source condition | Scenario / expected result | Level |
| --- | --- | --- |
| `10-api.md`: invalid input | rejected with defined error | integration |

## Non-functional verification

| Requirement | Method | Passing threshold | Evidence |
| --- | --- | --- | --- |
| NFR-001 | <measurement> | <threshold> | <command/report> |

## Completion rule

<the exact evidence required before the workflow can enter Integration or done>
```

Every `AC-*` has at least one planned check and every `FR-*`/`NFR-*` appears in
the coverage matrix. If a requirement cannot be tested automatically, identify
the review, measurement, or operational evidence and its passing threshold. A
missing verification approach is a refinement gap, not permission to proceed.
