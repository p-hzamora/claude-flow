# Trace Viewer

## What it shows
Per-action timeline, before/after DOM snapshots, log (including actionability waits), source, network, console, errors, DevTools.

## Recording
- Config `use.trace` defaults to `'on-first-retry'` in the generated config: a trace is recorded only when `retries > 0` and the first retry runs.
- Locally force it: `pnpm exec playwright test --trace on`.
- CLI modes: `on`, `off`, `on-first-retry`, `retain-on-failure`. Semantics of `retain-on-failure` beyond its name: Not recorded.

## Opening
- Trace icon in the HTML report (`pnpm exec playwright show-report [dir]`, default port 9323).
- `pnpm exec playwright show-trace trace.zip` (or a directory).

## Reading a failure
1. Select the failing action in the timeline.
2. Read the error and log: which actionability check was waiting (visible, stable, receives events, enabled, editable).
3. Compare before/after snapshots: was the element present, obscured, or different from expected?
4. Check network and console for failed requests or page errors.
5. Use the source tab to map the action to the test line.

## Tips
- Locally prefer UI mode (`--ui`).
- A missing trace usually means `retries` is 0 under `on-first-retry`.

## Sources
- https://playwright.dev/docs/trace-viewer-intro (read 2026-10-13)
- https://playwright.dev/docs/debug (read 2026-10-13)
- https://playwright.dev/docs/test-cli (read 2026-10-13)
