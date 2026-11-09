---
name: ddd-hexagonal-python
description: Framework-agnostic foundation for Python applications built with tactical DDD, CQRS, and strict Hexagonal Architecture. Use for bounded contexts, aggregates, ports, adapters, repositories, application handlers, error model, project topology, composition roots, and single-service, modular-monolith, or microservice layouts. Pair with an interface skill (ddd-interface-fastapi, ddd-interface-cli) for delivery code; not for simple CRUD or throwaway scripts.
---

# Tactical DDD + Hexagonal Architecture (Python foundation)

Design a domain that can run and be tested without delivery frameworks or concrete
infrastructure. This skill owns everything inside the hexagon plus the rules every
interface must follow. It does not depend on FastAPI, Typer, or any other delivery
framework. Prefer this approach for business rules, independent contexts, several entry
points, and long-lived systems; do not impose it mechanically on simple CRUD.

## Skill Family

| Skill | Owns |
| --- | --- |
| `ddd-hexagonal-python` (this) | Domain, application, infrastructure, shared kernel, error model, topology, composition root, deployment shapes, the interface adapter contract |
| `ddd-interface-fastapi` | HTTP delivery with FastAPI: routers, schemas, dependencies, `raised` RFC 9457 errors, HTTP tests |
| `ddd-interface-cli` | Command-line delivery with Typer: commands, output contract, exit codes, agent and hook integration, CLI tests |
| `ddd-interface-<kind>` | Each future interface (worker, consumer, gRPC, MCP), created per the [adapter contract](references/interfaces/adapter-contract.md) |

When work touches an interface, load this skill and the matching interface skill. The
interface skill never restates these rules; when both seem to apply, this skill wins
inside the hexagon and the interface skill wins at the edge. Use `python-syntax` for
Python syntax, typing, imports, and naming outside the architectural rules here.

## Non-Negotiable Boundaries

- Dependencies point inward: interfaces and infrastructure depend on application and
  domain; the domain depends on neither a framework nor I/O.
- A bounded context owns its model and business logic. Never import another context's
  internal model; use an ID, explicit contract, integration event, or ACL instead.
- Keep the shared kernel deliberately small: stable, intentionally shared technical
  capabilities and primitives, never convenience "common" code or a context's aggregates,
  repositories, ORM models, or business rules.
- An entity has identity and behaviour; a value object is immutable and equal by value. An
  aggregate is a transactional consistency boundary: mutate one aggregate per transaction
  and use events for cross-aggregate consistency.
- Expected failures raise typed project errors rooted in `raised.AppException`; inner
  layers never know about status codes, exit codes, or responses.

## Application Edges

- Command and query handlers are the application's inbound actions. Interfaces call
  handlers they receive from the composition root, never repositories or adapters.
- `application/ports/` holds outbound contracts only. Aggregate write-repository contracts
  live in `domain/repositories/`; CQRS read-repository contracts in
  `application/ports/read_repositories/`.
- Commands use the write model and a Unit of Work; queries use read models and return DTOs.
  A handler never exposes an entity or value object; interfaces build their own output
  models from DTOs.
- Application services orchestrate what happens through abstract contracts.
  Infrastructure adapters implement how a concrete database, broker, SDK, or transport is
  used. Concrete infrastructure classes end in `Adapter`, never `Service`.
- One composition root per process chooses concrete adapters. Process resources are
  interface-neutral.

## Deployment Shapes

The same contexts and layers run as a single service, as modules of a decomposable modular
monolith (the module boundary is the microservice boundary), or as microservices. Read the
[deployment overview](references/deployment/overview.md) first: it lists what never changes
and what differs between the shapes, and routes to each shape's topology.

## References

Read only the reference relevant to the decision at hand.

| Decision | Reference |
| --- | --- |
| Package layout, file and class naming, ports and adapters placement, settings policy, security contracts | [Project topology](references/architecture/project-topology.md) |
| Where wiring happens, process resources, sync/async bridging, a second interface | [Composition root](references/architecture/composition-root.md) |
| Layer responsibility or dependency direction | [Layers](references/architecture/layers.md), [Hexagonal architecture](references/architecture/hexagonal.md) |
| Exception hierarchy, error codes, messages, translating foreign errors | [Error model](references/errors/error-model.md) |
| What any interface must do; adding a new interface skill | [Interface adapter contract](references/interfaces/adapter-contract.md) |
| Single service vs modular monolith vs microservices | [Deployment overview](references/deployment/overview.md) |
| Modular monolith rules, layout, and import contracts | [Modular monolith](references/deployment/modular-monolith.md), [its topology](references/deployment/modular-monolith-topology.md) |
| Separately deployed services: contracts, sync and async calls, sagas | [Microservices](references/deployment/microservices.md) |
| Integration events, bus ports, ACL consumers, delivery guarantees | [Communication](references/deployment/communication.md) |
| Splitting a module into a service | [Extraction playbook](references/deployment/extraction-playbook.md) |
| Context boundaries and cross-context integration | [Bounded contexts](references/ddd/bounded-contexts/overview.md), [shared kernel](references/ddd/bounded-contexts/shared-kernel.md), [context mapping](references/ddd/context-mapping.md) |
| Entities, value objects, aggregates, repositories, services, factories, or UoW | [Tactical patterns](references/ddd/tactical-patterns.md) |
| Command/query separation, outbox, projections, sagas, or idempotency | [CQRS implementation](references/cqrs/implementation.md), [CQRS events](references/cqrs/events.md) |
| Specifications | [Specifications](references/patterns/specification.md) |
| Test strategy and architecture tests | [Testing](references/testing/strategy.md) |
| Telemetry ownership and lifecycle | [Observability skeleton](references/observability/skeleton.md) |
| Fast design check | [Cheatsheet](references/cheatsheet.md) |

## Review Checklist

- [ ] Dependencies point inward; domain logic is independent of delivery and infrastructure.
- [ ] Aggregate boundaries and transaction scope match invariants; cross-aggregate consistency is explicit.
- [ ] Context-owned models remain local; cross-context integration uses IDs, contracts, events, or an ACL.
- [ ] Handlers, ports, repositories, application services, and adapters have their correct ownership and direction; handlers return DTOs.
- [ ] Concrete infrastructure implementations use the `Adapter` suffix.
- [ ] Mappers only cast; rules and application policy sit in application services, business rules in the domain (entity, domain service, or specification); no `models/` folder exists in `domain/` or `application/` ([placement rules](references/architecture/project-topology.md#placing-non-entity-code)).
- [ ] Expected failures raise typed project errors; no inner layer imports a delivery framework or its exception types.
- [ ] One composition root per process; interfaces call handlers only; process resources take no framework object.
- [ ] Interface code satisfies the adapter contract and its interface skill's checklist.
- [ ] The deployment shape's rules hold: in a modular monolith, modules import only another module's `contracts/`, communicate by events, and own their data, interfaces, exceptions, and migrations; between microservices, contracts are versioned artifacts and synchronous calls go through a consumer-owned port and ACL adapter.
- [ ] When Python settings are changed, shared configuration policies have one owner and intentional overrides and inherited behaviour are verified.
- [ ] When telemetry changes, the telemetry wrapper owns configuration and entry points only gate and invoke it.
- [ ] The relevant routed reference was consulted for each non-trivial architecture decision.
