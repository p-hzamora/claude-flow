# Config options

Config lives in `playwright.config.ts` via `defineConfig`. Runner options are top level; test options go in `use`. A runner option inside `use` is ignored. `testDir` resolves relative to the config file.

## Top-level (runner) options

| Option | Notes | Default |
| --- | --- | --- |
| `testDir` | test folder | Not recorded (scaffold uses `tests`, or `e2e` if `tests` exists) |
| `projects` | named configurations | none |
| `retries` | retry count | 0 |
| `workers` | number or `'50%'` | 50% of CPU |
| `fullyParallel` | parallelize tests within files (global or per project) | false |
| `reporter` | string or `[name, options]` tuples | `list` local, `dot` CI |
| `timeout` | per test, includes fixtures and `beforeEach` | 30s |
| `globalTimeout` | whole run | none |
| `expect.timeout` | assertion timeout | 5s |
| `expect.toHaveScreenshot` / `toMatchSnapshot` | tolerances: `maxDiffPixels`, `maxDiffPixelRatio` (0-1) | Not recorded |
| `webServer` | start the app first | none |
| `globalSetup` / `globalTeardown` | module paths | none |

## `use` (test options)

| Option | Notes | Default |
| --- | --- | --- |
| `baseURL` | lets `goto('/path')` work | none |
| `trace` | `on`, `off`, `on-first-retry`, `retain-on-failure` | Not recorded |
| `actionTimeout` | per action | none |
| `navigationTimeout` | per navigation | none |

## Example

```ts
export default defineConfig({
  testDir: 'tests',
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: { baseURL: 'http://localhost:3000', trace: 'on-first-retry' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'pnpm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## webServer options

| Option | Notes | Default |
| --- | --- | --- |
| `command` | start command | required |
| `url` | ready when it answers 2xx/3xx/400-403 | none |
| `port` | deprecated, use `url` | none |
| `reuseExistingServer` | usually `!process.env.CI`; when false, throws if the port is in use | Not recorded |
| `timeout` | startup wait, ms | 60000 |
| `env` | environment | `process.env` plus `PLAYWRIGHT_TEST=1` |
| `cwd` | working dir | Not recorded |
| `stdout` / `stderr` | output handling | `ignore` / `pipe` |
| `name`, `ignoreHTTPSErrors` | label, TLS | Not recorded |
| `wait` | `{ stdout: /regex(?<name>..)/ }` stores the capture in env | none |
| `gracefulShutdown` | `{ signal, timeout }`; not on Windows | none (SIGKILL to process group) |

Pass an array for multiple servers. Pair with `use.baseURL`. Slow startup needs a larger `timeout`.

## Sources

- https://playwright.dev/docs/test-configuration (read 2026-10-13)
- https://playwright.dev/docs/test-webserver (read 2026-10-13)
