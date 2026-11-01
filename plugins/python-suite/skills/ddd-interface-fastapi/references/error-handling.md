# Error Handling with `raised`

The exception hierarchy, codes, messages, and status hints are defined by the foundation's
[error model](../../ddd-hexagonal-python/references/errors/error-model.md). This
reference covers only how FastAPI turns them into responses, using `raised[fastapi]`
(0.2.x). The `raised` README is stale; the APIs below are the ones in its code.

## What `raised.fastapi` Does

```text
exception raised anywhere below the router
        │
        ▼
FastAPIExceptionRegister handler      ← per exception type; returns an AppException
        │                               (defaults: RequestValidationError -> PydanticException 422,
        │                                AppException -> itself, Exception -> UnexpectedException 500)
        ▼
FastAPIExceptionLogger                ← one log line; ERROR + traceback for >= 500, WARNING for 4xx;
        │                               metadata logged with sensitive keys redacted
        ▼
FastAPIResponseMapper + RFC9457Strategy → JSONResponse, media type application/problem+json
```

Response body (`RFC9457Response`, serialized with `exclude_none=True`):

```json
{
  "error_code": "ORD-001",
  "type": "about:blank",
  "title": "ORDER_NOT_FOUND_ERROR",
  "status": "404",
  "detail": "Order '7f3c...' does not exist.",
  "instance": "/api/v1/orders/7f3c...",
  "trace_id": "d4f1...",
  "errors": null
}
```

- `detail` is the exception's `message`: it is public.
- `metadata` never appears in the body.
- `errors` comes from `as_error_details()`; for request validation it lists
  `{field, message, type, constraints?}` per failing field.
- Known gaps in 0.2.x: `status` is a string, `type` is always `about:blank` unless a custom
  strategy is registered, and `trace_id` is a fresh UUID that is not logged. Correlate logs
  through the correlation middleware's request ID instead.

## Registration

Register once, in the app factory, before routes:

```python
# app/interfaces/api/exceptions/registry.py
from fastapi import FastAPI, Request
from raised import AppException
from raised.fastapi import FastAPIExceptionRegister

from app.exceptions.base import (
    ApplicationException,
    CoreException,
    DomainException,
    InfrastructureException,
    InterfaceException,
)

PROJECT_EXCEPTION_TYPES = (
    ApplicationException,
    CoreException,
    DomainException,
    InfrastructureException,
    InterfaceException,
)


async def map_project_exception(_: Request, exception: AppException) -> AppException:
    return exception


def register_exception_handlers(app: FastAPI) -> None:
    errors = FastAPIExceptionRegister(app)
    for exception_type in PROJECT_EXCEPTION_TYPES:
        errors.add_exception(exception_type, map_project_exception)
    errors.register()
```

- Call `register()` last. Handlers added afterwards are ignored.
- Registering a type again replaces the default for that type.
- Do not register `RequestValidationError` or `Exception` yourself unless you need a
  different shape; the defaults already hide internals.

## Translating Foreign Exceptions

Prefer translating at the infrastructure adapter, as the error model requires. Use an
interface-level handler only for exceptions that escape adapters by nature (a library
raising from middleware, a framework-specific error):

```python
@errors.handler(StorageQuotaExceeded)
async def handle_quota(_: Request, error: StorageQuotaExceeded) -> AppException:
    return StorageUnavailableError(reason=str(error))   # an InfrastructureException, 503
```

A handler returns an `AppException`; it never builds a `JSONResponse`. `raised` keeps the
original exception for the log.

## Headers

Put response headers in the reserved metadata key of an interface error:

```python
class AuthenticationRequiredError(InterfaceException):
    __error_code__ = "AUTH-401"
    __http_error__ = 401

    def __init__(self) -> None:
        super().__init__(
            "Authentication is required.",
            metadata={"_response_headers": {"WWW-Authenticate": "Bearer"}},
        )
```

Only interface errors use `_response_headers`; domain and application errors never carry
HTTP headers.

## Never in Routers or Dependencies

```python
# Never
raise HTTPException(status_code=404, detail="Order not found")
return JSONResponse(status_code=409, content={"message": "..."})
try:
    dto = await handler.handle(command)
except OrderAlreadyShippedError:
    return JSONResponse(...)

# Instead: let the typed error propagate; raised maps it.
dto = await handler.handle(command)
```

`HTTPException` is acceptable only for pure transport concerns that have no application
meaning, such as a method FastAPI itself rejects; prefer an `InterfaceException` subclass
even then, so every error body has an `error_code`.

## Modular Monolith

The host owns the single `FastAPIExceptionRegister`. Each module adds its custom mappings
through its `register_<module>_api(app, errors=...)` entry point before the host calls
`errors.register()`. Module errors subclass the host's category bases, so most need no
mapping at all. See [topology and bootstrap](topology-and-bootstrap.md#modular-monolith).

## Review Checklist

- [ ] `FastAPIExceptionRegister` is created once in the app factory and `register()` is called last.
- [ ] Every project category base is registered; defaults handle request validation and unexpected errors.
- [ ] Custom handlers return `AppException`s; no router or dependency builds an error response or raises `HTTPException` for an application outcome.
- [ ] HTTP headers travel only in interface errors' `_response_headers` metadata.
- [ ] Routes document their error responses with `ErrorResponse`; clients branch on `error_code`, not on `detail`.
