# Composition Root and Process Resources

Read this when deciding where concrete adapters are chosen, where handlers are built, how
process-scoped resources (engines, pools, brokers) start and stop, or when a second
interface (CLI next to an API, a worker next to a CLI) joins a service.

## One Composition Root per Process

The composition root is the only code that knows both an abstract port and its concrete
adapter. It reads settings, builds adapters, injects them into handlers, and hands the
handlers to the interface. Nothing else instantiates infrastructure.

| Rule | Why |
| --- | --- |
| Inner layers never import the composition root | It depends on everything; importing it reverses the arrows |
| The interface calls handlers it received from the composition root, never repositories or adapters | The interface stays a translator; business flow stays testable without it |
| Settings are read here, not at import time of inner layers | Import-time I/O breaks `--help`, tests, and tooling |
| Replacement adapters enter through parameters (`build_ordering(settings, *, payments=None)`) | Tests substitute fakes without patching |
| No module-level singleton holds a connection | Lifetime must be explicit so it can be closed and re-created |
| Two modules or contexts never exchange objects through string keys on a shared state bag | A string key plus startup order is a hidden contract; return typed objects from the public bootstrap instead |

## Where It Lives

| Situation | Location |
| --- | --- |
| One interface | `interfaces/<kind>/bootstrap/` (or a single `bootstrap.py` module) inside that interface |
| Two or more interfaces build the same handlers | Shared wiring in `<package>/bootstrap/`; each interface keeps only its own lifecycle and state |
| Modular monolith | Each module's `modules/<module>/bootstrap.py` wires the module. The host interface's bootstrap only orders module entry points. See [modular monolith topology](../deployment/modular-monolith-topology.md) |
| Microservices | Each service has its own composition root; nothing is shared at runtime |

Do not create `<package>/bootstrap/` speculatively. Move wiring up when the second
interface arrives, in the same change, and leave each interface with a thin adapter:

```python
# app/bootstrap/ordering.py — shared by the API and the CLI
from collections.abc import Callable
from dataclasses import dataclass

from app.bounded_context.ordering.application.handlers.commands.place_order_handler import (
    PlaceOrderHandler,
)
from app.bounded_context.ordering.application.handlers.queries.get_order_handler import (
    GetOrderHandler,
)
from app.bounded_context.ordering.application.ports.read_repositories import (
    IOrderReadRepository,
)
from app.bounded_context.ordering.application.ports.transactions import IOrderingUnitOfWork


@dataclass(frozen=True, slots=True)
class OrderingHandlers:
    place_order: PlaceOrderHandler
    get_order: GetOrderHandler


def build_ordering(
    uow_factory: Callable[[], IOrderingUnitOfWork],
    read_repository: IOrderReadRepository,
) -> OrderingHandlers:
    return OrderingHandlers(
        place_order=PlaceOrderHandler(uow_factory),
        get_order=GetOrderHandler(read_repository),
    )
```

The HTTP interface calls `build_ordering(...)` from a request-scoped dependency; the CLI
calls it once per invocation. The handlers are the same, and each `handle` call opens its
own Unit of Work (and session) from the injected factory.

## Process Resources

A process resource owns something with a lifetime: a database engine, a connection pool,
a broker connection, a background poller. Model it with an interface-neutral port:

```python
# app/shared_kernel/application/ports/resources/i_resource.py
from typing import Protocol


class IResource(Protocol):
    """Something with a start and an end that the process must manage."""

    async def startup(self) -> None: ...

    async def shutdown(self) -> None: ...
```

- A resource exposes what it built through typed attributes or methods
  (`engine_resource.session_factory`). It never takes a framework object such as a
  FastAPI `app` and never writes into `app.state`. Publishing resources into framework
  state is the interface adapter's job.
- A registry starts resources in order and shuts them down in reverse order, also when a
  later startup fails. It is interface-neutral; keep it in
  `shared_kernel/infrastructure/resources/registry.py`.
- The interface decides when the registry runs: the FastAPI lifespan, the body of one CLI
  command, a worker's main loop.

The `python/ddd_fastapi` template currently types `IResource.startup(app: FastAPI)` and
writes to `app.state` from `shared_kernel/infrastructure/resources/`. That couples the
shared kernel to one interface and blocks a CLI or worker from reusing the resources.
Projects generated from it keep working. When a second interface is added, move to the
neutral port above and let the FastAPI bootstrap publish the resources into typed state.

## Sync and Async

Handlers and ports are `async` when any adapter performs I/O. The interface bridges:

- An ASGI server already runs an event loop; routes `await` handlers.
- A CLI command runs one `asyncio.run(...)` per invocation, around the whole command.
- A worker owns its loop and awaits handlers per message.

Never call `asyncio.run` inside application or infrastructure code.

## Review Checklist

- [ ] Exactly one place per process chooses concrete adapters; inner layers never import it.
- [ ] Interfaces call handlers they received from the composition root, never repositories or adapters.
- [ ] Settings are loaded by the composition root, not at import time of inner layers.
- [ ] Shared wiring lives in `<package>/bootstrap/` only once two interfaces need it.
- [ ] Resources implement the interface-neutral `IResource`; none takes a framework object or writes framework state.
- [ ] Shutdown runs in reverse order and also after a partial startup failure.
- [ ] No module-level singleton holds a connection; no cross-module exchange through string state keys.
