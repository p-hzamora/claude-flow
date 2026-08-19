---
name: clean-ddd-hexagonal-python
description: Proactively apply when designing APIs, microservices, or scalable backend structure in Python. Triggers on DDD, Clean Architecture, Hexagonal, ports and adapters, entities, value objects, domain events, CQRS, event sourcing, repository pattern, use cases, onion architecture, outbox pattern, aggregate root, anti-corruption layer. Use when working with domain models, aggregates, repositories, or bounded contexts. Clean Architecture + DDD + Hexagonal patterns for Python backend services.
---

# Clean Architecture + DDD + Hexagonal (Python)

Backend architecture combining DDD tactical patterns, Clean Architecture dependency rules, and Hexagonal ports/adapters for maintainable, testable Python systems.

## When to Use (and When NOT to)

| Use When                                 | Skip When                                |
| ---------------------------------------- | ---------------------------------------- |
| Complex business domain with many rules  | Simple CRUD, few business rules          |
| Long-lived system (years of maintenance) | Prototype, MVP, throwaway code           |
| Team of 5+ developers                    | Solo developer or small team (1-2)       |
| Multiple entry points (API, CLI, events) | Single entry point, simple API           |
| Need to swap infrastructure (DB, broker) | Fixed infrastructure, unlikely to change |
| High test coverage required              | Quick scripts, internal tools            |

**Start simple. Evolve complexity only when needed.** Most systems don't need full CQRS or Event Sourcing.

## CRITICAL: Code Standards

### Documentation Requirements (MANDATORY)

**Every Python file must follow these documentation standards:**

1. **Module Docstrings** - Every `.py` file MUST start with a module docstring:

   ```python
   """Brief description of what this module contains."""
   ```

2. **Class Docstrings** - Every class MUST have a docstring with Attributes section:

   ```python
   class Order:
       """Brief description of the class.

       Attributes:
           id: Description of id attribute
           status: Description of status attribute
       """
   ```

3. **Method/Function Docstrings** - All public methods MUST have docstrings:

   ```python
   def create(cls, customer_id: str) -> "Order":
       """Create a new order for a customer.

       Args:
           customer_id: The unique identifier of the customer

       Returns:
           The newly created Order instance

       Raises:
           ValueError: If customer_id is invalid
       """
   ```

4. **Type Hints** - ALWAYS use type hints for all parameters and return values
5. **Google Style** - Use Google-style docstrings (Args, Returns, Raises, Attributes)

### Modern Python Syntax (Python 3.12+)

**CRITICAL:** This template requires Python 3.12+ features:

1. **Generic Syntax** - Use `[T]` NOT `Generic[T]` (PEP 695):

   ```python
   # ✅ CORRECT - Modern syntax
   class Entity[T]:
       pass

   class IHandler[TCommand, TResult](Protocol):
       async def execute(self, command: TCommand) -> TResult: ...

   # ❌ WRONG - Old syntax (DO NOT USE)
   from typing import Generic, TypeVar
   T = TypeVar("T")
   class Entity(Generic[T]):
       pass
   ```

2. **Type Unions** - Use `|` NOT `Union` or `Optional`:

   ```python
   # ✅ CORRECT
   def find(id: str) -> Order | None:
       pass

   # ❌ WRONG
   from typing import Union, Optional
   def find(id: str) -> Optional[Order]:
       pass
   ```

3. **Value Objects** - Use Pydantic BaseModel, NOT dataclass with frozen:

   ```python
   # ✅ CORRECT - Pydantic with frozen config
   from pydantic import BaseModel, ConfigDict

   class ValueObject(BaseModel):
       model_config = ConfigDict(frozen=True, from_attributes=True)

   class Money(ValueObject):
       amount: float
       currency: str

   # ❌ WRONG - dataclass (DO NOT USE for Value Objects)
   from dataclasses import dataclass

   @dataclass(frozen=True)
   class Money:
       amount: float
       currency: str
   ```

4. **Entities** - Use dataclass with `slots=True, kw_only=True`:

   ```python
   # ✅ CORRECT
   from dataclasses import dataclass

   @dataclass(slots=True, kw_only=True)
   class Order:
       id: UUID
       status: OrderStatus
   ```

## CRITICAL: The Dependency Rule

Dependencies point **inward only**. Outer layers depend on inner layers, never the reverse.

```
Interfaces → Infrastructure → Application → Domain
 (routers)    (adapters)     (handlers)    (core)
```

**Violations to catch:**

- Domain importing database/HTTP libraries
- Routers calling repositories directly (bypassing handlers)
- Entities depending on application services

**Design validation:** "Create your application to work without either a UI or a database" — Alistair Cockburn. If you can run your domain logic from tests with no infrastructure, your boundaries are correct.

## Quick Decision Trees

### "Where does this code go?"

```
Where does it go?
├─ Pure business logic, no I/O           → domain/
├─ Orchestrates domain + has side effects → application/
├─ Talks to external systems              → infrastructure/
├─ Defines HOW to interact (interface)    → port (domain or application)
└─ Implements a port                      → adapter (infrastructure)
```

### "Is this an Entity or Value Object?"

```
Entity or Value Object?
├─ Has unique identity that persists → Entity
├─ Defined only by its attributes    → Value Object
├─ "Is this THE same thing?"         → Entity (identity comparison)
└─ "Does this have the same value?"  → Value Object (structural equality)
```

### "Should this be its own Aggregate?"

```
Aggregate boundaries?
├─ Must be consistent together in a transaction → Same aggregate
├─ Can be eventually consistent                 → Separate aggregates
├─ Referenced by ID only                        → Separate aggregates
└─ >10 entities in aggregate                    → Split it
```

**Rule:** One aggregate per transaction. Cross-aggregate consistency via domain events (eventual consistency).

## Directory Structure

```
app/
├── domain/                    # Core business logic (NO external dependencies)
│   ├── entities/             # Domain Entities (dataclasses)
│   ├── value_objects/        # Value Objects (FrozenObject/Pydantic)
│   ├── repository/           # Repository Protocols (DRIVEN PORTS)
│   └── services/             # Domain Services (stateless logic)
│
├── application/              # Use cases / Application layer
│   ├── handlers/             # CQRS Handlers
│   │   ├── commands/        # Command Handlers (write operations)
│   │   └── queries/         # Query Handlers (read operations)
│   ├── dtos/                # Data Transfer Objects (FrozenObject)
│   ├── mappers/             # {Entity}Assembler (Entity/VO → DTO)
│   ├── ports/               # Application Ports (Read Repositories)
│   └── services/            # Application Services
│
├── infrastructure/          # Adapters (external concerns)
│   ├── db/                  # Database Implementation
│   │   ├── models/         # SQLAlchemy ORM Models
│   │   ├── repository/     # Repository Implementations (Write)
│   │   ├── mappers/        # {Entity}Mapper (ORM↔Entity)
│   │   │   └── read_mappers/  # {Entity}ReadMapper (ORM→DTO), split from write-side Mapper
│   │   └── utils/          # DB Utilities
│   ├── read_model/         # CQRS Read Side (Query Repositories)
│   └── services/           # Infrastructure Services
│
├── interfaces/             # Interface layer (outermost)
│   └── api/
│       └── v1/
│           ├── routers/       # FastAPI Routers
│           ├── dependencies/  # DI Factory Functions
│           ├── schemas/       # API Request/Response Schemas
│           ├── mappers/       # {Entity}ApiMapper (DTO→Response) — exception, not default
│           └── middleware/    # Middleware
│
├── utils/                 # Utility classes
│   └── __init__.py        # FrozenObject utility (REQUIRED)
│
└── core/                  # Core configuration
```

## CQRS Pattern (Commands vs Queries)

### Commands (Write Operations)

**Commands** change state and use the **write model**:

```python
# application/handlers/commands/create_order_cmd.py
from app.utils import FrozenObject

class CreateOrderCommand(FrozenObject):
    customer_id: str
    items: list[dict]

class CreateOrderHandler(IHandler[CreateOrderCommand, OrderDto]):
    def __init__(self, uow: IOrderUoW) -> None:
        self._uow = uow

    async def handle(self, action: CreateOrderCommand) -> OrderDto:
        async with self._uow as uow:
            # Work with Entities
            order = Order.create(**action.model_dump())
            await uow.orders.save(order)
            await uow.commit()  # Explicit commit

        # Return DTO via Assembler
        return OrderAssembler.to_dto(order)
```

**Key characteristics:**

- Use **Unit of Work** for transactions
- Work with **Entities** (domain models)
- Return **DTOs** via Assemblers
- Implement `IHandler[TCommand, TResult]`

### Queries (Read Operations)

**Queries** retrieve data and use the **read model**:

```python
# application/handlers/queries/get_orders.py
class GetOrdersQuery(PaginationParams):
    status: str | None = None

class GetOrdersHandler:
    def __init__(self, repository: IOrderReadRepository) -> None:
        self._repository = repository

    async def handle(self, query: GetOrdersQuery) -> PaginationDto[OrderDto]:
        return await self._repository.get_orders(query)
```

**Key characteristics:**

- Use **Read Repositories** directly (no UoW)
- Work with **DTOs** directly
- May or may not implement `IHandler`
- Optimized for queries (denormalized data)

### DTO vs Value Object at the Handler Boundary

**A handler (command or query) never returns a Value Object as its response. It maps
VO → DTO first, via an Assembler.** A VO is an internal domain building block, not a
contract; a DTO is a contract the application layer controls independently of the
domain model. Return a VO and every external consumer is now silently coupled to the
domain's internal shape — a rename, a new invariant, or a refactor to a different value
representation breaks or silently reshapes every response, and that breakage tends to
surface during a migration, not during code review.

- **Command handlers:** return minimal output (ID, ack, or a DTO) — never work with
  Entities/VOs *just to serialize them out*. Returning a VO here is the stronger
  violation: a write-side domain artifact doing a read-side serialization job.
- **Query handlers:** the read model is independent of the domain model by CQRS's own
  premise — optimized for the client, not for enforcing invariants. Returning a VO
  leaks domain invariants/behavior the read model doesn't need. Weaker violation than
  the command case, but still a leak.
- **Narrow exception:** if the caller is strictly in-process (another in-process module,
  never serialized across an API/process boundary), reusing the VO isn't a DTO problem —
  there's no external contract being formed. The exception evaporates the moment the
  return value gets serialized into an API response.

See `references/CQRS-IMPLEMENTATION.md` for the worked Command/Query handler examples
with the VO→DTO mapping called out inline.

## DDD Building Blocks

| Pattern            | Purpose                 | Layer         | Key Rule                                 |
| ------------------ | ----------------------- | ------------- | ---------------------------------------- |
| **Entity**         | Identity + behavior     | Domain        | Equality by ID, use dataclass            |
| **Value Object**   | Immutable data          | Domain        | Equality by value, use FrozenObject      |
| **Aggregate**      | Consistency boundary    | Domain        | Only root is referenced externally       |
| **Domain Event**   | Record of change        | Domain        | Past tense naming (`OrderPlaced`)        |
| **Repository**     | Persistence abstraction | Domain (port) | Per aggregate, use Protocol              |
| **Domain Service** | Stateless logic         | Domain        | When logic doesn't fit an entity         |
| **Handler**        | CQRS operations         | Application   | Commands use UoW, Queries use Read Repos |

## Anti-Patterns (CRITICAL)

| Anti-Pattern               | Problem                                   | Fix                                  |
| -------------------------- | ----------------------------------------- | ------------------------------------ |
| **Anemic Domain Model**    | Entities are data bags, logic in services | Move behavior INTO entities          |
| **Repository per Entity**  | Breaks aggregate boundaries               | One repository per AGGREGATE         |
| **Leaking Infrastructure** | Domain imports DB/HTTP libs               | Domain has ZERO external deps        |
| **God Aggregate**          | Too many entities, slow transactions      | Split into smaller aggregates        |
| **Skipping Ports**         | Controllers → Repositories directly       | Always go through application layer  |
| **CRUD Thinking**          | Modeling data, not behavior               | Model business operations            |
| **Premature CQRS**         | Adding complexity before needed           | Start with simple read/write, evolve |
| **Cross-Aggregate TX**     | Multiple aggregates in one transaction    | Use domain events for consistency    |
| **VO as Handler Response** | Handler returns a Value Object, not a DTO | Map VO → DTO via Assembler (see below) |

## Implementation Order

1. **Discover the Domain** — Event Storming, conversations with domain experts
2. **Model the Domain** — Entities, value objects, aggregates (no infra)
3. **Define Ports** — Repository interfaces, external service interfaces
4. **Implement Use Cases** — Application services coordinating domain
5. **Add Adapters last** — HTTP, database, messaging implementations

**DDD is collaborative.** Modeling sessions with domain experts are as important as the code patterns.

## Template-Specific Patterns

### FrozenObject Utility (REQUIRED)

**Create this base class** to avoid duplicating `model_config` across all immutable objects:

```python
# app/utils/__init__.py
from pydantic import BaseModel, ConfigDict


class FrozenObject(BaseModel):
    """Base class for all immutable objects using Pydantic.

    Inherit from this for: Value Objects, DTOs, Commands, Queries, API Schemas.
    """
    model_config = ConfigDict(frozen=True, from_attributes=True)

    def __str__(self) -> str:
        if hasattr(self, "value"):
            return str(self.value)
        return super().__str__()
```

**Usage:**

```python
# Value Object
class Money(FrozenObject):
    amount: float
    currency: str

# Command
class CreateOrderCommand(FrozenObject):
    customer_id: str
    items: list[dict]

# DTO
class OrderDto(FrozenObject):
    id: str
    status: str
```

### Type System Decisions

| Type                                       | Use Case                                        | Example                                    |
| ------------------------------------------ | ----------------------------------------------- | ------------------------------------------ |
| **FrozenObject** (Pydantic)                | Value Objects, DTOs, Commands, Queries, Schemas | `Money`, `OrderDto`, `CreateOrderCommand`  |
| **Dataclass** (`slots=True, kw_only=True`) | Domain Entities (rich behavior)                 | `Order`, `Customer`, `Product`             |
| **Protocol**                               | Port definitions (interfaces)                   | `IOrderRepository`, `IOrderReadRepository` |

### Handler Organization

**Commands and Queries** are organized separately in `application/handlers/`:

```
application/handlers/
├── commands/
│   ├── __init__.py
│   ├── create_order_cmd.py      # Both Command and Handler in same file
│   └── cancel_order_cmd.py
└── queries/
    ├── __init__.py
    ├── get_order.py
    └── get_orders.py
```

**File naming:**

- Commands: `{verb}_{entity}_cmd.py`
- Queries: `{verb}_{entity}.py` or `{verb}_{entity}_query.py`

### Dependency Injection Pattern

**Factory functions** in `interfaces/api/v1/dependencies/{entity}_dpd.py`:

```python
from typing import Annotated
from fastapi import Depends

# Factory functions
def get_order_uow(session: GetAsyncSessionDpd) -> IOrderUoW:
    return SQLAlchemyOrderUoW(session)

def create_order_instance(uow: OrderUoWDpd) -> CreateOrderHandler:
    return CreateOrderHandler(uow)

# Type aliases for clean DI — one per line, wrapped in fmt:off/on so ruff
# does NOT line-wrap them. The `Dpd` suffix is MANDATORY (identifies a dependency,
# prevents name clashes).
# fmt: off
GetAsyncSessionDpd    = Annotated[AsyncSession,     Depends(get_async_session)]
OrderUoWDpd           = Annotated[IOrderUoW,        Depends(get_order_uow)]
CreateOrderHandlerDpd = Annotated[CreateOrderHandler, Depends(create_order_instance)]
# fmt: on
```

**Router usage — NEVER use the `handler = ...  # type: ignore[assignment]` sentinel.**
Inject like `Authorize`: bare `handler: CreateOrderHandlerDpd`, no default. Because a
non-default param cannot follow a defaulted one, place the `Dpd` param BEFORE any
optional/defaulted param (e.g. an `X-Request-ID` header that defaults to `None`):

```python
@router.post("/", response_model=CreateOrderResponse)
async def create_order(
    request: CreateOrderRequest,
    handler: CreateOrderHandlerDpd,          # ← bare Dpd, no `= ...` sentinel
    x_request_id: Annotated[str | None, Header(alias="X-Request-ID")] = None,
) -> CreateOrderResponse:
    cmd = CreateOrderCommand(**request.model_dump())
    return await handler.handle(cmd)
```

### Request Parameter Grouping

Group related endpoint inputs into a single Pydantic model instead of many loose params:

```python
# Query params → Annotated[Model, Query()]  (flattens to individual query params)
async def list_orders(params: Annotated[ListOrdersParams, Query()], handler: ...): ...

# JSON body → a plain request model
async def parse_rule(request: ParseRuleRequest, handler: ...): ...
```

**Exception — multipart uploads with a file.** Do NOT wrap multipart form fields in a
`Annotated[Model, Form()]` when the endpoint also has a separate `file: UploadFile`.
FastAPI then NESTS the model as a single sub-field (`body -> form`) instead of
flattening it, which breaks flat multipart clients (`422 "form: Field required"`).
For file-upload endpoints, keep flat `Annotated[T, Form(...)]` params.

### Exception Discipline

EVERY raised exception MUST inherit from `AppException` (or a subtype: `CoreException` /
`ApplicationException` / `DomainException` / `InfrastructureException` /
`InterfaceException`). Each custom exception declares `__error_code__`
(an `ErrorCodeEnum` member) and `__http_error__`. Never raise bare
`ValueError`/`RuntimeError`/`HTTPException` from domain/application/infrastructure code.

```python
class MissingCommandError(ApplicationException):
    __error_code__ = ErrorCodeEnum.CMN_012_MISSING_COMMAND
    __http_error__ = 422
    def __init__(self, command_name: str) -> None:
        super().__init__(f"{command_name} is required", metadata={"command": command_name})
```

**Two — and only two — allowed raw raises:**
1. Pydantic `field_validator` bodies MUST raise `ValueError` (framework contract). If a
   domain VO must satisfy this, give it a dual base: `class XError(DomainException, ValueError)`.
2. Pre-bootstrap config (`core/env.py`) runs BEFORE the exception handlers are registered;
   a raw crash there is intentional.

**Framework error → custom exception at the edge.** Translate third-party errors (e.g.
slowapi `RateLimitExceeded`) inside the central exception registry
(`interfaces/api/v1/exceptions/`), NOT in middleware. Middleware owns only its mechanism
(the limiter + `SlowAPIMiddleware`); the `RateLimitExceeded → 429` mapping lives in
`EXCEPTION_REGISTRY` so every response flows through the one RFC9457 mapper.

### Four-Mapper Architecture

Every mapper method is named `to_[destination]` — never `from_x`. The name always
tells you what's being produced, not what was consumed.

> ⚠️ **Three of these four are classes you actually write. The fourth,
> `{Entity}ApiMapper`, is not — it should be weird to even find one in the codebase.**
> Pydantic already does DTO → Response conversion natively: `ResponseSchema.model_validate(dto)`,
> called inline in the router, IS the mapping. That's the default for every single
> DTO → Response case, including when the Response's fields are a subset of (or
> trivially named like) the DTO's — `model_validate` handles that on its own, no code
> needed. Do not scaffold an `{Entity}ApiMapper` "for consistency" with the other three
> tiers. Write one only when the mapping needs logic `model_validate` genuinely cannot
> do — nested-object flattening, a rename it can't infer, a computed field — and even
> then, treat its existence as a sign to double check nothing simpler covers it.

| Mapper Type           | Direction     | Location                        | Purpose                                 |
| --------------------- | ------------- | -------------------------------- | ---------------------------------------- |
| **{Entity}Mapper**    | ORM ↔ Entity  | `infrastructure/db/mappers/`     | Persistence (write side): `to_orm`, `to_entity` |
| **{Entity}ReadMapper**| ORM → DTO     | `infrastructure/db/mappers/read_mappers/` | Read queries, skips Entity entirely: `to_dto` |
| **{Entity}Assembler** | Entity/VO → DTO | `application/mappers/`         | Command responses: `to_dto`             |
| **{Entity}ApiMapper** | DTO → Response | `interfaces/api/v1/mappers/`    | **Exception, not a peer tier** — default is `model_validate` inline, see warning above |

**Response schemas are sourced from a DTO only, never straight from an Entity or Value
Object.** Even an endpoint with no Command/Query handler behind it (e.g. an identity/auth
"whoami" route) must still produce a DTO first (via an Assembler) before an
`{Entity}ApiMapper`/`model_validate` turns it into a Response — mapping a VO or Entity
directly into an interface Response skips the one seam (`Assembler`) that keeps a domain
refactor from silently reshaping the API contract.

### Regional Imports

Organize imports in routers using regions:

```python
# region Queries
from app.application.handlers.queries import GetOrderQuery, GetOrdersQuery
# endregion

# region Commands
from app.application.handlers.commands import CreateOrderCommand, CancelOrderCommand
# endregion

# region Dependencies
from ..dependencies import CreateOrderHandlerDpd, GetOrderHandlerDpd
# endregion

# region Schemas
from ..schemas.order_schema import CreateOrderRequest, OrderResponse
# endregion
```

### Type Safety

- Use **type hints** everywhere (Python 3.10+)
- Use **Protocol** for port definitions
- Use **Annotated** for dependency injection
- Use generics (`[T]`) for type-safe collections

## Reference Documentation

| File                                                                   | Purpose                                              |
| ---------------------------------------------------------------------- | ---------------------------------------------------- |
| [references/LAYERS.md](references/LAYERS.md)                           | Complete layer specifications                        |
| [references/DDD-STRATEGIC.md](references/DDD-STRATEGIC.md)             | Bounded contexts, context mapping                    |
| [references/DDD-TACTICAL.md](references/DDD-TACTICAL.md)               | Entities, value objects, aggregates (Python)         |
| [references/HEXAGONAL.md](references/HEXAGONAL.md)                     | Ports, adapters, naming                              |
| [references/CQRS-EVENTS.md](references/CQRS-EVENTS.md)                 | Command/query separation, events                     |
| [references/CQRS-IMPLEMENTATION.md](references/CQRS-IMPLEMENTATION.md) | Template-specific CQRS implementation reference      |
| [references/ERROR_HANDLER.md](references/ERROR_HANDLER.md)             | Error handling workflow and exception best practices |
| [references/TESTING.md](references/TESTING.md)                         | Unit, integration, architecture tests                |
| [references/CHEATSHEET.md](references/CHEATSHEET.md)                   | Quick decision guide                                 |

## Sources

### Primary Sources

- [The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) — Robert C. Martin (2012)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) — Alistair Cockburn (2005)
- [Domain-Driven Design: The Blue Book](https://www.domainlanguage.com/ddd/blue-book/) — Eric Evans (2003)
- [Implementing Domain-Driven Design](https://openlibrary.org/works/OL17392277W) — Vaughn Vernon (2013)

### Pattern References

- [CQRS](https://martinfowler.com/bliki/CQRS.html) — Martin Fowler
- [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html) — Martin Fowler
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html) — Martin Fowler (PoEAA)
- [Unit of Work](https://martinfowler.com/eaaCatalog/unitOfWork.html) — Martin Fowler (PoEAA)
- [Bounded Context](https://martinfowler.com/bliki/BoundedContext.html) — Martin Fowler
- [Transactional Outbox](https://microservices.io/patterns/data/transactional-outbox.html) — microservices.io
- [Effective Aggregate Design](https://www.dddcommunity.org/library/vernon_2011/) — Vaughn Vernon

### Implementation Guides

- [Microsoft: DDD + CQRS Microservices](https://learn.microsoft.com/en-us/dotnet/architecture/microservices/microservice-ddd-cqrs-patterns/)
- [Domain Events](https://udidahan.com/2009/06/14/domain-events-salvation/) — Udi Dahan
