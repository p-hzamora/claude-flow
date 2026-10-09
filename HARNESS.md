# Harness: designed, audited Python work

How agents in this marketplace are routed, gated, and checked for Python/DDD work. It
records decisions and gates only; procedures live in the skills and agent files it names.

Load it from a consuming project or your user `CLAUDE.md` with an import such as
`@<path-to-claude-flow>/HARNESS.md`. Claude Code does not read this file by itself.

## Routing

| Task | Route |
| --- | --- |
| New feature from a spec, or any change that creates or reshapes a bounded context, aggregate, port, or cross-context link | `sdd-python-orchestrator` |
| New project or service from scratch | `ddd-scaffolder` (prepare, then render after you authorize the path); then `ddd-architect` for the domain |
| Ticket end to end | `jira-dev-workflow` |
| Where is X, what calls Y | graphify, or Grep/Glob/Read directly |
| Review a diff or branch | `ddd-reviewer`, `fastapi-reviewer`, `jira-tech-lead-reviewer` |
| Edit inside one already-designed aggregate, or a 1-2 file change | direct, no orchestrator |

Do not route questions, exploration, or small edits through the orchestrator: its
handoffs cost tokens that only pay off for spec-driven work.

## Pipeline

| Phase | Owner | Artifact (under `{root}/{id}/`) | Gate to advance |
| --- | --- | --- | --- |
| Design | `ddd-architect` | `specs/20-domain.md`, decisions in `00-overview.md`, architecture checks in `90-verification.md` | Verdict `DESIGN READY`; every `Q-*` answered by the user |
| Plan and build | `sdd-python-orchestrator` with `ddd-implementer`, `test-writer` | code in the run's worktree | tests pass |
| Audit | `ddd-auditor` | statuses written into `90-verification.md` | `AUDIT PASS` |

The orchestrator is the only writer of the planning folder. `ddd-architect` and `ddd-auditor`
return results and never write. Vault updates are not part of this pipeline: the
`obsidian-vault` plugin handles them separately. No new files: the layout in
`sdd-workflow`'s `PLANNING-FOLDER-STRUCTURE.md` is complete.

## Rules

- **Evidence.** A design decision cites the skill reference it rests on. An audit finding
  carries file, line, rule, and the verbatim offending line. Anything unproven is
  reported as unverifiable, never as passing.
- **Deterministic first.** `scripts/ddd-check.py` runs before any model judgment; agents
  review only what it cannot see, and only changed files, so old debt is not blamed on a
  run.
- **Budgets.** At most 2 design-challenge rounds and 2 audit-and-fix rounds; then escalate
  to the user with what remains. Model calls beyond the pipeline need a reason.
- **Read-only until approved.** Design and audit make no source changes. Source work
  happens only in the run's worktree.
- **Escalate, don't decide.** Business rules, unresolved disagreements, and
  `AUDIT INCOMPLETE` go to the user.

## Measuring the harness

A change to any agent, skill, or this file should not raise tokens per task without a gain
in caught violations. Compare a fixed prompt before and after with
`claude -p "<prompt>" --output-format json | jq '{usage, total_cost_usd}'`, and inspect the
baseline with `/context`.
