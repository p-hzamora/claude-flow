# Context-First Project Topology

This is the canonical layout of one deployable Python service that follows this skill.
It is an architectural profile, not a claim that every DDD project uses the same names.
Apply it when a project adopts it. Angle-bracket segments are placeholders chosen by the
project. Do not derive a domain, provider, or project name from this guide.

When a project adopts this profile, these placement and naming rules override the
illustrative paths in every other reference, including the interface skills.

The layout is the same whatever drives the application. A REST API, a CLI, a worker, and
a message consumer differ only below `interfaces/<kind>/`. For several business areas in
one deployable, or for several services, read the [deployment overview](../deployment/overview.md).
It reuses this layout inside every module and every service.

## Package Root

`<package>/` is the import root:

- `app/` in services rendered from the `project-templates` catalog (`python/ddd_fastapi`).
- `src/<distribution>/` for an installable tool, such as a CLI published with
  `[project.scripts]`.

Examples in this skill use `app`. Keep the project's actual root.

## Top-Level Packages

| Package | Owns | May import |
| --- | --- | --- |
| `core/` | Typed configuration (`configurations/<concern>_configuration.py`) and environment loading (`env.py`) | stdlib, pydantic-settings |
| `exceptions/` | Shared exception bases and service-wide errors (see [error model](../errors/error-model.md)) | `raised`, stdlib |
| `utils/` | Tiny technical primitives re-exported for every layer, such as `FrozenObject` | stdlib, pydantic |
| `shared_kernel/` | Deliberately shared technical capabilities, see [shared kernel](../ddd/bounded-contexts/shared-kernel.md) | its own layers |
| `bounded_context/<context>/` | One model: `domain/`, `application/`, `infrastructure/` | see [layers](layers.md) |
| `bootstrap/` | Wiring shared by two or more interfaces, see [composition root](composition-root.md). Absent while there is one interface | everything except `interfaces/` |
| `interfaces/<kind>/` | One delivery adapter (`api`, `cli`, `worker`, `consumer`, ...), its own composition root and output contract | `bootstrap/`, application, `core/`, `exceptions/`, `utils/` |
| `migrations/` | Schema migration runner and revisions, when the service persists data | ORM metadata |
| `main.py` / `__main__.py` | Process entry point of the interface, no wiring logic | the interface package |

`interfaces/<kind>/` is the only place where a delivery framework (FastAPI, Typer, a
broker SDK used as a driver) appears outside infrastructure adapters. Each kind follows
its own interface skill. The rules every interface skill must satisfy are in the
[interface adapter contract](../interfaces/adapter-contract.md).

## Layout

```text
<package>/
├── main.py | __main__.py              # entry point of the selected interface
├── core/
│   ├── configurations/
│   │   ├── base_settings.py            # AppBaseSettings, when several settings share a policy
│   │   └── <concern>_configuration.py
│   └── env.py
├── exceptions/
│   ├── base.py                         # Domain/Application/Infrastructure/Interface/CoreException
│   └── <context>_errors.py             # context errors, single-service layout
├── utils/                              # FrozenObject and other tiny primitives
├── shared_kernel/
│   ├── domain/                         # genuinely shared domain primitives only
│   │   ├── entities/                   # Entity, AggregateRoot bases
│   │   ├── value_objects/              # ValueObject base
│   │   ├── events/                     # DomainEvent base
│   │   └── specifications/             # ISpecification / Specification base, when used
│   ├── application/
│   │   ├── handlers/                   # IHandler protocol
│   │   ├── security/dtos/              # application-owned authentication context
│   │   └── ports/
│   │       ├── resources/              # IResource lifecycle port
│   │       ├── event_bus/              # IEventPublisher, IEventSubscriber
│   │       └── <capability>/           # outbox, inbox, messaging, security, ...
│   └── infrastructure/
│       ├── resources/                  # process-scoped resources, registry
│       ├── event_bus/                  # InMemoryEventBusAdapter
│       └── <capability>/
├── bounded_context/<context>/
│   ├── domain/
│   │   ├── entities/<aggregate>.py     # entities and aggregate roots
│   │   ├── value_objects/<value>.py
│   │   ├── enums/<name>_enum.py
│   │   ├── events/<fact>_event.py
│   │   ├── services/<name>_service.py
│   │   ├── specifications/<rule>_specification.py  # only when the context has one
│   │   └── repositories/i_<aggregate>_repository.py
│   ├── application/
│   │   ├── dtos/<name>_dto.py
│   │   ├── handlers/
│   │   │   ├── commands/<verb>_<noun>_handler.py   # Command class + handler
│   │   │   ├── queries/<verb>_<noun>_handler.py    # Query class + handler
│   │   │   └── events/<fact>_handler.py            # consumers of other contexts' events
│   │   ├── mappers/<aggregate>_assembler.py        # Entity/VO -> DTO
│   │   ├── services/<capability>/
│   │   └── ports/
│   │       ├── read_repositories/i_<name>_read_repository.py
│   │       ├── transactions/i_<context>_unit_of_work.py
│   │       └── <capability>/i_<capability>.py
│   └── infrastructure/
│       ├── inbound/<driver>/                       # schedulers, webhooks, consumers
│       ├── outbound/
│       │   ├── persistence/
│       │   │   ├── models/base.py              # <Context>Base: this context's declarative base
│       │   │   ├── models/<table>_model.py
│       │   │   ├── mappers/<aggregate>_mapper.py
│       │   │   ├── mappers/read_mappers/<name>_read_mapper.py
│       │   │   ├── repositories/<name>_repository_adapter.py
│       │   │   ├── projections/<name>_projection_adapter.py  # event-fed read models
│       │   │   ├── outbox/                     # outbox model, adapter, relay of this context
│       │   │   ├── inbox/                      # idempotent-consumer dedupe adapter
│       │   │   └── <context>_unit_of_work_adapter.py
│       │   └── <capability>/<provider>_<capability>_adapter.py
│       └── <mixed_subsystem>/                      # inbound + outbound together, e.g. messaging
├── bootstrap/                           # only once two interfaces share wiring
├── interfaces/<kind>/                   # one per delivery mechanism, see its interface skill
└── migrations/
```

Create a package only when it has a present, cohesive responsibility. The layout does
not authorize empty folders.

## Naming

| Element | File | Class |
| --- | --- | --- |
| Aggregate root / entity | `domain/entities/<aggregate>.py` | `Order` |
| Value object | `domain/value_objects/<value>.py` | `Money`, `OrderId` |
| Enum | `domain/enums/<name>_enum.py` | `OrderStatusEnum`. The `Enum` suffix is mandatory |
| Domain event | `domain/events/<fact>_event.py` | `OrderPlacedEvent` |
| Write repository port | `domain/repositories/i_<aggregate>_repository.py` | `IOrderRepository` |
| Read repository port | `application/ports/read_repositories/i_<name>_read_repository.py` | `IOrderReadRepository` |
| Unit of Work port | `application/ports/transactions/i_<context>_unit_of_work.py` | `IOrderingUnitOfWork` |
| Other outbound port | `application/ports/<capability>/i_<capability>.py` | `IPaymentGateway` |
| Command / query + handler | `application/handlers/{commands,queries}/<verb>_<noun>_handler.py` | `PlaceOrderCommand` + `PlaceOrderHandler` |
| DTO | `application/dtos/<name>_dto.py` | `OrderDTO` |
| Assembler (Entity/VO -> DTO) | `application/mappers/<aggregate>_assembler.py` | `OrderAssembler.to_dto` |
| ORM model | `infrastructure/outbound/persistence/models/<table>_model.py` | `OrderModel` |
| Persistence mapper (ORM <-> Entity) | `.../persistence/mappers/<aggregate>_mapper.py` | `OrderMapper.to_orm` / `to_entity` |
| Read mapper (ORM -> DTO) | `.../persistence/mappers/read_mappers/<name>_read_mapper.py` | `OrderReadMapper.to_dto` |
| Any port implementation or process resource | `<name>_adapter.py` | `SqlOrderRepositoryAdapter`, `DatabaseEngineResourceAdapter` |
| Exception | `exceptions/...` | concrete errors end in `Error`, bases in `Exception` |

- Each context has its own declarative base (`OrderingBase`) and therefore its own
  metadata, so its tables and migrations can move with it.
- Commands and queries live in their handler's file. They are the handler's input
  contract, not shared types.
- A DTO is the application's output contract. It lives in `dtos/` because several
  handlers return it. A handler never returns an entity, value object, or ORM model.
- Interface-owned output models (`<name>_schema.py` for HTTP, `<name>_response.py` for
  CLI) are defined by the interface skills. They are always built from a DTO.
- Mapper methods are named `to_<destination>` (`to_orm`, `to_entity`, `to_dto`,
  `to_schema`, `to_response`), never `from_<source>`.
- PEP 8 capitalizes acronyms (`OrderDTO`, `HTTPClientAdapter`). If a project already
  spells them `OrderDto`, keep that spelling consistently. Do not mix the two.

## Ports and Implementations

Command and query handlers are the inbound (driving) application ports. Do not add an
`application/ports/inbound/` package merely to mirror hexagonal terminology.
`application/ports/` is for outbound (driven) contracts grouped by technical capability.
The exception is the write repository of an aggregate root. It lives in
`domain/repositories/` because its contract protects domain invariants. CQRS read ports
remain in `application/ports/read_repositories/` and return DTOs.

An application **Service** in `application/services/` describes which workflow to
orchestrate through abstract contracts, for example prompt construction or strategy
selection. An infrastructure **Adapter** describes how to talk to a concrete dependency,
including SDK translation and transport error handling. Every class below
`infrastructure/` that implements a port or is a process resource uses the `Adapter`
suffix: `SqlProductRepositoryAdapter`, `OpenAiLlmAdapter`, and `RabbitMqPublisherAdapter`
are valid; `OpenAiLlmService` is not (`scripts/ddd-check.py` rejects the `Service` suffix
there). Supporting classes keep the suffix of their role: ORM models (`OrderModel`),
mappers (`OrderMapper`, `OrderReadMapper`), and technical helpers (`ResourceRegistry`).

Ports are `abc.ABC` when implementations must opt in explicitly and the contract guards
domain or application meaning: write repositories, Units of Work, read repositories,
gateways. Structural technical ports shared by many implementations (`IHandler`,
`IResource`, event-bus ports) are `typing.Protocol`. A project that already uses one style
for a port kind keeps it consistently.

## Hybrid Infrastructure Direction

Do not nest a redundant `infrastructure/adapters/` directory. Put single-direction drivers
under `infrastructure/inbound/` and single-direction driven implementations under
`infrastructure/outbound/`. Keep a subsystem with real inbound and outbound behaviour at
the infrastructure root. For example, `infrastructure/messaging/` can co-locate a broker
connection, consumer, publisher, and lifecycle.

`infrastructure/inbound/` holds drivers that belong to one context, such as its scheduler
or the anti-corruption layer that parses a webhook or hook payload. Process-level delivery
mechanisms that serve the whole service, such as the HTTP app or the CLI app, live in
`interfaces/<kind>/`.

## Runtime Provider Selection

When a request selects a provider at runtime:

1. Define the resolving-factory contract in
   `application/ports/<capability>/i_<capability>_factory.py`.
2. Implement routing in `application/services/<capability>/<capability>_resolver.py`. It
   is injected at composition time with a dictionary of abstract adapter references keyed
   by provider.
3. Keep concrete provider adapters in `infrastructure/outbound/<capability>/`.

## Shared Python Settings Policy

When several Pydantic Settings classes share one environment-loading and validation
policy, define that policy once in a narrow `AppBaseSettings(BaseSettings)` class in
`core/configurations/base_settings.py`. Its `model_config = SettingsConfigDict(...)` owns
the shared options, such as `env_file`, `env_file_encoding`, `extra`,
`hide_input_in_errors`, and field-name population. Concern-specific settings inherit it
and keep their own fields, aliases, defaults, and validators.

Settings are a configuration boundary, not a domain abstraction. Keep them out of the
domain, free of delivery-framework imports, and free of service connections. When they
are loaded is an interface decision: once at process start for a server, lazily per
invocation for a CLI. See the [composition root](composition-root.md).

Before extracting the base, compare every class's configuration. Preserve intentional
subclass overrides. Account explicitly for behaviour changes, such as enabling
`hide_input_in_errors` where it was absent. Verify inherited configuration, dotenv
loading, aliases, construction by field name, and validation-error rendering. Do not
force one policy onto independently configured components.

## Application Security Contracts

Authentication context, token metadata, permissions, and user-profile DTOs are
application contracts. They belong in `shared_kernel/application/security/dtos/`, built
on the application's DTO base. The token-validator port lives in
`shared_kernel/application/ports/security/` and returns those local DTOs. Concrete
validators live in `shared_kernel/infrastructure/security/` and map identity-provider
results to the DTOs. Do not re-export security models from an external package such as
`ddd_contracts.core.security.value_objects`. Preserve the application's actual claims and
authorization behaviour rather than copying another service's permissions. A genuine
domain identity primitive may stay in `shared_kernel/domain/` when its business meaning is
explicit. Domain code never imports application security contracts. How credentials
arrive (a bearer header, a CLI token file) is an interface concern.

## Telemetry

Process-wide telemetry configuration belongs in the
`shared_kernel/infrastructure/telemetry/` wrapper. The entry point only gates and invokes
it. See the [observability skeleton](../observability/skeleton.md).

## Review Checklist

- [ ] The package root and top-level packages match this profile, or the deviation is the project's established, consistent choice.
- [ ] Context boundaries and shared-kernel contents are intentional and free of direct business-logic sharing.
- [ ] `core/` and `exceptions/` import no delivery framework and no infrastructure.
- [ ] Delivery frameworks appear only in `interfaces/<kind>/` and in infrastructure adapters.
- [ ] Handlers are inbound actions; write, read, and other outbound contracts have their prescribed ownership.
- [ ] Commands and queries live in their handler's file; handlers return DTOs, never entities, value objects, or ORM models.
- [ ] Files and classes follow the naming table; enums end in `Enum`; mapper methods are `to_<destination>`.
- [ ] Infrastructure direction is hybrid where necessary, with no redundant `adapters/` nesting.
- [ ] Every changed port implementation and process resource below `infrastructure/` has the `Adapter` suffix; none ends in `Service`.
- [ ] Shared Python settings policies have one owner; overrides and inherited behaviour were reviewed when applicable.
- [ ] Security context DTOs and the token-validator port are application-owned in `shared_kernel/application/`.
