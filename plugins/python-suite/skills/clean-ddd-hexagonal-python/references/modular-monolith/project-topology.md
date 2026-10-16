# Modular Monolith Topology

Use this profile when a project adopts the decomposable modular monolith (see
[overview](overview.md)). It reuses the inner layout of the
[single-service topology](../architecture/project-topology.md) unchanged: domain,
application, and infrastructure folders, port ownership, hybrid infrastructure
direction, and the `Adapter` suffix all apply inside each bounded context. Only the
differences are described here. Angle-bracket segments are placeholders chosen by the
project.

## Layout

```text
src/
├── core/                              # as in the single-service topology
├── interfaces/api/                    # only when FastAPI is used
│   └── bootstrap/
│       ├── bootstrap.py             # calls public module bootstrap/API registration
│       └── registry.py              # shared lifecycle runner
├── shared_kernel/                     # technical capabilities only
│   ├── application/ports/             # IEventPublisher, IEventSubscriber
│   └── infrastructure/                # InMemoryEventBusAdapter
└── modules/
    └── <module>/
        ├── bootstrap.py               # public startup and HTTP registration entry points
        ├── exceptions/                # module-only errors, separated by layer/context
        │   └── <context>/
        │       ├── domain.py          # pure domain failures
        │       └── application.py     # safe use-case errors
        ├── interfaces/api/            # module-owned delivery adapters
        │   ├── exceptions/            # custom HTTP mappings, when needed
        │   └── v1/
        │       ├── routers/
        │       ├── schemas/
        │       └── dependencies/
        ├── migrations/                # module-owned revisions and metadata contribution
        │   └── <context>/versions/    # optional subdivision for independent branches
        ├── contracts/                 # public integration events, nothing else
        │   └── <event>_event.py
        └── bounded_context/<context_name>/
            ├── domain/
            │   ├── models/
            │   └── repositories/
            ├── application/
            │   ├── dtos/
            │   ├── handlers/
            │   │   ├── commands/
            │   │   ├── queries/
            │   │   └── events/        # consumers of other modules' contracts
            │   ├── services/<capability>/
            │   └── ports/
            └── infrastructure/
                ├── inbound/
                └── outbound/
                    └── persistence/
```

Inside `bounded_context/<context_name>/`, `domain/`, `application/`, and
`infrastructure/` follow the single-service topology exactly; abbreviated here. Create
a package only when it has a present, cohesive responsibility. A module is a small
DDD application: its exceptions, delivery adapters, and migration history travel with
its bounded contexts when it is extracted. The host supplies process-wide facilities;
it does not own every module's customizations.

## Placement Rules

- **`modules/<module>/contracts/`** holds the module's integration events and nothing
  else. A consumer imports from it; this is the only permitted cross-module import. It
  never imports from the module's contexts.
- **Command, query, and DTO classes** stay in their handler's file. They are not
  contracts and are not importable from another module.
- **`modules/<module>/bootstrap.py`** exposes `init_<module>_module(...)`. It receives
  the ports it needs (publisher, subscriber, session factory), builds its handlers,
  and registers its subscriptions. It also exposes module API registration when HTTP
  is used; that function mounts the module's router and any custom exception mappings.
  `interfaces/api/bootstrap/bootstrap.py` calls these public entry points and does not
  import module handlers, routers, schemas, or repositories directly. Resource-based
  asynchronous startup is also valid when the module needs managed lifecycle work;
  the host registers the module's public resource rather than its individual adapters.
- **`handlers/events/`** holds the consumer of another module's event. The consumer is
  the ACL: it maps the contract to a local command and dispatches it. See
  [module communication](module-communication.md#consumer-as-acl).
- **`shared_kernel/`** keeps the single-service meaning: technical capabilities with
  explicit ownership. The event bus ports and the in-memory adapter live here;
  see [shared kernel](../ddd/bounded-contexts/shared-kernel.md). It never holds a
  module's aggregates, events, or business rules.
- **`modules/<module>/interfaces/`** owns the module's delivery adapters, including
  routers, request/response schemas, dependency factories, and custom HTTP error
  mappings. Inner layers never import them. Global `interfaces/api/` owns the host
  application, middleware, shared authentication dependencies, health endpoints, shared
  error formatting, and module mounting. Importing public module bootstrap entry
  points from the host is a composition exception to cross-module isolation; modules
  must not use that exception to import another module's bootstrap or interfaces.
- **`modules/<module>/exceptions/`** owns module-specific custom errors. Separate
  domain failures from application and infrastructure errors, grouping by context when
  a module has several. Keep package initializers free of imports that pull outer-layer
  errors into the domain. Domain code may import only the pure domain subset. Global
  `exceptions/` keeps shared bases and genuinely service-wide errors; do not accumulate
  module business errors there or re-export them through a global registry.
- **`modules/<module>/migrations/`** owns the module's revision history and metadata
  contribution, optionally grouped by context when independent branches already exist.
  Keep the shared Alembic runner, environment, and revision template in global
  `migrations/`; configure its `version_locations` to the module revision directories.
  The runner consumes metadata through module migration entry points instead of
  importing individual ORM models. Relocating revisions must preserve revision IDs,
  parent IDs, branch labels, and upgrade/downgrade behavior, including databases already
  stamped with those revisions. Do not create migration folders for modules without
  persisted data.
- **Persistence** is per module: its own tables or schema, its own migrations, its own
  ORM models. No ORM relationship or foreign key crosses a module.

## Bootstrap Example

A module wires itself; the API composition only calls it. Paths and names are
illustrative.

```python
# modules/billing/bootstrap.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.modules.billing.bounded_context.payments.application.handlers.commands.charge_payment import (
    ChargePaymentCommandHandler,
)
from src.modules.billing.bounded_context.payments.application.handlers.events.order_placed import (
    OrderPlacedEventHandler,
)
from src.modules.billing.bounded_context.payments.infrastructure.outbound.persistence.uow import (
    SqlPaymentsUnitOfWorkAdapter,
)
from src.modules.ordering.contracts.order_placed_event import OrderPlacedEvent
from src.shared_kernel.application.ports.event_bus import IEventSubscriber


def init_billing_module(
    subscriber: IEventSubscriber, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    charge_payment = ChargePaymentCommandHandler(SqlPaymentsUnitOfWorkAdapter(session_factory))
    subscriber.subscribe(OrderPlacedEvent, OrderPlacedEventHandler(charge_payment).handle)
```

```python
# interfaces/api/bootstrap/bootstrap.py
def compose(app: FastAPI, session_factory: async_sessionmaker[AsyncSession]) -> None:
    bus = InMemoryEventBusAdapter()
    init_ordering_module(publisher=bus, session_factory=session_factory)
    init_billing_module(subscriber=bus, session_factory=session_factory)
```

The composition knows public module entry points and the bus; it knows no handler or
event. For HTTP, the module also owns its registration function:

```python
# modules/billing/bootstrap.py
from fastapi import FastAPI


def register_billing_api(app: FastAPI, *, prefix: str = "/api/v1") -> None:
    from .interfaces.api.v1.routers import router

    app.include_router(router, prefix=prefix)
```

The host calls `register_billing_api(app)` from its API bootstrap. Shared auth dependencies
and error response schemas may be reused from the host API boundary; business schemas,
dependency factories, and routes stay in the module. Keep registration free of service
connections so constructing the app and its OpenAPI document does not start resources.

## Import Rules

| From | May import | May not import |
| --- | --- | --- |
| `domain` | itself, `shared_kernel/domain`, its module's pure domain exceptions | application exceptions, `application`, `infrastructure`, all interfaces, any other module |
| `application` | its context's `domain`, its module's domain/application exceptions, `shared_kernel` ports | `infrastructure`, all interfaces, any other module except `contracts/` |
| `infrastructure` | its context's `domain` and `application`, `shared_kernel` | any other module |
| `modules.A` anything | `modules.B.contracts` | `modules.B` anything else |
| Host API bootstrap | public `modules.<module>.bootstrap` entry points | module handlers, business schemas, routers, repositories |
| Global migration runner | `modules.<module>.migrations` metadata entry points | individual module ORM model packages |

Contexts inside one module may use each other's application contracts directly. If that
coupling stops being acceptable, split the module.

## Enforcing the Rules

Documentation alone drifts. Prefer a deterministic import check such as
[import-linter](https://import-linter.readthedocs.io/). The project owns the config; this
shows the shape:

```toml
[tool.importlinter]
root_packages = ["src"]

[[tool.importlinter.contracts]]
name = "Modules are independent except for contracts"
type = "forbidden"
source_modules = ["src.modules.billing"]
forbidden_modules = ["src.modules.ordering"]
allow_indirect_imports = true
ignore_imports = ["src.modules.billing.** -> src.modules.ordering.contracts.**"]

[[tool.importlinter.contracts]]
name = "Domain does not import outward"
type = "forbidden"
source_modules = ["src.modules.*.bounded_context.*.domain"]
forbidden_modules = [
    "src.modules.*.bounded_context.*.application",
    "src.modules.*.bounded_context.*.infrastructure",
    "fastapi",
    "sqlalchemy",
]
```

Add one "independent modules" contract per module pair as modules appear. This reference
does not change `scripts/ddd-check.py`.

## Review Checklist

- [ ] Each module owns startup and API registration entry points in `bootstrap.py`; host API composition imports no module internals.
- [ ] `contracts/` contains only integration events and imports nothing from its module's contexts.
- [ ] Command, query, and DTO classes live in their handler's file, not in `contracts/`.
- [ ] The only cross-module import is `modules.<other>.contracts`.
- [ ] Each module owns its persistence; nothing relates tables across modules.
- [ ] `shared_kernel/` holds only technical capabilities, never module business objects.
- [ ] The inner layout of each context matches the single-service topology.
- [ ] Module routes, schemas, dependency factories, and custom HTTP mappings live under that module's `interfaces/`; global interfaces contain only host concerns.
- [ ] Module-specific errors live in its `exceptions/`, with a pure domain subset and no outer-layer imports through package initializers.
- [ ] Revisions live under `modules/<module>/migrations/`; the global runner uses module metadata entry points and configured version locations.
- [ ] Moves preserve the HTTP/OpenAPI contract, error behavior, and migration graph; architecture checks scan module interfaces and exceptions rather than stale global paths.
