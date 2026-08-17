# Error Handler Reference

This reference explains the complete workflow for raising and handling errors in this codebase. **Never use `ValueError(...)`, `Exception(...)`, or other built-ins directly** — always follow the custom error system described here.

---

## 1. Exception Hierarchy

All custom exceptions inherit from `AppException` (`app/exceptions/base.py`):

```
AppException (root)
├── CoreException       → HTTP 400 — business rule violations
├── DomainException     → HTTP 400/422 — domain invariant violations
├── InfrastructureException → HTTP 503 — DB, external services, not-found
└── InterfaceException  → HTTP 400/429 — API/CLI input errors
```

**Auto-generated error codes:** class names are automatically converted to `SCREAMING_SNAKE_CASE` error codes (e.g., `UserNotFoundError` → `USER_NOT_FOUND_ERROR`).

---

## 2. i18n Error Messages

All user-facing strings live in `ErrorMessage` objects — never hardcode strings inside exception classes.

### Defining messages

Create messages in `app/<context>/i18n/messages/<context>_error_messages.py`:

```python
from app.i18n import ErrorMessage

# Simple message
ENTITY_NOT_FOUND_MSG = ErrorMessage(
    key="client_not_found",
    template="Client with id '{id}' was not found.",
)

# Parametrized message
ENTITY_ALREADY_EXISTS_MSG = ErrorMessage(
    key="client_already_exists",
    template="Client with {field} '{value}' was already registered.",
)
```

### Key naming convention

`<context>.<category>.<specific>` — e.g.:
- `client_not_found`
- `auth.token.invalid`
- `shared.validation.phone_spanish`

### Using messages

```python
# Simple: str() returns the raw template
raise SomeError(str(ENTITY_NOT_FOUND_MSG))

# With params: call .format()
raise SomeError(ENTITY_NOT_FOUND_MSG.format(id=uuid))

# With dict params
raise SomeError(ENTITY_ALREADY_EXISTS_MSG.format({"field": "email", "value": "a@b.com"}))
```

---

## 3. Complete Workflow: Creating a Custom Error

### Step 1 — Define the i18n message

In `app/<context>/i18n/messages/<context>_error_messages.py`:

```python
from app.i18n import ErrorMessage

CLIENT_NOT_FOUND_MSG = ErrorMessage(
    key="client_not_found",
    template="Client with id '{id}' does not exist.",
)
```

### Step 2 — Create the exception class

In `app/exceptions/<context>_errors.py`, pick the right base class:

| Situation | Base class |
|---|---|
| Entity not found, DB constraint, external service | `InfrastructureException` |
| Business rule violated | `CoreException` |
| Domain invariant broken | `DomainException` |
| Bad API input / rate limit | `InterfaceException` |

```python
from app.exceptions import InfrastructureException
from app.i18n import messages as m

class ClientNotFoundError(InfrastructureException):
    def __init__(self, uuid: UUID):
        super().__init__(m.CLIENT_NOT_FOUND_MSG.format(id=uuid))
```

### Step 3 — Raise it where appropriate

**Infrastructure layer** (repositories):
```python
async def get_by_id(self, id: UUID) -> Client:
    result = await self._session.execute(stmt)
    entity = result.scalar_one_or_none()
    if not entity:
        raise ClientNotFoundError(id)
    return entity
```

**Application layer** (command/query handlers):
```python
async def handle(self, cmd: CreateClientCommand):
    if duplicate := await uow.clients.get_by_email(cmd.email):
        raise EmailClientAlreadyExistError(duplicate)
```

**Domain layer** (entities/value objects):
```python
class Client:
    def update_status(self, new_status: Status):
        if not self._is_valid_transition(new_status):
            raise InvalidStatusTransitionError(self.status, new_status)
```

---

## 4. Specialised Sub-errors (composition)

Group related errors using a base + specialisations pattern:

```python
class ClientAlreadyExistError(InfrastructureException):
    def __init__(self, client: Client, column: str):
        super().__init__(
            m.CLIENT_ALREADY_EXISTS_MSG.format(
                {"field": column, "value": str(getattr(client, column))}
            )
        )

class EmailClientAlreadyExistError(ClientAlreadyExistError):
    def __init__(self, client: Client):
        super().__init__(client, "email")

class CifClientAlreadyExistError(ClientAlreadyExistError):
    def __init__(self, client: Client):
        super().__init__(client, "cif")
```

---

## 5. FastAPI Exception Handlers

Handlers are registered in `app/interfaces/api/v1/exception_handler.py` and wired up in `app/main.py`.

| Exception type | HTTP status | Metadata exposed? |
|---|---|---|
| `CoreException` | 400 | Yes (via `to_dict()`) |
| `InfrastructureException` | 503 | No (security) |
| `AppException` (catch-all) | 500 | Yes |
| `Exception` (unexpected) | 500 | No — generic message |

Response format (from `to_dict()`):
```json
{
  "message": "Human-readable error",
  "error_code": "SCREAMING_SNAKE_CASE_ERROR_CODE",
  "metadata": {}
}
```

---

## 6. File Checklist When Adding a New Error

```
app/
├── <context>/i18n/messages/<context>_error_messages.py  ← 1. add ErrorMessage constant
└── exceptions/<context>_errors.py                       ← 2. add exception class(es)
```

Then raise the exception in the appropriate layer — no other files need changing unless you need a new HTTP mapping.

---

## 7. Anti-patterns to Avoid

```python
# ❌ Never do this
raise ValueError("Entity not found")
raise Exception(f"User {id} does not exist")
raise RuntimeError("Already exists")

# ✅ Do this instead
raise EntityNotFoundError(id)
raise EmailAlreadyExistError(entity)
```