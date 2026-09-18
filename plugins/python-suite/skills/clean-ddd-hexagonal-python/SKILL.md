---
name: clean-ddd-hexagonal-python
description: Design or refactor Python backends using tactical DDD, CQRS, and strict Hexagonal Architecture. Use for bounded contexts, aggregates, ports, adapters, repositories, application handlers, and cross-context integration; not for simple CRUD or throwaway scripts.
---

# Tactical DDD + Hexagonal Architecture (Python)

Design a domain that can run and be tested without delivery frameworks or concrete
infrastructure. Prefer this approach for business rules, independent contexts, multiple
entry points, and long-lived systems; do not impose it mechanically on simple CRUD.

## Non-Negotiable Boundaries

- Dependencies point inward: interfaces and infrastructure depend on application and
  domain; domain depends on neither framework nor I/O.
- A bounded context owns its model and business logic. Never import another context's
  internal model; use an ID, explicit contract, integration event, or ACL instead.
- Keep the shared kernel deliberately small. It may contain stable, intentionally
  shared technical capabilities and primitives, never convenience “common” code or a
  context's aggregates, repositories, ORM models, or business rules.
- An entity has identity and behavior; a value object is immutable and equal by value.
  An aggregate is a transactional consistency boundary: mutate one aggregate per
  transaction and use events for cross-aggregate consistency.

## Application Edges

- Command and query handlers are the application’s inbound actions. Delivery adapters
  call handlers, never repositories directly.
- Treat `application/ports/` as outbound contracts only. Put aggregate write-repository
  contracts in `domain/repositories/`; put CQRS read-repository contracts in
  `application/ports/read_repositories/`.
- Commands use the write model and a Unit of Work; queries use read models and return
  DTOs. A handler does not expose an entity or value object as its external response.
- Application services orchestrate what happens through abstract contracts.
  Infrastructure adapters implement how a concrete database, broker, SDK, or transport
  is used. Concrete infrastructure classes end in `Adapter`, never `Service`.

## Structural Decisions

When establishing or reviewing a project topology, shared-kernel placement, API
bootstrap, port ownership, infrastructure direction, or runtime provider selection,
read [the structural profile](references/architecture/project-topology.md). It defines
an opinionated context-first layout and the decisions behind it. Apply that layout only
when the project has adopted it; do not infer a project name or package root from an
illustrative tree.

Use `python-syntax` alongside this skill for Python syntax, typing, imports, and naming
outside the architectural `Adapter` rule.

## References

Read only the reference relevant to the decision at hand.

| Decision | Reference |
| --- | --- |
| Package topology, shared kernel, API bootstrap, ports, adapters, or dynamic providers | [Structural profile](references/architecture/project-topology.md) |
| Context boundaries and cross-context integration | [Bounded contexts](references/ddd/bounded-contexts/overview.md), [shared kernel](references/ddd/bounded-contexts/shared-kernel.md), [context mapping](references/ddd/context-mapping.md) |
| Entities, value objects, aggregates, repositories, services, factories, or UoW | [Tactical patterns](references/ddd/tactical-patterns.md) |
| Command/query separation, outbox, projections, sagas, or idempotency | [CQRS events](references/cqrs/events.md), [CQRS implementation](references/cqrs/implementation.md) |
| Layer responsibility or dependency direction | [Layers](references/architecture/layers.md), [Hexagonal architecture](references/architecture/hexagonal.md) |
| Specifications, errors, or tests | [Specifications](references/patterns/specification.md), [errors](references/error-handling/errors.md), [testing](references/testing/strategy.md) |
| Fast design check | [Cheatsheet](references/cheatsheet.md) |

## Review Checklist

- [ ] Dependencies point inward; domain logic is independent of delivery and infrastructure.
- [ ] Aggregate boundaries and transaction scope match invariants; cross-aggregate consistency is explicit.
- [ ] Context-owned models remain local; cross-context integration uses IDs, contracts, events, or an ACL.
- [ ] Handlers, ports, repositories, application services, and adapters have their correct ownership and direction.
- [ ] Concrete infrastructure implementations use the `Adapter` suffix.
- [ ] The relevant routed reference was consulted for each non-trivial architecture decision.
