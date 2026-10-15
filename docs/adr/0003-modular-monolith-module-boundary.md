# Module boundary is the microservice boundary in the modular monolith profile

`clean-ddd-hexagonal-python` gained a decomposable modular monolith profile
(`references/modular-monolith/`). A **module** (`modules/<module>/`, one or more bounded
contexts) is the extraction unit. Modules interact only through publisher-owned
integration events in `modules/<module>/contracts/`; consumers import that package and
nothing else from the publisher. Synchronous cross-module calls, query contracts,
foreign keys, and joins are forbidden; cross-module reads use an opaque ID or a local
projection fed by events. CQRS command, query, and DTO classes stay in their handler's
file, so `contracts/` holds events only.

**Considered:** each consumer redeclaring its own copy of the event class (avoids any
import between modules, but duplicates the schema and lets copies drift; accepted only
after extraction, guarded by a contract test). Events in `shared_kernel/` (rejected: the
kernel stays small). The source handoff's `float` money and a global bus singleton were
replaced by decimal strings and an injected `IEventPublisher`.

**Consequences:** a consumer that needs another module's data must keep a projection,
which adds eventual consistency. An in-memory bus loses events on a crash between commit
and publish; an outbox is mandatory before any broker adapter.
