---
name: playwright-testing
description: Use when writing, extending, refactoring, or reviewing Playwright Test specs in TypeScript or JavaScript (locators, web-first assertions, fixtures, page objects, tags, parametrized tests, snapshots, flaky-test fixes). Trigger words - playwright, spec, e2e test, getByRole, expect, toHaveScreenshot, test.extend.
---

# Playwright Testing

Write isolated, user-visible, auto-waiting tests with `@playwright/test`.

## Core workflow for a spec

1. Import `test` and `expect` from `@playwright/test`, or from the project's fixtures file if one exists (check first, reuse it).
2. Name the user behavior under test; one behavior per `test()`.
3. Navigate with `page.goto`, act through locators, assert with web-first assertions.
4. Put shared setup in `beforeEach` or a fixture. `beforeAll`/`afterAll` run once per worker, so never rely on them for per-test state.
5. Run the spec and confirm it passes; run it repeatedly (`--repeat-each=5`) if it touched timing.

```ts
import { test, expect } from '@playwright/test';

test('get started link opens installation', async ({ page }) => {
  await page.goto('https://playwright.dev/');
  await page.getByRole('link', { name: 'Get started' }).click();
  await expect(page.getByRole('heading', { name: 'Installation' })).toBeVisible();
});
```

Each test gets a fresh `page` from a new browser context, so no state leaks between tests.

## Locator priority

Pick the first that works:

1. `getByRole` (with `name`)
2. `getByLabel`
3. `getByPlaceholder`
4. `getByText`
5. `getByAltText`
6. `getByTitle`
7. `getByTestId` (`data-testid`; change via `testIdAttribute`). Add a test id when no accessible attribute exists.
8. `page.locator` with CSS/XPath: last resort, never long chains.

Narrow scope by chaining and filtering instead of indexing:

```ts
await page.getByRole('listitem').filter({ hasText: 'Product 2' })
  .getByRole('button', { name: 'Add to cart' }).click();
```

Tools: `.filter({ hasText, hasNotText, has, hasNot, visible })`, `.and()` (both match), `.or()` (either). Strictness: an action on a locator matching several elements throws; fix the locator, do not add `.first()`/`.nth()`.

## Web-first assertions

- Always `await expect(locator).toXxx()`; they retry until the timeout (default 5s).
- Prefer: `toBeVisible/Hidden/Enabled/Disabled/Checked/Focused/Attached`, `toHaveText/ContainText/Value/Count/Attribute/Class`, `toHaveURL`, `toHaveTitle`, `toHaveRole/AccessibleName`, `toHaveScreenshot`, `toMatchAriaSnapshot`.
- Never `expect(await locator.isVisible()).toBe(true)`: checks once, no waiting.
- Generic matchers (`toBe`, `toEqual`, `toContain`) do not retry; use them only on already-resolved values.
- Polling non-locator values: `await expect.poll(async () => (await page.request.get(url)).status()).toBe(200)`. Retrying a block: `expect(async () => {...}).toPass()`.
- `expect.soft(...)` records a failure and continues; add `expect(test.info().errors).toHaveLength(0)` to stop after soft failures. Custom message goes as 2nd argument to `expect`.

## Fixtures and page objects

- Built-ins: `page`, `context`, `browser`, `browserName`, `request`.
- Custom fixture: `base.extend<T>({ name: async ({ page }, use) => { setup; await use(value); teardown } })`. Code after `use()` is teardown. Export `expect` alongside the extended `test`.
- A fixture runs only if a test names it, unless `[fn, { auto: true }]`. Worker scope: `{ scope: 'worker' }`. Per-project option: `{ option: true }`. Combine with `mergeTests(a, b)`.
- Page object: locators in the constructor (built-in locators, not CSS), actions as methods, no assertions hidden in helpers unless named for it. Expose it as a fixture rather than constructing it in every test.

```ts
export const test = base.extend<{ todoPage: TodoPage }>({
  todoPage: async ({ page }, use) => {
    const p = new TodoPage(page);
    await p.goto();
    await use(p);
    await p.removeAll();
  },
});
export { expect } from '@playwright/test';
```

## Annotations and tags

- `test.skip` (not applicable), `test.fixme` (known broken, not run), `test.fail` (expected to fail), `test.slow` (3x timeout), `test.only` (local focus only; CI uses `--forbid-only`).
- Conditional: `test.skip(browserName === 'firefox', 'reason')`. Always give a reason.
- Tags: `test('x', { tag: '@fast' }, fn)`. Filter: `--grep @fast`, `--grep-invert @fast`, OR `"@fast|@slow"`, AND `"(?=.*@fast)(?=.*@slow)"`.
- Custom annotation: `{ annotation: { type: 'issue', description: url } }`; shows in the HTML report.

## Parametrization

- Loop data and call `test()` per entry; titles must be unique or the run fails.
- Hooks outside the loop run once; wrap each iteration in `test.describe` for per-iteration hooks.
- Per-project values: an option fixture `[default, { option: true }]` overridden in config `use`.
- Environment values: read `process.env` (e.g. baseURL per environment); do not hard-code.

```ts
[{ name: 'Alice', expected: 'Hello, Alice!' }].forEach(({ name, expected }) => {
  test(`greets ${name}`, async ({ page }) => { /* ... */ });
});
```

## Rules

- Always `await` every `expect` and every Playwright call; lint with `@typescript-eslint/no-floating-promises`.
- No manual waits (`waitForTimeout`, sleeps); rely on auto-waiting and web-first assertions.
- No `force: true`; fix the real obstruction instead.
- No `nth()`/`first()`/`last()` to dodge strictness; they silently retarget when the page changes.
- Tests are isolated: no ordering, no shared mutable state, own data.
- Test user-visible behavior, not implementation details or CSS structure.
- Mock third-party responses with `page.route`; reuse signed-in state via a setup project.
- Traces `on-first-retry`, not on every test.

## References

- `references/actionability.md`: read when an action hangs, or deciding what a click/fill/check waits for.
- `references/visual-comparisons.md`: read when adding or tuning `toHaveScreenshot` baselines.
- `references/aria-snapshots.md`: read when asserting page structure with `toMatchAriaSnapshot`.
- `references/clock-and-emulation.md`: read when a test depends on time, timers, device, locale, timezone, permissions, or color scheme.
- `references/frames-dialogs-downloads.md`: read when handling iframes, alert/confirm/prompt dialogs, or file downloads.
- `references/component-testing.md`: read when testing UI components in isolation with the `mount` fixture.

## Review Checklist

- [ ] Every `expect` and Playwright call is awaited.
- [ ] Locators follow the priority order; no `nth`/`first`/`last`, no long CSS chains.
- [ ] Only web-first assertions on page state; no `isVisible()` inside `expect(...).toBe`.
- [ ] No `waitForTimeout`, no `force: true`.
- [ ] Each test is independent and uses its own data; setup lives in fixtures or `beforeEach`.
- [ ] Page objects use built-in locators and are provided via fixtures.
- [ ] Skips and fixmes have a reason; no stray `test.only`; tags use `@name`.
- [ ] Parametrized titles are unique; snapshots reviewed, masked for dynamic content.
