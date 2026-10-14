---
name: playwright-network-and-auth
description: Use when authenticating Playwright tests (storageState, setup projects, multiple roles, per-worker accounts), mocking or modifying API responses with page.route, recording or replaying HAR files, waiting on network responses, or testing APIs with the request fixture.
---

# Playwright Network and Auth

Log in once, reuse the saved state, and mock only the network you do not control.

## Choose an auth strategy

1. Tests do not mutate server data and one account suffices: shared account, one setup project.
2. Tests mutate server data per user: per-worker account, a worker-scoped `storageState` fixture keyed on `test.info().parallelIndex`.
3. A login endpoint exists: API login (`request.post`, then `request.storageState`), faster than the UI.
4. Several roles: one setup per role and one state file each; pick with `test.use({ storageState })` per file or describe, or `browser.newContext({ storageState })` for two roles in one test.
5. A test must start logged out: `test.use({ storageState: { cookies: [], origins: [] } })`.

Details and pitfalls: [auth-strategies.md](references/auth-strategies.md). Read when picking or debugging a strategy, handling `sessionStorage`, or opting out.

## Setup project recipe

```ts
// playwright.config.ts
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
  {
    name: 'chromium',
    use: { ...devices['Desktop Chrome'], storageState: 'playwright/.auth/user.json' },
    dependencies: ['setup'],
  },
],
```

```ts
// auth.setup.ts
import { test as setup, expect } from '@playwright/test';
const authFile = 'playwright/.auth/user.json';

setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  await page.getByLabel('Username').fill(process.env.E2E_USER!);
  await page.getByLabel('Password').fill(process.env.E2E_PASSWORD!);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('/dashboard');            // final URL, after redirects
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  await page.context().storageState({ path: authFile });
});
```

Setup and teardown must be real `test()` calls. Prefer dependencies over `globalSetup`: they appear in reports and traces and can use fixtures.

## Mocking recipes

Register routes before `page.goto`.

```ts
// Fulfill: no network call
await page.route('*/**/api/v1/fruits', route =>
  route.fulfill({ json: [{ name: 'Strawberry', id: 21 }] }));

// Modify the real response
await page.route('*/**/api/v1/fruits', async route => {
  const response = await route.fetch();
  const json = await response.json();
  json.push({ name: 'Loquat', id: 100 });
  await route.fulfill({ response, json });
});

// Abort
await page.route('**/*.{png,jpg}', route => route.abort());

// Continue, optionally altered
await page.route('**/api/**', route =>
  route.continue({ headers: { ...route.request().headers(), 'x-test': '1' } }));

// Fallback: defer to the next matching handler
await page.route('**/api/**', route => route.fallback());

// Wait for a response: promise BEFORE the action, await AFTER
const responsePromise = page.waitForResponse(r =>
  r.url().includes('/api/items') && r.status() === 200);
await page.getByRole('button', { name: 'Load' }).click();
const response = await responsePromise;
```

```ts
// HAR: record once, replay afterwards
await page.routeFromHAR('tests/hars/items.har', { url: '**/api/**', update: true });
await page.routeFromHAR('tests/hars/items.har', { url: '**/api/**' });
```

- Globs, context vs page routing, redirects, events: [network-mocking.md](references/network-mocking.md). Read when a route does not match or must cover popups.
- Recording, replaying, CLI capture: [har.md](references/har.md). Read when you want recorded traffic instead of hand-written mocks.

## API testing recipe

```ts
test('creates an item', async ({ request }) => {
  const res = await request.post('/items', { data: { name: 'demo' } });
  expect(res.ok()).toBeTruthy();
  expect(await res.json()).toMatchObject({ name: 'demo' });
});
```

The `request` fixture honors `baseURL`, `extraHTTPHeaders` and `proxy`. Details: [api-testing.md](references/api-testing.md). Read when you need a standalone context, isolated cookies, or API-plus-UI tests.

## Rules

- Store state files in `playwright/.auth/` and add that folder to `.gitignore`. Never commit state: it holds live cookies.
- Register routes before `page.goto` or the triggering action.
- Mock only what you do not control (third parties, flaky or costly services, hard-to-reach error states). Keep your own backend real in end-to-end tests.
- Create the `waitForResponse` promise before the action, await it after.
- Wait for the post-login URL before saving state; regenerate expired state.
- Check `response.ok()` on every API call that sets up data.
- Credentials come from environment variables, never from source.

## Review Checklist

- [ ] State files live in `playwright/.auth/` and that path is gitignored; none is committed.
- [ ] The auth strategy matches the data-mutation profile (shared, per-worker, API, multi-role).
- [ ] The setup project is a `test()`, listed in `dependencies`, and waits for the final URL before saving state.
- [ ] Routes are registered before `goto` or the triggering action.
- [ ] Only external or uncontrollable endpoints are mocked; globs match the whole URL.
- [ ] Every `waitForResponse` promise is created before the action and awaited after.
- [ ] API calls check `.ok()`; standalone request contexts are disposed.
- [ ] Logged-out tests opt out of `storageState` explicitly; credentials come from env vars.
