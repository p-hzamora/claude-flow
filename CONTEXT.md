# claude-flow

A private multi-host plugin marketplace for SDD/Jira/Python workflows.

## Language

**Plugin**:
A top-level installable unit listed in `.claude-plugin/marketplace.json`'s `plugins[]`,
and `.agents/plugins/marketplace.json`'s `plugins[]`, defined by its own
`.claude-plugin/plugin.json` and, for Codex compatibility, its own
`.codex-plugin/plugin.json`. The plugin directory is the only structural container in
this repo.
_Avoid_: suite, bundle — as a distinct category from Plugin. `python-suite` and "agent bundle" (`jira-dev-workflow`'s own description) are informal descriptors baked into a name or a sentence, not a separate type with different rules. Every one of them is a Plugin.

**Agent**:
A host-specific configuration for a specialized, isolated worker. Claude Code uses a
full definition under a plugin's `agents/` folder (persona,
`tools`/`disallowedTools`, `model`) launched via its Agent tool. Codex uses a thin,
project-scoped TOML adapter under `.codex/agents/` (name, description, developer
instructions and optional sandbox/model settings). Both configurations must point to
shared Skills for procedures and knowledge instead of carrying duplicate workflow text.

**Skill**:
A `SKILL.md` under a plugin's `skills/` folder — instructions loaded straight into the calling thread's own context. No tool-permission frontmatter, no persona, no restriction mechanism. Reference knowledge or a procedure, not an actor.
_Avoid_: using "skill" and "agent" interchangeably when describing a plugin's contents — they're read and run differently.

**Script**:
An executable file under a plugin's `scripts/` folder — plain code (shell, Python, etc.) invoked via Bash, not read into context and not a persona. An Agent/Skill references it by an absolute, portable path (`${CLAUDE_PLUGIN_ROOT}/scripts/<name>`, the Claude Code env var that resolves to the installed plugin's own directory), never a bare relative path. Where an agent's instructions mark a script mandatory, that requirement is a hard constraint, not one option among several equivalent shell one-liners.

**Entity** / **Value Object** / **Aggregate** / **Port** / **Handler**:
DDD hexagonal-architecture terms. Full ruleset lives in the `clean-ddd-hexagonal-python` skill (`plugins/python-suite/skills/`) — this file only anchors the names:
- Entity — domain object with identity tracked across time.
- Value Object — immutable domain object defined by its attributes, not identity.
- Aggregate — cluster of Entities/Value Objects; one Repository per aggregate, never per entity.
- Port — interface declared in domain/application, implemented in infrastructure.
- Handler — application-layer class implementing one Command or Query.
_Avoid_: restating this checklist inside an agent file. `ddd-reviewer`, `ddd-implementer`, and `ddd-entity-generator` should point at `clean-ddd-hexagonal-python` as the single source of truth, not each carry their own copy.

**DTO** / **Response (schema)**:
Two more objects in the same skill's layering, sitting output-side of Entity/VO —
`clean-ddd-hexagonal-python` again owns the full ruleset ([ADR-0001](./docs/adr/0001-four-mapper-naming.md)):
- DTO — application-layer output contract a Command/Query handler returns; never a VO or
  Entity itself.
- Response — interface-layer schema an API route returns; sourced from a DTO only
  (`model_validate`, or an `{Entity}ApiMapper` in the rare case that needs real
  transform logic), never straight from a DTO-less Entity/VO.
_Avoid_: a mapper method named `from_x` anywhere in this taxonomy — the convention is
`to_[destination]` (`to_orm`, `to_entity`, `to_dto`, `to_schema`) on `{Entity}Mapper` /
`{Entity}ReadMapper` / `{Entity}Assembler` / `{Entity}ApiMapper` respectively.

## Relationships

- A **Plugin** holds many Claude Code **Agents**, many **Skills** shared by Claude
  Code and Codex, and optionally **Scripts**. The repository's `.codex/agents/`
  profiles make matching roles available to Codex as project configuration; Codex does
  not currently load custom agents from a plugin manifest.
- An **Agent** may consume one or more **Skills** as reference material (e.g. `ddd-implementer` reads `clean-ddd-hexagonal-python`), may delegate to another Agent (e.g. `jira-dev-workflow` delegates Markdown-to-LaTeX authoring and PDF export to `latex-tools` in Phase 6), and may be required to invoke a **Script** as a fixed tool.
- A **Plugin** may declare `dependencies` on other **Plugins** (`jira-dev-workflow` depends on `skills` and `python-suite`; `python-suite` depends on `skills`).

## Flagged ambiguities

- "suite" vs "bundle" — resolved above: both collapse into **Plugin**. Don't introduce either as a new structural term in future docs.
- The non-negotiable regexes (branch name, commit message, commit author email) are currently duplicated in both `jira-dev-workflow.md` and `jira-git-committer.md` — the README already flags this ("If DevOps changes these, update both files in the same commit"). Not yet resolved into a single source of truth; candidate for extraction into a shared skill.
