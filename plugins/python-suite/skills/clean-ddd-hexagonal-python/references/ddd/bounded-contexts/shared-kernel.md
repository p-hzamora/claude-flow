# Context-First Organization and Shared Kernel

Read this when a system has multiple **genuine** bounded contexts and you must decide where code
belongs, what may be shared, or how contexts integrate. It is a decision guide, not a mandatory
folder template.

## Start With the Model, Not the Tree

Use a bounded context when the business language, ownership, consistency boundary, or lifecycle
is genuinely distinct. A different noun, REST resource, database table, or Python module alone is
not enough.

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
| Application composition, dependency wiring, and process startup | Aggregates, entities, value objects, and domain services |
| Delivery mechanisms such as API, CLI, worker, or consumer setup | Commands, queries, handlers, DTOs, and assemblers |
| Shared operational configuration and observability wiring | Repository contracts and persistence adapters for that context |
| Versioned public integration contracts where explicitly owned | ORM models, read models, and context-specific mappers |

Use names such as `bootstrap`, `delivery`, or `interfaces` only when they clarify that outer
responsibility. DDD does not require a particular folder name.

## Keep the Shared Kernel Deliberately Small

A shared kernel is an explicit agreement between contexts. Its contents are stable, intentionally
shared concepts whose coupling both owners accept. Prefer small duplication to a shared abstraction
that changes whenever one context changes.

| May belong in `shared_kernel/` when genuinely stable | Must remain context-local |
| --- | --- |
| Generic domain primitives and base abstractions already established by the project | Aggregate roots, entities, and value objects that express one context's language |
| Compatibility façades maintained as a deliberate shared contract | Repository contracts, ORM models, persistence mappers, and read models |
| Narrow cross-context identifiers or integration-message primitives with clear ownership | Context-specific business rules, domain services, commands, queries, or handlers |
| Shared technical policies with no hidden business meaning | Convenience `common`, `core`, or `utils` dumping grounds |

Do not extract an abstraction merely because two contexts currently have similar code. Extract it
only when its meaning, owners, release cadence, and compatibility commitment are genuinely shared.
If those questions have no clear answer, duplicate the small piece and let each context evolve.

When a project provides aggregate-root or entity base abstractions that are architecturally
appropriate, use them consistently. Do not replace them with ad-hoc local bases merely to avoid a
dependency. That does not authorize moving aggregate-specific behavior into the shared kernel.

## Cross-Context Boundaries

Never import another context's internal aggregate or entity. The same real-world concept may have
a different model in each context, and an import silently turns that implementation detail into a
shared contract.

Choose an explicit boundary instead:

- Pass a context-local ID or reference when only identity is needed.
- Consume an explicit public application contract for a synchronous capability.
- Publish and consume a versioned integration event for asynchronous integration.
- Use an anti-corruption layer to translate an external or upstream model into the local model.

Integration contracts are not domain entities. Keep integration messages, API DTOs, persistence
models, read models, and domain models distinct even when their fields look similar.

## Ports Belong Where Their Meaning Lives

Inbound and outbound describe dependency roles, not compulsory folder names.

- Command and query handlers commonly express inbound application capabilities; they do not need
  an `inbound/` folder solely for terminology.
- A repository interface is an outbound port, but it may properly live in
  `domain/repositories` when it expresses collection access for an aggregate.
- A Unit of Work is outbound transaction coordination owned by the application boundary. Generic
  external capabilities without a more semantic home may live in `application/ports/outbound`.
- Infrastructure implements outbound ports. It must not pull an aggregate's business rules out of
  its context to make the package tree look symmetrical.

Choose the location that makes the port's business meaning and dependency direction easiest to
understand. Do not relocate a semantically clear interface just to satisfy a generic folder scheme.

## Review Checklist

- [ ] Each context represents a real model boundary, not a technical partition.
- [ ] Context-owned business code has one primary home; duplicate global technical roots do not
      compete with it.
- [ ] The shared kernel has named owners and intentionally stable contents.
- [ ] No context imports another context's internal domain model.
- [ ] Cross-context communication uses IDs, explicit contracts, integration events, or an ACL.
- [ ] Packages are cohesive and concrete; no empty folders exist only to satisfy a diagram.
- [ ] Port placement follows semantic ownership and dependency direction.
