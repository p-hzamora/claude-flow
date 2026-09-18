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

When FastAPI is the selected delivery adapter, all FastAPI-dependent code is in
`interfaces/api/`. Its bootstrap owns the web application: `composition.py` accepts
and mutates the `FastAPI` instance while wiring process-scoped resources, and
`registry.py` manages their startup/shutdown lifecycle.

`shared_kernel/` is exclusively for deliberately shared cross-context technical
capabilities: for example, transactional-outbox support, security-token validation,
and generic connection lifecycle hooks. Keep shared driven contracts in
`shared_kernel/application/ports/` and their implementations in
`shared_kernel/infrastructure/`. Domain primitives such as a shared `UserIdentity`
may live there when their ownership and stability are explicit.

## Layout

```text
src/
├── core/
│   ├── configurations/
│   │   └── <concern>_configuration.py
│   └── env.py
├── interfaces/api/                 # only when FastAPI is used
│   ├── bootstrap/
│   │   ├── composition.py
│   │   └── registry.py
│   ├── middleware/
│   └── routers/
├── shared_kernel/
│   ├── domain/security/value_objects/
│   ├── application/ports/
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
