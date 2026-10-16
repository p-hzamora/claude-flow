# Context-First Project Topology

Use this reference when a project adopts these structural conventions. They are an
architectural profile, not a claim that every DDD project has the same package root,
framework, or directory names. Angle-bracket segments are placeholders selected by the
project; do not derive a domain, provider, or project name from this guide.

When a project adopts this profile, these placement rules override illustrative paths
in the other architecture and CQRS references.

## Top-Level Boundaries

Each domain capability is an autonomous bounded context. Contexts sit at a physical
top-level boundary and never share functional business logic directly. Use explicit
application contracts, integration events, IDs/references, or an anti-corruption layer
for integration.

`core/` is global, framework-agnostic configuration: strongly typed configuration
definitions in `core/configurations/` and environment parsing in `core/env.py`. It
does not import FastAPI or infrastructure packages.

When FastAPI is the selected delivery adapter, HTTP delivery code lives in
`interfaces/api/`. Its bootstrap owns the web application: `bootstrap.py` accepts
and mutates the `FastAPI` instance while wiring process-scoped resources, and
`registry.py` manages their startup/shutdown lifecycle. In the
[modular monolith profile](../modular-monolith/project-topology.md), each module owns
its custom delivery adapters under `modules/<module>/interfaces/`; global API
bootstrap mounts them through public module entry points.

For typed application state and request access, follow the
[FastAPI application types convention](../../../fastapi-async-patterns/SKILL.md#typed-application-state-and-request-access).

`shared_kernel/` is exclusively for deliberately shared cross-context technical
capabilities: for example, transactional-outbox support, security-token validation,
and generic connection lifecycle hooks. Keep shared driven contracts in
`shared_kernel/application/ports/` and their implementations in
`shared_kernel/infrastructure/`. Application-owned authentication context, token metadata, permissions, and user
profile DTOs belong in `shared_kernel/application/security/dtos/`; token-validator ports stay
in `shared_kernel/application/ports/security/`, with concrete validators in
`shared_kernel/infrastructure/security/`. These are application security contracts,
not domain models or value objects. Define these DTOs in the application using its
DTO base; do not re-export user/security models from
`ddd_contracts.core.security.value_objects`. Own the token-validator port locally so
its return type references the application DTO. Map external identity-provider results
to these DTOs inside infrastructure adapters. Preserve the application's actual claims
and authorization behavior rather than copying another service's permissions.
A genuine domain identity primitive may remain in
`shared_kernel/domain/` when its business meaning and ownership are explicit; domain
code must not import application security contracts.

Process-wide telemetry configuration belongs in the outer
`shared_kernel/infrastructure/telemetry/` wrapper; `main.py` only gates and invokes it.
That wrapper may depend on the delivery framework for instrumentation. Follow the
[observability skeleton](../observability/skeleton.md) for ownership, settings mapping,
and lifecycle verification.

## Layout

```text
src/
├── core/
│   ├── configurations/
│   │   └── <concern>_configuration.py
│   └── env.py
├── interfaces/api/                 # only when FastAPI is used
│   ├── bootstrap/
│   │   ├── bootstrap.py
│   │   └── registry.py
│   ├── middleware/
│   └── routers/
├── shared_kernel/
│   ├── domain/                     # genuine shared domain primitives only
│   ├── application/
│   │   ├── security/dtos/
│   │   └── ports/
│   └── infrastructure/
│       ├── resilience/
│       └── resources/
└── bounded_context/<context_name>/
    ├── domain/
    │   ├── models/
    │   └── repositories/
    │       └── i_<aggregate>_repository.py
    ├── application/
    │   ├── dtos/
    │   ├── handlers/
    │   │   ├── commands/
    │   │   └── queries/
    │   ├── services/<capability>/
    │   └── ports/
    │       ├── read_repositories/
    │       └── <capability>/
    └── infrastructure/
        ├── inbound/schedulers/
        ├── outbound/
        │   ├── persistence/
        │   │   ├── models/
        │   │   └── mappers/
        │   └── <capability>/
        └── <mixed_subsystem>/
```

Create a package only when it has a present, cohesive responsibility; the layout does
not authorize empty folders.

## Shared Python Settings Policy

When a Python application uses Pydantic Settings and several settings classes share
one environment-loading and validation policy, define that policy once in a narrowly
scoped `AppBaseSettings(BaseSettings)` class. Its `model_config = SettingsConfigDict(...)`
owns the shared options, such as `env_file`, `env_file_encoding`, `extra`,
`hide_input_in_errors`, and field-name population. Concern-specific settings inherit
that base and retain their own fields, aliases, defaults, and validators.

Use the project's existing configuration package; for example, an adopted
`core/settings/` package can own `base_settings.py`. This is an application-wide
technical policy, not a domain abstraction or a reason to move settings into
`shared_kernel/`. Pydantic Settings is appropriate at this configuration boundary
when adopted by the project; keep it out of the domain and keep settings free of
FastAPI dependencies and service connections.

Before extracting the base, compare every class's configuration. Preserve intentional
subclass overrides and explicitly account for behavior changes such as enabling
`hide_input_in_errors` where it was previously absent. Verify inherited configuration,
dotenv loading, aliases and construction by field name, and validation-error rendering.
Do not force identical policy onto independently configured components or introduce
base classes solely because unrelated domain models look similar. The preference for
small duplication between independent bounded contexts does not justify repeating a
single application-owned settings policy.

## Ports and Implementations

Command and query handlers are the inbound (driving) application ports. Do not add an
`application/ports/inbound/` package merely to mirror Hexagonal terminology.
`application/ports/` is for outbound (driven) contracts grouped by technical
capability. The exception is a primary write repository for an aggregate root: it
lives in `domain/repositories/`, because its contract protects domain invariants.
CQRS read models remain in `application/ports/read_repositories/`.

An application **Service** in `application/services/` describes what business workflow
to orchestrate using abstract contracts: prompt construction, schemas, or strategy
selection are examples. An infrastructure **Adapter** describes how to communicate
with a concrete external dependency, including SDK translation and transport error
handling. Every concrete class created or modified anywhere below `infrastructure/`
must use the `Adapter` suffix: `SqlProductRepositoryAdapter`, `OpenAiLlmAdapter`, and
`RabbitMqPublisherAdapter` are valid; `OpenAiLlmService` is not.

## Hybrid Infrastructure Direction

Do not nest a redundant `infrastructure/adapters/` directory. Put single-direction
drivers under `infrastructure/inbound/` and single-direction driven implementations
under `infrastructure/outbound/`. Keep a subsystem with real inbound and outbound
behaviour at the infrastructure root. For example, `infrastructure/messaging/` can
co-locate RabbitMQ connection setup, consumer, publisher, configuration, and lifecycle
management.

## Runtime Provider Selection

When a request selects a provider at runtime (for example, one implementation key
versus another):

1. Define the resolving-factory contract in
   `application/ports/<capability>/i_<capability>_factory.py`.
2. Implement routing in `application/services/<capability>/<capability>_resolver.py`, injected at
   composition time with a dictionary of abstract adapter references keyed by provider.
3. Keep concrete provider adapters in `infrastructure/outbound/<capability>/`.

## Review Checklist

- [ ] Context boundaries and shared-kernel contents are intentional and free of direct business-logic sharing.
- [ ] `core/` remains framework-agnostic and API lifecycle wiring remains in API bootstrap.
- [ ] Handlers are inbound actions; outbound, write, and read contracts have their prescribed ownership.
- [ ] Infrastructure direction is hybrid where necessary, with no redundant adapters nesting.
- [ ] Every changed concrete infrastructure class has the `Adapter` suffix.
- [ ] Shared Python settings policies have one owner; repeated configuration, intentional overrides, and inherited behavior have been reviewed when applicable.
- [ ] API startup composition lives in `interfaces/api/bootstrap/bootstrap.py`; typed FastAPI state follows the linked application types convention when used.
- [ ] Authentication context, token metadata, permissions, and profiles are application-owned DTOs in `shared_kernel/application/security/dtos/`, not domain value objects or external security-model re-exports; the validator port returns the local DTO.
