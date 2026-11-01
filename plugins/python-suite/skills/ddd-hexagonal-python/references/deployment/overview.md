# Deployment Shapes: Single Service, Modular Monolith, Microservices

DDD does not depend on how code is deployed. The same bounded contexts, layers, and
tactical patterns run in one process or in many. Read this to choose a shape, and to know
which rules stay the same and which details change when moving between shapes.

| Shape | One deployable holds | Read |
| --- | --- | --- |
| Single service | One cohesive model: one or more bounded contexts that share a release cycle | [Project topology](../architecture/project-topology.md) |
| Modular monolith | Several business areas (modules), each a future service, in one process | [Modular monolith](modular-monolith.md), [its topology](modular-monolith-topology.md) |
| Microservices | One module per deployable, talking over the network | [Microservices](microservices.md) |

Interfaces are orthogonal to the shape. A single service, each module of a modular
monolith, and each microservice may have an API, a CLI, a worker, or several. They follow
the [interface adapter contract](../interfaces/adapter-contract.md) in every shape.

## What Never Changes

| Concern | Rule in every shape |
| --- | --- |
| Model | Entities, value objects, aggregates, domain events, and repositories follow [tactical patterns](../ddd/tactical-patterns.md) |
| Layers | Domain <- application <- infrastructure and interfaces; see [layers](../architecture/layers.md) |
| Context layout | `bounded_context/<context>/{domain,application,infrastructure}` with the same naming |
| Ports and adapters | Handlers are inbound ports; outbound ports are application- or domain-owned; concrete classes end in `Adapter` |
| CQRS | Commands go through aggregates and a Unit of Work; queries use read ports returning DTOs |
| Errors | One [error model](../errors/error-model.md), translated at each interface |
| Context isolation | No context imports another context's internal model; integration uses IDs, contracts, events, or an ACL |
| Composition | One composition root per process; inner layers never import it |

If a refactor to another shape requires changing any of these, a boundary was already
broken. Fix the boundary first.

## What Changes

| Concern | Single service | Modular monolith | Microservices |
| --- | --- | --- | --- |
| Extraction unit | The service | `modules/<module>/` | The service |
| Between contexts in the same unit | Application contracts (synchronous) or events, through an ACL | Same, inside one module | Same, inside one service |
| Between units | n/a | Integration events only, in-process bus | Integration events over a broker; synchronous request/reply only through a consumer-owned port and ACL adapter with resilience |
| Contracts | Context application contracts | `modules/<module>/contracts/` Python package, events only | Versioned, published distribution or JSON Schema owned by the publisher |
| Delivery guarantee | n/a | In-memory bus (level 0); outbox before any broker | Outbox plus broker (level 1) from the start; idempotent consumers; dead-letter queue |
| Data | One database, tables per context | One database, schema or tables per module, no cross-module foreign key | Database per service |
| Migrations | `migrations/` | Global runner; revisions in `modules/<module>/migrations/` | Per service |
| Errors | `exceptions/` | Host bases; module errors in `modules/<module>/exceptions/` | Per service |
| Interfaces | `interfaces/<kind>/` | Host `interfaces/<kind>/` for process concerns; business entry points in `modules/<module>/interfaces/<kind>/` | Per service |
| Composition | `interfaces/<kind>/bootstrap/` (or `bootstrap/` when shared) | Host orders public `modules/<module>/bootstrap.py` entry points | Per service |
| Enforcement | Import contracts between contexts | Import contracts between modules (contracts allowed) plus contexts | Network boundary; contract tests replace import contracts |
| Cross-unit consistency | Transactions inside one aggregate; events between aggregates | Same; eventual between modules | Same; sagas or process managers for multi-service workflows |

## Communication Patterns

| Pattern | Use | Never |
| --- | --- | --- |
| Opaque ID | Only identity is needed | Dereference the ID by importing the owner's repository |
| Application contract (Protocol of a handler) | Synchronous capability between contexts **inside one module or service**; the consumer wraps it in an ACL adapter | Across modules or services |
| Integration event | Notify other units that something happened; feed their projections | Carry entities, value objects, ORM objects, or `float` money |
| Local projection | A unit needs another's data to decide | Query the other unit synchronously at decision time inside a monolith |
| Request/reply over the network | Between microservices when the answer is needed now (pricing quote, authorization) | Without timeouts, a circuit breaker, a consumer-owned port, and error translation |
| Saga / process manager | A business process spanning units with compensations | A distributed transaction or two-phase commit |

Details and code: [communication](communication.md).

## Choosing

- Start with a **single service** for one cohesive domain, even with several contexts.
- Choose a **modular monolith** when the product has several business areas with their
  own language and lifecycle, and one deployable is still simpler to run. Each module
  boundary must be a plausible service boundary.
- Extract a **microservice** when a module needs independent scaling, release cadence,
  ownership, or a different runtime. Follow the [extraction playbook](extraction-playbook.md).
- Do not start with microservices to "be ready". A modular monolith with enforced
  boundaries keeps that option open at a fraction of the cost.

## Lessons From Real Projects

- **Hidden shared state.** Passing a callable from one module to another through a string
  key on framework state (`app.state.some_provider`) plus startup order is a synchronous
  cross-module call with an invisible contract. Replace it with an event-fed projection.
  Until then, record it as an extraction blocker and give the consumer its own port and
  ACL adapter.
- **Independence contracts and `contracts/`.** An import-linter `independence` contract
  between modules needs `ignore_imports` for `modules.*.contracts`, or the first legal
  contract import breaks the check.
- **Merging to legalize coupling.** Merging two contexts into one module makes their
  synchronous calls legal, but they become one extraction unit. Make that choice
  deliberately and record it.
- **Promised but missing pieces.** An empty `contracts/`, an unimplemented bus, or ports
  without adapters mean the module is not extractable yet. The extraction prerequisites
  check for them.

## Review Checklist

- [ ] The chosen shape is justified by the business areas and operational needs, not by anticipation.
- [ ] Everything in "What Never Changes" holds; moving between shapes changes only the "What Changes" rows.
- [ ] Communication between units uses the pattern the shape allows, with no hidden shared state.
- [ ] Data ownership matches the shape; no foreign key, join, or ORM relationship crosses a unit.
- [ ] Boundaries are enforced mechanically (import contracts in a monolith, contract tests between services).
