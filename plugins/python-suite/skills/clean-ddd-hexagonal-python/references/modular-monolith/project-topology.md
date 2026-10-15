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
│       ├── composition.py             # calls init_<module>_module(...) per module
│       └── registry.py
├── shared_kernel/                     # technical capabilities only
│   ├── application/ports/             # IEventPublisher, IEventSubscriber
│   └── infrastructure/                # InMemoryEventBusAdapter
└── modules/
    └── <module>/
        ├── bootstrap.py               # init_<module>_module(...)
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
a package only when it has a present, cohesive responsibility.

## Placement Rules

- **`modules/<module>/contracts/`** holds the module's integration events and nothing
  else. A consumer imports from it; this is the only permitted cross-module import. It
  never imports from the module's contexts.
- **Command, query, and DTO classes** stay in their handler's file. They are not
  contracts and are not importable from another module.
- **`modules/<module>/bootstrap.py`** exposes `init_<module>_module(...)`. It receives
  the ports it needs (publisher, subscriber, session factory), builds its handlers,
  and registers its subscriptions. `interfaces/api/bootstrap` calls it and sees nothing
  deeper.
- **`handlers/events/`** holds the consumer of another module's event. The consumer is
  the ACL: it maps the contract to a local command and dispatches it. See
  [module communication](module-communication.md#consumer-as-acl).
- **`shared_kernel/`** keeps the single-service meaning: technical capabilities with
  explicit ownership. The event bus ports and the in-memory adapter live here;
  see [shared kernel](../ddd/bounded-contexts/shared-kernel.md). It never holds a
  module's aggregates, events, or business rules.
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
# interfaces/api/bootstrap/composition.py
def compose(app: FastAPI, session_factory: async_sessionmaker[AsyncSession]) -> None:
    bus = InMemoryEventBusAdapter()
    init_ordering_module(publisher=bus, session_factory=session_factory)
    init_billing_module(subscriber=bus, session_factory=session_factory)
```

The composition knows two function names and one bus; it knows no handler or event.

## Import Rules

| From | May import | May not import |
| --- | --- | --- |
| `domain` | itself, `shared_kernel/domain` | `application`, `infrastructure`, any other module |
| `application` | its context's `domain`, `shared_kernel` ports | `infrastructure`, any other module except `contracts/` |
| `infrastructure` | its context's `domain` and `application`, `shared_kernel` | any other module |
| `modules.A` anything | `modules.B.contracts` | `modules.B` anything else |

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

- [ ] Every module has `bootstrap.py`, and the API bootstrap calls only `init_<module>_module(...)`.
- [ ] `contracts/` contains only integration events and imports nothing from its module's contexts.
- [ ] Command, query, and DTO classes live in their handler's file, not in `contracts/`.
- [ ] The only cross-module import is `modules.<other>.contracts`.
- [ ] Each module owns its persistence; nothing relates tables across modules.
- [ ] `shared_kernel/` holds only technical capabilities, never module business objects.
- [ ] The inner layout of each context matches the single-service topology.
