# Clock and emulation

## Clock (`page.clock`)

Controls time inside the page: Date, setTimeout/setInterval and clears, requestAnimationFrame, requestIdleCallback, performance, Event.timeStamp, Temporal.Now.

- `setFixedTime(date)`: freezes `Date.now` / `new Date`; timers keep running. First choice.
- `install({ time })`: takes over the clock. Afterwards: `pauseAt(date)`, `fastForward('30:00')` (jumps; due timers fire once), `runFor(ms)` (advances, firing timers and animation frames), `resume()`.
- `setSystemTime(date)`: advanced cases only.

```ts
await page.clock.install({ time: new Date('2024-02-02T08:00:00') });
await page.goto(url);
await page.clock.pauseAt(new Date('2024-02-02T10:00:00'));
await page.clock.fastForward('30:00');
```

Pitfalls:
- `install` must come before any other clock call.
- A setInterval created before `install` and cleared after it is undefined behavior.
- `setFixedTime` does not stop timers.

## Emulation

The `devices` registry holds presets (user agent, screen, viewport, touch): `...devices['Desktop Chrome']` in config, `devices['iPhone 13']` in the library.

- Viewport `{ width, height }` via config, `test.use`, or `newContext`; `page.setViewportSize` per page. `deviceScaleFactor` for high-DPI; `isMobile` enables meta viewport and touch.
- `locale`, `timezoneId` (browser only; the runner process uses the `TZ` env var).
- `permissions: [...]` in config or `newContext`; `context.grantPermissions(perms, { origin })`; `clearPermissions`.
- `geolocation { longitude, latitude }` plus the `geolocation` permission; `context.setGeolocation`.
- `colorScheme`: light, dark, no-preference; `page.emulateMedia` for color scheme and media type (e.g. print).
- `userAgent`, `offline: true`, `javaScriptEnabled: false`.

Scope: config applies to all tests, `test.use` to a file or describe block, `newContext` to library use.

```ts
test.use({ locale: 'en-GB', timezoneId: 'Europe/Paris', colorScheme: 'dark' });
```

Pitfalls:
- Set `viewport` after spreading a device, or the device viewport wins.
- Device presets assume a platform; `userAgent: undefined` uses the real one.
- `offline` does not affect WebRTC.

## Sources

- https://playwright.dev/docs/clock (read 2026-10-13)
- https://playwright.dev/docs/emulation (read 2026-10-13)
