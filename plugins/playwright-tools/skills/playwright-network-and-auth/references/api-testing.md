# API testing

## request fixture

Built in; honors `use.baseURL`, `extraHTTPHeaders` and `proxy`.

```ts
// playwright.config.ts
use: { baseURL: 'https://api.example.com', extraHTTPHeaders: { Authorization: `Bearer ${process.env.API_TOKEN}` } }
```

```ts
test('create and read', async ({ request }) => {
  const created = await request.post('/items', { data: { name: 'demo' } });
  expect(created.ok()).toBeTruthy();
  const item = await created.json();
  const got = await request.get(`/items/${item.id}`);
  expect(got.ok()).toBeTruthy();
  expect(await got.json()).toMatchObject({ name: 'demo' });
});
```

Always check `.ok()` before reading the body.

## State setup and teardown

```ts
let itemId: string;
test.beforeAll(async ({ request }) => {
  const r = await request.post('/items', { data: { name: 'seed' } });
  expect(r.ok()).toBeTruthy();
  itemId = (await r.json()).id;
});
test.afterAll(async ({ request }) => { await request.delete(`/items/${itemId}`); });
```

## Standalone context

Outside a test (scripts, fixtures, `beforeAll` with custom config):

```ts
import { request } from '@playwright/test';
const ctx = await request.newContext({ baseURL: 'https://api.example.com' });
// ... calls
await ctx.dispose();
```

Same as `playwright.request.newContext`. Always `dispose()`.

## Cookies: isolated vs shared

- `page.request` and `context.request` share cookies with the browser context: API calls can log in or alter the browser session.
- `request` fixture and `playwright.request.newContext` have isolated cookies: use when API calls must not alter the browser session.
- `apiRequestContext.storageState()` exports state to seed a browser context (`browser.newContext({ storageState })`).

## Mixing API and UI

- API then UI: create data via API, `page.goto`, verify in the page.
- UI then API: act in the UI, verify the server state via API.

```ts
test('item shows in list', async ({ page, request }) => {
  const r = await request.post('/items', { data: { name: 'demo' } });
  expect(r.ok()).toBeTruthy();
  await page.goto('/items');
  await expect(page.getByText('demo')).toBeVisible();
});
```

## Pitfalls

- Skipping the `.ok()` check hides setup failures until a confusing UI error.
- Shared-cookie contexts change browser auth state unexpectedly.
- Leaked standalone contexts keep resources open; dispose them.

## Sources

- https://playwright.dev/docs/api-testing (read 2026-10-13)
