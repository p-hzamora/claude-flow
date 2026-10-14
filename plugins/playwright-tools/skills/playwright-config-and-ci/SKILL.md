---
name: playwright-config-and-ci
description: Configure and run Playwright Test. Use when creating or changing playwright.config.ts, projects/browsers, workers/sharding, timeouts/retries, webServer, reporters, running tests from the CLI, or setting up CI (GitHub Actions).
---

# Playwright config and CI

## Baseline playwright.config.ts

```ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: 'tests',
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: process.env.CI
    ? [['dot'], ['html', { open: 'never' }]]
    : 'list',
  globalTimeout: process.env.CI ? 30 * 60 * 1000 : undefined,
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: {
    command: 'pnpm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
});
```

Adjust retries, workers and the globalTimeout value to the project; they are starting points, not documented defaults.

## Option placement

- Runner options go at the top level: `testDir`, `projects`, `retries`, `workers`, `reporter`, `timeout`, `globalTimeout`, `expect`, `webServer`, `fullyParallel`, `forbidOnly`.
- Test options go in `use`: `baseURL`, `trace`, `actionTimeout`, `navigationTimeout`, device settings.
- A runner option placed inside `use` is ignored. Move it out.
- `testDir` resolves relative to the config file.

## Decisions

Projects:
- One project per browser/device (`devices[...]`), or per environment (different `baseURL`/`retries`).
- Split files per project with `testMatch` / `testIgnore`.
- Shared setup (login, seed data): a setup project in `dependencies`, not `globalSetup`.
- Details: `references/projects-and-dependencies.md`, `references/global-setup-teardown.md`.

Timeouts:
- Slow test: `test.slow()` or `test.setTimeout(ms)`; do not raise the global value for one test.
- Stuck actions waiting the full test timeout: set `use.actionTimeout` / `navigationTimeout` (both unset by default).
- Slow assertion: per-call `expect(...).toBe...({ timeout })`, else `expect.timeout`.
- Slow fixture: give it its own `{ timeout }`.
- CI run cap: `globalTimeout` in config, so a report is still produced.

Retries:
- Off by default. Enable on CI (1-2); keep 0 locally so flakiness shows.
- A flaky outcome (failed then passed) is not green evidence; consider `--fail-on-flaky-tests` on CI.
- Per group: `test.describe.configure({ retries: 2 })`.

Parallelism:
- Files run in parallel; tests within a file run in order in one worker.
- `fullyParallel: true` parallelizes within files too; only when tests are isolated.
- `workers: 1` disables parallelism; default is 50% of CPU.
- Avoid `serial` mode; prefer independent tests.
- Several machines: `--shard=i/n` with the `blob` reporter, then `merge-reports`.

Reporters:
- Local `list`; CI `dot` plus `html` with `open: 'never'`; `github` for Actions annotations; `blob` for sharded runs; `junit`/`json` for tooling. See `references/reporters.md`.

## Common CLI

```sh
pnpm exec playwright test                              # all, headless
pnpm exec playwright test tests/a.spec.ts:42           # file and line
pnpm exec playwright test -g "login" --project=chromium
pnpm exec playwright test --headed --workers=1
pnpm exec playwright test --ui                         # watch + time travel
pnpm exec playwright test --debug                      # inspector, timeout 0
pnpm exec playwright test --last-failed
pnpm exec playwright test --shard=1/3 --reporter=blob
pnpm exec playwright test --forbid-only --retries=2 --trace on
pnpm exec playwright show-report
pnpm exec playwright show-trace trace.zip
pnpm exec playwright install --with-deps
pnpm exec playwright merge-reports ./blob-report --reporter html
```

Full list: `references/cli-reference.md`.

## CI checklist

1. `pnpm install --frozen-lockfile`, then `pnpm exec playwright install --with-deps` (browsers and OS deps).
2. Set `forbidOnly`, `retries`, `workers`, and a CI reporter from `process.env.CI`.
3. Set `globalTimeout` in config rather than relying on the job timeout.
4. `reuseExistingServer: !process.env.CI` for `webServer`.
5. Upload `playwright-report/` with `if: ${{ !cancelled() }}`.
6. HTML report `open: 'never'` so the run does not block.
7. Never upload traces/reports to untrusted stores (may contain credentials); fork PRs have no secrets.

Workflow example and sharding matrix: `references/ci-github-actions.md`.

## References

- `references/installation.md`: read when scaffolding or updating Playwright.
- `references/cli-reference.md`: read when you need a command or flag not listed above.
- `references/config-options.md`: read when you need an option name, placement or default.
- `references/projects-and-dependencies.md`: read when adding browsers, environments, setup projects.
- `references/timeouts-and-retries.md`: read when tuning timeouts or retry behavior.
- `references/reporters.md`: read when choosing or configuring reporters.
- `references/ci-github-actions.md`: read when writing or fixing a CI workflow.
- `references/global-setup-teardown.md`: read when choosing between project dependencies and globalSetup.
- `references/library-api.md`: read when using Playwright without the test runner.

## Review Checklist

- [ ] Runner options are top level; only test options sit in `use`.
- [ ] `retries`, `workers`, `reporter`, `forbidOnly` depend on `process.env.CI`.
- [ ] `trace` is `on-first-retry` (or stricter), not `on` everywhere.
- [ ] `webServer` has `url`, a sufficient `timeout`, and `reuseExistingServer: !process.env.CI`.
- [ ] Shared setup uses project `dependencies` unless `globalSetup` is justified.
- [ ] No global timeout was raised to hide one slow test or missing action timeout.
- [ ] CI installs browsers with `--with-deps`, sets `globalTimeout`, uploads the report with `!cancelled()`.
- [ ] Sharded runs use the `blob` reporter and a merge step.
