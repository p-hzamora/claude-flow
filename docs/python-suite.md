# python-suite

Reusable Python/DDD/FastAPI/SQLAlchemy agents and skills. Each agent is independently
usable, not only reachable through the orchestrator. No Jira coupling.

**Version:** 1.0.1
**Dependencies:** `skills` (auto-enabled on install)

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the reusable skills are packaged through
`../plugins/python-suite/.codex-plugin/plugin.json` and reuse the same files as the
Claude Code plugin. Matching project-scoped Codex profiles live in
[`../.codex/agents/`](../.codex/agents/); they reuse those skills and inherit the
caller-selected model. See [`../.codex/README.md`](../.codex/README.md) to use the
profiles from another project without copying them. Matching Claude/Codex agent
definitions carry the same unique routing phrases.

## Agents

| Agent | Path | Codex routing phrases |
|---|---|---|
| `sdd-python-orchestrator` | `agents/sdd-python-orchestrator.md` | `run a specification workflow`; `plan an SDD implementation` |
| `ddd-architect` | `agents/ddd-architect.md` — read-only design step before planning; the orchestrator runs it as a gate for new or reshaped contexts, aggregates, and ports. | `design a bounded context`; `weigh domain design options` |
| `ddd-auditor` | `agents/ddd-auditor.md` — read-only post-implementation audit; runs `ddd-check.py`, verifies the design's architecture checks with `file:line` evidence, and reviews only changed files. The orchestrator runs it as a gate before user review. | `audit implemented DDD code`; `verify design compliance` |
| `ddd-scaffolder` | `agents/ddd-scaffolder.md` — creates new DDD projects only through the project-templates `scaffold` runner: validate, dry-run, then render after explicit authorization of the output path. | `scaffold a DDD project`; `render a project template` |
| `ddd-reviewer` | `agents/ddd-reviewer.md` | `audit domain boundaries`; `check architecture layering` |
| `ddd-implementer` | `agents/ddd-implementer.md` | `build a bounded context`; `repair hexagonal layers` |
| `fastapi-endpoint-builder` | `agents/fastapi-endpoint-builder.md` | `create a REST route`; `design an API resource` |
| `fastapi-reviewer` | `agents/fastapi-reviewer.md` | `audit an async API`; `review an OpenAPI contract` |
| `orm-model-inspector` | `agents/orm-model-inspector.md` | `map ORM relationships`; `inspect an Alembic schema` |
| `ruff-linter` | `agents/ruff-linter.md` | `run Ruff checks`; `format Python with Ruff` |
| `sqlalchemy-expert-fixer` | `agents/sqlalchemy-expert-fixer.md` | `repair a SQLAlchemy session`; `implement an ORM query` |
| `test-writer` | `agents/test-writer.md` | `write pytest coverage`; `test changed behavior` |

## Skills

| Skill | Path |
|---|---|
| `clean-ddd-hexagonal-python` | `skills/clean-ddd-hexagonal-python/SKILL.md` — tactical DDD, CQRS, ports/adapters, and context-first topology guidance; delegates Python language and style rules to `python-syntax`. |
| `fastapi-async-patterns` | `skills/fastapi-async-patterns/SKILL.md` |
| `pytest-coverage` | `skills/pytest-coverage/SKILL.md` |
| `pytest` | `skills/pytest/SKILL.md` |
| `python-syntax` | `skills/python-syntax/SKILL.md` — single source of truth for Python language, typing, import, naming, and documentation conventions. |
| `sqlalchemy-orm` | `skills/sqlalchemy-orm/SKILL.md` |

## Script

| Script | Path |
|---|---|
| `ddd-check.py` | `scripts/ddd-check.py` — zero-dependency AST check of layer, context, shared-kernel, and `Adapter`-suffix rules for the context-first topology; `--changed-since REF` limits it to files changed from a ref. Exit 0 clean, 1 violations, 3 topology not found. |

## Install standalone

```
/plugin install python-suite
```
