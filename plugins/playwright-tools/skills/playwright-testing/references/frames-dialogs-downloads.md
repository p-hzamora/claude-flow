# Frames, dialogs, downloads

## Frames

A page has a main frame; iframe content is another frame.

- `page.frameLocator(selector)` lets you chain normal locators inside an iframe.
- `page.frame('name')` or `page.frame({ url: /regex/ })` returns a `Frame`, which may be `null`; guard it.
- Nested frames: Not recorded.

```ts
await page.frameLocator('.frame-class').getByLabel('User Name').fill('John');
```

## Dialogs

Covers alert, confirm, prompt, and beforeunload. With no `page.on('dialog')` listener, Playwright auto-dismisses them. To control one, register the listener before the triggering action and call `dialog.accept()` or `dialog.dismiss()`.

```ts
page.on('dialog', dialog => dialog.accept());
await page.getByRole('button').click();
```

- A listener that only logs (neither accepts nor dismisses) leaves the modal open and the click hangs.
- beforeunload: `page.close({ runBeforeUnload: true })` and handle the dialog (check `dialog.type()`); this is the case where `close()` does not wait for the page to close.
- Print dialog: override `window.print` with a promise after load, click, then `page.waitForFunction` on it.

## Downloads

Downloads emit `page.on('download')`. A `Download` exposes `url`, `suggestedFilename()`, `path()`, `saveAs()`. Start `page.waitForEvent('download')` before the click without awaiting, click, then await.

```ts
const p = page.waitForEvent('download');
await page.getByText('Download file').click();
const d = await p;
await d.saveAs('/path/' + d.suggestedFilename());
```

- `downloadsPath` in `browserType.launch()` persists the location.
- Files are deleted when the producing browser context closes; save first.
- Not awaiting the download lets the test end mid-download.
- Uploads (`setInputFiles`, file chooser): Not recorded.

## Sources

- https://playwright.dev/docs/frames (read 2026-10-13)
- https://playwright.dev/docs/dialogs (read 2026-10-13)
- https://playwright.dev/docs/downloads (read 2026-10-13)
