# Decomposable Modular Monolith

Read this when one deployable holds several independent business areas and any of them may
later become its own microservice. It is a profile on top of the foundation, not a
replacement: tactical DDD, CQRS, and hexagonal layering stay exactly as defined in
[tactical patterns](../ddd/tactical-patterns.md) and [layers](../architecture/layers.md).
The [deployment overview](overview.md) compares it with the other shapes.

## When to Use It

| Use | Do not use |
| --- | --- |
| One deployable, several business areas with their own language and lifecycle | A single cohesive domain: use the [single-service topology](../architecture/project-topology.md) |
| Extraction to a service is a plausible future step, not a date | Services already deployed separately: each follows [microservices](microservices.md) |
| The team wants one runtime now and cheap extraction later | Simple CRUD, where modules would only add ceremony |

## Vocabulary

- **Module**: the extraction unit. One `modules/<module>/` folder is one future
  microservice. It owns one or more bounded contexts together with its exceptions,
  interfaces, migrations, and bootstrap.
- **Bounded context**: the model boundary defined in
  [bounded contexts](../ddd/bounded-contexts/overview.md). Inside one module, contexts may
  call each other through application contracts wrapped in an ACL.
- **Integration contract**: a publisher-owned, versioned event in
  `modules/<module>/contracts/`. It is the module's Published Language (see
  [context mapping](../ddd/context-mapping.md)).
- **Host**: the process-level code outside `modules/`: `core/`, shared `exceptions/`,
  `shared_kernel/`, global `migrations/`, and the process concerns of each
  `interfaces/<kind>/`.

The rule that drives everything else: **the module boundary is the microservice
boundary.** Anything allowed across modules in the monolith must also work when the two
modules run in different processes.

## Defensive Rules

1. **No imports across modules except `contracts/`.** `modules.billing` may import
   `modules.ordering.contracts`, never `modules.ordering.<anything else>`.
2. **No shared business objects.** A `Product` in `ordering` and a `Product` in
   `inventory` are different classes. Never put an aggregate, entity, or value object in
   `shared_kernel/`.
3. **Serializable events.** An integration contract carries only JSON-native values. See
   [communication](communication.md#contract-shape).
4. **Consumer-side ACL.** The downstream module translates a contract into its own
   command. Its domain never adapts to the upstream contract.
5. **No synchronous cross-module calls.** Not through handlers, repositories, a query
   contract, or a callable placed on shared framework state. Cross-module reads use an
   opaque ID or a local projection fed by events.
6. **Data ownership.** Each module owns its tables or schema. No cross-module foreign key,
   join, or ORM relationship.
7. **Composition at the edge.** Each host interface's bootstrap calls the public wiring and
   registration entry points in each module's `bootstrap.py`. Each module owns its
   interfaces, exceptions, and migrations; the host knows nothing about individual
   handlers, business schemas, commands, or subscriptions.

## Reference Map

| Decision | Reference |
| --- | --- |
| Where modules, contracts, bootstrap, and shared kernel live; import rules | [Topology](modular-monolith-topology.md) |
| Command handler versus event handler, bus ports, ACL consumer, delivery guarantees | [Communication](communication.md) |
| Splitting a module into a service | [Extraction playbook](extraction-playbook.md) |
| How a module mounts its routes or commands | `ddd-interface-fastapi` / `ddd-interface-cli`, reference `topology-and-bootstrap.md` |

## Review Checklist

- [ ] The project has several independent business areas; otherwise the single-service topology is used.
- [ ] Every module boundary is a plausible service boundary.
- [ ] No module imports another module except its `contracts/`.
- [ ] No cross-module synchronous call, hidden shared-state callable, foreign key, join, or shared aggregate exists.
- [ ] Each module owns its interfaces, custom errors, and migration history; the host only provides shared facilities and invokes public module entry points.
