# playwright-tools

Playwright Test (TypeScript/JavaScript) agents and skills for frontend end-to-end testing:
write, review, and debug specs. Self-contained: no third-party agents and no external
knowledge store; every skill carries its own sources.

**Version:** 0.1.0
**Dependencies:** none

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the skills are packaged through
`../plugins/playwright-tools/.codex-plugin/plugin.json` and reuse the same files as the
Claude Code plugin. Matching project-scoped Codex profiles live in
[`../.codex/agents/`](../.codex/agents/). Matching Claude/Codex agent definitions carry
the same unique routing phrases.

## Agents

| Agent | Responsibility | Codex routing phrases |
|---|---|---|
| `playwright-test-writer` | Writes or extends specs, page objects, and fixtures for a described flow; runs them, runs `pw-check.py`, and re-runs with `--repeat-each=3 --workers=1`. Edits test code and Playwright config only. | `write Playwright tests`; `author end-to-end specs` |
| `playwright-reviewer` | Read-only. Runs `pw-check.py` first, then reviews what it cannot see. Findings carry file, line, rule, and the verbatim line. | `review Playwright specs`; `audit test flakiness` |
| `playwright-debugger` | Read-only. Reproduces a failing or flaky test, reads trace and error evidence, classifies the cause, and returns the smallest fix as a diff. | `diagnose a failing Playwright test`; `debug flaky end-to-end tests` |

## Skills

| Skill | Path |
|---|---|
| `playwright-testing` | `skills/playwright-testing/SKILL.md` — locators, web-first assertions, fixtures, page objects, tags, parametrization; references for visual comparisons, ARIA snapshots, clock and emulation, frames/dialogs/downloads, component testing, actionability. |
| `playwright-config-and-ci` | `skills/playwright-config-and-ci/SKILL.md` — baseline config, projects, parallelism, timeouts and retries, `webServer`, reporters, CLI, GitHub Actions, global setup. |
| `playwright-debugging` | `skills/playwright-debugging/SKILL.md` — triage procedure, failure-pattern table, trace viewer, debug modes, codegen, flaky diagnosis. |
| `playwright-network-and-auth` | `skills/playwright-network-and-auth/SKILL.md` — `storageState` strategies, mocking and HAR, `waitForResponse`, API testing. |

## Script

| Script | Path |
|---|---|
| `pw-check.py` | `scripts/pw-check.py` — zero-dependency line check of `*.spec.*` and `*.setup.*` files. Rules: PW001 `waitForTimeout`, PW002 `.only`, PW003 `.nth()`, PW004 string `locator()`, PW005 one-shot read inside `expect`, PW006 unawaited `expect`, PW007 `force: true`, PW008 `page.pause()`. `--changed-since REF` limits it to changed files; `pw-check: ignore PW00X` on a line skips a rule there. Exit 0 clean, 1 violations, 3 no specs found. |

## Using it in a harness

| Task | Route |
|---|---|
| Write or extend end-to-end specs | `playwright-test-writer` |
| Review specs or a test diff | `playwright-reviewer` |
| A test fails or is flaky | `playwright-debugger`, then `playwright-test-writer` to apply the fix |

Playwright also ships optional built-in agents (`pnpm exec playwright init-agents`) that drive a
real browser. This plugin does not depend on them.

## Install standalone

```
/plugin install playwright-tools
```
