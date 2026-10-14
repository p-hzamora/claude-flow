# Installation and project structure

```sh
pnpm create playwright@latest
```

Scaffolds Playwright or adds it to an existing project. Prompts: TypeScript or JavaScript (default TypeScript), tests folder (default `tests`, or `e2e` if `tests` exists), a GitHub Actions workflow, install browsers. Re-running does not overwrite existing tests.

Creates `playwright.config.ts`, package.json plus a lockfile, and `tests/example.spec.ts`. Tests run headless, in parallel, across Chromium, Firefox and WebKit by default.

## Run

```sh
pnpm exec playwright test
pnpm exec playwright test --headed
pnpm exec playwright test --project=chromium
pnpm exec playwright test tests/example.spec.ts
pnpm exec playwright test --ui
pnpm exec playwright show-report
```

## Update

```sh
pnpm add -D @playwright/test@latest
pnpm exec playwright install --with-deps
pnpm exec playwright --version
```

## Pitfalls

- The HTML report opens automatically only when tests fail.
- `--ui` gives watch mode, live steps and time-travel debugging.

## Sources

- https://playwright.dev/docs/intro (read 2026-10-13)
