# Interface Adapter Contract

An interface (a REST API, a CLI, a worker, a message consumer, a gRPC server, an MCP
server) is a driving adapter. It turns something from the outside world into a command or
query, runs a handler, and turns the DTO or error that comes back into something the
outside world understands. The domain and application are identical for every interface.

This file is the contract every interface follows and the template for every interface
skill. The foundation owns everything inside the hexagon; an interface skill owns only
what this contract lists.

## What Every Interface Does

| # | Responsibility | Foundation rule | The interface skill decides |
| --- | --- | --- | --- |
| 1 | Entry point and composition | One [composition root](../architecture/composition-root.md) per process; interfaces receive handlers, never build adapters inline | Where its bootstrap lives, what the process entry point is, when settings load |
| 2 | Input translation | Input becomes the handler's `Command`/`Query`, defined in the handler's file | Request schemas, argument parsing, payload parsing; how invalid input is reported (an `InterfaceException` subclass, or a documented framework default such as `raised`'s 422 `CMN-003`) |
| 3 | Invocation | Call handlers only, never repositories, adapters, or ORM sessions | How sync and async are bridged; per-request or per-invocation scope (Unit of Work, session) |
| 4 | Output contract | The interface's output models are built from DTOs (`Model.model_validate(dto)`), never from entities, value objects, or ORM models | The model family (`*_schema.py`, `*_response.py`, message schemas), envelope, and serialization |
| 5 | Error translation | The [error model](../errors/error-model.md): one hierarchy, status hints, last-resort handler | The mapping table to its transport (status codes, exit codes, retry/dead-letter) and the error body |
| 6 | State and lifecycle | [Process resources](../architecture/composition-root.md#process-resources) are interface-neutral | How resources are published to its own state (typed app state, per-invocation holder) |
| 7 | Placement per deployment | [Deployment overview](../deployment/overview.md) | Its folder inside a single service, inside each module, and in an extracted service |
| 8 | Edge testing | [Testing strategy](../testing/strategy.md): domain and handlers are tested without the interface | How to drive it in-process, what to assert (status/exit code and the machine-readable body) |

An interface never:

- contains a business rule, a transaction boundary, or a query against storage;
- imports another interface;
- is imported by `domain/`, `application/`, `infrastructure/`, `core/`, or `exceptions/`;
- returns or prints a DTO, entity, or value object directly as its public contract.

## Folder Shape

```text
<package>/interfaces/<kind>/
├── bootstrap/ | bootstrap.py     # composition root of this interface (or a thin call into <package>/bootstrap/)
├── <inputs>/                     # request schemas, option types, payload parsers
├── <outputs>/                    # schemas/ (HTTP), responses/ (CLI), ...
├── <entry modules>/              # routers/, commands/, consumers/
└── exceptions/ | errors.py       # transport mapping of the error model
```

In a modular monolith each module owns `modules/<module>/interfaces/<kind>/` for its own
entry modules and outputs, and exposes a public registration function from its
`bootstrap.py` (`register_<module>_api(app)`, `register_<module>_cli(app)`). The host
interface owns process-level concerns only: the application object, global options,
shared error formatting, health or diagnostics. See the
[modular monolith topology](../deployment/modular-monolith-topology.md).

## Enforcement

Add these to the project's import-linter configuration (or architecture tests) when an
interface is introduced:

```toml
[[tool.importlinter.contracts]]
name = "Nothing below interfaces imports them"
type = "forbidden"
source_modules = ["app.bounded_context", "app.shared_kernel", "app.core", "app.exceptions"]
forbidden_modules = ["app.interfaces"]

[[tool.importlinter.contracts]]
name = "Inner layers import no delivery framework"
type = "forbidden"
source_modules = ["app.bounded_context", "app.shared_kernel.domain", "app.shared_kernel.application"]
forbidden_modules = ["fastapi", "starlette", "typer", "click"]

[[tool.importlinter.contracts]]
name = "Interfaces are independent"
type = "independence"
modules = ["app.interfaces.api", "app.interfaces.cli"]
```

## Adding a New Interface Skill

When a new kind of interface appears (worker, consumer, gRPC, MCP server), create a new
skill named `ddd-interface-<kind>` in the same plugin rather than extending the
foundation or an existing interface skill.

1. Copy the section shape of an existing interface skill: `SKILL.md` with non-negotiables,
   a routing table to its references, and a Review Checklist.
2. Answer the eight rows of the table above, and only those. Link to the foundation for
   anything inside the hexagon; never restate layer rules, tactical patterns, CQRS, or
   the error hierarchy.
3. Add its row to [How Interfaces Use the Hint](../errors/error-model.md#5-how-interfaces-use-the-hint).
4. Add its folder to the topology examples only through the `interfaces/<kind>/`
   placeholder; do not hard-code it into the foundation trees.
5. Register the skill in the plugin's documentation, and in the agents that review or
   implement interface code.

If a rule turns out to be true for every interface, move it into the foundation and link
to it from each interface skill. If a foundation rule only makes sense for one interface,
move it into that interface skill.

## Review Checklist

- [ ] The interface only translates input, calls handlers, and translates DTOs and errors; it holds no business rule, transaction, or storage query.
- [ ] Its output models are built from DTOs and are its public contract.
- [ ] Its error mapping covers every category base and has a last-resort handler.
- [ ] No inner layer, `core/`, or `exceptions/` imports it, and it imports no other interface.
- [ ] Its placement matches the deployment profile: host concerns in the host, business entry points in the owning module.
- [ ] A new interface kind got its own `ddd-interface-<kind>` skill instead of new foundation rules.
