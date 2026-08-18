# Error Handler Reference

Complete workflow for raising and handling errors in this codebase. **Never use
`ValueError(...)`, `Exception(...)`, or other built-ins directly** — always follow the
custom error system described here.

**No i18n.** Error messages are plain English, built directly inside the exception —
never route them through an `ErrorMessage`/i18n class or a translation catalog. That
indirection adds a layer of ceremony (define message → import message → format message →
raise) for no benefit when the app only ever renders English. Write the string where the
exception is raised.

---

## 1. Exception Hierarchy

All custom exceptions inherit from `AppException` (`app/exceptions/base.py`):

```
AppException (root)
├── ApplicationException  → HTTP 400/422 — application/use-case invariant violations
├── CoreException         → HTTP 400 — business rule violations (default)
├── DomainException       → HTTP 400/422 — domain invariant violations
├── InfrastructureException → HTTP 503 — DB, external services, not-found
└── InterfaceException    → HTTP 400/429 — API/CLI input errors
```

Each base sets a sane default via `__http_error__`; a concrete exception overrides it
when its real status differs (e.g. a `*NotFoundError` on `InfrastructureException`
overrides the base's 503 down to 404).

`AppException` itself carries three class-level attributes a subclass fills in:

```python
class AppException(Exception):
    __error_code__: ClassVar[str] = "CMN_500_INTERNAL_SERVER_ERROR"  # explicit, not derived
    __error_title__: ClassVar[str]   # auto-derived from the class name, see below
    __http_error__: ClassVar[int] = 500

    def __init__(self, message: str, metadata: dict[str, Any] | None = None) -> None:
        self._message = message
        self._metadata = metadata or {}
        super().__init__(message)
```

- **`__error_code__` is explicit, not auto-generated.** Set it per exception (or per
  small group of sibling exceptions) — a plain string, or a member of a shared error-code
  enum if the project has one (`app/exceptions/error_code.py: ErrorCodeEnum`). Don't
  derive it from the class name; two exceptions can legitimately share a code (a subclass
  inherits its parent's `__error_code__` unless it needs its own, narrower one).
- **`__error_title__` *is* auto-derived** from the class name (`format_exception_name` in
  `app/exceptions/utils.py`: strips the `Error`/`Exception` suffix, converts
  `CamelCase` → `SCREAMING_SNAKE_CASE`). This is the one place class-name-derivation still
  happens — it feeds the `title` field of the HTTP response, not the error code.
- `message` and `metadata` are plain instance properties — `metadata` is extra structured
  context (never secrets) that gets logged but is stripped before reaching the client on
  5xx responses.

---

## 2. Writing Error Messages — No `ErrorMessage`, No i18n Catalog

Two valid ways to write the message text, chosen by how many exceptions need it:

### A. Inline — the default

Build the string directly inside `__init__` with an f-string. This is the right call for
the vast majority of exceptions: one exception, one message, no reuse.

```python
class RuleNotFoundError(InfrastructureException):
    __error_code__ = "RLE_001_RULE_NOT_FOUND"
    __http_error__ = 404

    def __init__(self, identifier: str | object) -> None:
        super().__init__(f"Rule with id '{identifier}' was not found.")
```

```python
class AppVersionNotEditableError(DomainException):
    __error_code__ = "RLE_406_APP_VERSION_NOT_EDITABLE"
    __http_error__ = 409

    def __init__(self, app_version_id: str, current_status: str, editable_states: list[str]) -> None:
        self.app_version_id = app_version_id
        self.current_status = current_status
        self.editable_states = editable_states
        super().__init__(
            f"AppVersion '{app_version_id}' is in status '{current_status}' and cannot be "
            f"edited. Editable statuses: {', '.join(editable_states)}.",
            metadata={
                "app_version_id": app_version_id,
                "current_status": current_status,
                "editable_states": editable_states,
            },
        )
```

### B. Module-level string constants — only when several exceptions share text

When a family of sibling exceptions in the same module reuses the same phrasing (e.g. all
auth failures), extract to plain string constants — **not** an `ErrorMessage` object, just
a `str` with `{}` placeholders and `.format()`:

```python
# app/core/messages/auth_error_messages.py
INVALID_TOKEN = "Invalid authentication token"
INVALID_ISSUER = "Token issuer '{issuer}' is not trusted. Expected: '{expected}'"
INSUFFICIENT_PERMISSIONS = "User must have at least one of the following roles: {roles}"
```

```python
from ..messages import auth_error_messages as auth_errors

class InvalidIssuerError(AuthenticationError):
    def __init__(self, issuer: str, expected: str) -> None:
        super().__init__(
            message=auth_errors.INVALID_ISSUER.format(issuer=issuer, expected=expected),
            metadata={"issuer": issuer, "expected": expected},
        )
```

Reach for (B) only when duplication is real — copy-pasting the same sentence into three
`__init__` bodies is the signal to extract, not a rule to apply upfront. Default to (A).

---

## 3. Complete Workflow: Creating a Custom Error

### Step 1 — Pick the right base class

| Situation | Base class |
|---|---|
| Entity not found, DB constraint, external service | `InfrastructureException` |
| Business rule violated | `CoreException` |
| Domain invariant broken | `DomainException` |
| Application/use-case invariant broken | `ApplicationException` |
| Bad API input / rate limit | `InterfaceException` |

### Step 2 — Write the exception class

In `app/exceptions/<context>_errors.py`:

```python
class ClientNotFoundError(InfrastructureException):
    __error_code__ = "CTX_001_CLIENT_NOT_FOUND"
    __http_error__ = 404

    def __init__(self, uuid: UUID) -> None:
        super().__init__(f"Client with id '{uuid}' does not exist.")
```

No message file, no i18n import — the string lives right where it's raised.

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
async def handle(self, cmd: CreateClientCommand) -> None:
    if duplicate := await uow.clients.get_by_email(cmd.email):
        raise EmailClientAlreadyExistError(duplicate)
```

**Domain layer** (entities/value objects):
```python
class Client:
    def update_status(self, new_status: Status) -> None:
        if not self._is_valid_transition(new_status):
            raise InvalidStatusTransitionError(self.status, new_status)
```

---

## 4. Specialised Sub-errors (composition)

Group related errors using a base + specialisation pattern — the base carries the shared
message shape and error code; each subclass fixes one parameter:

```python
class RuleAlreadyExistError(InfrastructureException):
    __error_code__ = "RLE_002_RULE_ALREADY_EXISTS"
    __http_error__ = 409

    def __init__(self, field: str, value: str) -> None:
        super().__init__(f"Rule with {field} '{value}' was already registered.")


class RuleCodeAlreadyExistError(RuleAlreadyExistError):
    def __init__(self, rule_code: str) -> None:
        super().__init__("rule_code", rule_code)
```

When a subclass needs to skip its immediate parent's `__init__` (e.g. to build a
differently-shaped message while still inheriting error code/HTTP status), call the
grandparent explicitly:

```python
class UnknownDiscriminatorError(AstDeserializationError):
    def __init__(self, discriminator_value: str, valid_values: list[str]) -> None:
        self.discriminator_value = discriminator_value
        self.valid_values = valid_values
        message = f"Unknown discriminator '{discriminator_value}'. Valid values: {', '.join(valid_values)}."
        DomainException.__init__(self, message)  # bypass AstDeserializationError.__init__
```

---

## 5. FastAPI Exception Handlers

Response format is **RFC 9457 ProblemDetails**, not an ad-hoc `{message, error_code,
metadata}` shape. The pipeline is layered so each concern is independently testable:

```
AppException
    │
    ▼
ExceptionResponseMapper.map()   ← single choke point: logs, then delegates
    │  - derives log level from __http_error__ (5xx=error+traceback, 4xx=warning, else info)
    │  - structured log carries message + metadata; metadata never reaches the client on 5xx
    ▼
ApiError                        ← adapter: AppException → JSONResponse
    │
    ▼
ProblemDetailError (e.g. RFC9457)  ← formats the response body
```

`handlers.py` stays thin — each handler adapts the incoming exception (if needed) and
delegates to the mapper:

```python
async def handle_core_exception(request: Request, exc: AppException) -> JSONResponse:
    return HandlerConfig.mapper.map(request, exc)
```

Registration is a dict of exception type → handler, applied once at startup:

```python
EXCEPTION_REGISTRY: dict[type[Exception], ExceptionHandler] = {
    RequestValidationError: handlers.handle_request_validation_error,
    ValueError: handlers.handle_value_error,
    CoreException: handlers.handle_core_exception,
    InfrastructureException: handlers.handle_infrastructure_exception,
    AppException: handlers.handle_app_exception,   # catch-all for AppException
    Exception: handlers.handle_unexpected_error,    # catch-all for everything else
}

def register_exception_handlers(app: FastAPI) -> None:
    for exc_type, handler_func in EXCEPTION_REGISTRY.items():
        app.add_exception_handler(exc_type, handler_func)
```

Response body (`RFC9457.to_json()`):
```json
{
  "error_code": "RLE_001_RULE_NOT_FOUND",
  "type": "https://tools.mycompany.com/errors/RLE_001_RULE_NOT_FOUND",
  "title": "RULE_NOT_FOUND_ERROR",
  "status": "404",
  "detail": "Rule with id 'abc' was not found.",
  "instance": "/api/v1/rules/abc",
  "trace_id": "..."
}
```

A raw, unexpected `Exception` (not an `AppException`) is never surfaced to the client
as-is — wrap it first so internals don't leak:

```python
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    return HandlerConfig.mapper.map(
        request,
        UnexpectedException(
            message="An unexpected error occurred. Please try again later.",
            metadata={"original_error_type": type(exc).__name__},
        ),
    )
```

---

## 6. File Checklist When Adding a New Error

```
app/exceptions/<context>_errors.py   ← exception class(es), message inline (§2A)
                                        or module message constants if reused (§2B)
```

One file, not two — there is no separate i18n/message-catalog file to keep in sync. Then
raise the exception in the appropriate layer; no other files need changing unless the
error needs a new HTTP status mapping or its own handler.

---

## 7. Anti-patterns to Avoid

```python
# ❌ Never do this
raise ValueError("Entity not found")
raise Exception(f"User {id} does not exist")
raise RuntimeError("Already exists")

# ❌ Don't reintroduce i18n/ErrorMessage indirection
raise SomeError(ErrorMessage(key="...", template="...").format(id=uuid))

# ✅ Do this instead
raise EntityNotFoundError(id)              # message built inline, plain English
raise EmailAlreadyExistError(entity)
```
