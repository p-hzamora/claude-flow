# Extraction Playbook

Use this when a module is to become its own service. If the rules in
[modular monolith](modular-monolith.md) were kept, extraction moves one folder and swaps adapters. Check
the prerequisites first; any failure means the module is not yet extractable, and the
fix belongs in the monolith.

## Prerequisites

- [ ] No import from another module except `modules.<other>.contracts` (run the import check from [topology](modular-monolith-topology.md#enforcing-the-rules)).
- [ ] Module owns its tables or schema; no foreign key, join, or ORM relationship crosses it.
- [ ] No synchronous call into another module; cross-module reads use IDs or local projections.
- [ ] Contracts carry `event_id`, `occurred_at`, and `schema_version`, and contain no `float` money.
- [ ] Consumers are idempotent on `event_id`.
- [ ] An outbox exists for every event the module publishes (required before a broker).
- [ ] The module's tests pass without importing another module's internals.
- [ ] No callable or object reaches the module through shared framework state; everything it receives comes through its public bootstrap parameters.

## Steps

1. **Cut the folder.** Move `modules/<module>/` into a new repository, with the parts of
   `core/` and `shared_kernel/` it uses. The new service adopts the
   [single-service topology](../architecture/project-topology.md) and the
   [microservices](microservices.md) rules: the module's
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
   using the field rules in [module communication](communication.md#contract-shape).
5. **Replace in-process requests.** Any synchronous capability the module still consumes
   becomes a consumer-owned port with an ACL adapter over the network, with timeouts and a
   circuit breaker, or a projection fed by events. See [microservices](microservices.md#synchronous-communication).
6. **Move the data.** Migrate the module's tables or schema to its own database.
   Projections in other modules keep working from events.
7. **Sever the monolith.** Remove the module's entry points from every host interface's
   composition and delete the module folder. Other modules keep consuming through the
   broker, whose published contracts did not change.
8. **Mount its existing interfaces** (API routes, CLI commands) through the module's
   registration entry points in the new host; preserve paths, commands, schemas, error
   responses, exit codes, and auth behaviour. Add new entry points only when extraction
   requirements call for them.

## What Should Not Be Needed

Domain rewrites, handler rewrites, or contract redesign. If one is needed, a defensive
rule was broken inside the monolith; fix the rule violation first and record it.

## Review Checklist

- [ ] Every prerequisite passes before extraction starts.
- [ ] Only the bus adapter, serialization, and composition changed; handlers and domain are untouched.
- [ ] Consumed contracts are versioned and covered by a contract test.
- [ ] The monolith no longer references the extracted module.
- [ ] Module-owned interfaces, errors, and revisions moved with the module; interface compatibility and existing migration stamps were preserved.
