# Flaky Diagnosis

## Retries
- Off by default. Enable: `--retries=3`, `retries` in config, or `test.describe.configure({ retries: 2 })`.
- Outcomes: passed, flaky (failed then passed on retry), failed.
- A failure discards the worker and browser; a new worker runs the retry (clean state).
- Serial groups retry as a whole, including `beforeAll`.
- `testInfo.retry` gives the retry index (use for diagnostics, for example to reset state or log).
- `--fail-on-flaky-tests` makes flaky outcomes fail the run (CLI flag).
- Retries are a detector, not a fix. A "flaky" result means find the cause.

## Timeouts
| Kind | Default | Control |
| --- | --- | --- |
| Test | 30s | `timeout`, `test.setTimeout`, `testInfo.setTimeout`, `--timeout` (0 = none) |
| Expect | 5s | `expect.timeout` or per call |
| Action | none | `use.actionTimeout` |
| Navigation | none | `use.navigationTimeout` |
| Global | none | `globalTimeout` |
| beforeAll/afterAll | 30s | own timeout |
| Fixture | shares test timeout | `{ timeout }` |
`test.slow()` triples the test timeout. With no action timeout, a stuck action waits the whole test timeout.

## Classification procedure
1. `--repeat-each=N --workers=1` on one test: still flaky means timing or the app.
2. Fails only with parallel workers: shared state or data collision.
3. Passes locally, fails on CI: environment (resources, config, data).
4. Trace the failing run (`--trace on`); a trace on a passing run helps compare.
5. Also useful: `--shuffle [seed]` (ordering dependence), `--last-failed`, `--max-failures`/`-x`.

## Common causes (recorded)
- Unawaited `expect`; non-retrying assertion on an async value; one-shot `isVisible()` check.
- `force: true` clicking obscured elements; `nth()` retargeting.
- Strictness violations when a list changes size.
- Soft assertions only work in the Playwright runner; stop after soft failures with `expect(test.info().errors).toHaveLength(0)`.

## Not recorded
Isolation of storage/auth state between tests, route ordering, dialogs, downloads, OS screenshot differences.

## Sources
- https://playwright.dev/docs/test-retries (read 2026-10-13)
- https://playwright.dev/docs/test-timeouts (read 2026-10-13)
- https://playwright.dev/docs/test-cli (read 2026-10-13)
- https://playwright.dev/docs/test-assertions (read 2026-10-13)
- https://playwright.dev/docs/actionability (read 2026-10-13)
- https://playwright.dev/docs/locators (read 2026-10-13)
