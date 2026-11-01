# Microservices

Read this when contexts or modules run as separately deployed services. Each service is a
small single-service application: inside it, the [project topology](../architecture/project-topology.md)
applies unchanged. This file covers only what crossing a network adds. For what stays the
same, see the [deployment overview](overview.md).

## Repository Layout

Either one repository per service, or a monorepo with one root per service. Never a shared
`src/` imported by several services.

```text
services/
├── ordering/                      # a complete single-service project
│   ├── app/                       # project topology, unchanged
│   ├── contracts/                 # optional: published separately as ordering-contracts
│   ├── tests/
│   └── pyproject.toml
├── billing/
│   └── ...
└── libs/                          # technical packages only: raised, observability, ...
```

`libs/` (or an internal package index) holds technical packages with no business meaning.
A package that contains an aggregate, a business rule, or a context's DTOs is not a shared
library; it is hidden coupling.

## Contracts

- The publisher owns its contracts: integration events and, when it exposes them, request
  and response schemas of its synchronous API.
- Publish them as a versioned distribution (`ordering-contracts==2.1.0`) or as JSON Schema
  / OpenAPI documents. A consumer depends on that artifact, never on the publisher's code.
- Contracts follow the [contract shape](communication.md#contract-shape): JSON-native
  fields, `event_id`, `occurred_at`, `schema_version`, no `float` money.
- Additive changes are minor versions. A breaking change is a new event type or a new
  `schema_version`, published next to the old one until every consumer has moved.
- Consumers run a contract test against the published schema in CI.

## Asynchronous Communication

- Publish through a transactional outbox: the event row is written in the same
  transaction as the state change, and a relay publishes it to the broker. A service never
  publishes to a broker inside a request without one.
- Consumers are idempotent on `event_id` and acknowledge only after the local transaction
  commits.
- Failures go to retry with back-off, then to a dead-letter queue with an alert. Use the
  error model's status hint: 503-class or `InfrastructureException` retries; 4xx-class
  dead-letters immediately.
- The consumer's handler is an ACL: it maps the contract to a local command. Its placement
  is `application/handlers/events/`; the broker driver that receives messages is an
  inbound adapter in `infrastructure/inbound/consumers/` (context-specific) or the process
  loop of a worker interface (`interfaces/worker/`).

## Synchronous Communication

Allowed between services when the caller needs an answer to continue, and only like this:

1. The consumer declares the capability it needs as its own port:
   `application/ports/<capability>/i_<capability>.py`, returning its own DTOs.
2. An adapter implements it: `infrastructure/outbound/<upstream>/<upstream>_<capability>_adapter.py`.
   It calls the upstream API, translates its schemas into the consumer's DTOs, and
   translates its errors into the consumer's `InfrastructureException` subclasses. This
   adapter is the ACL.
3. The adapter sets timeouts, retries only idempotent calls, and wraps calls in a circuit
   breaker (`resilient`), raising a typed 503-class error when open.
4. Prefer a local projection fed by events when the data changes rarely or the call sits on
   a hot path.

Never share a database, read another service's tables, or join across services.

## Workflows Across Services

There is no distributed transaction. A business process that spans services is a saga:

- **Choreography**: each service reacts to events and emits its own. Fine for short
  chains with few branches.
- **Orchestration**: a process manager (an aggregate in the owning service) tracks state,
  sends commands, and issues compensations. Use it when steps branch or compensate.

Every step and compensation is idempotent.

## Cross-Cutting Concerns per Service

- Each service owns its exceptions, settings, migrations, and interfaces.
- Correlation and trace IDs propagate through HTTP headers and message metadata. The
  telemetry wrapper of each service configures it (see the
  [observability skeleton](../observability/skeleton.md)).
- Authentication context is validated by each service at its interface and mapped into its
  own application security DTOs.

## Review Checklist

- [ ] Each service follows the single-service topology internally; no business code is shared through a library.
- [ ] Contracts are publisher-owned, versioned, published as an artifact, and covered by consumer contract tests.
- [ ] Every published event goes through an outbox; consumers are idempotent and dead-letter permanent failures.
- [ ] Synchronous calls go through a consumer-owned port and an ACL adapter with timeouts and a circuit breaker.
- [ ] No database, table, or join is shared between services.
- [ ] Multi-service workflows are sagas with idempotent steps and compensations.
