# A vertical feature in React and TypeScript

Example ownership for an edit-profile flow in the lightweight profile:

```text
src/features/edit-profile/
  api/save-profile.ts         transport status, validation, DTO mapping
  model/profile.ts           domain values and pure validation
  model/use-edit-profile.ts  draft/submission orchestration if substantial
  ui/EditProfileForm.tsx      fields, feedback, accessible interaction
  ui/EditProfileForm.test.tsx behavior at the user boundary
  index.ts                   deliberate external exports
src/pages/ProfilePage.tsx     composes feature with page data and navigation
```

This is a placement example, not a mandatory file count. A simple feature can be one
component plus a pure helper; introduce a Hook or adapter when there is real logic.
The generic architecture skill owns the import graph. The model's pure rules should
remain usable without React; a React orchestration Hook can live in model when this
matches the project, but keep pure code independent of that Hook.

The adapter accepts an explicit input contract, checks transport success, validates
untrusted response data, and maps transport differences before exposing application
values. Share an existing low-level HTTP client; keep endpoint and feature policy
inside the feature. Do not import UI into adapters or transport into pure domain rules.

The UI renders and collects intent. It may use the feature's existing query/mutation
integration or receive a narrow callback when that makes composition simpler. Avoid
passing a giant service container. Wire navigation and coordination between features
in the page/app layer. Public exports should expose the form/entry component and only
contracts consumers require, not every internal Hook or DTO.

Define who owns persisted server values, editable drafts, and URL parameters. A draft
must not reset on every background refetch. Explain when to reset it and what happens
on concurrent changes. Include the relevant identity/filter in cache keys, invalidate
or update affected cache entries after a mutation, and use the installed library's
cancellation/retry conventions. Optimistic updates need rollback or reconciliation;
do not add them without a user benefit. Clear user-specific cached data on identity
changes using the application's auth lifecycle.

Test the completed user behavior and failure recovery, plus pure rules where they
carry business risk. Keep HTTP tests at the adapter or network boundary rather than
mocking the component's own Hooks. Server authorization remains required even when
buttons are hidden or disabled. For server-rendered applications, retain framework
route and client/server directives and avoid serializing callbacks across a server
boundary; use that framework's supported action/data contracts.
