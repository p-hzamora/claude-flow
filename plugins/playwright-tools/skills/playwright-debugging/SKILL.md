---
name: playwright-debugging
description: Diagnose failing or flaky Playwright tests, read traces, reproduce failures, pick a debug mode, and use codegen to find locators. Use for "test fails", "flaky", "timeout", "trace viewer", "strict mode violation", "debug playwright".
---

# Playwright Debugging

Find the cause from evidence, make the smallest fix, re-run to confirm. Never raise timeouts or add retries as a first move.

## Triage procedure

1. **Reproduce narrowly.** Run one project and one test:
   `pnpm exec playwright test path/file.spec.ts:LINE --project=chromium --workers=1 --trace on`
   Use `-g "title"` if the line is unknown. `--workers=1` removes parallel interference.
2. **Check flakiness.** Add `--repeat-each=N` (for example 10). Fails always: deterministic. Fails sometimes: timing, data or isolation. Fails only with default workers but not `--workers=1`: shared state or ordering.
3. **Read the evidence.** Open the trace (`pnpm exec playwright show-trace <trace.zip>` or the HTML report). Go to the failing action: read the error, log (actionability waits), before/after DOM snapshot, network, console. See `references/trace-viewer.md`.
4. **Classify** the failure:
   - **Locator**: matches 0 or several elements, or the wrong one.
   - **Timing/assertion**: a check ran once instead of retrying, or a missing `await`.
   - **Data/isolation**: depends on state left by another test or a previous run.
   - **Environment**: browser, OS, CI resources, config, base URL, credentials.
   - **Real bug**: the app behaves wrongly; the trace shows it. Report it, do not mask it.
5. **Fix minimally.** One change that addresses the classified cause (table below). Do not touch unrelated tests.
6. **Confirm.** Re-run the same command plus `--repeat-each`. Then run the whole file without the narrowing flags.

If stuck interactively, switch to a debug mode (`references/debug-modes.md`). If the trace is missing, re-run with `--trace on`.

## Failure pattern, cause, fix

| Symptom | Cause | Fix |
| --- | --- | --- |
| Error: locator resolved to multiple elements (strictness) | Action on a locator matching more than one element | Narrow with role/name, `.filter({ hasText })`, chaining, `.and()`. `first()`/`last()`/`nth()` opt out of strictness but retarget silently when the page changes; last resort |
| Assertion passes or fails inconsistently; no waiting | `expect` not awaited | `await` every web-first `expect` |
| `expect(await loc.isVisible()).toBe(true)` flakes | Checks once, no retry | `await expect(loc).toBeVisible()` |
| `toBe`/`toEqual`/`toHaveLength` on async value flakes | Non-retrying assertion | Use a web-first assertion, `expect.poll(fn)` or `expect(...).toPass()` |
| Click lands on wrong/obscured element | `force: true` skips the receives-events check | Remove `force`; wait for the overlay to go, fix the real blocker |
| Test passes alone, fails in suite (or reverse) | Shared state across tests | Make each test set up its own data; prove with `--workers=1` and `--repeat-each` |
| "Test timeout of 30000ms exceeded" | Whole test too slow, or a stuck action (no action timeout by default) | Find the slow/stuck step in the trace; set `use.actionTimeout` to fail fast; `test.slow()` or `test.setTimeout` only if the work is legitimately long |
| "Timeout 5000ms" on `expect` | Expect timeout (5s) | Verify the condition can become true; raise per call only when justified |
| Hook or fixture times out | `beforeAll`/`afterAll` have own 30s; a fixture shares the test timeout | Give the fixture `{ timeout }` |
| Fails after being fine for days; redirects to login | Auth state expiry | Not recorded in the sources; verify in the trace and regenerate the stored state |
| Mock/route not applied | Route registered after `goto` | Not recorded in the sources; check order in the trace network tab |
| Test hangs on a dialog | Dialog listener never resolves | Not recorded in the sources; inspect the trace |
| Download assertion fails | Download not awaited | Not recorded in the sources; inspect the trace |
| Screenshot diff only on another machine | OS-dependent screenshots | Not recorded; `-u` updates snapshots, regenerate on the target environment only after confirming the diff is benign |

Rows marked "Not recorded" are common patterns whose details were not verified; confirm with the trace and official docs before acting.

## Debug tooling cheat sheet

| Tool | Use |
| --- | --- |
| `--debug` | Headed, timeout 0, opens Inspector: step, pick locator, see actionability log |
| `await page.pause()` | With `--debug`, stops at that line; Resume continues |
| `PWDEBUG=console` | Exposes `playwright` in DevTools (`$`, `$$`, `locator`, `selector`, `inspect`) |
| `DEBUG=pw:api` | Verbose API call logs |
| `--ui` | UI mode; preferred for local debugging |
| `--trace on` | Always record a trace locally |
| `show-trace` | Open a trace zip |
| `codegen [url]` | Record actions, pick locators |
| `--headed`, `slowMo` | Watch the run; `chromium.launch({ headless: false, slowMo: 100 })` |

Details: `references/debug-modes.md`, `references/codegen.md`, `references/flaky-diagnosis.md`.

## Escalation: built-in agents

Playwright ships optional agents (planner, generator, healer), installed with `pnpm exec playwright init-agents --loop=<vscode|claude|codex|opencode>`. They drive a real browser; the healer replays a failing test, inspects the UI, patches locators/waits/data and re-runs. Their tool details and guardrails are Not recorded here. Never depend on them: the procedure above must work without them. Treat any healer patch as a proposal and review it against the trace.

## Review Checklist

- [ ] Failure reproduced with a single `file:line`, `--project`, `--workers=1`, and `--repeat-each` before changing anything
- [ ] Cause classified (locator, timing/assertion, data/isolation, environment, real bug) with trace evidence cited
- [ ] No `force: true`, `nth()`, blanket timeout increase or added retry used to hide the cause
- [ ] Every `expect` is awaited and web-first (no `expect(await x.isVisible())`)
- [ ] Fix is minimal and limited to the failing test or its direct helper
- [ ] Re-run passed repeatedly (`--repeat-each`) and the full file passes without narrowing flags
- [ ] Unverified patterns reported as unverified, real app bugs reported rather than masked
