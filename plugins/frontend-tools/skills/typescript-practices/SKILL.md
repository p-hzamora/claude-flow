---
name: typescript-practices
description: Compatibility entry point for the former frontend TypeScript skill. When explicitly invoked, use typescript-suite's typescript-syntax and typescript-clean-code; new TypeScript work should select those canonical skills directly.
---

# TypeScript practices — compatibility entry point

The language-wide rules now live in the independently installable `typescript-suite`
plugin. This entry point preserves existing invocations and owns no language rules.

Load `typescript-syntax` from the installed `typescript-suite` for all TypeScript work.
Load `typescript-clean-code` for SOLID/design decisions and `typescript-testing` for
unit/contract/type tests as needed. Resolve those names through the host's installed
skill catalog, not by assuming separately installed plugins are sibling directories.

If the dependency is missing, report the missing `typescript-suite` installation;
do not reconstruct its rules from memory or fetch external guidance. Claude Code
metadata declares the dependency; Codex users install it explicitly. The local
[sources record](references/sources.md) documents the migration.

## Review Checklist

- [ ] The canonical typescript-suite skill was resolved and read.
- [ ] Applicable canonical checklists passed, or missing dependencies/checks are reported.
- [ ] No duplicate TypeScript conventions were introduced here.
