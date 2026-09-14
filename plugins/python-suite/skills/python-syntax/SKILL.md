---
name: python-syntax
description: Proactively apply when writing or reviewing Python code. Triggers on type hints, naming conventions, imports, function signatures, class definitions, variable declarations, docstrings, f-strings, pattern matching, generics, protocols. Enforces modern Python 3.13+ syntax, hard type hints, PEP naming conventions, and idiomatic patterns. Use as a reference for code style, documentation standards, and good practices.
---

# Python Syntax & Conventions (Python 3.13+)

Comprehensive guide for writing idiomatic, strongly-typed, modern Python code. All code MUST follow these conventions. This skill serves as the single source of truth for syntax decisions across the project.

## Target Version

- **Minimum Python version:** 3.13
- **Type checking:** strict mode (mypy or pyright)
- **Linter/formatter:** ruff

---

## 1. Naming Conventions

### Variables, Functions, Methods, Parameters

Use `snake_case`. Names should be descriptive and unambiguous.

```python
# ✅ CORRECT
user_name: str = "Pablo"
total_amount: Decimal = Decimal("100.50")
is_active: bool = True

def calculate_total_price(items: list[Item], discount: Decimal) -> Decimal:
    ...

async def fetch_user_by_email(email: str) -> User | None:
    ...

# ❌ WRONG
userName: str = "Pablo"          # camelCase
TotalAmount = Decimal("100.50")  # PascalCase
x: int = 42                      # non-descriptive (except in math/loops)
def calcPrice(i, d): ...         # camelCase, abbreviations, no types
```

### Classes

Use `PascalCase`. No suffixes like `Class` or `Obj`.

```python
# ✅ CORRECT
class OrderRepository:
    ...

class UserCreatedEvent:
    ...

class PaymentGateway(Protocol):
    ...

# ❌ WRONG
class order_repository: ...   # snake_case
class orderRepository: ...    # camelCase
class OrderRepositoryClass: ... # redundant suffix
```

### Constants

Use `UPPER_SNAKE_CASE`. Define at module level.

```python
# ✅ CORRECT
MAX_RETRY_COUNT: int = 3
DEFAULT_TIMEOUT_SECONDS: float = 30.0
DATABASE_URL: str = "postgresql+asyncpg://localhost/db"
API_VERSION: str = "v1"

# ❌ WRONG
maxRetryCount = 3         # camelCase, no type hint
default_timeout = 30.0    # looks like a variable
```

### Private and Protected Members

Use a single leading underscore `_` for internal/protected. Avoid double underscores `__` (name mangling) unless strictly necessary.

```python
# ✅ CORRECT
class Order:
    def __init__(self) -> None:
        self._status: OrderStatus = OrderStatus.PENDING
        self._events: list[DomainEvent] = []

    def _validate_transition(self, new_status: OrderStatus) -> None:
        ...

# ❌ WRONG - avoid name mangling unless truly needed
class Order:
    def __init__(self) -> None:
        self.__status = OrderStatus.PENDING  # name mangling, avoid
```

### Module and Package Names

Use `snake_case`, short, lowercase. No hyphens.

```
# ✅ CORRECT
user_repository.py
order_service.py
payment_gateway/

# ❌ WRONG
UserRepository.py      # PascalCase
order-service.py       # hyphens
paymentGateway/        # camelCase
```

### Enum Members

Use `UPPER_SNAKE_CASE` for enum values.

```python
# ✅ CORRECT
from enum import StrEnum

class OrderStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    CANCELLED = "cancelled"

# ❌ WRONG
class OrderStatus(StrEnum):
    pending = "pending"      # lowercase
    Confirmed = "confirmed"  # PascalCase
```

---

## 2. Type Hints (Hard Typing — Mandatory)

**Every** function parameter, return value, and variable declaration MUST have explicit type hints. No exceptions.

### Built-in Generic Types (PEP 585 — No `typing` imports)

```python
# ✅ CORRECT — use built-in generics directly
items: list[str] = []
user_map: dict[str, User] = {}
unique_ids: set[int] = set()
coordinates: tuple[float, float] = (0.0, 0.0)
mixed: tuple[str, int, bool] = ("a", 1, True)
variable_length: tuple[int, ...] = (1, 2, 3)
frozen: frozenset[str] = frozenset({"a", "b"})

# ❌ WRONG — never import these from typing
from typing import List, Dict, Set, Tuple, FrozenSet  # BANNED
items: List[str] = []
```

### Union Types (PEP 604 — Use `|` operator)

```python
# ✅ CORRECT
def find_user(user_id: str) -> User | None:
    ...

def parse_value(raw: str | int | float) -> Decimal:
    ...

error: str | Exception | None = None

# ❌ WRONG
from typing import Union, Optional  # BANNED
def find_user(user_id: str) -> Optional[User]: ...
def parse_value(raw: Union[str, int, float]) -> Decimal: ...
```

### Generic Classes (PEP 695 — New `[T]` syntax)

```python
# ✅ CORRECT — Python 3.12+ generic syntax
class Repository[T]:
    async def find_by_id(self, entity_id: str) -> T | None:
        ...

    async def save(self, entity: T) -> None:
        ...

class Result[TSuccess, TError]:
    def __init__(self, value: TSuccess | None = None, error: TError | None = None) -> None:
        self._value = value
        self._error = error

# ❌ WRONG — old TypeVar + Generic syntax
from typing import TypeVar, Generic  # BANNED
T = TypeVar("T")
class Repository(Generic[T]): ...
```

### Type Aliases (PEP 695 — `type` statement)

```python
# ✅ CORRECT — Python 3.12+ type alias syntax
type UserId = str
type Email = str
type JsonDict = dict[str, Any]
type EventHandler[T] = Callable[[T], Awaitable[None]]
type Result[T] = T | Error

# ❌ WRONG — old TypeAlias syntax
from typing import TypeAlias  # BANNED
UserId: TypeAlias = str
```

### Callable Types

```python
# ✅ CORRECT
from collections.abc import Callable, Awaitable

type SyncHandler = Callable[[Request], Response]
type AsyncHandler = Callable[[Request], Awaitable[Response]]
type Middleware[T] = Callable[[T], Awaitable[T]]

def register_handler(handler: Callable[[str], None]) -> None:
    ...

# ❌ WRONG
from typing import Callable  # BANNED — use collections.abc
```

### Protocol for Structural Typing

```python
# ✅ CORRECT
from typing import Protocol, runtime_checkable

@runtime_checkable
class Serializable(Protocol):
    def to_dict(self) -> dict[str, Any]: ...

class HasId(Protocol):
    @property
    def id(self) -> str: ...

class CommandHandler[TCommand, TResult](Protocol):
    async def execute(self, command: TCommand) -> TResult: ...

# Use protocols instead of ABCs when possible
def serialize(obj: Serializable) -> str:
    return json.dumps(obj.to_dict())
```

### Self Type

```python
# ✅ CORRECT — Python 3.11+
from typing import Self

class Builder:
    def with_name(self, name: str) -> Self:
        self._name = name
        return self

    @classmethod
    def create(cls) -> Self:
        return cls()
```

### TypeGuard and TypeIs

```python
# ✅ CORRECT — Python 3.13+ TypeIs (PEP 742)
from typing import TypeIs

def is_string_list(value: list[object]) -> TypeIs[list[str]]:
    return all(isinstance(item, str) for item in value)

# TypeGuard for narrower cases
from typing import TypeGuard

def is_not_none[T](value: T | None) -> TypeGuard[T]:
    return value is not None
```

### Never and NoReturn

```python
# ✅ CORRECT
from typing import Never, NoReturn

def unreachable(value: Never) -> Never:
    raise AssertionError(f"Unexpected value: {value}")

def fatal_error(message: str) -> NoReturn:
    raise SystemExit(message)
```

---

## 3. Function and Method Signatures

### Always Annotate Everything

```python
# ✅ CORRECT — fully typed
def create_order(
    customer_id: str,
    items: list[OrderItem],
    *,
    discount: Decimal = Decimal("0"),
    notes: str | None = None,
) -> Order:
    ...

async def process_payment(
    order: Order,
    gateway: PaymentGateway,
) -> PaymentResult:
    ...

# ❌ WRONG — missing annotations
def create_order(customer_id, items, discount=0, notes=None):
    ...
```

### Use Keyword-Only Arguments (`*`)

Force clarity for functions with multiple parameters or optional arguments.

```python
# ✅ CORRECT
def send_notification(
    *,
    recipient: str,
    subject: str,
    body: str,
    priority: Priority = Priority.NORMAL,
) -> None:
    ...

# Called as:
send_notification(recipient="user@example.com", subject="Hello", body="World")

# ❌ WRONG — positional arguments create ambiguity
def send_notification(recipient, subject, body, priority="normal"):
    ...
```

### Return `None` Explicitly

```python
# ✅ CORRECT
def log_event(event: DomainEvent) -> None:
    logger.info("Event: %s", event)

# ❌ WRONG — implicit None return
def log_event(event):
    logger.info("Event: %s", event)
```

---

## 4. Classes and Data Structures

### Dataclasses with `slots=True, kw_only=True`

```python
# ✅ CORRECT
from dataclasses import dataclass, field
from uuid import UUID, uuid4

@dataclass(slots=True, kw_only=True)
class Order:
    id: UUID = field(default_factory=uuid4)
    customer_id: str
    status: OrderStatus = OrderStatus.PENDING
    items: list[OrderItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

# ❌ WRONG — missing slots and kw_only
@dataclass
class Order:
    id: UUID
    customer_id: str
```

### Enums — Use `StrEnum` or `IntEnum`

```python
# ✅ CORRECT — Python 3.11+ StrEnum
from enum import StrEnum, IntEnum, auto

class OrderStatus(StrEnum):
    PENDING = auto()
    CONFIRMED = auto()
    SHIPPED = auto()

class HttpStatus(IntEnum):
    OK = 200
    NOT_FOUND = 404
    INTERNAL_ERROR = 500

# ❌ WRONG — plain Enum with string values
from enum import Enum
class OrderStatus(Enum):
    PENDING = "pending"
```

### NamedTuple (Immutable Records)

```python
# ✅ CORRECT — class syntax
from typing import NamedTuple

class Coordinate(NamedTuple):
    latitude: float
    longitude: float
    altitude: float = 0.0

# ❌ WRONG — functional syntax (harder to type-check)
Coordinate = namedtuple("Coordinate", ["latitude", "longitude"])
```

---

## 5. Import Conventions

### Import Order (enforced by ruff/isort)

```python
# 1. Standard library
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import UUID

# 2. Third-party
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

# 3. Local application
from app.domain.entities.order import Order
from app.domain.events.order_events import OrderCreatedEvent
from app.application.handlers.create_order import CreateOrderHandler
```

### Import Style

```python
# ✅ CORRECT — import specific names
from collections.abc import Callable, Awaitable
from dataclasses import dataclass, field

# ✅ CORRECT — import module for namespacing when names clash
import logging
import json


# ❌ WRONG — Wildcard imports are discouraged. When required, include an inline commnet jutifying their use
from typing import *
from os.path import *

# ✅ CORRECT Using * and adding an asterisk
from custom_implementation import * # I need to add all of them since I'm using this file as a router to other module.

# ❌ WRONG — importing deprecated typing generics
from typing import List, Dict, Optional, Union, Tuple
```

### Banned Imports

These imports are **never** allowed:

```python
# ❌ BANNED — replaced by built-in generics (PEP 585)
from typing import List, Dict, Set, Tuple, FrozenSet, Type

# ❌ BANNED — replaced by | operator (PEP 604)
from typing import Union, Optional

# ❌ BANNED — replaced by [T] syntax (PEP 695)
from typing import TypeVar, Generic

# ❌ BANNED — replaced by type statement (PEP 695)
from typing import TypeAlias

# ❌ BANNED — replaced by collections.abc
from typing import Callable, Awaitable, Iterator, Iterable, Sequence, Mapping

# ✅ USE INSTEAD
from collections.abc import Callable, Awaitable, Iterator, Iterable, Sequence, Mapping
```

---

## 6. String Formatting

### Always Use f-strings

```python
# ✅ CORRECT
message: str = f"Order {order_id} created for {customer_name}"
log_entry: str = f"[{timestamp:%Y-%m-%d %H:%M}] {event.type}: {event.payload}"
url: str = f"/api/v1/orders/{order_id}/items/{item_id}"

# ✅ CORRECT — multiline f-string
query: str = (
    f"SELECT * FROM orders "
    f"WHERE customer_id = '{customer_id}' "
    f"AND status = '{status.value}'"
)

# ❌ WRONG — old formatting styles
message = "Order %s created for %s" % (order_id, customer_name)
message = "Order {} created for {}".format(order_id, customer_name)
message = "Order " + str(order_id) + " created for " + customer_name
```

### Logging — Use `%` style (lazy evaluation)

```python
# ✅ CORRECT — logger uses lazy % formatting
logger.info("Processing order %s for customer %s", order_id, customer_id)
logger.error("Failed to process order %s: %s", order_id, error)
logger.debug("Query returned %d results in %.2fms", count, elapsed_ms)

# ❌ WRONG — f-string in logging (evaluated even if level is disabled)
logger.info(f"Processing order {order_id} for customer {customer_id}")
```

---

## 7. Pattern Matching (PEP 634 — `match/case`)

```python
# ✅ CORRECT — structural pattern matching
def handle_command(command: Command) -> Result:
    match command:
        case CreateOrder(customer_id=cid, items=items):
            return _create_order(cid, items)
        case CancelOrder(order_id=oid, reason=reason):
            return _cancel_order(oid, reason)
        case UpdateOrder(order_id=oid, changes=changes):
            return _update_order(oid, changes)
        case _:
            raise ValueError(f"Unknown command: {type(command).__name__}")

# ✅ CORRECT — matching on types and guards
def process_event(event: DomainEvent) -> None:
    match event:
        case OrderCreated() if event.is_priority:
            notify_warehouse(event)
        case OrderCreated():
            log_creation(event)
        case PaymentReceived(amount=amount) if amount > Decimal("1000"):
            flag_for_review(event)
        case _:
            pass

# ✅ CORRECT — matching on values
def http_status_message(status: int) -> str:
    match status:
        case 200:
            return "OK"
        case 404:
            return "Not Found"
        case 500:
            return "Internal Server Error"
        case _:
            return f"Status {status}"
```

---

## 8. Error Handling

### Typed Exceptions with Exception Groups (Python 3.11+)

```python
# ✅ CORRECT — custom exceptions with context
class DomainError(Exception):
    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.code: str | None = code

class OrderNotFoundError(DomainError):
    def __init__(self, order_id: str) -> None:
        super().__init__(f"Order not found: {order_id}", code="ORDER_NOT_FOUND")
        self.order_id: str = order_id

class ValidationError(DomainError):
    def __init__(self, field: str, message: str) -> None:
        super().__init__(f"Validation error on '{field}': {message}", code="VALIDATION_ERROR")
        self.field: str = field
```

### Exception Groups (Python 3.11+)

```python
# ✅ CORRECT — exception groups for multiple errors
def validate_order(order: Order) -> None:
    errors: list[ValidationError] = []

    if not order.items:
        errors.append(ValidationError("items", "Order must have at least one item"))
    if order.total <= Decimal("0"):
        errors.append(ValidationError("total", "Total must be positive"))

    if errors:
        raise ExceptionGroup("Order validation failed", errors)

# Handle with except*
try:
    validate_order(order)
except* ValidationError as eg:
    for error in eg.exceptions:
        logger.warning("Validation: %s", error)
```

---

## 9. Comprehensions and Generators

```python
# ✅ CORRECT — list comprehension (when result fits in memory)
active_users: list[User] = [user for user in users if user.is_active]

# ✅ CORRECT — dict comprehension
user_by_id: dict[str, User] = {user.id: user for user in users}

# ✅ CORRECT — set comprehension
unique_emails: set[str] = {user.email.lower() for user in users}

# ✅ CORRECT — generator expression (lazy, memory efficient)
total: Decimal = sum(item.price for item in order.items)

# ✅ CORRECT — generator function with type hints
def paginate[T](items: Sequence[T], *, page_size: int = 20) -> Iterator[Sequence[T]]:
    for i in range(0, len(items), page_size):
        yield items[i : i + page_size]
```

---

## 10. Async Patterns

### Async Function Signatures

```python
# ✅ CORRECT
async def get_order(order_id: str) -> Order:
    ...

async def list_orders(
    *,
    customer_id: str,
    status: OrderStatus | None = None,
    limit: int = 50,
) -> list[Order]:
    ...
```

### Async Context Managers

```python
# ✅ CORRECT
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    session: AsyncSession = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
```

### Async Iterators

```python
# ✅ CORRECT
from collections.abc import AsyncIterator

async def stream_events(topic: str) -> AsyncIterator[DomainEvent]:
    async with consumer(topic) as stream:
        async for message in stream:
            yield deserialize_event(message)
```

---

## 11. Docstrings (Google Style — Mandatory)

### Module Docstring

Every `.py` file MUST start with a module-level docstring.

```python
"""Order domain entity and related business logic."""
```

### Class Docstring

```python
class OrderService:
    """Orchestrates order lifecycle operations.

    Attributes:
        repository: Repository for persisting orders.
        event_bus: Bus for publishing domain events.
    """

    def __init__(
        self,
        repository: OrderRepository,
        event_bus: EventBus,
    ) -> None:
        self.repository: OrderRepository = repository
        self.event_bus: EventBus = event_bus
```

### Method Docstring

```python
async def create_order(
    self,
    *,
    customer_id: str,
    items: list[OrderItem],
) -> Order:
    """Create a new order for the given customer.

    Args:
        customer_id: Unique identifier of the customer.
        items: List of items to include in the order.

    Returns:
        The newly created Order with a generated ID.

    Raises:
        CustomerNotFoundError: If customer_id does not exist.
        EmptyOrderError: If items list is empty.
    """
```

---

## 12. Context Managers

```python
# ✅ CORRECT — class-based with type hints
class Timer:
    def __init__(self, label: str) -> None:
        self.label: str = label
        self._start: float = 0.0

    def __enter__(self) -> Self:
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        elapsed: float = time.perf_counter() - self._start
        logger.info("%s took %.3fs", self.label, elapsed)
        return False

# ✅ CORRECT — function-based
from contextlib import contextmanager
from collections.abc import Iterator

@contextmanager
def temporary_setting(key: str, value: str) -> Iterator[None]:
    original: str = get_setting(key)
    set_setting(key, value)
    try:
        yield
    finally:
        set_setting(key, original)
```

---

## 13. Decorators with Type Hints

```python
# ✅ CORRECT — typed decorator preserving signature
from functools import wraps
from collections.abc import Callable, Awaitable
import time

def retry[T](
    *,
    max_attempts: int = 3,
    delay: float = 1.0,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Retry an async function on failure."""

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_error: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error  # type: ignore[misc]

        return wrapper

    return decorator
```

---

## 14. Property and Descriptor Patterns

```python
# ✅ CORRECT
from dataclasses import dataclass

@dataclass(slots=True, kw_only=True)
class Order:
    _status: OrderStatus = OrderStatus.PENDING
    _items: list[OrderItem] = field(default_factory=list)

    @property
    def status(self) -> OrderStatus:
        """Current order status (read-only)."""
        return self._status

    @property
    def total(self) -> Decimal:
        """Calculate total from line items."""
        return sum(item.subtotal for item in self._items)

    @property
    def is_cancellable(self) -> bool:
        """Whether the order can be cancelled."""
        return self._status in {OrderStatus.PENDING, OrderStatus.CONFIRMED}
```

---

## 15. Quick Reference Table

| Element            | Convention            | Example                        |
| ------------------ | --------------------- | ------------------------------ |
| Variable           | `snake_case`          | `user_name: str`               |
| Function / Method  | `snake_case`          | `def get_user() -> User:`      |
| Class              | `PascalCase`          | `class OrderService:`          |
| Constant           | `UPPER_SNAKE_CASE`    | `MAX_RETRIES: int = 3`         |
| Module / Package   | `snake_case`          | `order_service.py`             |
| Enum Member        | `UPPER_SNAKE_CASE`    | `PENDING = auto()`             |
| Type Alias         | `PascalCase`          | `type UserId = str`            |
| Private            | `_leading_underscore` | `self._status`                 |
| Generic            | `[T]` syntax          | `class Repo[T]:`               |
| Union              | `\|` operator         | `str \| None`                  |
| Built-in generics  | lowercase             | `list[str]`, `dict[str, int]`  |
| Docstring style    | Google                | `Args:`, `Returns:`, `Raises:` |
| String formatting  | f-strings             | `f"Hello {name}"`              |
| Logging formatting | `%` style             | `logger.info("Hi %s", name)`   |

---

## 16. Anti-Patterns to Avoid

```python
# ❌ NEVER use `Any` as a lazy escape hatch
def process(data: Any) -> Any: ...  # Too broad

# ❌ NEVER use bare `except`
try:
    ...
except:  # Catches SystemExit, KeyboardInterrupt
    ...

# ❌ NEVER use mutable default arguments
def add_item(items: list[str] = []) -> None: ...  # Shared mutable state

# ❌ NEVER use `type()` for type checking
if type(obj) == SomeClass: ...  # Use isinstance()

# ❌ NEVER shadow built-in names
list: list[str] = []     # Shadows built-in
id: str = "abc"           # Shadows built-in
type: str = "order"       # Shadows built-in

# ❌ NEVER use string concatenation for SQL. # CRITICAL
query = f"SELECT * FROM users WHERE id = '{user_id}'"  # SQL injection

# ✅ CORRECT alternatives
def process(data: OrderData) -> ProcessResult: ...  # Specific types
try:
    ...
except ValueError as e:  # Specific exception
    ...
def add_item(items: list[str] | None = None) -> None:
    items = items or []
if isinstance(obj, SomeClass): ...
order_list: list[str] = []
entity_id: str = "abc"
order_type: str = "order"
```

## Review Checklist

- [ ] Python syntax, typing, and imports match the project's supported Python version.
- [ ] Public APIs have precise parameter and return type hints.
- [ ] Names, docstrings, exceptions, and control flow make the code's intent clear.
- [ ] No legacy typing or syntax pattern was introduced where the supported modern form is clearer.
