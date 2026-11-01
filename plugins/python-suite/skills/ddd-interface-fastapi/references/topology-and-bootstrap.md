# Topology and Bootstrap

Where HTTP delivery code lives, how the app is assembled, and how it changes in a modular
monolith or a microservice. The rest of the service follows the foundation's
[project topology](../../ddd-hexagonal-python/references/architecture/project-topology.md).

## Layout (single service)

Matches the `python/ddd_fastapi` template of the `project-templates` catalog, with the
foundation's naming suffixes.

```text
app/
├── main.py                             # create_app() + lifespan; assembles, never wires
└── interfaces/api/
    ├── bootstrap/
    │   └── composition.py              # bootstrap_infrastructure(app): resources -> typed state
    ├── state.py                        # typed view of app.state (fastapi-async-patterns)
    ├── telemetry.py                    # HTTP instrumentation on the neutral config builder
    ├── exceptions/
    │   ├── registry.py                 # register_exception_handlers(app)
    │   └── schema.py                   # ErrorResponse = raised RFC9457Response, for OpenAPI
    ├── middleware/
    │   ├── correlation.py
    │   ├── timing.py
    │   └── registration.py             # register_middlewares(app)
    ├── routers/
    │   └── health.py                   # unversioned process routes
    └── v1/
        ├── routers/<resource>_router.py
        ├── schemas/<resource>_schema.py
        ├── dependencies/
        │   ├── <resource>_dpd.py
        │   └── auth_dpd.py
        └── mappers/<resource>_api_mapper.py   # rare; only real transform logic
```

The template currently names routers and schemas after the resource only
(`v1/routers/product.py`) and dependencies `<resource>_dpd.py`. Keep a generated project's
existing names consistently; use the suffixed names for new projects and new files.

## App Factory

```python
# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core import env
from app.interfaces.api.bootstrap.composition import bootstrap_infrastructure
from app.interfaces.api.exceptions.registry import register_exception_handlers
from app.interfaces.api.middleware.registration import register_middlewares
from app.interfaces.api.routers.health import router as health_router
from app.interfaces.api.v1 import router as v1_router
from app.interfaces.api.telemetry import configure_fastapi_telemetry


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = await bootstrap_infrastructure(app)
    try:
        yield
    finally:
        await registry.shutdown_all()


def create_app() -> FastAPI:
    app = FastAPI(title=env.RUNTIME_SETTINGS.app_name, lifespan=lifespan)
    register_exception_handlers(app)
    register_middlewares(app)
    app.include_router(health_router)
    app.include_router(v1_router, prefix="/api/v1")
    if env.OBSERVABILITY_SETTINGS.otel_enabled:
        configure_fastapi_telemetry(app)
    return app


app = create_app()
```

- Exception handlers are registered before routes so every route is covered.
- Constructing the app (and its OpenAPI document) never opens a connection; resources
  start in the lifespan.
- A server reads settings once at process start (`app/core/env.py`). This is the
  foundation's composition-root rule applied to a long-running process.

## Interface Bootstrap

`interfaces/api/bootstrap/composition.py` is the API's composition root. It starts the
interface-neutral [process resources](../../ddd-hexagonal-python/references/architecture/composition-root.md#process-resources)
through the resource registry and publishes what routes need into typed application state.

```python
# app/interfaces/api/bootstrap/composition.py
from fastapi import FastAPI

from app.core import env
from app.interfaces.api.state import ApiState
from app.shared_kernel.infrastructure.resources.database_engine_resource_adapter import (
    DatabaseEngineResourceAdapter,
)
from app.shared_kernel.infrastructure.resources.registry import ResourceRegistry


async def bootstrap_infrastructure(app: FastAPI) -> ResourceRegistry:
    database = DatabaseEngineResourceAdapter(env.DATABASE_SETTINGS)
    registry = ResourceRegistry([database])
    await registry.startup_all()
    ApiState.publish(app, session_factory=database.session_factory)
    return registry
```

For the typed state object and request access, follow the
[typed application state convention](../../fastapi-async-patterns/SKILL.md#typed-application-state-and-request-access).
Dependency factories read from that typed state, never from untyped `app.state` attributes.

When a second interface (a CLI, a worker) needs the same handlers, move the shared wiring
to `app/bootstrap/` as the foundation describes; this bootstrap then keeps only the
FastAPI lifespan and state publishing.

## Modular Monolith

```text
app/
├── interfaces/api/                     # HOST: app factory, middleware, health, auth deps,
│   └── bootstrap/composition.py        #       shared error registration, module mounting
└── modules/<module>/
    ├── bootstrap.py                    # init/resource entry point + register_<module>_api
    └── interfaces/api/
        ├── state.py                    # typed view of the state keys this module publishes
        ├── exceptions.py               # module-specific custom mappings, when needed
        └── v1/{routers,schemas,dependencies}/
```

Each module exposes its HTTP registration from `bootstrap.py`. The host passes the shared
exception register so module mappings join the single registration:

```python
# app/modules/billing/bootstrap.py
from fastapi import FastAPI
from raised.fastapi import FastAPIExceptionRegister


def register_billing_api(
    app: FastAPI, *, errors: FastAPIExceptionRegister, prefix: str = "/api/v1"
) -> None:
    from app.modules.billing.interfaces.api.exceptions import add_billing_error_mappings
    from app.modules.billing.interfaces.api.v1.routers import router

    add_billing_error_mappings(errors)
    app.include_router(router, prefix=prefix)
```

```python
# app/interfaces/api/exceptions/registry.py — host
def register_exception_handlers(app: FastAPI, module_registrations: Sequence[ModuleApi]) -> None:
    errors = FastAPIExceptionRegister(app)
    for exception_type in PROJECT_EXCEPTION_TYPES:
        errors.add_exception(exception_type, map_project_exception)
    for register_module_api in module_registrations:
        register_module_api(app, errors=errors)
    errors.register()          # last: handlers added after register() are ignored
```

- Registration must not open connections, so building the app and its OpenAPI document
  never starts resources.
- Shared authentication dependencies and the error response schema may be reused from the
  host; business schemas, dependency factories, and routes stay in the module.
- A module's typed state view declares only the keys its own bootstrap publishes. Reading
  another module's state key is a hidden cross-module call; see the foundation's
  [deployment overview](../../ddd-hexagonal-python/references/deployment/overview.md#lessons-from-real-projects).

## Microservices

Each service has its own `interfaces/api/` exactly as in the single-service layout.
Request and response schemas a service exposes to other services are part of its published
contract (OpenAPI document or contracts package); consumers never import them as code.
Outbound calls to another service are infrastructure adapters, not interface code.

## Review Checklist

- [ ] `main.py` assembles the app (errors, middleware, routers, lifespan, telemetry gate) and contains no wiring.
- [ ] `interfaces/api/bootstrap/` starts interface-neutral resources through the registry and publishes them into typed state.
- [ ] Constructing the app and its OpenAPI document opens no connection.
- [ ] Versioned business routes live under `v1/`; process routes (health) are unversioned.
- [ ] In a modular monolith, each module mounts its routes and error mappings through `register_<module>_api`; the host calls `errors.register()` once, last.
- [ ] No module reads another module's state keys.
