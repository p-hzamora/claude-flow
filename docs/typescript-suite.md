# typescript-suite

Framework-independent TypeScript skills and agents for services, libraries, scripts,
and frontend code. Like python-suite, the plugin has a single language-conventions
owner, focused design/testing skills, and independently usable implementation/review
roles. It has no dependency on React, frontend-tools, Jira, or a particular test runner.

**Version:** 0.1.0
**Dependencies:** none

## Skills

| Skill | Responsibility | Local references |
|---|---|---|
| [typescript-syntax](../plugins/typescript-suite/skills/typescript-syntax/SKILL.md) | Mandatory language profile: explicit declarations/signatures, naming, imports, readonly contracts, validation, exceptions, async ownership, and documentation. | Declarations and functions; types and boundaries; classes and modules; async and errors; tooling and enforcement; sources. |
| [typescript-clean-code](../plugins/typescript-suite/skills/typescript-clean-code/SKILL.md) | Concrete SOLID, consumer-owned ports, composition, responsibility boundaries, and scoped refactoring. | SOLID and boundaries; sources. |
| [typescript-testing](../plugins/typescript-suite/skills/typescript-testing/SKILL.md) | Unit, contract, async, and compile-time API tests using the project's runner. | Behavior and type contracts; sources. |

## Agents

| Agent | Responsibility | Routing phrases |
|---|---|---|
| `typescript-implementer` | Implements scoped changes and verifies language, design, and behavior through shared skills. | `implement a TypeScript module`; `refactor TypeScript behavior` |
| `typescript-reviewer` | Read-only evidence-based review; identifies rule violations and unverified checks without editing or running emitting commands. | `audit TypeScript conventions`; `review a TypeScript contract` |

Claude Code profiles live in `plugins/typescript-suite/agents/`. Thin Codex profiles
live in [.codex/agents](../.codex/agents/) and refer to the same skills. They inherit
the selected Codex model. Shared procedures are never copied into host adapters.

## What is mandatory

New or changed authored TypeScript follows typescript-syntax, including explicit named
variable/property types and parameter/return contracts. It has a closed list of useful
exceptions for typed inline callbacks, language binding syntax, literal tables, and
proven external typing defects. Compiler inference is not a general excuse to omit
annotations. Assertions cannot replace runtime validation.

The skill defines precise names, named exports/type-only imports, immutable boundary
contracts, exhaustive alternatives, promise/error ownership, and module/API documentation.
Correct and incorrect examples make the policy reviewable. New-project compiler
checks are supplied as a fragment, with runtime/module choices kept host-specific.
Existing explicit repository instructions take precedence, and legacy migrations stay
within the requested scope. The profile does not mechanically translate Python syntax
or require React, classes everywhere, decorators, DDD layers, or a dependency container.

Examples target TypeScript 5.0+ and ES2022 libraries; installed project compatibility
must be checked. This is not a pinned compiler recommendation or an upgrade request.
Typed lint rules cover part of the profile; semantic review covers the documented gaps.
Every skill ends with a completion checklist.

## Relationship with frontend-tools

`frontend-tools` depends on this plugin for TypeScript language rules. Its old
`typescript-practices` entry point forwards to these canonical skills. React, UI tests,
and feature folder architecture retain their frontend owners. Pure TypeScript consumers
install typescript-suite alone. Cross-plugin skills are resolved through the installed
skill catalog rather than assuming neighboring installation directories.

## Install

Claude Code:

```text
/plugin install typescript-suite
```

Codex, after adding this marketplace:

```text
codex plugin add typescript-suite@claude-flow
```

For frontend work, install typescript-suite before frontend-tools in Codex. To use the
project-scoped agent adapters elsewhere, follow [.codex/README.md](../.codex/README.md).

## Sources and maintenance

Reviewed primary TypeScript Handbook, TSConfig, and typescript-eslint documentation on
2026-10-22. Each skill records source titles locally. The mandatory style is an explicit
repository policy inspired by python-syntax's rigor, not a claim of universal upstream
style. All references and examples ship locally with no external URLs or remote includes.
