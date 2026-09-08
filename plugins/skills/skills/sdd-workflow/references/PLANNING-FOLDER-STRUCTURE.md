# Planning-folder structure

Each SDD run is an auditable, resumable record at `{root}/{id}/`. The folder is
not a scratchpad and it is not an implementation directory: it records the
request, the refined contracts, the workflow checkpoint, and the final outcome.
Keep all material for one run inside its one id folder.

```text
{root}/{id}/
  request.md
  state.json
  specs/
    README.md
    00-overview.md
    10-<concern>.md        # zero or more concern specifications
    90-verification.md
  summary.md               # terminal states only
```

Numbers give a stable reading order; they do not imply a sequence of
implementation. Use lowercase kebab-case for `<id>` and `<concern>`. A ticket
key that contains uppercase letters may retain them if the tracker is the
caller-supplied identifier. Do not create `notes.md`, `todo.md`, or an
unindexed specification: put durable decisions in the relevant spec, and keep
ephemeral agent working notes outside the run folder.

## Creation and lifecycle

Create `request.md`, `specs/`, and `state.json` with status `draft` before
refinement starts. Create `specs/README.md` and `specs/00-overview.md` during
refinement. Create a concern file only when that concern has requirements or
decisions that would make `00-overview.md` unclear; omit inapplicable concerns.
Create `90-verification.md` before implementation, as the output of test
design. Create `summary.md` only after the workflow is `done` or `blocked`.

On resume, read `state.json`, then `request.md`, then `specs/README.md` and
`00-overview.md` before delegating or making a new decision. Existing specs are
the current contract; amend them deliberately rather than silently replacing
them.

## `request.md`: preserved input

`request.md` answers “what was asked before we refined it?” Its request body is
never edited after capture. Use this shape:

```markdown
# Original request

**Run:** `<id>`

**Captured:** `<UTC ISO 8601 timestamp>`

**Capture type:** `verbatim | faithful summary`

**Source:** `<user, ticket URL/key, or other origin>`

## Request

<verbatim request, or a faithful summary clearly labelled as such>
```

If the source is a ticket or document, link it rather than copying unrelated
history. A faithful summary must retain requested behaviour, constraints,
acceptance criteria, and explicitly stated exclusions. Never put refinement,
assumptions, or a proposed solution here; those belong in `specs/`.

## `state.json`: workflow checkpoint

`state.json` is the only machine-readable source of current workflow state. It
uses the base shape in `SKILL.md`. `phase` is one of `Specification refinement`,
`Test design`, `Code generation`, `Validation`, or `Integration`; use `Terminal`
only for `done` and `blocked`. `specs` lists every spec file relative to the run
folder, in reading order. `blockers` contains open, actionable reasons and is
empty in all non-blocked states.

Example while refining:

```json
{
  "id": "add-export",
  "status": "refining",
  "phase": "Specification refinement",
  "summary": "Requirements are being refined; CSV format remains open.",
  "specs": ["specs/README.md", "specs/00-overview.md"],
  "blockers": [],
  "updated": "2026-09-08T09:15:00Z"
}
```

Update it atomically at every phase transition. It is a checkpoint, not a
history log: retain the current concise status rather than appending events.

## `summary.md`: terminal handoff

Write this file exactly once when `state.json.status` becomes `done` or
`blocked`. It must let a reader understand the outcome without replaying the
whole run.

```markdown
# Run summary: `<id>`

**Outcome:** `done | blocked`

**Completed:** `<UTC ISO 8601 timestamp>`

## Delivered outcome

<what is implemented, or why no implementation could proceed>

## Requirements and verification

| Requirement / criterion | Result | Evidence |
| --- | --- | --- |
| FR-001 / AC-001 | passed | `<test, command, review, or link>` |

## Key decisions and deviations

<decision IDs, approved amendments, and any deliberate deviation from the request>

## Changed artifacts

<paths or a concise “none”>

## Remaining work or blockers

<empty only when done with no follow-up; exact blockers when blocked>
```

Do not use the summary as a progress diary or create it merely because a session
is pausing. A non-terminal run resumes from `state.json` and the specs.
