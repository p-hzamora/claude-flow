---
name: ddd-interface-cli
description: Command-line (Typer) interface for Python DDD/hexagonal applications built on ddd-hexagonal-python. Use when adding or reviewing CLI delivery code - command groups and options, per-invocation bootstrap, JSON/text output contract and responses, exit codes and error rendering, agent-facing design (skill guides, hooks reading stdin), or CLI tests.
---

# CLI Interface for DDD Applications

A CLI is a driving adapter, exactly like an HTTP API: it parses argv (and sometimes stdin)
into a command or query, calls a handler it received from the composition root, and turns
the returned DTO or error into output and an exit code. Everything inside the hexagon comes
from `ddd-hexagonal-python`; load it first. This skill answers only the rows of its
[interface adapter contract](../ddd-hexagonal-python/references/interfaces/adapter-contract.md)
for the command line.

What differs from a server: **one process per invocation.** Nothing survives in memory
between calls, settings are chosen per call (`--env-file`), the caller may be a person, a
script, or an AI agent, and the exit code is the status.

Related skills: `python-syntax` for code style, `pytest` for test mechanics.

## Non-Negotiables

- Commands translate and delegate: options -> `Command`/`Query` -> handler from the CLI
  bootstrap -> `Response.model_validate(dto)` -> `emit(...)`. No business rule, storage
  access, or adapter construction in a command.
- One output path: every command prints through `emit`/`emit_error`. Results go to stdout;
  logs, progress, and text errors go to stderr. Every command accepts `--json`.
- The JSON envelope (`{"ok": true, "result": ...}` / `{"ok": false, "error": ...}`) and
  every response in `responses/` is a public, versioned contract built from DTOs.
- Exit codes are owned by the CLI: 0 ok, 1 the operation failed, 2 invalid usage, 130
  interrupted. They are derived from the error model's categories at one top-level
  handler; inner layers never call `sys.exit` or raise `typer.Exit`.
- Settings and handlers are built lazily inside the command, so `--help`, `--version`,
  and usage errors never read configuration or touch I/O.
- A command meant for automation never prompts, never blocks on a TTY, and is safe to
  re-run.

## References

| Decision | Reference |
| --- | --- |
| Folder layout, entry point, per-invocation bootstrap, settings, async bridge, resources, logging, module and microservice placement | [Topology and bootstrap](references/topology-and-bootstrap.md) |
| Command groups, naming, options and flags, mutations (preview, `--yes`, `--force`), idempotency, help, streams | [Command design](references/command-design.md) |
| `--json` envelope, `responses/`, `emit`, text formatters, schema evolution | [Output contract](references/output-contract.md) |
| Exit codes, the top-level handler, error rendering, interrupts, unexpected errors | [Error handling](references/error-handling.md) |
| Designing for AI agents: skill stub and version-matched guides, hooks on stdin, installers, diagnostics | [Agent integration](references/agent-integration.md) |
| In-process tests, isolation, JSON and exit-code assertions, hooks, guide drift, smoke test | [Testing](references/testing.md) |

## Review Checklist

- [ ] Every command only parses, calls a handler from the CLI bootstrap, builds a response from the DTO, and emits it.
- [ ] Every command accepts `--json`; results go to stdout and everything else to stderr.
- [ ] Every printed result is a model from `responses/`, built from a DTO (or from interface-only data for commands with no handler); none prints a DTO or entity.
- [ ] Exit codes come from one top-level handler: 0, 1, 2, 130; errors render as the JSON error envelope or a text block with code, message, and next steps.
- [ ] `--help`, `--version`, and usage errors read no configuration; settings and handlers are built per invocation.
- [ ] Mutating commands preview by default or require `--yes`/`--force`; re-running them is safe and says so.
- [ ] Automation-facing commands never prompt; hook commands print nothing and always exit 0.
- [ ] Tests drive `run(argv)` in-process, assert exit code and JSON, and isolate config and state directories.
- [ ] The foundation's Review Checklist holds for the code behind the commands.
