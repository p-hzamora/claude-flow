# Library API (no test runner)

Install: `pnpm add -D playwright`, then `pnpm exec playwright install chromium`. Import from `playwright` and run with node.

You launch the browser, create context and page, and close them yourself. There are no web-first assertions, and operations have ~30s timeouts.

```ts
import { chromium, devices } from 'playwright';

const browser = await chromium.launch();
const context = await browser.newContext(devices['iPhone 11']);
const page = await context.newPage();
await context.route('**.jpg', r => r.abort());
await page.goto('https://example.com/');
await context.close();
await browser.close();
```

The runner (`@playwright/test`) adds fixtures, assertions, projects, parallelism, reporters, retries and tracing.

## Pitfalls

- Forgetting `close()` keeps the process alive.
- Do not mix `playwright` and `@playwright/test` imports for tests.

## Sources

- https://playwright.dev/docs/library (read 2026-10-13)
