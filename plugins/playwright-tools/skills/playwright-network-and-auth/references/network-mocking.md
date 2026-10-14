# Network mocking

`page.route(urlGlob, handler)` intercepts matching requests. Register before `page.goto`.

## Glob rules

- `*` matches within one path segment, not across `/`.
- `**` matches across `/`.
- `{a,b}` alternates: `**/*.{png,jpg}`.
- The pattern must match the whole URL, so prefix with `*/**/` or `**/` to ignore the origin.
- Use a RegExp or predicate function for complex cases.

## Page vs context routing

- `page.route` affects that page only.
- `context.route` affects all pages of the context, including popups and pages opened later. Use it when the app opens new windows.

## Route methods

```ts
await page.route('**/api/items', route => route.fulfill({ status: 200, json: [] }));   // mock, no network
await page.route('**/api/items', async route => {                                      // modify real response
  const response = await route.fetch();
  await route.fulfill({ response, json: { ...(await response.json()), extra: true } });
});
await page.route('**/api/**', route => route.continue({ method: 'POST', headers: {...route.request().headers(), 'x-a': '1'} })); // pass through, altered
await page.route('**/*.png', route => route.abort());                                  // fail request
await page.route('**/api/**', route => route.fallback());                               // defer to next handler
```

- `fulfill` takes `json`, `status`, `body`, `headers`, or `response` plus overrides.
- `continue` accepts `method`, `headers`, `url`, `postData`.
- Handlers run most recently registered first; `fallback()` passes to the previous one, `continue()` ends the chain.
- Remove with `page.unroute(glob)`.

## Waiting and events

```ts
const p = page.waitForResponse('**/api/items');   // create BEFORE the action
await page.getByRole('button', { name: 'Load' }).click();
const res = await p;                               // await AFTER
```

Accepts a URL glob, RegExp, or predicate. Observe traffic with `page.on('request', r => ...)` and `page.on('response', r => ...)`.

`waitForRequest`: Not recorded.

## Redirects and headers

- Fulfilling with a 3xx does not re-intercept the redirected request.
- A `cookie` header passed to `route.continue` is ignored.
- `request.allHeaders()` is complete only when no routes are involved; with routing, use it with care.

## Pitfalls

- Route registered after `goto` misses early requests.
- Glob without the origin prefix silently matches nothing.
- Mocking your own backend hides integration bugs; mock third parties.

## Sources

- https://playwright.dev/docs/mock (read 2026-10-13)
- https://playwright.dev/docs/network (read 2026-10-13)
