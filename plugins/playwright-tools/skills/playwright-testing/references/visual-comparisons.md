# Visual comparisons

`await expect(page).toHaveScreenshot()` creates a baseline on first run (accepted once two consecutive captures match) and compares on later runs.

- Default name: test name + counter + browser + platform (e.g. `example-test-1-chromium-darwin.png`). Pass a name to override; use `.webp` or `expect.toHaveScreenshot.type: 'webp'` for webp.
- Baselines live in `<testfile>-snapshots`; configure with `snapshotPathTemplate`.
- Update with `--update-snapshots`.
- `toMatchSnapshot` covers text and binary data.

```ts
await expect(page).toHaveScreenshot('home.png', { maxDiffPixels: 10 });
```

## Options

Defaults can be set under `expect.toHaveScreenshot` in config.

- `mask`: locators covered with a colored box (also if invisible); `maskColor`: CSS color, default `#FF00FF`.
- `fullPage`: default `false`.
- `animations`: `'disabled'` (default) or `'allow'`.
- `caret`: `'hide'` (default) or `'initial'`.
- `clip`: `{ x, y, width, height }`.
- `omitBackground`: default `false`; not for JPEG.
- `scale`: `'css'` (default) or `'device'`.
- `threshold`: default 0.2; `maxDiffPixels`; `maxDiffPixelRatio` (0 to 1).
- `stylePath`: CSS file that hides volatile elements.
- `timeout`: defaults to `expect.timeout`.

## Pitfalls

- Rendering differs by OS, version, and hardware. Generate and compare baselines in the same environment (for example the CI container).
- Baselines are per browser and platform.
- Move the mouse off hover targets (`page.mouse.move(-1, -1)`) before capturing.
- Mask or hide dynamic content (dates, ads, avatars) instead of loosening thresholds.
- Review updated baselines before committing.

## Sources

- https://playwright.dev/docs/test-snapshots (read 2026-10-13)
- https://playwright.dev/docs/api/class-pageassertions (read 2026-10-13)
