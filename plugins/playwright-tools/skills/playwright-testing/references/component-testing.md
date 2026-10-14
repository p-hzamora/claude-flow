# Component testing

The experimental packages (`@playwright/experimental-ct-react`, `-ct-react17`, `-ct-vue`) are removed; projects still on them should stay on Playwright 1.62 until migrating.

Current approach: the built-in `mount` fixture of `@playwright/test`. No extra packages, bundler integration, or runtime. You own a "gallery" page served by your dev server; it is framework-agnostic.

- Setup: `pnpm exec playwright init-skills`, then ask a coding agent using the `playwright-component-testing` skill, or write the gallery by hand.
- `mount('components/Button/Primary', props)` renders a story by id and returns a Locator for the gallery root.
- `component.update(props)` and `component.unmount()`.
- Config: a project with `testDir`, `baseURL` pointing at the gallery, `serviceWorkers: 'block'`, `reuseContext: true`, plus `webServer`.

```ts
const c = await mount('components/Expandable/Stateful');
await c.getByRole('button').click();
await expect(c.getByTestId('expanded')).toHaveValue('true');
```

## Pitfalls

- Component instance and method access is unsupported.
- Story ids are strings; renaming breaks at runtime. Type with `mount<typeof Story>`.
- No per-test JSX; each composition must be a named story.
- Props must be serializable; callbacks live in the story.

## Sources

- https://playwright.dev/docs/test-components (read 2026-10-13)
