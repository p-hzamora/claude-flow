# Debug Modes

## `--debug`
Runs headed, sets timeout to 0, opens the Inspector: step through, pick a locator, view the actionability log. Accepts `inspector|cli`.
```
pnpm exec playwright test example.spec.ts:10 --project=chromium --debug
```
Always narrow with `file:line` and `--project`.

## `page.pause()`
With `--debug`, execution stops there; Resume continues.

## Environment variables
- `PWDEBUG=console`: exposes a `playwright` object in browser DevTools: `playwright.$`, `$$`, `locator`, `selector`, `inspect`.
- `DEBUG=pw:api`: verbose API logs.

## Headed in code
`chromium.launch({ headless: false, slowMo: 100 })`

## Other
- `--headed` shows the browser without the Inspector.
- UI mode (`--ui`): preferred locally.
- VS Code extension: breakpoints, Debug Test, Show Browser.

## Pitfalls
- `--debug` timeout 0 hides timeout failures; reproduce timeouts without it.
- Details of `--debug cli` vs `inspector`: Not recorded.

## Sources
- https://playwright.dev/docs/debug (read 2026-10-13)
- https://playwright.dev/docs/test-cli (read 2026-10-13)
