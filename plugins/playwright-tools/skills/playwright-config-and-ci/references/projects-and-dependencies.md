# Projects and dependencies

A project is a named configuration run.

## Uses

- Browsers and devices via the `devices[...]` registry.
- `channel: 'chrome'` for branded browsers.
- Different `baseURL` or `retries` per environment.
- `testMatch` / `testIgnore` to split files.
- `fullyParallel` per project.

## Dependencies and teardown

- `dependencies: ['setup']` runs the setup project first; dependents then run in parallel.
- A failed dependency skips its dependents.
- `teardown` on the setup project names a project that runs after all dependents finish.
- `--project=firefox` selects a project; dependencies of the selected tests also run.
- `--no-deps` skips dependencies and teardowns.

```ts
projects: [
  { name: 'setup', testMatch: '**/*.setup.ts' },
  { name: 'chromium', use: { ...devices['Desktop Chrome'] }, dependencies: ['setup'] },
]
```

With teardown:

```ts
projects: [
  { name: 'setup db', testMatch: /global\.setup\.ts/, teardown: 'cleanup db' },
  { name: 'cleanup db', testMatch: /global\.teardown\.ts/ },
  { name: 'chromium', dependencies: ['setup db'] },
]
```

## Pitfalls

- `--grep`, `--shard` and `test.only` still pull in dependencies.
- `--no-deps` can leave dependents running against missing state.
- Parametrized projects: Not recorded.

## Sources

- https://playwright.dev/docs/test-projects (read 2026-10-13)
