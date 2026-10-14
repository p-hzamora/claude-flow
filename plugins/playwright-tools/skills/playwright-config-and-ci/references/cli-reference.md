# CLI reference

`pnpm exec playwright --help` is authoritative. Commands: `test`, `show-report`, `install`, `install-deps`, `uninstall`, `codegen`, `show-trace`, `merge-reports`, `clear-cache`.

## test [options] [filter...]

```sh
pnpm exec playwright test file.spec.ts
pnpm exec playwright test file.spec.ts:42        # by line
pnpm exec playwright test -g "title"             # -G inverts
pnpm exec playwright test --project=chromium     # wildcards ok
pnpm exec playwright test --workers=1
pnpm exec playwright test --debug [inspector|cli]
pnpm exec playwright test --ui
```

| Flag | Meaning |
| --- | --- |
| `--headed` | show the browser |
| `-j`, `--workers` | worker count (default 50% of CPU) |
| `-x`, `--max-failures N` | stop after N failures |
| `--retries` | retry count |
| `--timeout` | per-test timeout (default 30s, 0 = none) |
| `--global-timeout` | whole-run cap |
| `--repeat-each` | run each test N times |
| `--shard 3/5` | run one slice of the suite |
| `--shuffle [seed]` | randomize order |
| `--last-failed` | rerun only previous failures |
| `--only-changed [ref]` | tests affected by changes |
| `--list` | list tests without running |
| `--forbid-only` | fail on `test.only` (use on CI) |
| `--fail-on-flaky-tests` | fail when a test is flaky |
| `--fully-parallel` | parallelize tests within files |
| `--pass-with-no-tests` | do not fail when nothing matches |
| `--no-deps` | skip project dependencies and teardowns |
| `--quiet` | suppress output |
| `--reporter` / `--add-reporter` | set / add reporters |
| `--trace on\|off\|on-first-retry\|retain-on-failure` | trace mode |
| `-u`, `--update-snapshots [all\|changed\|missing\|none]` | update snapshots |
| `--ignore-snapshots` | skip snapshot assertions |
| `--test-list` | run tests from a list file |
| `-c`, `--config` | config path |
| `--output` | artifacts dir (default `test-results`) |
| `--tsconfig` | tsconfig path |
| `--run-agents missing\|all\|none` | generate `page.perform` code (default none) |

Example:

```sh
pnpm exec playwright test --project=chromium -g "login" --retries=1 --trace on
```

## Other commands

```sh
pnpm exec playwright show-report [dir] [--host H --port P]   # default port 9323
pnpm exec playwright install [browser...] [--with-deps --force --dry-run --list --only-shell --no-shell]
pnpm exec playwright install-deps --dry-run
pnpm exec playwright codegen [url] -b chromium -o out.ts --target playwright-test --test-id-attribute data-qa
pnpm exec playwright show-trace [trace.zip|dir]
pnpm exec playwright merge-reports <blob dir> --reporter html
```

`codegen --target` accepts javascript, playwright-test, python.

## Pitfalls

- `--debug` sets the timeout to 0.
- Use `--forbid-only` on CI to block a stray `test.only`.
- `--grep`, `--shard` and `test.only` still pull in project dependencies.

## Sources

- https://playwright.dev/docs/test-cli (read 2026-10-13)
