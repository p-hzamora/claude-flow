# Error Model

One exception hierarchy serves every interface. Inner layers raise typed errors that know
nothing about HTTP responses or exit codes; each interface translates them at its edge.
How an interface renders them is in its interface skill (`ddd-interface-fastapi` and
`ddd-interface-cli`, reference `error-handling.md`).

**Never raise `ValueError`, `Exception`, `RuntimeError`, or another built-in for an
expected failure.** Built-ins are for bugs. Every failure a caller should understand is a
typed project error.

## 1. The Root: `raised.AppException`

Projects root their hierarchy in `raised.AppException` (the `raised` package: core
install `raised`, FastAPI extra `raised[fastapi]`). Its core is standard-library only and
imports no framework, so every layer may import the project's exception bases.

```python
class AppException(Exception, metaclass=AppExceptionMeta):
    __error_code__: ClassVar[str] = "CMN-500"     # stable code, set per error
    __error_title__: ClassVar[str]                 # derived from the class name
    __http_error__: ClassVar[int] = 500            # transport-neutral status hint

    def __init__(self, message: str, metadata: Mapping[str, Any] | None = None, *args): ...
    # properties: message, metadata, error_code, status_code; as_error_details() -> None
```

- `__error_code__` is explicit, never derived. It is the value callers branch on. Once
  published it never changes; the message may improve.
- `__error_title__` is derived per class: `OrderNotFoundError` gives
  `ORDER_NOT_FOUND_ERROR`, and a trailing `Exception` becomes `ERROR`. Override it only
  on purpose.
- `__http_error__` is a **status hint**. It names the outcome class with HTTP numbers
  because they are the most widely understood vocabulary (`404` not found, `409`
  conflict, `422` rule violated, `503` dependency unavailable). The FastAPI adapter
  returns it as the status code; the CLI adapter maps it to an exit code; a worker maps
  it to retry or dead-letter. It never means the domain knows about HTTP.
- `message` is public: interfaces show it to users and agents. Never put secrets,
  tokens, SQL, or stack details in it.
- `metadata` is structured diagnostic context. It is logged (`raised` redacts keys such
  as `password`, `token`, `authorization`) and never returned in an HTTP body. The key
  `_response_headers` is reserved for HTTP headers; only interface errors use it.
- `as_error_details()` returns per-field details for validation-style errors.

Do not rely on the `raised` README; it still describes an older `error_handler` package.
The code (`raised/core/exceptions/app_exception.py`) is the authority.

## 2. Category Bases

`<package>/exceptions/base.py` declares one base per category, as in the
`python/ddd_fastapi` template. Every base sets a default code and status hint, so a leaf
that forgets one still lands in the right outcome class.

| Base | Raised by | Meaning | Default code / hint |
| --- | --- | --- | --- |
| `DomainException` | domain | An invariant or business rule rejected the operation | `DOM-422` / 422 |
| `ApplicationException` | application | A use case cannot proceed: missing resource, invalid state for this use case | `APP-500` / 500; leaves override (404, 409) |
| `InfrastructureException` | infrastructure adapters | A concrete dependency failed, after translating its native error | `INF-500` / 500; `503` when unavailable |
| `InterfaceException` | interfaces | Input the delivery adapter could not accept: malformed payload, bad arguments, missing credentials | `INT-400` / 400 |
| `CoreException` | `core/`, bootstrap | Configuration or process-policy failures around a use case | `CORE-500` / 500 |

```python
# app/exceptions/base.py
from raised import AppException


class DomainException(AppException):
    """Base exception for violated domain invariants."""

    __error_code__ = "DOM-422"
    __http_error__ = 422
```

Leaves set their own code and override the hint when the outcome differs:

```python
# app/exceptions/ordering_errors.py
from app.exceptions.base import ApplicationException, DomainException


class OrderNotFoundError(ApplicationException):
    __error_code__ = "ORD-001"
    __http_error__ = 404

    def __init__(self, order_id: str) -> None:
        super().__init__(f"Order '{order_id}' does not exist.", metadata={"order_id": order_id})


class OrderAlreadyShippedError(DomainException):
    __error_code__ = "ORD-002"
    __http_error__ = 409

    def __init__(self, order_id: str) -> None:
        super().__init__(
            f"Order '{order_id}' has already shipped and cannot change.",
            metadata={"order_id": order_id},
        )
```

### Codes

- Format `<PREFIX>-<NNN>`: a context prefix (`ORD`, `PAY`) and a number unique within it.
  `CMN-003` and `CMN-500` are reserved by `raised`.
- Siblings may share a code when a caller should treat them alike; a subclass inherits
  its parent's code unless it needs a narrower one.
- Keep the published codes discoverable: a table in the module docstring, or the
  interface's help or agent guide when agents branch on them.
- A project with an established format (for example `CTX_NNN_NAME`) keeps it
  consistently. Do not mix formats in one service.

### Messages

Plain English, built inside the exception's `__init__` with an f-string: what failed,
which value, and, when useful, how to fix it. No i18n catalog and no `ErrorMessage`
indirection. Extract module-level string constants only when several sibling exceptions
genuinely share phrasing.

### Recovery Hints

When an interface serves people or agents who can act on an error (typically a CLI), the
project's bases add a keyword-only `next_steps: Sequence[str] = ()` stored as a tuple.
It describes actions, never internals. The CLI skill renders it; the default FastAPI
problem format does not, so do not depend on it for HTTP clients.

## 3. Placement

| Layout | Shared bases | Context and module errors |
| --- | --- | --- |
| Single service | `exceptions/base.py` | `exceptions/<context>_errors.py` |
| Modular monolith | host `exceptions/base.py` (bases and service-wide errors only) | `modules/<module>/exceptions/<context>/{domain,application,infrastructure}.py` |
| Microservice | the service's `exceptions/base.py` | as in a single service |

Domain code imports only the pure domain subset: the bases and its context's errors, from
a module that itself imports nothing but the bases. Keep package initializers free of
imports that would pull outer-layer errors into the domain. When a context's error module
grows, split it like a module's: `exceptions/<context>/{domain,application,infrastructure}.py`. Interface-only errors (malformed CLI input, a missing bearer token) live
with the bases or under the owning interface, never in a context's domain.

## 4. Translating Foreign Errors

Translate where the foreign error is born:

- An infrastructure adapter catches its driver's exceptions (SQLAlchemy `IntegrityError`,
  an HTTP client timeout, a subprocess failure) and raises a typed
  `InfrastructureException` subclass, keeping the original as `__cause__`
  (`raise ... from error`).
- An anti-corruption layer translates an upstream context's errors into its own context's
  errors. The downstream context never catches an upstream error type.
- The interface translates its own parsing failures (request validation, argument
  parsing, malformed stdin) into `InterfaceException` subclasses.

Every interface also has a last-resort handler for anything else. It hides internals from
the caller, logs the full traceback, and reports a generic unexpected error. With
`raised[fastapi]` this is built in; the CLI skill defines its own.

## 5. How Interfaces Use the Hint

| Interface | Translation |
| --- | --- |
| HTTP (FastAPI) | `status_code` becomes the response status; the body is RFC 9457 via `raised.fastapi`. Request-body validation keeps `raised`'s default: 422 with code `CMN-003` and per-field `errors` |
| CLI | `InterfaceException` exits 2 (usage); every other `AppException` exits 1; Ctrl-C exits 130 |
| Worker / consumer | A 503 hint or an `InfrastructureException` means retry with back-off; a 4xx-class hint means the message can never succeed, so dead-letter it |

A new interface documents its own row in its skill. It never adds attributes such as
`__exit_code__` to domain or application exceptions.

## 6. Anti-patterns

```python
# Never
raise ValueError("Order not found")
raise Exception(f"User {user_id} does not exist")
raise HTTPException(status_code=404)                          # framework type in an inner layer
raise typer.Exit(code=1)                                      # framework type in an inner layer
raise SomeError(ErrorMessage(key="...").format(id=order_id))  # i18n indirection

# Instead
raise OrderNotFoundError(order_id)
```

## Review Checklist

- [ ] Every expected failure raises a typed project error rooted in the category bases; no built-in exception signals an expected outcome.
- [ ] Each base sets a default code and status hint; each leaf sets its own stable code and overrides the hint when the outcome differs.
- [ ] Messages are plain English, built inline, free of secrets and internals; diagnostic context goes to `metadata`.
- [ ] Errors live where the layout prescribes; domain code imports only the pure domain subset.
- [ ] Infrastructure adapters translate driver errors at the adapter, with `raise ... from error`.
- [ ] No inner layer imports a delivery framework's exception type or adds interface-specific attributes.
- [ ] Each interface has a last-resort handler that hides internals and logs the traceback.
