# Topology and Bootstrap

Where CLI code lives, how one invocation is assembled, and how it changes in a modular
monolith or a microservice. The rest of the application follows the foundation's
[project topology](../../ddd-hexagonal-python/references/architecture/project-topology.md).

## Layout (single application)

An installable CLI usually uses the `src/` layout; a CLI added to a service rendered from
the templates lives under `app/interfaces/cli/` with the same shape.

```text
src/<package>/
├── __main__.py                        # `python -m <package>`: calls interfaces.cli.app.main()
└── interfaces/cli/
    ├── app.py                         # root Typer app, root callback, run(argv) -> int, main()
    ├── bootstrap.py                   # composition root: build_<context>(...) per command group
    ├── state.py                       # CliState: per-invocation, lazy settings holder
    ├── options.py                     # shared Annotated option types (--json, --env-file, ...)
    ├── output.py                      # emit / emit_error / JSON mode / output_scope
    ├── exit_codes.py                  # ExitCodeEnum and exit_code_for(error)
    ├── responses/
    │   ├── __init__.py                # re-exports; documents the contract
    │   ├── success_response.py        # SuccessResponse[T]
    │   ├── error_response.py          # ErrorResponse, ErrorDetail
    │   └── <name>_response.py         # one file per command output (+ its nested/list models)
    ├── commands/
    │   ├── __init__.py                # exports the sub-apps
    │   └── <group>_commands.py        # one Typer sub-app per noun group, with its text formatters
    └── guides/<name>.md               # version-matched agent guides, shipped as package data
```

```toml
# pyproject.toml
[project.scripts]
<tool> = "<package>.interfaces.cli.app:main"
```

`__main__.py` exists so the CLI can re-invoke itself reliably
(`[sys.executable, "-m", "<package>", ...]`) from a detached child process or a hook,
without depending on `PATH`.

## The Root App

```python
# src/<package>/interfaces/cli/app.py
import typer

from <package>.interfaces.cli.commands import config_app, order_app
from <package>.interfaces.cli.options import EnvFileOption, VersionOption
from <package>.interfaces.cli.state import CliState

app = typer.Typer(
    help="One-line purpose of the tool.",
    epilog="Every command accepts --json and --help. "
    "Exit codes: 0 ok, 1 the operation failed, 2 invalid command line.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(order_app, name="order")
app.add_typer(config_app, name="config")


@app.callback()
def root(
    context: typer.Context, env_file: EnvFileOption = None, version: VersionOption = False
) -> None:
    """Global options are parsed here and stored for this invocation only."""
    context.obj = CliState(env_file=env_file)
```

`run(argv) -> int` and `main()` wrap this app with the top-level error handler; see
[error handling](error-handling.md#the-top-level-handler).

## Per-Invocation State and Settings

```python
# src/<package>/interfaces/cli/state.py
from dataclasses import dataclass, field
from pathlib import Path

import typer

from <package>.core.env import Environment, load_environment


@dataclass(slots=True)
class CliState:
    env_file: Path | None = None
    _environment: Environment | None = field(default=None, init=False)

    def environment(self) -> Environment:
        if self._environment is None:
            self._environment = load_environment(self.env_file)
        return self._environment


def cli_state(context: typer.Context) -> CliState:
    obj = context.find_root().obj
    return obj if isinstance(obj, CliState) else CliState()
```

- Settings load lazily, the first time a command needs them. `--help`, `--version`, and
  usage errors never read configuration, and a broken config file cannot block them.
- `load_environment(env_file)` replaces the server's import-time `env.py` singletons: a
  CLI chooses its `.env` per invocation.
- Precedence: command-line option > environment variable (`<TOOL>_*`) > the user config
  file (`$XDG_CONFIG_HOME/<tool>/.env`) > defaults. Do not read a `.env` from the current
  directory when the tool runs inside arbitrary repositories (hooks, agents); it would
  silently pick up a project's unrelated settings.
- Collect every settings validation problem into one `CoreException` subclass
  (`InvalidConfigurationError` with a `problems` list), so the user fixes them in one pass.
- Keep independent configuration sources separate (for example the tool's own settings
  and a third-party tool's settings file), so a problem in one does not block commands
  that only need the other.

## Composition Root

`interfaces/cli/bootstrap.py` follows the foundation's
[composition root](../../ddd-hexagonal-python/references/architecture/composition-root.md):
one builder per command group returns a frozen dataclass of wired handlers. Replacement
adapters enter through keyword arguments, so tests need no patching. Required settings are
checked here, lazily, and raise a `CoreException` subclass with `next_steps`.

```python
# src/<package>/interfaces/cli/bootstrap.py
from functools import partial

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


def require_database_url(environment: Environment) -> str:
    if not environment.database.url:
        raise DatabaseNotConfiguredError(
            next_steps=["Run `tool config init --database-url <url>`."]
        )
    return environment.database.url


def build_ordering_handlers(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    uow_factory: Callable[[], IOrderingUnitOfWork] | None = None,
    read_repository: IOrderReadRepository | None = None,
) -> OrderingHandlers:
    return OrderingHandlers(
        place_order=PlaceOrderHandler(
            uow_factory or partial(SqlOrderingUnitOfWorkAdapter, session_factory)
        ),
        get_order=GetOrderHandler(
            read_repository or SqlOrderReadRepositoryAdapter(session_factory)
        ),
    )
```

`OrderingHandlers` is the frozen dataclass from the foundation's composition-root example.

When the same handlers are also served by an API or a worker, move the builders to
`<package>/bootstrap/` and import them here.

## Async Bridge and Resources

Handlers are async when adapters do I/O, and a command runs exactly one event loop. When
handlers need process resources (here a database engine), the whole command runs inside one
coroutine that starts and stops them through the foundation's resource registry:

```python
# src/<package>/interfaces/cli/commands/order_commands.py
async def _with_ordering[T](
    context: typer.Context, use: Callable[[OrderingHandlers], Awaitable[T]]
) -> T:
    environment = cli_state(context).environment()
    database = DatabaseEngineResourceAdapter(require_database_url(environment))
    registry = ResourceRegistry([database])
    await registry.startup_all()
    try:
        return await use(build_ordering_handlers(database.session_factory))
    finally:
        await registry.shutdown_all()


@order_app.command("show")
def show_order(
    context: typer.Context,
    order_id: Annotated[UUID, typer.Argument(help="Order to show.")],
    as_json: JsonOption = False,
) -> None:
    """Show one order."""
    query = GetOrderQuery(order_id=order_id)
    dto = asyncio.run(_with_ordering(context, lambda h: h.get_order.handle(query)))
    emit(OrderResponse.model_validate(dto), _format_order)
```

Never call `asyncio.run` twice in one command, and never inside application or
infrastructure code.

## Imports, Logging, Telemetry

- Keep module-level imports in `app.py` and `commands/` light; import heavy dependencies
  (SDKs, ORMs) inside the function that needs them, so `--help` stays fast.
- Log to stderr (or a log file under the state directory), never to stdout. Level comes
  from settings; default to warnings only.
- A short-lived CLI rarely exports traces. If it does, configure it in
  `interfaces/cli/telemetry.py` on the foundation's neutral config builder, call it from the
  root callback, and flush providers before exit.

## Modular Monolith

```text
<package>/
├── interfaces/cli/                    # HOST: root app, global options, output, exit codes,
│                                      #       top-level handler, doctor, config, guides
└── modules/<module>/
    ├── bootstrap.py                   # wiring entry point + register_<module>_cli
    └── interfaces/cli/
        ├── commands/<group>_commands.py
        └── responses/<name>_response.py
```

```python
# app/modules/billing/bootstrap.py
import typer


def register_billing_cli(app: typer.Typer) -> None:
    from app.modules.billing.interfaces.cli.commands import billing_app

    app.add_typer(billing_app, name="billing")
```

The host calls each module's `register_<module>_cli(app)`; modules reuse the host's
`output.py`, `options.py`, envelope responses, and state, and never import another
module's commands or responses. Registration must not read settings or open resources.

## Microservices

Each service ships its own CLI (maintenance, migrations, admin tasks) with this layout.
A CLI that only drives a remote service is a thin client: its handlers call an outbound
port implemented by an HTTP adapter (`infrastructure/outbound/<service>/<service>_api_adapter.py`)
that translates the remote error body into local errors. It never re-implements the
remote domain and never reads the remote service's database.

## Review Checklist

- [ ] The entry point is `[project.scripts]` -> `interfaces.cli.app:main`, with `__main__.py` for `python -m`.
- [ ] Global options are parsed in the root callback into a per-invocation `CliState`; settings load lazily from it.
- [ ] Configuration precedence is option > environment > user config file > defaults; no current-directory `.env` for tools run inside other repositories.
- [ ] Handlers come from builders in `interfaces/cli/bootstrap.py` (or `<package>/bootstrap/`) with keyword-argument overrides.
- [ ] Each command runs one `asyncio.run`; resources start and stop inside it through the registry.
- [ ] Heavy imports are deferred; logs never go to stdout.
- [ ] In a modular monolith, modules register their command groups through `register_<module>_cli`; the host owns output, exit codes, and global options.
