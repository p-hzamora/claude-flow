# python-suite

Reusable Python/DDD/FastAPI/SQLAlchemy agents and skills. Each agent is independently
usable, not only reachable through the orchestrator. No Jira coupling.

**Version:** 0.5.0
**Dependencies:** `skills` (auto-enabled on install)

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the reusable skills are packaged through
`../plugins/python-suite/.codex-plugin/plugin.json` and reuse the same files as the
Claude Code plugin. Matching project-scoped Codex profiles live in
[`../.codex/agents/`](../.codex/agents/); they reuse those skills and inherit the
caller-selected model. See [`../.codex/README.md`](../.codex/README.md) to use the
profiles from another project without copying them.

## Agents

| Agent | Path |
|---|---|
| `sdd-python-orchestrator` | `agents/sdd-python-orchestrator.md` |
| `ddd-reviewer` | `agents/ddd-reviewer.md` |
| `ddd-implementer` | `agents/ddd-implementer.md` |
| `ddd-entity-generator` | `agents/ddd-entity-generator.md` |
| `fastapi-endpoint-builder` | `agents/fastapi-endpoint-builder.md` |
| `fastapi-reviewer` | `agents/fastapi-reviewer.md` |
| `orm-model-inspector` | `agents/orm-model-inspector.md` |
| `ruff-linter` | `agents/ruff-linter.md` |
| `sqlalchemy-expert-fixer` | `agents/sqlalchemy-expert-fixer.md` |
| `test-writer` | `agents/test-writer.md` |

## Skills

| Skill | Path |
|---|---|
| `clean-ddd-hexagonal-python` | `skills/clean-ddd-hexagonal-python/SKILL.md` — bounded-context-first DDD/CQRS guidance; delegates Python language and style rules to `python-syntax`. |
| `fastapi-async-patterns` | `skills/fastapi-async-patterns/SKILL.md` |
| `pytest-coverage` | `skills/pytest-coverage/SKILL.md` |
| `pytest` | `skills/pytest/SKILL.md` |
| `python-syntax` | `skills/python-syntax/SKILL.md` — single source of truth for Python language, typing, import, naming, and documentation conventions. |
| `sqlalchemy-orm` | `skills/sqlalchemy-orm/SKILL.md` |

## Install standalone

```
/plugin install python-suite
```
