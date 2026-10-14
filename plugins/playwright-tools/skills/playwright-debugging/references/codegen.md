# Codegen

`pnpm exec playwright codegen [url]` opens a browser plus the Inspector; interactions become code.

## Use
- Record button starts/stops; copy the code; clear to restart.
- Assertion toolbar adds assert visibility, text, value.
- After stopping, "Pick Locator": hover/click an element to see its locator in the playground; edit and copy.
- Emulation: viewport, device, color scheme, geolocation, language, timezone.

## Options
`-b` browser, `-o` output file, `--target` (javascript, playwright-test, python), `--test-id-attribute`.
```
pnpm exec playwright codegen --target=playwright-test -o tests/new.spec.ts https://playwright.dev
```

## Using it for debugging
Use Pick Locator to find a unique locator for an element a strictness violation or wrong match involved. Then refine.

## Locator preference
`getByRole`, `getByLabel`, `getByPlaceholder`, `getByText`, `getByAltText`, `getByTitle`, `getByTestId`; CSS/XPath last. Generated locators are a starting point: refine to role, label or test id. Add test ids when no accessible attribute exists.

## Not recorded
Saving/loading auth state in codegen.

## Sources
- https://playwright.dev/docs/codegen-intro (read 2026-10-13)
- https://playwright.dev/docs/test-cli (read 2026-10-13)
- https://playwright.dev/docs/locators (read 2026-10-13)
