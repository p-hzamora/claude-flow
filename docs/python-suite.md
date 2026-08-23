# python-suite

Reusable Python/DDD/FastAPI/SQLAlchemy agents and skills. Each agent is independently
usable, not only reachable through the orchestrator. No Jira coupling.

**Version:** 0.3.3
**Dependencies:** `skills` (auto-enabled on install)

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
| `clean-ddd-hexagonal-python` | `skills/clean-ddd-hexagonal-python/SKILL.md` |
| `fastapi-async-patterns` | `skills/fastapi-async-patterns/SKILL.md` |
| `pytest-coverage` | `skills/pytest-coverage/SKILL.md` |
| `pytest` | `skills/pytest/SKILL.md` |
| `python-syntax` | `skills/python-syntax/SKILL.md` |
| `sqlalchemy-orm` | `skills/sqlalchemy-orm/SKILL.md` |

## Install standalone

```
/plugin install python-suite
```
