# FastAPI Observability

Ownership, lifecycle, and testing rules come from the foundation's
[observability skeleton](../../ddd-hexagonal-python/references/observability/skeleton.md).
This reference adds the HTTP-specific instrumentation in `interfaces/api/telemetry.py`; it
reuses the interface-neutral `build_observability_config()` from the shared-kernel wrapper,
which never imports FastAPI.

This example uses the `observability` package API available in the reference
application. Read the target project's installed version and configuration models first.
Preserve its service identity, signal flags, export policy, and excluded URLs; add only
options the project actually supports.

```python
# app/interfaces/api/telemetry.py
from fastapi import FastAPI
from observability.instrumentations.fastapi.config import (
    configure_telemetry as _configure_telemetry,
)
from opentelemetry.sdk.metrics.export import MetricReader
from opentelemetry.sdk.trace.export import SpanExporter
from opentelemetry.trace import TracerProvider
from sqlalchemy.ext.asyncio import AsyncEngine

from app.shared_kernel.infrastructure.telemetry import build_observability_config

HTTP_EXCLUDED_URLS = "/health,/health/live"


def configure_fastapi_telemetry(
    app: FastAPI,
    *,
    engine: AsyncEngine | None = None,
    span_exporter: SpanExporter | None = None,
    metric_reader: MetricReader | None = None,
    set_global_provider: bool = True,
) -> TracerProvider:
    """Delegate HTTP instrumentation while supplying service-owned configuration."""
    config = build_observability_config().model_copy(
        update={"trace_excluded_urls": HTTP_EXCLUDED_URLS}
    )
    return _configure_telemetry(
        app,
        config=config,
        engine=engine,
        span_exporter=span_exporter,
        metric_reader=metric_reader,
        set_global_provider=set_global_provider,
    )
```

`build_observability_config()` is the interface-neutral builder from the foundation. If
the installed `ObservabilityConfig` is not a Pydantic model or takes the excluded URLs
elsewhere, pass them the way that version supports.

In the app factory, after creating the app and registering routes:

```python
if env.OBSERVABILITY_SETTINGS.otel_enabled:
    configure_fastapi_telemetry(app)
```

Pass the database engine only after the lifespan has created it, when database
instrumentation is enabled. Health routes stay excluded from traces.

## Review Checklist

- [ ] HTTP instrumentation lives in `interfaces/api/telemetry.py` on top of the neutral config builder; `main.py` only gates and calls it.
- [ ] Health and liveness routes are excluded from traces.
- [ ] Engine instrumentation happens after the lifespan created the engine.
- [ ] Tests use in-memory exporters or non-global providers.
