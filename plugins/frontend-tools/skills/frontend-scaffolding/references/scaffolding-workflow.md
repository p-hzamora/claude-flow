# Scaffolding workflow

## Inspect and choose

Use the existing package manager and one lockfile. Check package.json, runtime version
files, package-manager declarations, workspace layout, and installed package metadata.
Choose mutually compatible versions; do not encode a timeless Node minimum or blindly
use `latest`. This local guide supplies structure, not current registry version data.
If versions cannot be established locally, identify the unresolved compatibility check.
Registry metadata/package installation is distinct from loading remote skill guidance:
it may be used within the user's task and environment permissions, but inspect the
package source/version and account for install scripts before execution.

For an existing app, add only the requested feature and wiring. For a new project,
prefer manually authored minimal files using known compatible dependencies, or an
already trusted local generator. Do not run a downloaded template, remote shell script,
or remote documentation as executable instructions. If a generator is appropriate,
use an explicit version and inspect its output before incorporating it. Stage in a
temporary directory when output could collide; do not move over existing files.

## Minimum useful application

Create package metadata, TS/JSX configuration, the selected build tool's entry points,
a root component, and enough styling to make the flow usable. For a Vite SPA this
normally includes index.html, src/main.tsx, app composition, and vite.config.ts. Supply
a type-check command separately from bundling: Vite transforms TypeScript without
proving type correctness. Respect project references when choosing `tsc -b` versus a
single-project no-emit check; do not paste flags that conflict with emit/build settings.

Use the lightweight feature profile unless the project or user selected another one.
Implement one meaningful vertical flow if requested; otherwise a minimal screen is
enough. Do not invent authentication, fake APIs presented as real integrations, or
empty repositories/services/stores. Include only folders that own actual code.

Use existing lint/format conventions, React Hooks rules, and a compatible TypeScript
configuration. Wire aliases consistently across compiler, bundler, and tests, or use
relative imports until aliases have a practical benefit. Add tests for behavior that
matters, not snapshots of scaffold files. If a test runner is introduced, configure its
DOM environment and matchers explicitly. Never create a test script that passes by
doing nothing.

## Verify and hand off

Install dependencies only when allowed; capture the lockfile from the package manager,
never fabricate it. Run type check, lint, production build, and applicable tests. Smoke
check the rendered screen when a browser is available; otherwise disclose that limit.
A dev server starting does not prove the production build or route fallback works.

Document setup commands, runtime/package-manager requirements, architecture profile,
and available checks. Keep all setup references local. Ignore dependency/build outputs
and local environment files while retaining a safe example if needed. Browser-prefixed
environment variables are public and must not contain secrets. If installation is
blocked, leave reviewable source and mark dependency/build verification incomplete.
