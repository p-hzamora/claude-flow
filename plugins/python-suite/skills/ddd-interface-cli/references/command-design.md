# Command Design

How commands are named, grouped, and parameterized so that people, scripts, and agents can
use them without guessing. Typer mechanics are shown where they matter.

## Grammar

- **Noun, then verb**: `<tool> <group> <verb>` (`tool order place`, `tool order show`).
  Nest a further noun for an integration target: `tool integrate claude-code install`. Use
  one order everywhere.
- One module per group: `commands/<group>_commands.py` exposing `<group>_app = typer.Typer(...)`,
  mounted by the root app. A group usually maps to one bounded context or one integration.
- Name the command explicitly when the verb shadows a builtin:
  `@order_app.command("list")` on `def list_orders(...)`.
- No abbreviations of commands or flags, no catch-all subcommand, no hidden aliases. A
  shorthand (`-h`, `-n`, `-f`, `-y`) is added only for the standard flags below.
- Every Typer (root and groups) sets `no_args_is_help=True`. A group with a single command
  still needs a callback, or Typer collapses it into the parent.

## Options and Arguments

- Prefer named options. Use at most one kind of positional argument per command (the thing
  acted on: a ticket, a query text).
- Declare shared options once in `options.py` as `Annotated` aliases and reuse them; the
  same flag name always means the same thing across the tool.

```python
# src/<package>/interfaces/cli/options.py
from pathlib import Path
from typing import Annotated

import typer

from <package>.interfaces.cli.output import remember_json_mode

JsonOption = Annotated[
    bool,
    typer.Option("--json", help="Print a JSON envelope instead of text.", callback=remember_json_mode),
]
EnvFileOption = Annotated[
    Path | None,
    typer.Option("--env-file", envvar="<TOOL>_ENV_FILE", dir_okay=False, help="Settings file to use."),
]
SessionOption = Annotated[
    str,
    typer.Option("--session", envvar="<TOOL>_SESSION_ID", show_envvar=True, help="Agent session id."),
]
YesOption = Annotated[bool, typer.Option("--yes", "-y", help="Apply the change (default: preview only).")]
```

- Use enums for closed choices (`--mode live|dry-run`), `min`/`max` for numbers,
  `Path(dir_okay=False, exists=...)` for files, flag pairs (`--park/--no-park`) for
  booleans with a meaningful default.
- Values agents or hooks provide implicitly (a session id) also read an environment
  variable, shown in help with `show_envvar=True`.
- Secrets never travel as flag values (they leak into shell history and process lists):
  read them from the environment, a file, or stdin.
- Validate everything (options, files, stdin payloads) before any side effect. Turn a
  parse failure into an `InterfaceException` subclass with `next_steps`; see
  [error handling](error-handling.md#interface-errors).

## Standard Flags

| Flag | Meaning everywhere |
| --- | --- |
| `--json` | Machine-readable envelope on stdout; required on every command |
| `-h`, `--help` | Help, generated from the declarations |
| `--version` | Version from package metadata, on stdout, exit 0 (eager root option) |
| `-y`, `--yes` | Apply a mutation that otherwise only previews |
| `-f`, `--force` | Overwrite or proceed despite a safety check (an existing file, a dirty state) |
| `-n`, `--dry-run` | Run the whole command without side effects, when preview-by-default does not fit |
| `--no-input` | Never prompt; fail with a usage error if input is missing |
| `-q`, `--quiet` | Suppress non-essential text output (never the JSON envelope) |
| `--env-file` | Settings file for this invocation |

## Mutations and Danger Levels

| Level | Example | Behaviour |
| --- | --- | --- |
| Read-only | `status`, `list`, `search` | Run immediately |
| Reversible state change | `order hold`, `order release` | Run immediately; report what changed |
| Change to user files or config | `integrate ... install`, `config init` | Preview the change (diff) by default; write only with `--yes`; keep a timestamped backup; refuse to overwrite without `--force` |
| Destructive or irreversible | delete data, rewrite history | Require `--yes` or `--force`; when interactive and without the flag, a TTY prompt may ask; with `--no-input`, `--json`, or no TTY, fail with a usage error instead of prompting |

- **Idempotent re-runs.** Running a mutation again leaves the same state and says so
  (`already up to date`), with exit 0.
- **Least surprise.** An integrator removes only what it added (its own hooks, its own
  keys) and leaves everything else untouched.
- Text output after a preview ends with the exact command to apply it
  (`Preview only. Re-run with --yes to write this change.`).

## Commands Without a Handler

Interface-only commands (`--version`, `config show`, `config init`, `skills list|get`,
`doctor`) have no use case behind them and may read configuration, package data, or
diagnostics directly. They still print a model from `responses/` and raise project
errors; they never contain business rules. When such a command grows logic that a second
interface would need, it becomes a handler in a context or a host-level package (for
example `diagnostics/`), and the command calls it.

- `doctor` runs checks (configuration, folders, required executables), prints each check
  with a `next_step`, and exits 1 if any fails. A broken settings file is a failed check,
  not a crash.
- `config show` prints the effective settings and the file they came from; `config init`
  writes a commented settings file.

## Help

- The first docstring line of each command is its one-line summary; every option has
  `help=`.
- The root epilog states the output and exit-code contract.
- Rich markup treats `[...]` as markup and drops it; escape brackets or set
  `rich_markup_mode=None` when help shows literal brackets.
- Examples in help or guides must be real, runnable commands; tests check them (see
  [testing](testing.md#guide-and-help-drift)).

## Streams

| Stream | Carries |
| --- | --- |
| stdout | The result: the JSON envelope with `--json`, otherwise the formatted text. Also `--version` and `--help` |
| stderr | Text errors, warnings, logs, progress |
| stdin | Payloads (hook JSON, an order file given as `-`), never prompts in automation |

Respect `NO_COLOR` and detect a TTY before using color or progress bars; never emit ANSI
codes into JSON or redirected output.

## Review Checklist

- [ ] Commands follow noun-then-verb consistently, one module and sub-app per group, with explicit names where verbs shadow builtins.
- [ ] Shared options are declared once in `options.py`; the same flag means the same thing everywhere; standard flags use the standard names.
- [ ] Input is validated before side effects; secrets never arrive as flag values.
- [ ] Mutations follow the danger-level table, are idempotent, and report what changed or how to apply the preview.
- [ ] Interface-only commands print responses and raise project errors without business logic.
- [ ] Every command and option has help text; stdout carries only results.
