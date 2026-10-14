# Actionability (auto-waiting)

Before each action, Playwright waits for the relevant checks: Visible, Stable, Receives Events, Enabled, Editable. No manual waits are needed.

| Action | Checks |
|---|---|
| click, check, uncheck, dblclick, tap, setChecked | visible, stable, receives events, enabled |
| hover, dragTo | visible, stable, receives events |
| fill, clear | visible, enabled, editable |
| selectOption | visible, enabled |
| screenshot | visible, stable |
| scrollIntoViewIfNeeded | stable |
| focus, press, setInputFiles, blur, dispatchEvent | none |

```ts
await page.getByRole('button', { name: 'Save' }).click(); // waits until actionable
```

## Notes

- `force: true` disables the non-essential checks. On click it skips receives-events and can hit an obscured element. Avoid it; remove the overlay or wait for the real state.
- An action that hangs means one of its checks never passes (hidden, moving, covered, disabled, read-only). Identify which and fix the cause.
- `focus`, `press`, `setInputFiles`, `blur`, `dispatchEvent` do no checks; assert the state first if it matters.

## Sources

- https://playwright.dev/docs/actionability (read 2026-10-13)
