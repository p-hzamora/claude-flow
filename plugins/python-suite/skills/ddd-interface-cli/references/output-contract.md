# Output Contract

A CLI's output is an API. People read the text; scripts and agents parse `--json`. Both
come from the same response models, printed through one module.

## The Envelope

With `--json`, stdout carries exactly one JSON document:

```json
{"ok": true, "result": {"id": "7f3c...", "status": "placed", "currency": "EUR", "total_amount": "42.50"}}
```

```json
{
  "ok": false,
  "error": {
    "code": "CORE-002",
    "title": "DATABASE_NOT_CONFIGURED_ERROR",
    "message": "No database URL is configured.",
    "metadata": {"env_file": "/home/me/.config/tool/.env"},
    "next_steps": ["Run `tool config init --database-url <url>`."]
  }
}
```

- `ok` lets a caller branch without inspecting the rest.
- `error.code` is the stable value to branch on; `message` may change between versions.
- Errors in JSON mode go to stdout inside the envelope (the caller asked for JSON), and the
  exit code is still non-zero. Without `--json`, errors are a text block on stderr.
- Unlike HTTP, the CLI envelope includes `metadata`: the caller is the local user, and
  structured context (paths, available names) is what makes the error actionable. Never
  put secrets in it.

## `responses/`

```text
interfaces/cli/responses/
├── __init__.py                 # re-exports every response; docstring states the contract
├── success_response.py         # SuccessResponse[T]
├── error_response.py           # ErrorDetail, ErrorResponse
├── order_response.py           # OrderResponse, OrderLineResponse
└── order_page_response.py      # OrderPageResponse
```

- One file per command output, named `<name>_response.py`; its nested and list models live
  in the same file. The package `__init__` re-exports them, so commands import from
  `interfaces.cli.responses`.
- Responses subclass the project's `FrozenObject` (`frozen=True, from_attributes=True`),
  so `OrderResponse.model_validate(dto)` reads a DTO directly.
- A response is built from a DTO, never from an entity or value object, and a command
  never prints a DTO. Responses duplicate DTO fields on purpose: a DTO refactor must not
  silently change what scripts and agents read.
- Interface-only commands build their response from interface data (settings, package
  files, diagnostics results).
- Add a field computed by the interface (a warning) with
  `response.model_copy(update={"warning": ...})`.

```python
# interfaces/cli/responses/success_response.py
from typing import Literal

from <package>.utils import FrozenObject


class SuccessResponse[T: FrozenObject](FrozenObject):
    ok: Literal[True] = True
    result: T
```

## `output.py`

```python
# interfaces/cli/output.py
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token

from <package>.interfaces.cli.responses import ErrorDetail, ErrorResponse, SuccessResponse
from <package>.utils import FrozenObject

_JSON_MODE: ContextVar[bool] = ContextVar("json_mode", default=False)


@contextmanager
def output_scope() -> Iterator[None]:
    """Start each invocation in text mode; restore afterwards (in-process reuse, tests)."""
    token: Token[bool] = _JSON_MODE.set(False)
    try:
        yield
    finally:
        _JSON_MODE.reset(token)


def remember_json_mode(enabled: bool) -> bool:
    """Typer callback of --json."""
    if enabled:
        _JSON_MODE.set(True)
    return enabled


def _dump(response: FrozenObject) -> str:
    # serialize_as_any keeps the concrete result's fields behind the generic envelope
    return response.model_dump_json(indent=2, serialize_as_any=True) + "\n"


def emit[T: FrozenObject](result: T, formatter: Callable[[T], str]) -> None:
    if _JSON_MODE.get():
        sys.stdout.write(_dump(SuccessResponse(result=result)))
    else:
        sys.stdout.write(formatter(result).rstrip("\n") + "\n")
```

- `emit_error(error)` builds `ErrorResponse(error=ErrorDetail(...))` the same way, or the
  text block described in [error handling](error-handling.md#rendering).
- The JSON mode lives in a `ContextVar` so the top-level error handler, which runs outside
  any command, also honours `--json`. The trade-off: each command declares
  `as_json: JsonOption = False` even though its body never reads it; the declaration is
  what registers the flag. Keep it, and say so in a comment the first time.
- `output_scope()` wraps every `run(argv)` so a `--json` from one in-process invocation
  never leaks into the next.

## Text Formatters

- Private functions in the command module, `_format_<thing>(response) -> str`, taking the
  response model, never the DTO.
- Say what happened or changed, in a few lines; end with the next step when there is one.
- No color or decoration unless stdout is a TTY and `NO_COLOR` is unset.
- Text output is for people and may change; tell automation to use `--json`.

## Evolution

- The envelope and response schemas follow semantic versioning of the tool: adding a field
  is minor; renaming, removing, or changing a field's type is major.
- Never repurpose an error code; add a new one.
- Deprecate before removing: keep the old field or command for at least one minor release
  and mention the replacement in its help.

## Review Checklist

- [ ] Every command prints through `emit`/`emit_error`; with `--json`, stdout holds exactly one envelope.
- [ ] Each output has a `<name>_response.py` model built from a DTO (or interface data); no DTO or entity is printed directly.
- [ ] The envelope uses `serialize_as_any=True`, and the JSON mode is reset per invocation with `output_scope()`.
- [ ] Error envelopes carry code, title, message, metadata, and next steps, with a non-zero exit code.
- [ ] Text formatters take responses, say what changed, and avoid color without a TTY.
- [ ] JSON changes follow additive-first versioning; error codes are never repurposed.
