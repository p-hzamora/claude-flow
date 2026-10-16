# Extraction Playbook

Use this when a module is to become its own service. If the rules in
[overview](overview.md) were kept, extraction moves one folder and swaps adapters. Check
the prerequisites first; any failure means the module is not yet extractable, and the
fix belongs in the monolith.

## Prerequisites

- [ ] No import from another module except `modules.<other>.contracts` (run the import check from [topology](project-topology.md)).
- [ ] Module owns its tables or schema; no foreign key, join, or ORM relationship crosses it.
- [ ] No synchronous call into another module; cross-module reads use IDs or local projections.
- [ ] Contracts carry `event_id`, `occurred_at`, and `schema_version`, and contain no `float` money.
- [ ] Consumers are idempotent on `event_id`.
- [ ] An outbox exists for every event the module publishes (required before a broker).
- [ ] The module's tests pass without importing another module's internals.

## Steps

1. **Cut the folder.** Move `modules/<module>/` into a new repository, with the parts of
   `core/` and `shared_kernel/` it uses. The new service adopts the
   [single-service topology](../architecture/project-topology.md): the module's
   `bounded_context/` folders become its contexts. Move its existing `interfaces/`,
   `exceptions/`, and `migrations/` with them; do not reconstruct these from global
   host folders. Reconnect module migration metadata and revision locations to the
   new service's Alembic runner without changing the revision graph.
2. **Resolve the contracts it consumes.** Publish each upstream `contracts/` package as
   a versioned package, or vendor a copy, and add a contract test against the JSON
   schema. After extraction, a copied schema is acceptable because transport is now
   JSON rather than a Python import.
3. **Swap the bus adapter.** Replace `InMemoryEventBusAdapter` in composition with a
   broker adapter (`RabbitMqPublisherAdapter`, `KafkaPublisherAdapter`) and a consumer
   adapter. Handlers, contracts, and domain code do not change.
   Only the composition changes. Illustrative shape, with `billing` extracted:

   ```python
   # monolith composition: ordering now publishes to the broker
   init_ordering_module(publisher=RabbitMqPublisherAdapter(broker_url), session_factory=sf)

   # billing service composition: the same init function, a broker subscriber
   init_billing_module(subscriber=RabbitMqConsumerAdapter(broker_url), session_factory=sf)
   ```

   `init_billing_module` and every handler are byte-for-byte unchanged.
4. **Serialize contracts.** Convert the `FrozenObject` to JSON (`model_dump(mode="json")`) and back
   (`model_validate`) at the adapter,
   using the field rules in [module communication](module-communication.md#contract-shape).
5. **Move the data.** Migrate the module's tables or schema to its own database.
   Projections in other modules keep working from events.
6. **Sever the monolith.** Remove `init_<module>_module(...)` from the monolith's API
   composition and delete the module folder. Other modules keep consuming through the
   broker, whose published contracts did not change.
7. **Mount its existing HTTP API** through the module's registration entry point in
   the new host; preserve paths, schemas, error responses, and auth behavior. Add new
   endpoints only when extraction requirements call for them.

## What Should Not Be Needed

Domain rewrites, handler rewrites, or contract redesign. If one is needed, a defensive
rule was broken inside the monolith; fix the rule violation first and record it.

## Review Checklist

- [ ] Every prerequisite passes before extraction starts.
- [ ] Only the bus adapter, serialization, and composition changed; handlers and domain are untouched.
- [ ] Consumed contracts are versioned and covered by a contract test.
- [ ] The monolith no longer references the extracted module.
- [ ] Module-owned HTTP adapters, errors, and revisions moved with the module; API compatibility and existing migration stamps were preserved.
