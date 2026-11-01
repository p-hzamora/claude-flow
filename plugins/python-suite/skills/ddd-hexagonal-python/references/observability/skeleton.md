# Python DDD Observability Skeleton

Read this when adding or reviewing service telemetry, OpenTelemetry configuration,
logging policy, or instrumentation wiring. Use the project's installed observability
package and inspect its supported API before adapting an example. Do not copy another
service's settings or reimplement exporters, providers, or instrumentors that the package
supplies.

## Ownership

| Piece | Location | May depend on |
| --- | --- | --- |
| Telemetry policy (service identity, signal flags, export policy) | `core/configurations/observability_configuration.py` | pydantic-settings |
| Interface-neutral config builder: settings -> package config object | `shared_kernel/infrastructure/telemetry/__init__.py` | the observability package |
| Interface-specific instrumentation (HTTP server, CLI, worker loop) | `interfaces/<kind>/telemetry.py`, calling the neutral builder | that interface's framework, the observability package |
| Decision to enable | the interface entry point (`main.py`, the CLI root callback) | settings |

The wrapper is an outer technical adapter and imports no delivery framework, so the shared
kernel stays interface-neutral. Domain and application code never import it,
the telemetry SDK, or instrumentors. In a modular monolith, process-wide telemetry belongs
to the host, not to a business module; modules never install global providers.
Module-specific instrumentation, when required, stays in their outer adapters.

The entry point only gates and invokes:

```python
if env.OBSERVABILITY_SETTINGS.otel_enabled:
    configure_<interface>_telemetry(<interface object>)
```

Never construct the package config, exporter endpoints, resource attributes, or
instrumentor lists inline in an entry point. The wrapper owns the settings-to-config
mapping; the observability package owns the reusable setup.

```python
# app/shared_kernel/infrastructure/telemetry/__init__.py — interface-neutral part
from observability import ObservabilityConfig

from app.core import env


def build_observability_config() -> ObservabilityConfig:
    """Build the service identity and telemetry policy from current settings."""
    return ObservabilityConfig(
        service_name=env.LOGGING_SETTINGS.service_name,
        service_version=env.RUNTIME_SETTINGS.app_version,
        environment=env.RUNTIME_SETTINGS.env,
        service_namespace=env.RUNTIME_SETTINGS.service_namespace,
        otlp_export_enabled=env.OBSERVABILITY_SETTINGS.otel_export_enabled,
    )
```

Interface-specific instrumentation lives in the interface skills: `ddd-interface-fastapi`
reference `observability.md` for HTTP; `ddd-interface-cli` reference
`topology-and-bootstrap.md` for logging to stderr and when a short-lived process should
not export at all.

## Lifecycle Rules

- Instrument a database engine only after it exists, at the lifecycle stage that owns it.
- Respect the package's idempotency and shutdown contract: never install global providers
  twice or add a parallel lifecycle system. Exporters and readers close through their
  owning package or lifecycle resource.
- Keep configuration construction free of connections and provider installation.
- Support in-memory exporters and readers and non-global providers when the installed API
  supports them, so tests collect signals without network export or global-state leaks.
- Correlation and trace IDs propagate through every inbound and outbound boundary (HTTP
  headers, message metadata, environment of spawned processes).

## Review Checklist

- [ ] The telemetry wrapper owns service configuration; entry points only gate and invoke it.
- [ ] Domain and application layers do not depend on the wrapper, telemetry SDK, or instrumentors.
- [ ] Configuration preserves current identity, signal flags, export policy, and exclusions.
- [ ] Installed package APIs were checked; reusable instrumentation was delegated, not duplicated.
- [ ] Database instrumentation uses an initialized engine; provider setup and cleanup respect the package lifecycle.
- [ ] Applicable verification checks emitted signals with network export disabled and avoids leaking global providers into other tests.
