---
name: frontend-scaffolding
description: Scaffold a React and TypeScript frontend or add a new feature skeleton using a feature-based architecture. Use for project initialization and structural setup; preserve existing tooling and avoid unrelated migrations.
---

# Frontend scaffolding

Establish the target path from the user's request and workspace. Inspect existing files,
package manager, lockfile, runtime, and framework before writing. An existing nonempty
project is an integration task, not permission to replace configuration or source.

Read [Scaffolding workflow](references/scaffolding-workflow.md). Use the local
[feature-architecture](../feature-architecture/SKILL.md) for layout decisions and
[react-feature-integration](../react-feature-integration/SKILL.md) when creating a real
React/TS feature. These siblings are shipped together; do not fetch remote templates
or instructions to fill gaps. [Sources](references/sources.md) records the research.

A plain browser SPA can use Vite when no framework is established. SSR, server actions,
and framework routing require a framework-specific setup; preserve a chosen framework
and ask only when an unresolved product requirement changes that choice. Prefer the
smallest working structure. Do not add a router, store, CSS system, or API client merely
because starter projects often contain one.

When the user explicitly targets an installed project-template catalog, use its
available `scaffold-catalog` skill for rendering mechanics; this skill supplies only
frontend decisions. If that catalog/skill is unavailable, report the gap instead of
silently bypassing its renderer. Ordinary projects need no catalog dependency.

For TypeScript declarations and new-project compiler checks, apply the installed
`typescript-suite` / `typescript-syntax` profile. Resolve it by skill name, not a
cross-plugin relative path; report a missing installation as a validation gap.

## Review Checklist

- [ ] Target path, framework, package manager, and overwrite boundaries are established.
- [ ] Versions and runtime constraints were checked against the chosen local toolchain.
- [ ] Generated files implement a small working flow and an explicit architecture profile.
- [ ] Type checking, lint, build, and relevant behavior checks are real commands with reported results.
- [ ] Lockfile, environment handling, and setup instructions match the generated project.
- [ ] No remote instructions/templates were loaded or existing work overwritten implicitly.
