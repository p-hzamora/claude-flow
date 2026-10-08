# skills

Cross-cutting, language-agnostic skills reused across the other plugins in this marketplace.

**Version:** 1.2.0
**Dependencies:** none

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the shared skills are also packaged through
`../plugins/skills/.codex-plugin/plugin.json`. Claude Code's agent components are
host-specific, while the skills remain the portable unit used by both hosts. Matching
Claude/Codex agents declare the same unique routing phrases, verified by
`scripts/validate_multihost.py`.

## Agents

| Agent | Responsibility | Codex routing phrases |
|---|---|---|
| `git-worktree-expert` | Exclusive specialist for Git worktree lifecycle operations; uses `git-worktree-management` as its authoritative procedure. | `allocate an isolated checkout`; `clean up a worktree` |
| `process-summarizer` | Read-only summarizer for a finished SDD run; emits brain notes (one run note, one per material decision) in its final message, which the plugin's `SubagentStop` hook files into the vault via `scripts/brain-file.py`. Claude Code only. | `summarize a finished run`; `file brain notes` |
| `template-scaffolder` | Expert on a template catalog's `config.yaml` and `scaffold` CLI, for any language or pattern: writes schema-valid configs, compares variants or verifies properties in throwaway sandbox renders, renders the final project only after the output path is authorized; uses `scaffold-catalog` as its procedure. | `author a scaffold config`; `compare template variants` |

### Brain filing

The hook in `hooks/hooks.json` matches `process-summarizer` and runs `scripts/brain-file.py`,
which validates each `<<<NOTE name.md ... NOTE>>>` block in the agent's final message
(frontmatter, safe names), files it under `projects/` or `decisions/` in the vault
(`$BRAIN_VAULT`, default `~/Documents/brain`), and appends run notes to `index.md`.
Invalid notes block the agent once with the reason; a second failure goes to `_rejected/`.

### Worktree delegation flow

Development agents request isolated worktrees from `git-worktree-expert`, which
inspects or creates them through `git-worktree-management`. For SDD work, the request
is bound to the planning folder ID and `state.json` records the returned absolute path;
that path is the only directory where the requesting agent performs the task's work.

```text
                    ┌──────────────────────┐
                    │       Agent A        │
                    │ backend / feature    │
                    └──────────┬───────────┘
                               │
                    "I need an isolated
                     worktree for ABC-1234"
                               │
                               ▼
                  ┌──────────────────────────┐
                  │   git-worktree-expert    │
                  │                          │
                  │ uses                     │
                  │ git-worktree-management  │
                  │ skill                    │
                  └────────────┬─────────────┘
                               │
                        create / inspect
                               │
                               ▼
               ~/project-wt/bugfix-ABC-1234
                               │
                               ▼
                    returns absolute path
                               │
                               ▼
                    ┌──────────────────────┐
                    │       Agent A        │
                    │ works ONLY there     │
                    └──────────────────────┘
```

## Skills

| Skill | Path |
|---|---|
| `grill-with-context` | `skills/grill-with-context/SKILL.md` — rounds/frontier interview grounded in the target repo's `CONTEXT.md`/`CONTEXT-MAP.md` and `docs/adr/` (soft dependency, degrades gracefully if absent); writes resolved glossary terms and hard-to-reverse decisions back to those files as the session progresses |
| `commit-message-generator` | `skills/commit-message-generator/SKILL.md` |
| `claude-sdk-expert` | `skills/claude-sdk-expert/SKILL.md` |
| `graphify` | `skills/graphify/SKILL.md` |
| `api-rest-designer` | `skills/api-rest-designer/SKILL.md` |
| `git-worktree-management` | `skills/git-worktree-management/SKILL.md` — safe, deterministic inspection, creation, reuse, removal, and stale-metadata cleanup for Git worktrees; includes a lifecycle helper script |
| `sdd-workflow` | `skills/sdd-workflow/SKILL.md` — stack-agnostic SDD orchestration methodology with planning-ID-bound worktree isolation, auditable records, and uniform, traceable specification templates; any stack orchestrator (e.g. `sdd-python-orchestrator`) invokes this first, then layers its own stack context on top |
| `handoff` | `skills/handoff/SKILL.md` — compacts the conversation into a portable handoff markdown file (written to the OS temp dir) for a fresh agent, colleague, or forked side task to pick up; user-invoked only (`/handoff`), never model-triggered |
| `prototype` | `skills/prototype/SKILL.md` — builds a throwaway prototype (UI variations behind a toggle, or a terminal REPL for a state machine) in its own directory to settle a design question code can answer and words can't; pairs with `handoff` to carry the settled decision back to the originating session |
| `scaffold-catalog` | `skills/scaffold-catalog/SKILL.md` — procedure for authoring a catalog `config.yaml` from the template's schema and driving the `scaffold` CLI: sandbox compare/verify renders, then an authorized final render; defers fields and commands to the catalog's own docs and schema |

## Install standalone

```
/plugin install skills
```
