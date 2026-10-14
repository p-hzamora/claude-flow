# Auth strategies

Log in once, save with `storageState` to `playwright/.auth/*.json` (gitignored), load it in projects or tests.

## Shared account

Setup project does the UI login and saves state; browser projects load it.

```ts
projects: [
  { name: 'setup', testMatch: /.*\.setup\.ts/ },
  { name: 'chromium',
    use: { ...devices['Desktop Chrome'], storageState: 'playwright/.auth/user.json' },
    dependencies: ['setup'] },
]
```

```ts
setup('authenticate', async ({ page }) => {
  await page.goto('/login');
  // fill, submit
  await page.waitForURL('/dashboard');
  await page.context().storageState({ path: 'playwright/.auth/user.json' });
});
```

Use only when tests do not mutate server data for that account.

## Per-worker account

Override the `storageState` fixture at worker scope; one account per `parallelIndex`.

```ts
import { test as baseTest, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

export const test = baseTest.extend<{}, { workerStorageState: string }>({
  storageState: ({ workerStorageState }, use) => use(workerStorageState),
  workerStorageState: [async ({ browser }, use) => {
    const id = test.info().parallelIndex;
    const file = path.resolve(test.info().project.outputDir, `.auth/${id}.json`);
    if (fs.existsSync(file)) return use(file);
    const page = await browser.newPage({ storageState: undefined });
    // log in as account `user${id}`, wait for final URL
    await page.context().storageState({ path: file });
    await page.close();
    await use(file);
  }, { scope: 'worker' }],
});
```

Pass `storageState: undefined` when logging in so the default state is not applied.

## API login

Skip the UI.

```ts
setup('authenticate', async ({ request }) => {
  await request.post('/api/login', { data: { user, password } });
  await request.storageState({ path: 'playwright/.auth/user.json' });
});
```

## Multiple roles

Per file or describe:

```ts
test.use({ storageState: 'playwright/.auth/admin.json' });
```

Two roles in one test:

```ts
const adminCtx = await browser.newContext({ storageState: 'playwright/.auth/admin.json' });
const userCtx  = await browser.newContext({ storageState: 'playwright/.auth/user.json' });
const adminPage = await adminCtx.newPage();
const userPage  = await userCtx.newPage();
// ... close both contexts at the end
```

Create one setup test (and one file) per role.

## sessionStorage

`storageState` does not persist it. Capture and restore manually.

```ts
// save (in setup)
const ss = await page.evaluate(() => JSON.stringify(sessionStorage));
fs.writeFileSync('playwright/.auth/session.json', ss);

// restore (in a fixture or beforeEach, before navigation)
const data = JSON.parse(fs.readFileSync('playwright/.auth/session.json', 'utf-8'));
await context.addInitScript(d => {
  if (window.location.hostname === 'app.example.com')
    for (const [k, v] of Object.entries(d)) window.sessionStorage.setItem(k, v as string);
}, data);
```

## Opt out

```ts
test.use({ storageState: { cookies: [], origins: [] } });
```

Use for login-page and anonymous-user tests.

## Pitfalls

- The state file holds sensitive cookies: gitignore it, never commit.
- A shared account is unsafe if tests mutate server data.
- Auth can be browser-specific: do not assume Chromium state works in Firefox or WebKit.
- UI mode skips the setup project by default: run it manually or enable the filter.
- Wait for the final URL after redirects before saving, or state is incomplete.
- State expires: regenerate it (delete the file or rerun setup).
- `--no-deps` skips setup, so dependents may run with missing or stale state.

## Sources

- https://playwright.dev/docs/auth (read 2026-10-13)
- https://playwright.dev/docs/test-global-setup-teardown (read 2026-10-13)
- https://playwright.dev/docs/test-projects (read 2026-10-13)
- https://playwright.dev/docs/test-fixtures (read 2026-10-13)
