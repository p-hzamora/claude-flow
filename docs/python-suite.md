# python-suite

Reusable Python/DDD/FastAPI/SQLAlchemy agents and skills. Each agent is independently
usable, not only reachable through the orchestrator. No Jira coupling.

**Version:** 0.5.4
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
| `ddd-reviewer` | `agents/ddd-reviewer.md` | `audit domain boundaries`; `check architecture layering` |
| `ddd-implementer` | `agents/ddd-implementer.md` | `build a bounded context`; `repair hexagonal layers` |
| `ddd-entity-generator` | `agents/ddd-entity-generator.md` | `design a value object`; `model an aggregate` |
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

## Install standalone

```
/plugin install python-suite
```
