# Modular Monolith Topology

Use this profile when a project adopts the decomposable modular monolith (see
[modular monolith](modular-monolith.md)). It reuses the inner layout of the
[single-service topology](../architecture/project-topology.md) unchanged: domain,
application, and infrastructure folders, port ownership, hybrid infrastructure direction,
naming, and the `Adapter` suffix all apply inside each bounded context. Only the
differences are described here. Angle-bracket segments are placeholders chosen by the
project; `<kind>` is an interface kind such as `api` or `cli`.

## Layout

```text
<package>/
├── main.py | __main__.py              # entry point of the host interface
├── core/                              # as in the single-service topology
├── exceptions/                        # shared bases and service-wide errors only
├── utils/
├── interfaces/<kind>/                 # HOST: process-level concerns of each interface
│   └── bootstrap/                     # orders public module entry points; shared lifecycle
├── migrations/                        # global runner and environment only
├── shared_kernel/                     # technical capabilities only
│   ├── application/ports/             # IEventPublisher, IEventSubscriber, IResource
│   └── infrastructure/                # InMemoryEventBusAdapter, resource registry
└── modules/
    └── <module>/
        ├── bootstrap.py               # public entry points: wiring + per-interface registration
        ├── contracts/                 # public integration events, nothing else
        │   └── <fact>_event.py
        ├── exceptions/                # module-only errors, separated by context and layer
        │   └── <context>/
        │       ├── domain.py          # pure domain failures
        │       ├── application.py     # use-case errors
        │       └── infrastructure.py
        ├── interfaces/<kind>/         # module-owned entry modules and outputs
        ├── migrations/                # module-owned revisions and metadata contribution
        │   └── <context>/versions/    # optional subdivision for independent branches
        └── bounded_context/<context>/
            ├── domain/
            ├── application/
            │   └── handlers/events/   # consumers of other modules' contracts (the ACL)
            └── infrastructure/
```

Inside `bounded_context/<context>/`, the layers follow the single-service topology exactly;
they are abbreviated here. Create a package only when it has a present, cohesive
responsibility. A module is a small DDD application: its exceptions, interfaces, and
migration history travel with its bounded contexts when it is extracted.

## Placement Rules

- **`modules/<module>/contracts/`** holds the module's integration events and nothing else.
  A consumer imports from it; this is the only permitted cross-module import. It never
  imports from the module's contexts. `FrozenObject` comes from `<package>/utils/`.
- **Commands and queries** stay in their handler's file and **DTOs** in their context's
  `dtos/`. Neither is a contract; neither is importable from another module.
- **`modules/<module>/bootstrap.py`** is the module's composition root. It exposes:
  - a wiring entry point that receives the shared ports it needs (publisher, subscriber,
    session factory), builds its handlers, and registers its subscriptions. Use a
    function `init_<module>_module(...)` for synchronous wiring, or a resource class
    implementing `IResource` when the module has startup and shutdown work;
  - one registration function per interface it serves, such as
    `register_<module>_api(app)` or `register_<module>_cli(app)`. The interface skills
    show their shape.

  The host bootstrap calls these public entry points in order and imports nothing else from
  a module. Importing public module bootstrap entry points from the host is a composition
  exception to module isolation; modules never use it to import each other's bootstrap.
- **What one module gives another** at composition time is a typed object returned from its
  public entry point and passed explicitly by the host, never a string key on shared
  framework state. Prefer events; see [communication](communication.md).
- **`handlers/events/`** holds the consumer of another module's event. The consumer is the
  ACL: it maps the contract to a local command and dispatches it.
- **`shared_kernel/`** keeps the single-service meaning: technical capabilities with explicit
  ownership. The event-bus ports, the in-memory adapter, and the resource registry live
  here. It never holds a module's aggregates, events, or business rules.
- **`modules/<module>/interfaces/<kind>/`** owns the module's entry modules (routers,
  commands), input and output models, and custom error mappings. Inner layers never import
  it. The host `interfaces/<kind>/` owns the process: the application object, middleware or
  global options, shared authentication, health or diagnostics, shared error formatting, and
  module registration.
- **`modules/<module>/exceptions/`** owns module-specific errors. Separate domain failures
  from application and infrastructure errors, grouped by context. Keep package initializers
  free of imports that pull outer-layer errors into the domain. Domain code imports only the
  pure domain subset. Global `exceptions/` keeps shared bases and genuinely service-wide
  errors; do not re-export module errors through a global registry.
- **`modules/<module>/migrations/`** owns the module's revision history and metadata
  contribution (for example a `CONTEXT_METADATA` mapping per context), optionally grouped by
  context. The shared Alembic runner, environment, and revision template stay in global
  `migrations/`, configured with `version_locations` pointing at the module revision
  directories. The runner consumes metadata through module migration entry points, not by
  importing ORM models. Relocating revisions preserves revision IDs, parent IDs, branch
  labels, and upgrade/downgrade behaviour. Do not create migration folders for modules
  without persisted data.
- **Persistence** is per module: its own tables or schema, migrations, and ORM models. No
  foreign key, join, or ORM relationship crosses a module.

## Wiring Example

A module wires itself; the host only calls it. Names are illustrative.

```python
# app/modules/billing/bootstrap.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.billing.bounded_context.payments.application.handlers.commands.charge_payment_handler import (
    ChargePaymentHandler,
)
from app.modules.billing.bounded_context.payments.application.handlers.events.order_placed_handler import (
    OrderPlacedHandler,
)
from app.modules.billing.bounded_context.payments.infrastructure.outbound.persistence.payments_unit_of_work_adapter import (
    SqlPaymentsUnitOfWorkAdapter,
)
from app.modules.ordering.contracts.order_placed_event import OrderPlacedEvent
from app.shared_kernel.application.ports.event_bus import IEventSubscriber


def init_billing_module(
    subscriber: IEventSubscriber, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    charge_payment = ChargePaymentHandler(lambda: SqlPaymentsUnitOfWorkAdapter(session_factory))
    subscriber.subscribe(OrderPlacedEvent, OrderPlacedHandler(charge_payment).handle)
```

```python
# app/interfaces/<kind>/bootstrap/composition.py — host
def compose(session_factory: async_sessionmaker[AsyncSession]) -> None:
    bus = InMemoryEventBusAdapter()
    init_ordering_module(publisher=bus, session_factory=session_factory)
    init_billing_module(subscriber=bus, session_factory=session_factory)
```

The host knows public module entry points and the bus; it knows no handler or event. How a
module registers its routes or commands with the host is in the interface skills
(`ddd-interface-fastapi`, `ddd-interface-cli`, reference `topology-and-bootstrap.md`).

## Import Rules

| From | May import | May not import |
| --- | --- | --- |
| `domain` | itself, `shared_kernel/domain`, `utils`, its module's pure domain exceptions | application exceptions, `application`, `infrastructure`, any interface, any other module |
| `application` | its context's `domain`, its module's domain/application exceptions, `shared_kernel` ports | `infrastructure`, any interface, any other module except `contracts/` |
| `infrastructure` | its context's `domain` and `application`, `shared_kernel` | any other module except `contracts/` |
| `modules.A` anything | `modules.B.contracts` | `modules.B` anything else |
| Host interface bootstrap | public `modules.<module>.bootstrap` entry points | module handlers, routers, commands, schemas, repositories |
| Global migration runner | `modules.<module>.migrations` metadata entry points | individual module ORM model packages |

Contexts inside one module may use each other's application contracts directly through an
ACL adapter. If that coupling stops being acceptable, split the module.

## Enforcing the Rules

Documentation alone drifts. Use import-linter (or equivalent AST architecture tests). The
project owns the configuration; this shows the shape:

```toml
[tool.importlinter]
root_packages = ["app"]
include_external_packages = true

[[tool.importlinter.contracts]]
name = "Modules are independent except for contracts"
type = "independence"
modules = ["app.modules.ordering", "app.modules.billing", "app.modules.catalog"]
ignore_imports = ["app.modules.* -> app.modules.*.contracts"]

[[tool.importlinter.contracts]]
name = "Contracts import nothing from their module"
type = "forbidden"
source_modules = ["app.modules.*.contracts"]
forbidden_modules = ["app.modules.*.bounded_context", "app.modules.*.interfaces"]

[[tool.importlinter.contracts]]
name = "Domain does not import outward"
type = "forbidden"
source_modules = ["app.modules.*.bounded_context.*.domain"]
forbidden_modules = [
    "app.modules.*.bounded_context.*.application",
    "app.modules.*.bounded_context.*.infrastructure",
    "app.interfaces",
    "fastapi",
    "typer",
    "sqlalchemy",
]
```

Without `ignore_imports`, the independence contract rejects the first legal contracts
import. `scripts/ddd-check.py` checks the single-service `bounded_context/` layout; module
rules rely on the project's import contracts.

## Review Checklist

- [ ] Each module owns its wiring and per-interface registration in `bootstrap.py`; the host imports no module internals.
- [ ] `contracts/` contains only integration events and imports nothing from its module's contexts.
- [ ] Commands, queries, and DTOs are not in `contracts/` and are not imported across modules.
- [ ] The only cross-module import is `modules.<other>.contracts`; nothing passes between modules through string keys on shared state.
- [ ] Each module owns its persistence; nothing relates tables across modules.
- [ ] `shared_kernel/` holds only technical capabilities, never module business objects.
- [ ] The inner layout of each context matches the single-service topology.
- [ ] Module entry modules, input/output models, and custom error mappings live under the module's `interfaces/<kind>/`; host interfaces contain only process concerns.
- [ ] Module-specific errors live in its `exceptions/`, with a pure domain subset and no outer-layer imports through package initializers.
- [ ] Revisions live under `modules/<module>/migrations/`; the global runner uses module metadata entry points and configured version locations.
- [ ] Import contracts enforce module independence with an explicit exception for `contracts/`.
