---
name: feature-architecture
description: Design or refactor frontend feature boundaries, public exports, and dependency direction. Use for feature-based folder architecture in any frontend framework; distinguish a lightweight feature layout from formal Feature-Sliced Design.
---

# Feature architecture

Start from business capabilities and existing ownership, not a generic folder tree.
Identify the user action, data ownership, and consumers before moving files. This
skill is framework-independent and does not choose a router, state library, or build tool.

Read [Boundaries and layouts](references/boundaries-and-layouts.md) to select or adapt
a profile. Read [Migration and enforcement](references/migration-and-enforcement.md)
for existing code or import rules. [Sources](references/sources.md) separates researched
FSD conventions from this plugin's lightweight local policy.

Keep one canonical boundary policy in project documentation. Small applications can
start with app composition, a few features, and shared primitives. Do not impose
formal FSD just because a project has a `features/` directory. Preserve an established
profile unless changing it is part of the request.

For React and TypeScript placement details, optionally use
[react-feature-integration](../react-feature-integration/SKILL.md).

## Review Checklist

- [ ] Feature boundaries reflect business ownership and an explicit architecture profile.
- [ ] Dependency direction and allowed public imports are documented and checked.
- [ ] Shared code has real consumers and does not conceal feature-specific policy.
- [ ] Composition avoids cycles, deep imports, and accidental peer-feature coupling.
- [ ] Migration preserves behavior and stays within scope; enforcement limitations are stated.
