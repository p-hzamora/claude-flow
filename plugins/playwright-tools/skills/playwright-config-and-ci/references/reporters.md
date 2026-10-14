# Reporters

Built-in: `list` (local default), `line`, `dot` (CI default), `html`, `blob` (merging sharded runs), `json`, `junit`, `perfetto`, `github` (Actions annotations).

Pick one on the CLI (`--reporter=line`) or in config as a string. Pass options with a tuple inside an array. Several reporters can run at once; the choice can depend on the environment.

```ts
reporter: process.env.CI ? 'dot' : 'list',
reporter: [['json', { outputFile: 'results.json' }]],
reporter: [['list'], ['html', { outputFolder: 'my-report', open: 'never' }]],
```

## HTML reporter options

| Option | Default |
| --- | --- |
| `open` (`always`, `never`, `on-failure`) | `on-failure` |
| `outputFolder` | `playwright-report` |
| `host` | Not recorded |
| `port` | 9323 |
| `title`, `attachmentsBaseURL`, `noCopyPrompt`, `noSnippets`, `doNotInlineAssets`, `mergeFiles` | Not recorded |

Each option has a matching `PLAYWRIGHT_HTML_*` env var.

View with `pnpm exec playwright show-report`.

## Pitfalls

- On CI set `open: 'never'` so the run does not block serving the report.
- For sharded runs use `blob`, then `pnpm exec playwright merge-reports <dir> --reporter html`.

## Sources

- https://playwright.dev/docs/test-reporters (read 2026-10-13)
- https://playwright.dev/docs/test-cli (read 2026-10-13)
