---
name: ddd-interface-fastapi
description: FastAPI interface for Python DDD/hexagonal services built on ddd-hexagonal-python. Use when adding or reviewing HTTP delivery code - app factory and lifespan, interface bootstrap, routers, request/response schemas, dependency factories, raised RFC 9457 error handling, HTTP tests, or mounting module APIs in a modular monolith.
---

# FastAPI Interface for DDD Services

The FastAPI app is a driving adapter. It parses HTTP input into a command or query, calls a
handler it received from the composition root, and turns the returned DTO or error into
an HTTP response. Everything inside the hexagon comes from `ddd-hexagonal-python`;
load it first. This skill answers only the rows of its
[interface adapter contract](../ddd-hexagonal-python/references/interfaces/adapter-contract.md)
for HTTP.

Related skills: `fastapi-async-patterns` for async mechanics and typed application state,
`api-rest-designer` (base `skills` plugin) for resource and URL design, `python-syntax`
for code style, `pytest` for test mechanics.

## Non-Negotiables

- Routers translate and delegate: request schema -> `Command`/`Query` -> injected handler
  -> `Response.model_validate(dto)`. No business rule, transaction, ORM session, or
  repository in a router.
- Handlers reach routers only through dependency factories in `dependencies/*_dpd.py`,
  built per request from the session factory in typed state; each `handle` call opens its
  own Unit of Work. No module-level singleton holds a connection.
- A response schema is built from a DTO only, never from an entity, value object, or ORM
  model. A dedicated `{Resource}ApiMapper` exists only for real transform logic.
- Errors go through `raised.fastapi.FastAPIExceptionRegister`, registered once in the app
  factory. Routers never build error responses or raise `HTTPException` for domain
  outcomes; handlers translating foreign exceptions return an `AppException`.
- `main.py` only assembles: exception handlers, middleware, routers, lifespan, telemetry
  gate. Wiring lives in `interfaces/api/bootstrap/`.
- Process resources stay interface-neutral; the API bootstrap publishes them into typed
  application state.

## References

| Decision | Reference |
| --- | --- |
| Folder layout, app factory, lifespan, typed state, module API registration, microservice placement | [Topology and bootstrap](references/topology-and-bootstrap.md) |
| Routers, request/response schemas, DTO -> response, status codes, pagination | [Routers and schemas](references/routers-and-schemas.md) |
| Dependency factories, per-request handlers and Unit of Work factories, `*Dpd` aliases, auth dependencies | [Dependencies](references/dependencies.md) |
| `raised` registration, RFC 9457 body, custom handlers, headers, validation errors, OpenAPI error docs | [Error handling](references/error-handling.md) |
| HTTP tests, dependency overrides, module mount tests | [Testing](references/testing.md) |
| FastAPI instrumentation through the telemetry wrapper | [Observability](references/observability.md) |

## Review Checklist

- [ ] Every router only translates input, calls an injected handler, and validates its response from the DTO.
- [ ] Commands and queries are imported from their handler files; response schemas are built from DTOs; any `ApiMapper` has real transform logic.
- [ ] Dependency factories build handlers per request from the session factory in typed state; no connection-holding module-level singleton.
- [ ] Errors are registered once through `FastAPIExceptionRegister`; custom handlers return `AppException`s; no `HTTPException` for domain outcomes.
- [ ] `main.py` only assembles the app; wiring lives in `interfaces/api/bootstrap/`; resources are published into typed state by the API bootstrap.
- [ ] In a modular monolith, business routes, schemas, dependencies, and custom mappings live under the module's `interfaces/api/` and are mounted through `register_<module>_api`.
- [ ] HTTP tests assert status and the `error_code` of RFC 9457 bodies, and override dependencies instead of patching.
- [ ] The foundation's Review Checklist holds for the code behind the routes.
