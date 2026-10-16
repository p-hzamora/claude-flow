# Python DDD Observability Skeleton

Read this when adding or reviewing service telemetry, OpenTelemetry configuration, or
instrumentation wiring. Use the project's installed observability package and inspect
its supported API before adapting the example; do not copy another service's settings
or reimplement exporters, providers, or instrumentors supplied by that package.

## Ownership

Keep service-specific configuration and instrumentation delegation in
`shared_kernel/infrastructure/telemetry/__init__.py`. It is an outer technical adapter,
so it may depend on FastAPI, SQLAlchemy, and the telemetry SDK. Domain and application
code must not import this wrapper or those instrumentation dependencies.

```text
app/
├── main.py                                    # checks enabled flag, calls wrapper
├── core/settings/observability_settings.py    # environment-backed telemetry policy
└── shared_kernel/infrastructure/telemetry/
    └── __init__.py                            # builds config and delegates setup
```

Paths illustrate the adopted DDD profile; preserve the project's actual package root.
For a project with an established single-service `infrastructure/telemetry/` package,
keep that equivalent location. In a modular monolith, process-wide telemetry belongs
to the shared host, not to a business module. Modules do not each install global
providers. Module-specific instrumentation, when required, stays in its outer adapters.

`main.py` owns the decision to enable telemetry and calls `configure_telemetry(app)`.
Do not construct `ObservabilityConfig`, exporter endpoints, resource attributes, or
instrumentor lists inline in `main.py`. The wrapper owns the settings-to-config mapping;
the observability package owns the reusable setup.

## Service Wrapper Example

This example uses the `observability` package API and settings available in the
reference application. Read the target project's installed version and configuration
models first. Preserve its service identity, signal flags, export policy, and excluded
URLs; add only options that the project actually supports.

```python
"""Bind the observability package to the service's settings."""

from fastapi import FastAPI
from observability import ObservabilityConfig
from observability.instrumentations.fastapi.config import (
    configure_telemetry as _configure_telemetry,
)
from opentelemetry.sdk.metrics.export import MetricReader
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.trace import TracerProvider
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core import env


def build_observability_config() -> ObservabilityConfig:
    """Build the service identity and telemetry policy from current settings."""
    return ObservabilityConfig(
        service_name=env.LOGGING_SETTINGS.service_name,
        service_version=env.RUNTIME_SETTINGS.app_version,
        environment=env.RUNTIME_SETTINGS.env,
        service_namespace=env.RUNTIME_SETTINGS.service_namespace,
        trace_excluded_urls="/health,/health/live",
        otlp_export_enabled=env.OBSERVABILITY_SETTINGS.otel_export_enabled,
    )


def configure_telemetry(
    app: FastAPI,
    *,
    engine: AsyncEngine | None = None,
    span_exporter: SpanExporter | None = None,
    metric_reader: MetricReader | None = None,
    set_global_provider: bool = True,
) -> TracerProvider:
    """Delegate instrumentation while supplying service-owned configuration."""
    return _configure_telemetry(
        app,
        config=build_observability_config(),
        engine=engine,
        span_exporter=span_exporter,
        metric_reader=metric_reader,
        set_global_provider=set_global_provider,
    )


__all__ = ["build_observability_config", "configure_telemetry"]
```

Inside the app factory, after creating the application and registering routes:

```python
if env.OBSERVABILITY_SETTINGS.otel_enabled:
    configure_telemetry(app)
```

Import that function from the service wrapper. If the project owns an async database
engine and enables database instrumentation, pass the engine only after it exists at
the appropriate lifecycle stage. Preserve the package's idempotency and shutdown
contract; do not install global providers twice or add a parallel lifecycle system.
Exporters and readers must close through their owning package or lifecycle resource.

Keep configuration construction free of connections and provider installation. Support
in-memory exporters/readers and non-global providers when the installed API supports
them, so verification can collect signals without network export or global test-state
pollution. Forward additional supported signal options only when needed by the project.

## Review Checklist

- [ ] The telemetry wrapper owns service configuration; `main.py` only gates and invokes it.
- [ ] Domain/application layers do not depend on the wrapper, telemetry SDK, or instrumentors.
- [ ] Configuration preserves current identity, signal flags, export policy, and route exclusions.
- [ ] Installed package APIs were checked; reusable instrumentation was delegated, not duplicated.
- [ ] Database instrumentation uses an initialized engine; provider setup and cleanup respect the package lifecycle.
- [ ] Applicable verification checks emitted signals and exclusions with network export disabled and avoids leaking global providers into other tests.
