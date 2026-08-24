# skills

Cross-cutting, language-agnostic skills reused across the other plugins in this marketplace.

**Version:** 0.4.0
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
| `handoff` | `skills/handoff/SKILL.md` — compacts the conversation into a portable handoff markdown file (written to the OS temp dir) for a fresh agent, colleague, or forked side task to pick up; user-invoked only (`/handoff`), never model-triggered |
| `prototype` | `skills/prototype/SKILL.md` — builds a throwaway prototype (UI variations behind a toggle, or a terminal REPL for a state machine) in its own directory to settle a design question code can answer and words can't; pairs with `handoff` to carry the settled decision back to the originating session |

## Install standalone

```
/plugin install skills
```
