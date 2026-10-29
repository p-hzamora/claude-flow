# Migration and enforcement

1. Map one requested flow and its imports. Identify data, UI, side effects, and current
   consumers; do not reorganize an entire repository to deliver a small feature.
2. Choose the owner and minimum public API. Keep the existing route/framework tree
   when it is required for discovery; route files can delegate to feature entry points.
3. Move one vertical slice, update consumers, and check for cycles. Preserve behavior
   before combining movement with a substantial rewrite. Temporary re-exports can
   preserve consumers, but record their removal condition and avoid duplicate logic.
4. Check both source and test imports. Test code should not introduce production-only
   dependency exceptions; focused internal unit tests can import their own internals.
5. Run relevant type, lint, build, and behavioral checks. Document any remaining
   boundary violations with concrete paths and an incremental follow-up.

Prefer an existing import-boundary tool. A carefully scoped ESLint restriction can
reject deep feature imports and forbidden layer access; simple string patterns may
miss relative paths, aliases, dynamic imports, or re-exports. Use a resolver-aware
checker when these matter. Include type imports in the policy. Do not claim a grep
scan or successful build proves an acyclic dependency graph.

When adding enforcement, verify at least one allowed import and representative
forbidden imports, including a relative peer import and a deep alias import. A rule
that blocks all feature internals or ignores relative traversal is not useful.
Avoid new dependency tooling if the user only asked for an architecture explanation.

Extraction questions: Who owns this rule? Do its consumers share semantics or just
syntax? Can one feature change without coordinating others? If two features always
change together, reassess their boundary before creating another abstraction.
