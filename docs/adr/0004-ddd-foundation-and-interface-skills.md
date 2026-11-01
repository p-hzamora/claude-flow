# DDD foundation skill plus one skill per interface

`clean-ddd-hexagonal-python` claimed to be framework-independent, but its references mixed
FastAPI routers, `Depends` factories, HTTP status codes, and RFC 9457 handlers into the
layer, CQRS, testing, and error guidance. Adding a CLI (noesis) exposed it: half of the
skill did not apply, and the parts that did were hard to find.

**Decided:**

- The skill is renamed `clean-ddd-hexagonal-python` -> `ddd-hexagonal-python` and becomes
  the framework-agnostic foundation: domain, application, infrastructure, shared kernel, context-first topology
  and naming, composition root with interface-neutral process resources, the error model,
  deployment shapes (single service, modular monolith, microservices), and an **interface
  adapter contract** (`references/interfaces/adapter-contract.md`) listing the eight things
  every interface must define. The new name groups it with the `ddd-interface-<kind>`
  skills; every agent, Codex profile, and document was updated in the same change
  (a breaking rename, plugin 2.0.0). ADR-0001 and ADR-0003 keep the old name as history.
- Each delivery mechanism gets its own skill, `ddd-interface-<kind>`, that answers only
  the contract's rows and links to the foundation for everything else:
  `ddd-interface-fastapi` (routers, `*_schema.py`, `*_dpd.py`, `raised` RFC 9457) and
  `ddd-interface-cli` (Typer commands, `--json` envelope, `responses/*_response.py`, exit
  codes, agent guides and hooks). A future worker, consumer, gRPC, or MCP interface is a
  new skill, not new foundation rules.
- One exception hierarchy for every interface, rooted in `raised.AppException` (its core
  has no dependencies). `__http_error__` is read as a transport-neutral status hint;
  interfaces map it (HTTP status, CLI exit code, worker retry or dead-letter). No exception
  carries interface-specific attributes such as `__exit_code__`.
- The composition root belongs to the interface (`interfaces/<kind>/bootstrap/`) and moves
  to `<package>/bootstrap/` only when a second interface shares the wiring. Process
  resources implement an interface-neutral `IResource` that takes no framework object.
- Deployment guidance moved from `references/modular-monolith/` to
  `references/deployment/`, adding a shape comparison (what never changes, what does) and
  a microservices reference. Lessons from `agentic-ai` (hidden shared-state callables,
  import-linter independence needing a `contracts/` exception) are recorded there.
- The four-mapper rule of ADR-0001 stands, generalized: the fourth mapper is "DTO →
  interface output model", defaulting to `Model.model_validate(dto)` in the interface.
  ADR-0001's paths (`infrastructure/db/mappers/`, `interfaces/api/v1/mappers/`) are
  superseded by the context-first paths in `references/architecture/project-topology.md`.

**Considered:** keeping `clean-ddd-hexagonal-python` (no breaking change, but "clean"
added nothing and hid the family relation with the interface skills); `ddd-foundation-python`; one combined interface skill with FastAPI and
CLI sections (re-creates the coupling and grows with every interface); keeping
`__exit_code__` on exceptions as noesis does (puts a CLI concern into inner layers and
forces every future interface to add its own attribute).

**Consequences:** the `python/ddd_fastapi` template and noesis now deviate from the skills
in known places (template: `IResource.startup(app: FastAPI)`, no `Adapter` suffix, HTTP
status set only on some bases; noesis: own `AppException` with `__exit_code__`). They keep
working; they are follow-ups, not part of this change.
