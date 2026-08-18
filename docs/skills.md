# skills

Cross-cutting, language-agnostic skills reused across the other plugins in this marketplace.

**Version:** 0.2.0
**Dependencies:** none

## Skills

| Skill | Path |
|---|---|
| `grill-with-context` | `skills/grill-with-context/SKILL.md` — rounds/frontier interview grounded in the target repo's `CONTEXT.md`/`CONTEXT-MAP.md` and `docs/adr/` (soft dependency, degrades gracefully if absent); writes resolved glossary terms and hard-to-reverse decisions back to those files as the session progresses |
| `commit-message-generator` | `skills/commit-message-generator/SKILL.md` |
| `claude-sdk-expert` | `skills/claude-sdk-expert/SKILL.md` |
| `graphify` | `skills/graphify/SKILL.md` |
| `api-rest-designer` | `skills/api-rest-designer/SKILL.md` |
| `sdd-workflow` | `skills/sdd-workflow/SKILL.md` — stack-agnostic SDD orchestration methodology; any stack orchestrator (e.g. `sdd-python-orchestrator`) invokes this first, then layers its own stack context on top |

## Install standalone

```
/plugin install skills
```
