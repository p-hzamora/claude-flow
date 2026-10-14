# HAR record and replay

## Record from a test

```ts
await page.routeFromHAR('tests/hars/api.har', {
  url: '**/api/**',
  update: true,       // record real traffic into the file
});
await page.goto('/');
```

## Replay

```ts
await page.routeFromHAR('tests/hars/api.har', { url: '**/api/**' });  // update defaults to false
```

- Matching uses URL and method, and the POST payload for POST requests.
- `url` limits which requests are served from the HAR; others go to the network.
- Call before `page.goto`.

## Record from the CLI

```sh
pnpm exec playwright open --save-har=api.har --save-har-glob="**/api/**" https://example.com
```

Browse the flow, close the browser, and the HAR is written.

## Workflow

1. Record once against a real environment with `update: true`.
2. Switch to replay (remove `update`) and commit the HAR only if it holds no secrets.
3. Re-record when the API contract changes.

## Pitfalls

- HARs may contain tokens, cookies and personal data: review before committing.
- Stale HARs mask API changes; re-record on contract changes.
- Leaving `update: true` in place re-records on every run.
- Narrow `url` to the API; recording everything bloats the file.

## Sources

- https://playwright.dev/docs/mock (read 2026-10-13)
- https://playwright.dev/docs/network (read 2026-10-13)
