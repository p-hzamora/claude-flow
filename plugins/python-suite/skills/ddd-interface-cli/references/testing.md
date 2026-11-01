# Testing the CLI

Domain objects and handlers are tested without the CLI, as the foundation's
[testing strategy](../../ddd-hexagonal-python/references/testing/strategy.md)
describes. CLI tests verify only the edge: parsing, the output contract, exit codes, and
the wiring in `bootstrap.py`. Use the `pytest` skill for fixture mechanics.

## Three Levels

| Level | Drives | Use for |
| --- | --- | --- |
| Logic | Handlers, formatters, response models directly | Most behaviour |
| In-process | `run(argv)` with `capsys` | Every command's contract: exit code, JSON, stderr |
| Subprocess smoke | The installed entry point (`python -m <package> --version`) | One or two tests that prove packaging and `main()` work |

Prefer `run(argv)` over Typer's `CliRunner` for in-process tests: `CliRunner` invokes the
Typer app directly and bypasses `run()`, so the top-level error handling and exit-code
mapping go untested.

```python
def test_unknown_command_is_a_usage_error(capsys):
    assert run(["bogus"]) == 2
    assert "No such command" in capsys.readouterr().err


def test_place_order_json_envelope(capsys, order_file):
    assert run(["order", "place", "--from-file", str(order_file), "--json"]) == 0
    envelope = json.loads(capsys.readouterr().out)
    assert envelope["ok"] is True
    assert envelope["result"]["status"] == "placed"


def test_missing_database_reports_code_and_next_step(capsys):
    assert run(["order", "show", str(uuid4()), "--json"]) == 1
    error = json.loads(capsys.readouterr().out)["error"]
    assert error["code"] == "CORE-002"
    assert error["next_steps"]
```

Assert exit codes and parsed JSON. Assert text output only for the few properties people
rely on (a preview ends with the `--yes` hint), never whole paragraphs.

## Isolation

An autouse fixture points every location the CLI reads at `tmp_path` and clears the tool's
environment variables, so a developer's real configuration can never leak into a test:

```python
@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    for name in [key for key in os.environ if key.startswith("<TOOL>_")]:
        monkeypatch.delenv(name)
```

- Replace external executables with fakes placed first on `PATH`; use real temporary git
  repositories or files rather than mocks of them.
- Replace adapters through the keyword arguments of the `bootstrap.py` builders instead of
  patching modules.
- Repeated in-process invocations rely on `output_scope()`; add one test that runs a
  `--json` command and then a text command and checks the second prints text.

## Hooks

```python
def test_hook_prints_nothing_and_logs_failures(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO('{"hook_event_name": "Stop", "session_id": "s1"}'))
    assert run(["hook", "handle"]) == 0
    assert capsys.readouterr() == ("", "")
```

Also cover: malformed JSON (exit 0, nothing printed), an internal failure (exit 0, logged to
the hook error log), and the recursion guard.

## Guide and Help Drift

- Every `<tool> ...` command quoted in a packaged guide or in help epilogs must answer
  `--help` with exit 0. Extract them with a regular expression and run each.
- Test that the skill stub resolves the executable and calls `skills get`.

## Architecture

Run the import contracts from the foundation's
[adapter contract](../../ddd-hexagonal-python/references/interfaces/adapter-contract.md#enforcement)
in the test suite, plus CLI-specific ones: bounded contexts never import `typer`, and
nothing below `interfaces` imports them.

## Review Checklist

- [ ] Command tests drive `run(argv)` in-process and assert exit codes and parsed JSON.
- [ ] An autouse fixture isolates config and state directories and clears the tool's environment variables.
- [ ] External tools are faked on `PATH`; adapters are replaced through bootstrap keyword arguments.
- [ ] Hook tests cover silence, exit 0, malformed input, logged failures, and the recursion guard.
- [ ] Commands quoted in guides and help are checked to exist; one subprocess smoke test covers the entry point.
