# Boundaries and layouts

## Lightweight feature profile (local policy)

```text
src/
  app/                    bootstrap, providers, routing composition
  pages/                  optional screen composition when it earns its place
  features/
    checkout/
      ui/                 checkout UI
      model/              state and business rules
      api/                transport and mapping
      index.ts            explicit supported exports
  shared/
    ui/                   domain-neutral primitives
    lib/                  focused reusable utilities
```

Create directories only when they contain useful code. These segment names describe
purpose; do not create empty api/model/ui directories for every feature. Colocate tests
and styles with their owners. Avoid global components/hooks/types folders that become
an inventory of unrelated features.

Allowed imports: app composes pages/features/shared; pages compose features/shared;
features use their own internals and shared; shared never imports upper layers.
Peer features do not import each other in this profile, even through public exports.
An app/page coordinator can connect them through callbacks and data. A truly shared
business concept may justify an explicitly documented lower domain layer or a different
profile; do not relabel it a generic shared utility to evade the boundary.

A feature index exports only what consumers need. Outside consumers use that public
entry point; internal files import each other directly to avoid self-barrel cycles.
Avoid `export *` across large trees. Shared primitives can have narrow entry points
per component or utility rather than a single application-wide barrel. Type-only
imports still establish architectural dependencies. A path alias is not enforcement.

## Formal Feature-Sliced Design (opt-in)

FSD orders layers downward as app, pages, widgets, features, entities, shared. Processes
is deprecated. Omit unused layers. App and Shared are segmented without business
slices; other layers organize slices by purpose. A slice may depend on lower layers,
not other slices on its layer. Public APIs define what can cross a slice boundary.
Entities represent business concepts; features represent reusable user actions;
widgets compose larger independent blocks; pages own screen-specific composition.

Do not split every page-local interaction into a feature. Keep code local until reuse
or ownership calls for extraction. FSD has specialized entity cross-reference patterns;
prefer ordinary lower-layer composition and consult a separately reviewed local policy
before adding exceptions. This plugin's default does not enable such exceptions.

Choose FSD when those layers clarify a sufficiently complex product and the team wants
its rules. The lightweight profile is an independent convention inspired by cohesion
and explicit APIs, not a claim of full FSD compliance.
