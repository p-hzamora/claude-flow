# CI with GitHub Actions

`pnpm create playwright` can generate `.github/workflows/playwright.yml`, triggered on push and PR to main/master. Steps: checkout, pnpm/action-setup, setup-node (LTS), `pnpm install --frozen-lockfile`, `pnpm exec playwright install --with-deps`, `pnpm exec playwright test`, upload `playwright-report/` as an artifact (name `playwright-report`, kept 30 days) with `if: ${{ !cancelled() }}` so it uploads on failure too.

```yaml
- uses: pnpm/action-setup@v4   # before setup-node; version comes from packageManager
- uses: actions/setup-node@v4
  with: { node-version: lts/*, cache: pnpm }
- run: pnpm install --frozen-lockfile
- run: pnpm exec playwright install --with-deps
- run: pnpm exec playwright test
- uses: actions/upload-artifact@v4
  if: ${{ !cancelled() }}
  with:
    name: playwright-report
    path: playwright-report/
    retention-days: 30
```

## Sharding (blob + merge)

Sharded workflow layout is composed from the documented flags, not from a recorded workflow:

```sh
pnpm exec playwright test --shard=1/3 --reporter=blob   # per matrix job
pnpm exec playwright merge-reports ./all-blob-reports --reporter html
```

Upload each job's blob report, download all into one directory in a final job, and run `merge-reports`.

## Guidance

- Set `globalTimeout` in config rather than relying on the job timeout, so a report is still produced when time runs out.
- View a report: download the artifact, run `pnpm exec playwright show-report <folder>`; the trace icon opens the Trace Viewer.

## Pitfalls

- The HTML report needs a web server; opening the file directly fails.
- Traces and reports may contain credentials; upload only to trusted stores.
- Fork PRs cannot access secrets.
- Other CI providers: Not recorded.

## Sources

- https://playwright.dev/docs/ci-intro (read 2026-10-13)
- https://playwright.dev/docs/test-cli (read 2026-10-13)
