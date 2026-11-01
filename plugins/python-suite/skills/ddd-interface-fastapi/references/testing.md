# Testing the HTTP Interface

Domain objects and handlers are tested without FastAPI, as the foundation's
[testing strategy](../../ddd-hexagonal-python/references/testing/strategy.md)
describes. HTTP tests verify only the edge: routing, request validation, the response
schema, status codes, and the error body. Use the `pytest` skill for fixture and async
mechanics.

## Client

Drive the ASGI app in-process with `httpx`:

```python
# tests/integration/interfaces/api/conftest.py
from collections.abc import AsyncIterator, Iterator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app() -> Iterator[FastAPI]:
    application = create_app()
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
```

Use `asgi-lifespan` (`LifespanManager`) when the test needs the lifespan's resources; most
router tests override the handler dependency instead and need no resources.

## Override Dependencies, Do Not Patch

Replace the handler a route receives with a fake that returns DTOs or raises project
errors:

```python
async def test_get_unknown_order_returns_problem_details(app, client):
    class MissingOrderHandler:
        async def handle(self, query: GetOrderQuery) -> OrderDTO:
            raise OrderNotFoundError(str(query.order_id))

    app.dependency_overrides[get_get_order_handler] = MissingOrderHandler

    response = await client.get(f"/api/v1/orders/{uuid4()}")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    assert response.json()["error_code"] == "ORD-001"
```

- Assert the status code and `error_code`; do not assert on `detail` wording.
- For success, assert the response schema fields that the contract promises.
- The `app` fixture clears `dependency_overrides` on teardown.

## What to Cover per Route

| Case | Assertion |
| --- | --- |
| Valid request | status, response body fields |
| Invalid body | 422, `error_code == "CMN-003"`, `errors[].field` |
| Each documented application error | its status and `error_code` |
| Unexpected exception in the handler | 500, `error_code == "CMN-500"`, no internals in `detail` |
| Auth required | 401 and the `WWW-Authenticate` header |

## Architecture and Module Tests

- The import contracts from the
  [adapter contract](../../ddd-hexagonal-python/references/interfaces/adapter-contract.md#enforcement)
  run in the test suite.
- In a modular monolith, mount one module on a bare `FastAPI()` through its
  `register_<module>_api` and assert that only its paths appear. This proves the module's
  API does not depend on other modules' routers.
- Snapshot the OpenAPI document when the API is consumed by other services, so contract
  changes are reviewed.

## Review Checklist

- [ ] HTTP tests drive the app in-process with `httpx` and override handler dependencies instead of patching.
- [ ] Every route's documented errors are asserted by status and `error_code`.
- [ ] Validation, unexpected-error, and auth behaviours are covered once per API, not per route.
- [ ] Module APIs mount independently in a modular monolith; OpenAPI changes are reviewed when other services consume the API.
