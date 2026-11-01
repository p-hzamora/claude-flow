# Error Handling and Exit Codes

The exception hierarchy, codes, messages, and recovery hints come from the foundation's
[error model](../../ddd-hexagonal-python/references/errors/error-model.md): project
errors subclass the category bases rooted in `raised.AppException`, and the bases accept
`next_steps`. This reference covers how the CLI turns them into output and exit codes.
`raised` has no CLI integration; the CLI owns this small adapter.

## Exit Codes

Exit codes are the CLI's status codes. They belong to the interface, in
`interfaces/cli/exit_codes.py`; no exception class carries one.

```python
# interfaces/cli/exit_codes.py
from enum import IntEnum

from raised import AppException

from <package>.exceptions.base import InterfaceException


class ExitCodeEnum(IntEnum):
    OK = 0
    FAILURE = 1        # the operation failed (any AppException except interface errors)
    USAGE = 2          # invalid command line or input (InterfaceException, Typer usage errors)
    INTERRUPTED = 130  # Ctrl-C


def exit_code_for(error: AppException) -> ExitCodeEnum:
    return ExitCodeEnum.USAGE if isinstance(error, InterfaceException) else ExitCodeEnum.FAILURE
```

- Keep to these codes. Add another only when callers need to branch on it, document it in
  the root epilog, and avoid 126 and above (reserved by shells for signals and launch
  failures).
- Callers branch on `error.code` from the JSON envelope for finer distinctions, not on new
  exit codes.

## The Top-Level Handler

Errors are caught in exactly one place, `run(argv)`, which runs the Typer app with
`standalone_mode=False` so the CLI, not Click, decides what is printed and returned.

```python
# interfaces/cli/app.py
import sys
from collections.abc import Sequence

import typer
from raised import AppException

from <package>.interfaces.cli.exit_codes import ExitCodeEnum, exit_code_for
from <package>.interfaces.cli.output import emit_error, emit_unexpected, output_scope


def run(argv: Sequence[str]) -> int:
    with output_scope():
        try:
            result = app(args=list(argv), standalone_mode=False)
        except KeyboardInterrupt:
            return ExitCodeEnum.INTERRUPTED
        except typer.Abort as abort:           # older Click wraps Ctrl-C in Abort
            interrupted = isinstance(abort.__cause__, KeyboardInterrupt)
            return ExitCodeEnum.INTERRUPTED if interrupted else ExitCodeEnum.FAILURE
        except typer.TyperException as error:  # usage errors: bad option, missing argument
            error.show()
            return int(getattr(error, "exit_code", ExitCodeEnum.USAGE))
        except AppException as error:
            emit_error(error)
            return exit_code_for(error)
        except BrokenPipeError:
            _silence_stdout()                  # reader went away (`tool list | head`)
            return ExitCodeEnum.FAILURE
        except Exception as error:             # a bug: never leak internals, never hide it
            emit_unexpected(error)
            return ExitCodeEnum.FAILURE
        return result if isinstance(result, int) else ExitCodeEnum.OK


def main() -> None:
    sys.exit(run(sys.argv[1:]))
```

- With `standalone_mode=False`, usage errors are not printed for you: call `error.show()`.
- With `standalone_mode=False`, Typer 0.27 returns the code of a `typer.Exit` and returns
  130 for Ctrl-C instead of raising. Older Click versions raise `Abort` for Ctrl-C; pin the
  behaviour with a test (`run` on a command that raises `KeyboardInterrupt` returns 130).
- Typer vendors Click from 0.26 on: catch `typer` exception types; `click.*` types do not
  match.
- `_silence_stdout()` points stdout at `os.devnull` so interpreter shutdown does not print a
  second broken-pipe traceback.
- Commands that end early without an error (a failed `doctor` check) raise
  `typer.Exit(ExitCodeEnum.FAILURE)`; inner layers never do.
- Hook commands are the exception to this flow: they catch everything themselves and
  always return 0. See [agent integration](agent-integration.md#hooks).

## Unexpected Errors

An exception that is not an `AppException` is a bug. `emit_unexpected(error)`:

1. writes the full traceback to a log file under the state directory
   (`$XDG_STATE_HOME/<tool>/errors.log`), or to stderr when `<TOOL>_DEBUG=1`;
2. prints a short message with the log path, as text on stderr or, with `--json`, as an
   error envelope with code `CMN-500`, title `UNEXPECTED_ERROR`, and a next step pointing
   to the log;
3. exits 1.

Never print a raw traceback by default, and never swallow it silently.

## Rendering

Text mode, on stderr:

```text
error [ORD-002]: Order '7f3c' has already shipped and cannot change.
  order_id: 7f3c
  next: Run `tool order show 7f3c` to see its shipment.
```

The order is always: what went wrong (code and message), the context (metadata, one line
per key, lists expanded), and how to fix it (`next:` lines). JSON mode prints the error
envelope from the [output contract](output-contract.md#the-envelope) on stdout.

## Interface Errors

Input problems detected by the CLI itself become `InterfaceException` subclasses, so they
exit 2 and render like every other error:

```python
# <package>/exceptions/interface_errors.py
class InvalidOrderFileError(InterfaceException):
    __error_code__ = "INT-010"

    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(
            f"Cannot read {path} as an order: {reason}.",
            metadata={"order_file": str(path)},
            next_steps=["Pass a JSON file shaped like `tool order place --help` describes."],
        )


# <package>/interfaces/cli/commands/order_commands.py
def _load_order_file(path: Path) -> PlaceOrderRequest:
    try:
        return PlaceOrderRequest.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError) as error:
        raise InvalidOrderFileError(path, str(error).splitlines()[0]) from error
```

The message is built inside the error's `__init__`, as the
[error model](../../ddd-hexagonal-python/references/errors/error-model.md#messages)
requires; the call site passes only values.

Choose the base by who can fix the problem: the caller fixing their input or arguments is
an `InterfaceException` (exit 2); a rule of the domain rejecting a well-formed request is a
`DomainException` (exit 1), even when the value came from a flag.

## Review Checklist

- [ ] Exit codes are defined in the interface and derived from error categories; no exception carries an exit code.
- [ ] `run(argv)` is the only place that catches errors: KeyboardInterrupt and Abort-from-Ctrl-C (130), other Abort (1), Typer usage errors (`show()`), AppException, BrokenPipeError, then unexpected exceptions; a test pins Ctrl-C to 130.
- [ ] Unexpected errors log the traceback to a file (or stderr in debug) and print a short, actionable message.
- [ ] Text errors go to stderr as code, message, metadata, and next steps; JSON errors are the envelope on stdout with a non-zero exit.
- [ ] Input parsing failures become `InterfaceException` subclasses with next steps.
