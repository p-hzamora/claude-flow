# Global setup and teardown

Two ways to run setup/teardown once around a run.

## Recommended: project dependencies

A setup project (`testMatch` e.g. `global.setup.ts`) is listed in `dependencies` of the projects that need it. It can name a `teardown` project that runs after all dependents. Setup and teardown must be regular `test()` calls.

Benefits: appear in the HTML report and traces, can use fixtures and the `browser` fixture, config options like `headless` apply.

```ts
projects: [
  { name: 'setup db', testMatch: /global\.setup\.ts/, teardown: 'cleanup db' },
  { name: 'cleanup db', testMatch: /global\.teardown\.ts/ },
  { name: 'chromium', dependencies: ['setup db'] },
]
```

## Second: globalSetup / globalTeardown

Config keys pointing to modules that each export one function receiving the config. The setup function may return a function used as teardown. Pass data to tests through `process.env`.

Drawbacks: no report entry, no traces, no fixtures, manual `browserType.launch()`, `headless` and `testIdAttribute` ignored.

```ts
export default defineConfig({
  globalSetup: require.resolve('./global-setup'),
  globalTeardown: require.resolve('./global-teardown'),
});
```

(The `require.resolve` form is the usual style; exact form Not recorded.)

## Choosing

- Dependencies: new setup, reporting, shared login.
- `globalSetup`: minimal, legacy, or non-test setup.

## Pitfalls

- A plain function as a dependency setup does not work; it must be a `test()`.
- `--no-deps` skips setup and teardown; dependents may hit missing state.
- Env vars set in `globalSetup` are visible only inside `test()` bodies, not at module scope.
- Filters (`--grep`, `--shard`, `test.only`) still pull in dependencies.
- To trace a `globalSetup` failure: start tracing, wrap in try/catch, stop tracing in both branches, rethrow.

## Sources

- https://playwright.dev/docs/test-global-setup-teardown (read 2026-10-13)
