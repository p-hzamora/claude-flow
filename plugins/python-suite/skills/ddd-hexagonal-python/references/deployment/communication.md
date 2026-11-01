# Module Communication

Modules talk through integration events only. This file defines the handler types, the
contract shape, the bus ports, and the delivery guarantees. For event concepts, outbox,
and idempotent consumers, link to [CQRS events](../cqrs/events.md) rather than copying
it. Placement is in the [modular monolith topology](modular-monolith-topology.md); between services, see [microservices](microservices.md).

## Two Kinds of Handler

Confusing them couples the modules.

| | Command handler (CQRS) | Event handler (EDA) |
| --- | --- | --- |
| Intent | Proactive: "do this". The domain may reject it | Reactive: "this happened". It cannot be cancelled |
| Called by | An interface (HTTP, CLI, worker) or a scheduler | The bus, through a subscription |
| Input | A command class in the handler's file | An integration contract from another module |
| Layer | Application | Application, acting as the ACL |
| Location | `application/handlers/commands/` | `application/handlers/events/` |

An event handler never contains business rules. It translates the contract into a local
command and dispatches that command to a command handler.

## Contract Shape

A contract is a Pydantic `FrozenObject` subclass in `modules/<module>/contracts/`, named
for a fact in the past tense, matching the project's convention for value objects,
commands, DTOs, and domain events (not a frozen `@dataclass`). `FrozenObject` is a
shared technical primitive, so it lives in `<package>/utils/` and `contracts/` imports it
from there, never from a module. A contract serializes with `model_dump(mode="json")`
and parses with `model_validate`, so extraction needs no rewrite and a consumer rejects
a malformed payload at the boundary.

- Allowed fields: `str`, `int`, `bool`, `None`, lists of those, and flat nested
  `FrozenObject`s of those.
- Datetimes are ISO-8601 `str`. IDs are `str`.
- **Money is never `float`.** Use `amount: str` (decimal string) plus `currency: str`,
  or integer minor units.
- Every contract carries `event_id`, `occurred_at`, and `schema_version`. A breaking
  change creates a new version; do not mutate a published one.
- No entity, value object, enum from a domain, or ORM object appears in a contract.

```python
from app.utils import FrozenObject


class OrderPlacedEvent(FrozenObject):
    event_id: str
    occurred_at: str
    order_id: str
    customer_id: str
    total_amount: str
    currency: str
    schema_version: int = 1
```

## Bus Ports

The bus is a driven capability in `shared_kernel/`, injected, never a module-level
singleton.

```python
# app/shared_kernel/application/ports/event_bus/i_event_bus.py
from collections.abc import Awaitable, Callable
from typing import Protocol


class IEventPublisher(Protocol):
    async def publish[E](self, event: E) -> None: ...


class IEventSubscriber(Protocol):
    def subscribe[E](
        self, event_type: type[E], handler: Callable[[E], Awaitable[None]]
    ) -> None: ...
```

`InMemoryEventBusAdapter` in `shared_kernel/infrastructure/` implements both. It
isolates handler failures so a consumer error never reaches the publishing command:

```python
# app/shared_kernel/infrastructure/event_bus/in_memory_event_bus_adapter.py
import logging
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)


class InMemoryEventBusAdapter:
    def __init__(self) -> None:
        self._handlers: dict[type, list[Callable[[Any], Awaitable[None]]]] = {}

    def subscribe[E](
        self, event_type: type[E], handler: Callable[[E], Awaitable[None]]
    ) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish[E](self, event: E) -> None:
        for handler in self._handlers.get(type(event), []):
            try:
                await handler(event)
            except Exception:
                logger.exception("handler failed for %s", type(event).__name__)
```

A
`RabbitMqPublisherAdapter` or `KafkaPublisherAdapter` replaces it at composition time
only; no handler changes. Follow the repo's interface naming convention if it differs
from `I<Name>`.

## Publishing

The command handler persists through the Unit of Work, then publishes a contract built
from the committed state. The aggregate and its domain events stay inside the module; the
handler maps them to a contract.

```python
# app/modules/ordering/bounded_context/ordering/application/handlers/commands/place_order_handler.py (excerpt)
class PlaceOrderHandler(IHandler[PlaceOrderCommand, OrderDTO]):
    def __init__(
        self,
        uow_factory: Callable[[], IOrderingUnitOfWork],
        publisher: IEventPublisher,
    ) -> None:
        self._uow_factory = uow_factory
        self._publisher = publisher

    async def handle(self, action: PlaceOrderCommand) -> OrderDTO:
        async with self._uow_factory() as uow:
            order = Order.create(
                customer_id=CustomerId(value=action.customer_id), currency=action.currency
            )
            ...  # add_item per line, as in CQRS implementation
            order.place()
            await uow.orders.save(order)
            await uow.commit()
        for event in order.pull_domain_events():
            if (contract := OrderContractMapper.to_contract(event)) is not None:
                await self._publisher.publish(contract)
        return OrderAssembler.to_dto(order)
```

`OrderContractMapper` is shown in [CQRS events](../cqrs/events.md#mapping-a-domain-event-to-a-contract).
This direct publish is delivery level 0; use the outbox variant there before a broker.

## Consumer as ACL

The consumer lives in the downstream module and maps the contract to a local command.

```python
from app.modules.ordering.contracts.order_placed_event import OrderPlacedEvent


class OrderPlacedHandler:
    def __init__(self, charge_payment: ChargePaymentHandler) -> None:
        self._charge_payment = charge_payment

    async def handle(self, event: OrderPlacedEvent) -> None:
        await self._charge_payment.handle(
            ChargePaymentCommand(
                external_order_id=event.order_id,
                amount=Money.from_string(event.total_amount, event.currency),
                idempotency_key=event.event_id,
            )
        )
```

The consumer imports the publisher's `contracts/` module only. Billing's domain never
imports the contract; only this handler does.

## Delivery Guarantees

The in-memory bus is **level 0**: fine inside one process, with known gaps.

| Level | Transport | Rule |
| --- | --- | --- |
| 0 | In-memory bus | Event can be lost if the process dies between commit and publish. Handlers run in the publisher's call path |
| 1 | Outbox plus relay, then broker | Event stored in the same transaction as the state change. Required before any broker adapter. See [outbox](../cqrs/events.md) |

Rules that apply from day one, at both levels:

- **Handlers are idempotent.** Deduplicate on `event_id`; see the idempotent consumer
  pattern in [CQRS events](../cqrs/events.md).
- **A handler must not break the publisher.** The bus adapter isolates and logs a
  handler failure; the publishing command has already committed and must not fail
  because a consumer did. Failed handling needs a retry or dead-letter path before it is
  trusted for real money or stock.
- **Do not depend on handler order** or on a handler finishing before the publisher
  returns.

## Cross-Module Reads

No synchronous call into another module. A module needing another's data stores the ID
as opaque, or builds a local projection fed by the other module's events, in its own
tables. Validate through the event flow, not by asking.

## Review Checklist

- [ ] Command handlers and event handlers are separate, in `commands/` and `events/`.
- [ ] Event handlers only translate and dispatch a local command; no business rule.
- [ ] Contracts extend `FrozenObject` (not `@dataclass`), are JSON-serializable, versioned, and contain no `float` money.
- [ ] The bus is injected through `IEventPublisher` / `IEventSubscriber`; no global singleton.
- [ ] Handlers are idempotent on `event_id` and cannot fail the publishing command.
- [ ] An outbox exists before any broker adapter replaces the in-memory bus.
- [ ] No cross-module synchronous call exists; reads use an ID or a local projection.
