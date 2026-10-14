# Aria snapshots

`expect(page | locator).toMatchAriaSnapshot(yaml)` compares the accessibility tree with a YAML template.

```ts
await expect(page.getByRole('main')).toMatchAriaSnapshot(`
  - heading "Title" [level=1]
  - button "Toggle" [pressed=true]
`);
```

## Template syntax

- Node: `- role "name" [attr=value]`. Quoted text is exact; `/regex/` allowed; brackets hold ARIA state. Indentation means nesting.
- Matching is case-sensitive, whitespace-normalized, and order-sensitive.
- A template is a constraint, not a full dump: omitted names or attributes are ignored (`- button` matches any button) and a partial list matches.
- `/children` strictness: `contain` (default, extra children allowed), `equal` (direct children must match exactly), `deep-equal`. Set globally in config at `expect.toMatchAriaSnapshot.children`.

## Generating and updating

- Codegen "Assert snapshot" action, or `page.ariaSnapshot()` / `locator.ariaSnapshot()`.
- An empty template `''` generates on the fly.
- `--update-snapshots` modes: `default` (missing generated, test still fails), `missing`, `changed` (`-u`), `all`, `none`.
- `--update-source-method`: `patch`, `3way`, or `overwrite`.
- `{ name: 'main.aria.yml' }` stores the snapshot in a separate file (path template configurable).

## Pitfalls

- Accepting updates without review hides bugs.
- Large snapshots are hard to review; scope to a locator.
- Dynamic content makes snapshots unstable; use regex or omit names.
- Reordered elements fail the match.
- `equal` / `deep-equal` require every child to be listed.
- If generation exceeds the test timeout, raise `--timeout`.

## Sources

- https://playwright.dev/docs/aria-snapshots (read 2026-10-13)
