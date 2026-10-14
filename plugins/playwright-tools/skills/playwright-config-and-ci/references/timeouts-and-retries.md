# Timeouts and retries

## Timeouts

| Timeout | Default | Set with |
| --- | --- | --- |
| Test | 30s | config `timeout`, `test.setTimeout`, `testInfo.setTimeout` |
| Expect | 5s | `expect.timeout` or per call |
| Action | none | `use.actionTimeout` |
| Navigation | none | `use.navigationTimeout` |
| Global | none | `globalTimeout` |
| `beforeAll` / `afterAll` | 30s | Not recorded |
| Fixture | shares the test timeout | `{ timeout }` on the fixture |

- `test.slow()` triples the test timeout.
- With no action timeout, a stuck action waits the whole test timeout.

```ts
test.setTimeout(120_000);
// config
use: { actionTimeout: 10_000 }
```

## Retries

Off by default. Enable with:

```sh
pnpm exec playwright test --retries=3
```

```ts
retries: process.env.CI ? 2 : 0,
// per group
test.describe.configure({ retries: 2 });
```

- Outcomes: passed, flaky (failed then passed on retry), failed.
- A failure discards the worker and browser; a new worker runs the retry.
- Serial groups retry as a whole, including `beforeAll`.
- `testInfo.retry` exposes the retry index.
- `--repeat-each` and `--fail-on-flaky-tests` are CLI flags (see cli-reference.md).

## Sources

- https://playwright.dev/docs/test-timeouts (read 2026-10-13)
- https://playwright.dev/docs/test-retries (read 2026-10-13)
