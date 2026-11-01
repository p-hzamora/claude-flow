# Routers and Schemas

For resource naming, URL structure, methods, status codes, pagination, and filtering,
follow the `api-rest-designer` skill. This reference covers how routers connect HTTP to
the application layer.

## Router Rules

A router function does exactly four things:

1. Receive a validated request schema, path, and query parameters.
2. Build the handler's `Command` or `Query` (imported from the handler's file).
3. Await the handler injected through a `*Dpd` alias.
4. Return a response schema built from the returned DTO.

```python
# app/interfaces/api/v1/routers/order_router.py
from uuid import UUID

from fastapi import APIRouter, status

from app.bounded_context.ordering.application.handlers.commands.place_order_handler import (
    PlaceOrderCommand,
)
from app.bounded_context.ordering.application.handlers.queries.get_order_handler import (
    GetOrderQuery,
)
from app.interfaces.api.exceptions.schema import ErrorResponse
from app.interfaces.api.v1.dependencies.order_dpd import GetOrderHandlerDpd, PlaceOrderHandlerDpd
from app.interfaces.api.v1.schemas.order_schema import OrderResponse, PlaceOrderRequest

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorResponse}},
)
async def place_order(request: PlaceOrderRequest, handler: PlaceOrderHandlerDpd) -> OrderResponse:
    dto = await handler.handle(PlaceOrderCommand(**request.model_dump()))
    return OrderResponse.model_validate(dto)


@router.get("/{order_id}", responses={404: {"model": ErrorResponse}})
async def get_order(order_id: UUID, handler: GetOrderHandlerDpd) -> OrderResponse:
    dto = await handler.handle(GetOrderQuery(order_id=order_id))
    return OrderResponse.model_validate(dto)
```

Never in a router: `if`-logic on business state, a `try/except` that turns a domain error
into a response, an ORM session, a repository, a call to another router, or more than one
handler call that must succeed together (that is a use case; write a handler).

## Schemas

`v1/schemas/<resource>_schema.py` holds the resource's request and response models.

| Model | Name | Built from |
| --- | --- | --- |
| Request body | `<Action><Resource>Request` (`PlaceOrderRequest`) | the HTTP body, by FastAPI |
| Query parameters | `<Resource>Filters`, `PaginationParams` | `Annotated[Model, Query()]` |
| Response | `<Resource>Response` (`OrderResponse`) | a DTO, with `model_validate` |
| Collection response | `<Resource>PageResponse` | a page DTO |

```python
# app/interfaces/api/v1/schemas/order_schema.py
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OrderLineRequest(BaseModel):
    product_id: UUID
    quantity: int
    unit_price: Decimal


class PlaceOrderRequest(BaseModel):
    customer_id: UUID
    currency: str = Field(min_length=3, max_length=3)
    lines: list[OrderLineRequest] = Field(min_length=1)


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    total_amount: Decimal  # serialized as a JSON string by pydantic
    currency: str
```

- Request and response schemas are the public HTTP contract. They are independent of DTOs
  even when the fields match, so a DTO change cannot silently change the API.
- `from_attributes=True` lets `OrderResponse.model_validate(dto)` read a DTO directly.
- Request schemas validate shape (types, lengths, required fields). Business validity is
  the domain's job; do not duplicate invariants in schemas.
- Money crosses HTTP as a decimal string plus currency, never `float`.

## DTO to Response

The default is `Response.model_validate(dto)` inline in the router, also when the response
exposes a subset of the DTO or renames nothing. Write
`v1/mappers/<resource>_api_mapper.py` with `{Resource}ApiMapper.to_schema(dto)` only when
the mapping needs real logic `model_validate` cannot express: flattening nested DTOs,
renames, computed fields. A response is never built from an entity or value object, even
for handler-less endpoints such as "who am I": produce a DTO first.

## Status Codes

| Outcome | Status |
| --- | --- |
| Created | `201`, with the new resource in the body (and `Location` when the API uses it) |
| Read, update returning state | `200` |
| Accepted for asynchronous processing | `202` |
| Delete or update without body | `204` |
| Any failure | from the exception's status hint, through `raised`; never set in the router |

Document expected error responses on each route with `responses={code: {"model": ErrorResponse}}`
so OpenAPI shows the RFC 9457 body.

## Review Checklist

- [ ] Routers do only the four steps; one handler call per route.
- [ ] Commands and queries come from their handler files; responses come from DTOs via `model_validate` unless an `ApiMapper` has real logic.
- [ ] Schemas live in `<resource>_schema.py` with `Request`/`Response` suffixes and validate shape, not business rules.
- [ ] Success status codes are explicit; failure status comes from the error model, and error responses are documented in OpenAPI.
