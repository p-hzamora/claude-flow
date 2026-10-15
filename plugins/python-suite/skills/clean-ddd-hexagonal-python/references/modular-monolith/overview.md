# Decomposable Modular Monolith

Read this when one deployable holds several independent business areas and any of them
may later become its own microservice. It is a profile on top of the skill's core rules,
not a replacement: tactical DDD, CQRS, and hexagonal layering stay exactly as defined in
[tactical patterns](../ddd/tactical-patterns.md) and [layers](../architecture/layers.md).

## When to Use It

| Use | Do not use |
| --- | --- |
| One deployable, several business areas with their own language and lifecycle | A single cohesive domain: use the [single-service topology](../architecture/project-topology.md) |
| Extraction to a service is a plausible future step, not a date | Services already deployed separately: each one adopts the single-service topology |
| The team wants one runtime now and cheap extraction later | Simple CRUD, where modules would only add ceremony |

## Vocabulary

- **Module**: the extraction unit. One `modules/<module>/` folder is one future
  microservice. It holds one or more bounded contexts.
- **Bounded context**: the model boundary defined in
  [bounded contexts](../ddd/bounded-contexts/overview.md). Inside one module, contexts
  may call each other through application contracts.
- **Integration contract**: a publisher-owned, versioned event in
  `modules/<module>/contracts/`. It is the module's Published Language (see
  [context mapping](../ddd/context-mapping.md)).

The rule that drives everything else: **the module boundary is the microservice
boundary.** Anything allowed across modules in the monolith must also work when the two
modules run in different processes.

## Defensive Rules

1. **No imports across modules except `contracts/`.** `modules.billing` may import
   `modules.ordering.contracts`, never `modules.ordering.<context>.domain`,
   `application`, or `infrastructure`.
2. **No shared business objects.** A `Product` in `ordering` and a `Product` in
   `inventory` are different classes. Never put an aggregate, entity, or value object
   in `shared_kernel/`.
3. **Serializable events.** An integration contract carries only primitives that map
   to JSON. See [module communication](module-communication.md#contract-shape).
4. **Consumer-side ACL.** The downstream module translates a contract into its own
   command. Its domain never adapts its design to the upstream contract.
5. **No synchronous cross-module calls.** Not through handlers, repositories, or a
   query contract. Cross-module reads use an opaque ID or a local projection fed by
   events.
6. **Data ownership.** Each module owns its tables or schema. No cross-module foreign
   key, join, or ORM relationship.
7. **Composition at the edge.** The API bootstrap calls one `init_<module>_module(...)`
   per module and knows nothing about individual handlers or subscriptions.

CQRS command, query, and DTO classes stay in their handler's file. `contracts/` is for
events only.

## Reference Map

| Decision | Reference |
| --- | --- |
| Where modules, contracts, bootstrap, and shared kernel live; import rules | [Topology](project-topology.md) |
| Command handler versus event handler, bus ports, ACL consumer, delivery guarantees | [Module communication](module-communication.md) |
| Splitting a module into a service | [Extraction playbook](extraction-playbook.md) |

## Review Checklist

- [ ] The project needs several independent business areas; otherwise the single-service topology is used.
- [ ] Every module boundary is a plausible service boundary.
- [ ] No module imports another module except its `contracts/`.
- [ ] No cross-module synchronous call, foreign key, join, or shared aggregate exists.
