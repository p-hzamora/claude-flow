# Context-First Organization and Shared Kernel

Read this when a system has multiple **genuine** bounded contexts and you must decide where code
belongs, what may be shared, or how contexts integrate. It is a decision guide, not a mandatory
folder template.

## Start With the Model, Not the Tree

Use a bounded context when the business language, ownership, consistency boundary, or lifecycle
is genuinely distinct. A different noun, API resource, CLI command group, database table, or
Python module alone is not enough.

When contexts are genuine, make each context the primary home of its domain model and
the application and infrastructure code that serves it. For the skill's canonical
context-first topology, read [the structural profile](../../architecture/project-topology.md);
this guide intentionally does not duplicate that layout.

Add a package only when it has an immediate, coherent responsibility. Within a context, split aggregates, entities, value
objects, enums, events, repositories, and domain services into concise purpose-based modules when
that improves navigation; do not accumulate an unrelated "models" module or empty tactical
folders merely to match a diagram.

## Avoid Duplicate Technical Roots

Do not place context packages alongside global `domain/`, `application/`, and
`infrastructure/` packages that contain those same contexts' business code. That
produces two competing boundaries and makes ownership ambiguous.

Global outer packages remain useful when their responsibility is genuinely service-wide:

| Appropriate outside a context | Keep inside the owning context |
| --- | --- |
| Composition and process startup: `interfaces/<kind>/bootstrap/`, or `bootstrap/` once two interfaces share wiring | Aggregates, entities, value objects, and domain services |
| Delivery mechanisms in `interfaces/<kind>/`: API, CLI, worker, or consumer | Commands, queries, handlers, DTOs, and assemblers |
| Configuration in `core/`, shared exception bases in `exceptions/`, tiny primitives in `utils/` | Repository contracts and persistence adapters for that context |
| Versioned public integration contracts with explicit ownership (`modules/<module>/contracts/` in a modular monolith) | ORM models, read models, and context-specific mappers |

These are the names of the [structural profile](../../architecture/project-topology.md).
A project with established names for the same outer responsibilities keeps them; DDD does
not require a particular folder name.

## Keep the Shared Kernel Deliberately Small

In classic DDD a shared kernel is a subset of the domain model that two teams agree to
share. This skill is stricter: `shared_kernel/` holds **technical capabilities and generic
primitives** whose coupling every context accepts, never one context's business concepts.
Prefer small duplication to a shared abstraction that changes whenever one context changes.

| May belong in `shared_kernel/` when genuinely stable | Must remain context-local |
| --- | --- |
| Domain base abstractions established by the project (`Entity`, `AggregateRoot`, `ValueObject`, `DomainEvent`, the specification base) | Aggregate roots, entities, and value objects that express one context's language |
| A genuine identity primitive whose business meaning is explicit and agreed | Repository contracts, ORM models, persistence mappers, and read models |
| Technical ports and adapters: process resources, event bus, security validation, telemetry | Context-specific business rules, domain services, commands, queries, or handlers |
| Application security DTOs shared by every context | A convenience `common` or `helpers` package used as a dumping ground |

`utils/` and `core/` are not dumping grounds either: `utils/` holds tiny technical
primitives such as `FrozenObject`, and `core/` holds configuration only.

Do not extract an abstraction merely because two contexts currently have similar code. Extract it
only when its meaning, owners, release cadence, and compatibility commitment are genuinely shared.
If those questions have no clear answer, duplicate the small piece and let each context evolve.

When a project provides aggregate-root or entity base abstractions that are architecturally
appropriate, use them consistently. Do not replace them with ad-hoc local bases merely to avoid a
dependency. That does not authorize moving aggregate-specific behavior into the shared kernel.

### What the Shared Kernel Holds in This Profile

Placement follows the [structural profile](../../architecture/project-topology.md); this
list explains why each item qualifies.

| Item | Location | Why it is shared |
| --- | --- | --- |
| `FrozenObject` | `utils/` (not `shared_kernel/`) | A technical primitive used by value objects, events, DTOs, and contracts in every layer |
| Domain bases | `shared_kernel/domain/{entities,value_objects,events}/` | Identity, immutability, and event-recording semantics are the same everywhere |
| `IHandler` protocol | `shared_kernel/application/handlers/` | One handler shape for every context and every interface |
| `IResource` port | `shared_kernel/application/ports/resources/` | Interface-neutral lifecycle of process resources (see the [composition root](../../architecture/composition-root.md#process-resources)) |
| Resource registry | `shared_kernel/infrastructure/resources/` | Starts and stops resources in order for any interface |
| Event-bus ports | `shared_kernel/application/ports/event_bus/` (`IEventPublisher`, `IEventSubscriber`) | Contexts and modules publish and subscribe without knowing the transport |
| `InMemoryEventBusAdapter` | `shared_kernel/infrastructure/event_bus/` | Level-0 transport, replaced by a broker adapter at composition time (see [communication](../../deployment/communication.md#bus-ports)) |
| Security DTOs and token-validator port | `shared_kernel/application/security/dtos/`, `shared_kernel/application/ports/security/` | Authentication context is an application contract; how credentials arrive is an interface concern |
| Security validators | `shared_kernel/infrastructure/security/` | Map identity-provider results to the local DTOs |
| Telemetry wrapper | `shared_kernel/infrastructure/telemetry/` | Process-wide configuration; see the [observability skeleton](../../observability/skeleton.md) |

None of these imports a delivery framework. A resource never takes a framework object
such as an application instance; publishing resources into framework state is the
interface's job.

### Ownership per Deployment Shape

- **Single service:** the shared kernel is part of the service and changes with it.
- **Modular monolith:** the shared kernel is **host-owned technical code**, outside
  `modules/`. Modules depend on it; it never imports a module and never holds a module's
  aggregates, events, or business rules (see the
  [modular monolith topology](../../deployment/modular-monolith-topology.md)).
- **Microservices:** there is no shared kernel across services. What was technical becomes
  **versioned technical libraries** (`libs/` or an internal index: exception bases, the
  observability wrapper, resource lifecycle). A library that contains an aggregate, a
  business rule, or a context's DTOs is hidden coupling, not a library (see
  [microservices](../../deployment/microservices.md)). Each service keeps its own
  application security DTOs.

If something in the shared kernel could not become a business-free library when a module
is extracted, it does not belong there.

## Cross-Context Boundaries

Never import another context's internal aggregate or entity. The same real-world concept may have
a different model in each context, and an import silently turns that implementation detail into a
shared contract.

Choose an explicit boundary instead, as the
[communication patterns](../../deployment/overview.md#communication-patterns) allow for
the deployment shape:

- Pass a context-local ID or reference when only identity is needed.
- Consume an explicit public application contract for a synchronous capability, only
  between contexts inside one module or service, wrapped in a consumer-owned port and ACL
  adapter.
- Publish and consume a versioned integration event across modules or services, and build
  a local projection from it when another unit's data is needed to decide.
- Between microservices only, call the upstream over the network through a consumer-owned
  port and an ACL adapter with timeouts and a circuit breaker.
- Use an anti-corruption layer to translate an external or upstream model into the local model.

Integration contracts are not domain entities. Keep integration messages, interface output
models (HTTP schemas, CLI responses), DTOs, persistence models, read models, and domain
models distinct even when their fields look similar. Worked examples are in
[context mapping](../context-mapping.md).

## Ports Belong Where Their Meaning Lives

Inbound and outbound describe dependency roles, not compulsory folder names.

- Command and query handlers express inbound application capabilities; they do not need
  an `inbound/` folder solely for terminology.
- A write repository interface is an outbound port, but it properly lives in
  `domain/repositories/` because it expresses collection access for an aggregate and
  protects its invariants. CQRS read ports live in `application/ports/read_repositories/`.
- A Unit of Work is outbound transaction coordination owned by the application boundary:
  `application/ports/transactions/i_<context>_unit_of_work.py`. Other outbound capabilities
  are grouped by capability: `application/ports/<capability>/i_<capability>.py`.
- Infrastructure implements outbound ports, in classes ending in `Adapter`. It must not pull
  an aggregate's business rules out of its context to make the package tree look symmetrical.
- A port used by every context (resources, event bus, security) lives in
  `shared_kernel/application/ports/<capability>/`; a port used by one context stays in it.

Choose the location that makes the port's business meaning and dependency direction easiest to
understand. Do not relocate a semantically clear interface just to satisfy a generic folder scheme.

## Review Checklist

- [ ] Each context represents a real model boundary, not a technical partition.
- [ ] Context-owned business code has one primary home; duplicate global technical roots do not
      compete with it.
- [ ] The shared kernel has named owners and holds only stable technical capabilities and
      generic primitives: domain bases, `IResource` and the resource registry, event-bus ports
      and adapter, security DTOs and validator port, telemetry.
- [ ] `FrozenObject` lives in `utils/`; `utils/` and `core/` are not dumping grounds.
- [ ] Nothing in the shared kernel imports a delivery framework, a context, or a module.
- [ ] In a modular monolith the shared kernel is host-owned; between microservices it exists
      only as versioned technical libraries with no business code.
- [ ] No context imports another context's internal domain model.
- [ ] Cross-context communication uses the mechanism the deployment shape allows: IDs,
      application contracts inside one module or service, integration events, projections,
      or network request/reply between microservices, each behind an ACL.
- [ ] Packages are cohesive and concrete; no empty folders exist only to satisfy a diagram.
- [ ] Port placement follows semantic ownership and dependency direction.
