# Testing Strategy

> Sources:
> - [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) — Alistair Cockburn
> - [Test Pyramid](https://martinfowler.com/bliki/TestPyramid.html) — Martin Fowler
> - [Architecture Patterns with Python](https://www.cosmicpython.com/) — Percival & Gregory

Read this to decide what to test at which level in a DDD + hexagonal + CQRS service, where
each test lives, and how architecture rules are enforced. Generic pytest mechanics
(fixtures, parametrization, markers, async plugins, coverage, configuration, command line)
belong to the [`pytest`](../../../pytest/SKILL.md) skill. Examples use the `ordering`
context and the `app` package root from the [project topology](../architecture/project-topology.md),
and assume `asyncio_mode = "auto"`.

## Levels

The hexagon is testable without any interface or concrete infrastructure. Most tests
therefore sit at the two inner levels and run in milliseconds.

| Level | Subject | Real dependencies | Location |
| --- | --- | --- | --- |
| Domain unit | Aggregates, entities, value objects, domain services, specifications | None, no test doubles either | `tests/unit/bounded_context/<context>/domain/` |
| Application unit | Command, query, and event handlers | None: fakes implement the ports | `tests/unit/bounded_context/<context>/application/` |
| Infrastructure integration | Each `...Adapter`: repositories, Unit of Work, read repositories, gateways | The real technology (database, broker, HTTP stub) | `tests/integration/bounded_context/<context>/infrastructure/` |
| Interface | Each `interfaces/<kind>/` at its edge | Composition root with fakes or real adapters | Defined by the interface skill |
| Architecture | Import direction and context independence | None | `tests/architecture/` |
| End to end | A few business journeys across the deployed stack | All | `tests/e2e/`, optional |

Test business rules where they live. A rule tested through a handler or an interface is
tested at the wrong level: the failure points at plumbing instead of the rule.

## Test Organization

Tests mirror the package layout, so the path of a test names the layer and the context it
protects.

```text
tests/
├── conftest.py                          # fixtures shared by every level only
├── builders/
│   └── order_builder.py                 # valid aggregates built through behaviour
├── fakes/
│   └── ordering.py                      # in-memory implementations of ordering ports
├── unit/bounded_context/ordering/
│   ├── domain/
│   │   ├── test_order.py
│   │   └── test_money.py
│   └── application/
│       ├── test_place_order_handler.py
│       └── test_get_order_handler.py
├── integration/bounded_context/ordering/infrastructure/
│   ├── test_sql_order_repository_adapter.py
│   └── test_sql_order_read_repository_adapter.py
├── architecture/
│   └── test_import_contracts.py
└── e2e/
```

Interface tests follow the folder their interface skill prescribes. In a
[modular monolith](../deployment/modular-monolith-topology.md), insert the module:
`tests/unit/modules/<module>/bounded_context/<context>/...`. A context that is later
extracted takes its tests with it unchanged.

## Domain Tests

The domain imports no framework and no I/O, so its tests need no fixtures and no test
doubles. Assert observable behaviour: state after a transition, recorded events, and the
typed error with its stable code. Never assert on private attributes or error messages.

```python
# tests/unit/bounded_context/ordering/domain/test_order.py
from decimal import Decimal

import pytest

from app.bounded_context.ordering.domain.entities.order import Order
from app.bounded_context.ordering.domain.enums.order_status_enum import OrderStatusEnum
from app.bounded_context.ordering.domain.events.order_placed_event import OrderPlacedEvent
from app.bounded_context.ordering.domain.value_objects.customer_id import CustomerId
from app.bounded_context.ordering.domain.value_objects.money import Money
from app.bounded_context.ordering.domain.value_objects.product_id import ProductId
from app.exceptions.ordering_errors import EmptyOrderError, InvalidQuantityError

EUR_10 = Money(amount=Decimal("10.00"), currency="EUR")


def draft_order() -> Order:
    return Order.create(customer_id=CustomerId())


class TestOrder:
    def test_new_order_is_draft_without_items(self) -> None:
        order = draft_order()

        assert order.status is OrderStatusEnum.DRAFT
        assert order.items == ()

    def test_adding_the_same_product_twice_merges_quantities(self) -> None:
        order = draft_order()
        product_id = ProductId()

        order.add_item(product_id=product_id, quantity=2, unit_price=EUR_10)
        order.add_item(product_id=product_id, quantity=3, unit_price=EUR_10)

        assert len(order.items) == 1
        assert order.items[0].quantity == 5
        assert order.total == Money(amount=Decimal("50.00"), currency="EUR")

    @pytest.mark.parametrize("quantity", [0, -1])
    def test_rejects_a_non_positive_quantity(self, quantity: int) -> None:
        with pytest.raises(InvalidQuantityError):
            draft_order().add_item(product_id=ProductId(), quantity=quantity, unit_price=EUR_10)

    def test_place_records_order_placed_event(self) -> None:
        order = draft_order()
        order.add_item(product_id=ProductId(), quantity=1, unit_price=EUR_10)

        order.place()

        assert order.status is OrderStatusEnum.PLACED
        assert isinstance(order.domain_events[-1], OrderPlacedEvent)

    def test_an_empty_order_cannot_be_placed(self) -> None:
        with pytest.raises(EmptyOrderError) as caught:
            draft_order().place()

        assert caught.value.error_code == "ORD-003"
```

Value objects are tested for validation, equality by value, and immutability. A
`FrozenObject` rejects assignment with pydantic's `ValidationError`:

```python
# tests/unit/bounded_context/ordering/domain/test_money.py
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.bounded_context.ordering.domain.value_objects.money import Money
from app.exceptions.ordering_errors import CurrencyMismatchError


def test_money_is_equal_by_value() -> None:
    assert Money(amount=Decimal("10.00"), currency="EUR") == Money(
        amount=Decimal("10.00"), currency="EUR"
    )


def test_money_is_immutable() -> None:
    money = Money(amount=Decimal("10.00"), currency="EUR")

    with pytest.raises(ValidationError):
        money.amount = Decimal("20.00")


def test_money_rejects_mixed_currencies() -> None:
    euros = Money(amount=Decimal("1.00"), currency="EUR")
    dollars = Money(amount=Decimal("1.00"), currency="USD")

    with pytest.raises(CurrencyMismatchError):
        euros.add(dollars)
```

## Application Tests

A handler test proves orchestration: the right aggregate behaviour runs, the Unit of Work
commits only on success, and a DTO comes back. It uses **fakes**, small in-memory classes
that implement the port Protocols. Do not patch module paths (`unittest.mock.patch`) and
do not mock the domain. The handler receives its collaborators through its constructor,
exactly as the [composition root](../architecture/composition-root.md) wires it, so the
test substitutes them the same way.

```python
# tests/fakes/ordering.py
from types import TracebackType
from typing import Self

from app.bounded_context.ordering.domain.entities.order import Order
from app.bounded_context.ordering.domain.value_objects.order_id import OrderId


class FakeOrderRepository:
    """In-memory implementation of IOrderRepository."""

    def __init__(self) -> None:
        self.saved: dict[OrderId, Order] = {}

    async def get_by_id(self, order_id: OrderId) -> Order | None:
        return self.saved.get(order_id)

    async def save(self, order: Order) -> None:
        self.saved[order.id] = order


class FakeOrderingUnitOfWork:
    """In-memory implementation of IOrderingUnitOfWork that records the outcome."""

    def __init__(self) -> None:
        self.orders = FakeOrderRepository()
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True
```

```python
# tests/unit/bounded_context/ordering/application/test_place_order_handler.py
from decimal import Decimal
from uuid import uuid4

import pytest

from app.bounded_context.ordering.application.dtos.order_dto import OrderDTO
from app.bounded_context.ordering.application.handlers.commands.place_order_handler import (
    PlaceOrderCommand,
    PlaceOrderHandler,
    PlaceOrderLine,
)
from app.exceptions.ordering_errors import EmptyOrderError
from tests.fakes.ordering import FakeOrderingUnitOfWork


def place_order_command(*lines: PlaceOrderLine) -> PlaceOrderCommand:
    return PlaceOrderCommand(customer_id=uuid4(), currency="EUR", lines=lines)


async def test_places_the_order_and_returns_a_dto() -> None:
    uow = FakeOrderingUnitOfWork()
    handler = PlaceOrderHandler(lambda: uow)
    command = place_order_command(
        PlaceOrderLine(product_id=uuid4(), quantity=2, unit_price=Decimal("10.00")),
        PlaceOrderLine(product_id=uuid4(), quantity=1, unit_price=Decimal("5.00")),
    )

    result = await handler.handle(command)

    assert isinstance(result, OrderDTO)
    assert result.status == "placed"
    assert result.total_amount == Decimal("25.00")
    assert uow.committed
    assert len(uow.orders.saved) == 1


async def test_an_empty_order_is_rejected_without_committing() -> None:
    uow = FakeOrderingUnitOfWork()
    handler = PlaceOrderHandler(lambda: uow)

    with pytest.raises(EmptyOrderError):
        await handler.handle(place_order_command())

    assert not uow.committed
    assert uow.orders.saved == {}
```

- A fake is complete enough to honour the port's contract and nothing more. When a type
  checker reports that the fake no longer satisfies the Protocol, the port changed; update
  the fake in the same change.
- Keep fakes in `tests/fakes/<context>.py`; interface tests reuse them through the
  composition root.
- Assert that the handler returned a DTO. A handler that returns an entity, value object,
  or ORM model is a defect, not a style choice.
- Query handlers are tested the same way with a fake read repository that returns DTOs.

## Infrastructure Integration Tests

Each adapter is tested against the real technology it wraps. These tests prove the
mapping (`OrderMapper.to_orm` / `to_entity`, `OrderReadMapper.to_dto`), the query, and the
translation of driver errors into typed `InfrastructureException` subclasses. They do not
re-test business rules.

```python
# tests/integration/bounded_context/ordering/infrastructure/test_sql_order_repository_adapter.py
from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.bounded_context.ordering.domain.value_objects.order_id import OrderId
from app.bounded_context.ordering.infrastructure.outbound.persistence.models.base import (
    OrderingBase,
)
from app.bounded_context.ordering.infrastructure.outbound.persistence.repositories.sql_order_repository_adapter import (
    SqlOrderRepositoryAdapter,
)
from tests.builders.order_builder import OrderBuilder


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(OrderingBase.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


async def test_round_trips_the_aggregate(session: AsyncSession) -> None:
    repository = SqlOrderRepositoryAdapter(session)
    order = OrderBuilder().with_item(quantity=2).placed().build()

    await repository.save(order)
    await session.commit()
    session.expunge_all()  # force a real reload through the mapper

    loaded = await repository.get_by_id(order.id)

    assert loaded is not None
    assert loaded.id == order.id
    assert loaded.status is order.status
    assert loaded.total == order.total


async def test_returns_none_for_an_unknown_order(session: AsyncSession) -> None:
    assert await SqlOrderRepositoryAdapter(session).get_by_id(OrderId()) is None
```

- Use the production database engine (for example through a container) when the adapter
  relies on dialect features: JSON columns, locking, upserts, schema-per-context. In-memory
  SQLite is acceptable only for portable SQL.
- Test the Unit of Work adapter for its boundary: changes are visible after `commit()` and
  absent after an exception inside `async with`.
- A gateway adapter is tested against a local stub of the remote API; assert both the
  success mapping and that timeouts and error statuses become typed infrastructure errors
  with the original as `__cause__`.

## Test Data Builders

Builders create valid aggregates through the aggregate's own behaviour, so every test
object satisfies the invariants the production code enforces. Never assemble an aggregate
by setting fields or by constructing ORM rows.

```python
# tests/builders/order_builder.py
from decimal import Decimal
from typing import Self

from app.bounded_context.ordering.domain.entities.order import Order
from app.bounded_context.ordering.domain.value_objects.customer_id import CustomerId
from app.bounded_context.ordering.domain.value_objects.datetime import Datetime
from app.bounded_context.ordering.domain.value_objects.money import Money
from app.bounded_context.ordering.domain.value_objects.product_id import ProductId


class OrderBuilder:
    def __init__(self) -> None:
        self._customer_id = CustomerId()
        self._lines: list[tuple[ProductId, int, Money]] = []
        self._placed_at: Datetime | None = None
        self._placed = False
        self._shipped = False

    def for_customer(self, customer_id: CustomerId) -> Self:
        self._customer_id = customer_id
        return self

    def with_item(self, *, quantity: int = 1, unit_price: Decimal = Decimal("10.00")) -> Self:
        self._lines.append((ProductId(), quantity, Money(amount=unit_price, currency="EUR")))
        return self

    def placed(self, *, at: Datetime | None = None) -> Self:
        self._placed, self._placed_at = True, at
        return self

    def shipped(self) -> Self:
        self._shipped = True
        return self

    def build(self) -> Order:
        order = Order.create(customer_id=self._customer_id)
        for product_id, quantity, unit_price in self._lines:
            order.add_item(product_id=product_id, quantity=quantity, unit_price=unit_price)
        if self._placed or self._shipped:
            order.place(at=self._placed_at)
        if self._shipped:
            order.ship()
        return order
```

## Interface Tests

Each interface is tested at its edge: drive it in-process the way its users do (an HTTP
request, a CLI argument vector, a message), then assert the machine-readable output and
the status or exit code. The domain and the handlers are already covered without it, so
an interface test checks only translation: input parsing, the output model built from the
DTO, and the [error model](../errors/error-model.md) mapping, including the last-resort
handler. Build the interface through its composition root with fakes from
`tests/fakes/` unless the test is explicitly end to end.

How to drive each interface and what to assert are owned by its interface skill:
`ddd-interface-fastapi` and `ddd-interface-cli`, reference `testing.md`. The rules every
interface follows are in the [interface adapter contract](../interfaces/adapter-contract.md).

## Architecture Tests

Dependency rules are enforced mechanically, not by review. Two complementary tools apply.

### Import Contracts

The project declares its rules as [import-linter](https://import-linter.readthedocs.io/)
contracts. They extend the ones in the
[interface adapter contract](../interfaces/adapter-contract.md#enforcement). List every
context explicitly in `containers` and in the independence contract; add a context to
both when it is created.

```toml
# pyproject.toml
[tool.importlinter]
root_package = "app"
include_external_packages = true   # required to forbid third-party packages

[[tool.importlinter.contracts]]
name = "Context layers point inward"
type = "layers"
containers = ["app.bounded_context.ordering", "app.bounded_context.billing"]
layers = ["infrastructure", "application", "domain"]

[[tool.importlinter.contracts]]
name = "Contexts are independent"
type = "independence"
modules = ["app.bounded_context.ordering", "app.bounded_context.billing"]

[[tool.importlinter.contracts]]
name = "Domain performs no I/O"
type = "forbidden"
source_modules = ["app.bounded_context.*.domain", "app.shared_kernel.domain"]
forbidden_modules = ["sqlalchemy", "alembic", "httpx", "aio_pika"]

[[tool.importlinter.contracts]]
name = "Nothing below interfaces imports them"
type = "forbidden"
source_modules = ["app.bounded_context", "app.shared_kernel", "app.core", "app.exceptions"]
forbidden_modules = ["app.interfaces"]

[[tool.importlinter.contracts]]
name = "Inner layers import no delivery framework"
type = "forbidden"
source_modules = ["app.bounded_context", "app.shared_kernel.domain", "app.shared_kernel.application"]
forbidden_modules = ["fastapi", "starlette", "typer", "click"]

[[tool.importlinter.contracts]]
name = "Interfaces are independent"
type = "independence"
modules = ["app.interfaces.api", "app.interfaces.cli"]
```

- The `layers` contract gives both directional rules: the domain imports neither
  application nor infrastructure, and the application does not import infrastructure.
- Pydantic is not forbidden in the domain: value objects build on `FrozenObject`.
- Keep only the interface packages that exist in the independence contract; it needs at
  least two.
- A modular monolith adds module contracts, including `ignore_imports` for
  `modules.*.contracts`; see the [modular monolith topology](../deployment/modular-monolith-topology.md).
  Between microservices, contract tests replace import contracts.

Run `lint-imports` in CI. To fail the test suite as well, wrap it once:

```python
# tests/architecture/test_import_contracts.py
import subprocess


def test_import_contracts_hold() -> None:
    result = subprocess.run(["lint-imports"], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stdout
```

### Topology Check

`scripts/ddd-check.py` in this plugin checks the context-first `bounded_context/` layout
with no configuration and the standard library only:

```bash
python <plugin>/scripts/ddd-check.py <repo> [--changed-since <ref>]
```

It reports one `RULE path:line message` per violation: the domain importing a framework,
application, infrastructure, or interfaces; the application importing infrastructure or
interfaces; a context importing another context's internals; the shared kernel importing a
context; `core/` importing infrastructure or a delivery framework; and an infrastructure
class named `...Service` instead of `...Adapter`. It exits 0 when clean, 1 on violations,
and 3 when no `bounded_context/` package exists. Use `--changed-since` in reviews so
pre-existing debt is not attributed to the change. Module rules of a modular monolith rely
on the project's import contracts.

## Principles

1. Test behaviour through public methods, not implementation details.
2. Business rules are tested in the domain, with no test doubles.
3. Handlers are tested with fakes that implement ports and are injected through the
   constructor; nothing is patched.
4. Adapters are tested against the real technology they wrap.
5. Interfaces are tested only for translation, at their edge.
6. Architecture rules are executable: import contracts plus the topology check.
7. Assert typed errors and their stable codes, never messages.

## Review Checklist

- [ ] Each test sits at the level of what it protects; business rules are tested in the domain, not through handlers or interfaces.
- [ ] Test paths mirror the context-first layout (`tests/<level>/bounded_context/<context>/<layer>/`).
- [ ] Domain tests use no test doubles and no fixtures that touch I/O.
- [ ] Handler tests use fakes implementing the port Protocols, injected through the constructor; no `mock.patch` of module paths.
- [ ] Handler tests assert a DTO result and the Unit of Work outcome (committed on success, not committed on failure).
- [ ] Every `...Adapter` has an integration test against its real technology, including error translation.
- [ ] Test data is built through aggregate behaviour (builders), never by setting fields or inserting ORM rows.
- [ ] Interface tests assert the machine-readable output and status or exit code, following the interface skill.
- [ ] Import contracts cover inward layers, context independence, no delivery framework in inner layers, and nothing importing `interfaces`; `lint-imports` and `scripts/ddd-check.py` run in CI or review.
- [ ] Expected failures are asserted by error type and code, not by message text.
