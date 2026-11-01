# Dependencies

FastAPI's `Depends` is the API's request-scoped composition. Dependency factories turn
process resources from typed state into a request's session, Unit of Work, and handlers.
There is no DI container.

## Factories and Aliases

`v1/dependencies/<resource>_dpd.py` holds the factories for one resource and an
`Annotated` alias per injectable, suffixed `Dpd`.

```python
# app/interfaces/api/v1/dependencies/order_dpd.py
from functools import partial
from typing import Annotated

from fastapi import Depends, Request

from app.bounded_context.ordering.application.handlers.commands.place_order_handler import (
    PlaceOrderHandler,
)
from app.bounded_context.ordering.application.handlers.queries.get_order_handler import (
    GetOrderHandler,
)
from app.bounded_context.ordering.infrastructure.outbound.persistence.ordering_unit_of_work_adapter import (
    SqlOrderingUnitOfWorkAdapter,
)
from app.bounded_context.ordering.infrastructure.outbound.persistence.repositories.sql_order_read_repository_adapter import (
    SqlOrderReadRepositoryAdapter,
)
from app.interfaces.api.state import api_state


def get_place_order_handler(request: Request) -> PlaceOrderHandler:
    session_factory = api_state(request).session_factory
    return PlaceOrderHandler(partial(SqlOrderingUnitOfWorkAdapter, session_factory))


def get_get_order_handler(request: Request) -> GetOrderHandler:
    return GetOrderHandler(SqlOrderReadRepositoryAdapter(api_state(request).session_factory))


PlaceOrderHandlerDpd = Annotated[PlaceOrderHandler, Depends(get_place_order_handler)]
GetOrderHandlerDpd = Annotated[GetOrderHandler, Depends(get_get_order_handler)]
```

- Routers depend only on handler aliases (`PlaceOrderHandlerDpd`) and auth aliases. They
  never depend on a session, repository, or Unit of Work alias.
- The Unit of Work adapter opens its own session from the session factory on each
  `handle` call and commits inside the handler, never in the dependency.
- When handlers are also built by another interface, call the shared builder in
  `app/bootstrap/` from the factory instead of repeating the wiring.
- Factories never construct engines, clients, or pools; those are process resources read
  from typed state.
- Module-level handler or repository singletons (as in the template's in-memory examples)
  are acceptable only for in-memory demo adapters; replace them with request-scoped
  factories as soon as a real adapter exists.

## Authentication Dependencies

`v1/dependencies/auth_dpd.py` reads credentials from the request, calls the
token-validator port from typed state, and returns the application-owned security DTO
(`UserContextDTO`) defined by the foundation's
[application security contracts](../../ddd-hexagonal-python/references/architecture/project-topology.md#application-security-contracts).
Missing or invalid credentials raise interface errors such as `AuthenticationRequiredError`
with `metadata={"_response_headers": {"WWW-Authenticate": "Bearer"}}`.

```python
CurrentUserDpd = Annotated[UserContextDTO, Depends(get_current_user)]
```

Handlers that need the caller receive the DTO's relevant fields in their command
(`PlaceOrderCommand(customer_id=user.subject, ...)`), never the request.

## Review Checklist

- [ ] Each resource's factories and `*Dpd` aliases live in `v1/dependencies/<resource>_dpd.py`.
- [ ] Routers depend only on handler and auth aliases.
- [ ] Handlers are built per request; each `handle` call opens its own Unit of Work from the session factory in typed state; no connection-holding singleton.
- [ ] Authentication dependencies return application-owned security DTOs and raise interface errors with challenge headers.
