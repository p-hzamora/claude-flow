# Agent Integration

More and more CLI callers are AI coding agents: they run commands through a shell tool,
read the output, and decide what to do next. They also call CLIs from hooks, where the CLI
reacts to the agent's own events. Design for them explicitly; it also makes the tool
better for scripts.

## Commands Agents Can Use

- **`--json` on every command**, with the stable envelope and error codes of the
  [output contract](output-contract.md). Agents branch on `error.code`, never on text.
- **`next_steps` on every error a caller can fix.** Write them as concrete commands
  (`Run \`tool config init --database-url <url>\`.`); an agent can follow them, with the
  user's consent.
- **No prompts, no pagers, no TTY assumptions.** Missing input is a usage error with a next
  step, not a question.
- **Discoverability.** `--help` on every level is accurate and complete, because an agent
  that is unsure must run it instead of guessing flags. Unknown commands fail fast with
  exit 2.
- **Safe defaults.** Mutations preview by default (`--yes` to apply) and are idempotent,
  so an agent retrying after an interruption does no harm.
- **Diagnostics.** A `doctor` command tells an agent (and a person) what is missing and how
  to fix it, with one `next_step` per failed check.

## Skill Stub and Version-Matched Guides

Agent instructions drift when they are copied into an installed skill and the tool
upgrades underneath. Ship the instructions **with the tool** and keep the installed skill
as a thin stub that fetches them.

```text
skills/<tool>/SKILL.md                 # in the repository; installed into the agent
src/<package>/interfaces/cli/guides/
└── <tool>.md                          # the real guide, packaged with the CLI
```

The stub only:

1. resolves the executable explicitly (`<tool> --version`); if it fails, reports the error
   and stops. It never tries another executable or guesses commands;
2. runs `<tool> skills get <tool>` and follows the guide it prints;
3. passes any agent-provided context the CLI needs (for example a session id variable).

Its frontmatter `description` decides when the agent loads it; write it as the user's
intent, not the tool's internals.

The CLI serves the guides:

- `<tool> skills list` lists packaged guides; `<tool> skills get <name>` prints one. An
  unknown name is an interface error whose metadata lists the available guides.
- Guides are package data under `interfaces/cli/guides/`, read with
  `importlib.resources.files(...)`. They change with the CLI, so they live with it, not
  with a bounded context.
- A guide states: always use `--json`; branch on `error.code`; follow `next_steps` only
  when the user agrees; never guess commands or flags (run `--help`); run costly or
  settings-changing commands only when the user asks; the common error codes and what to
  do about each.

## Hooks

A hook command runs inside the agent's own loop (after a tool call, at session end). It
must never disturb the agent.

| Rule | How |
| --- | --- |
| Read the event from stdin | Parse JSON with a tolerant model (`extra="ignore"`); ignore unknown events |
| Print nothing | No stdout, no stderr on success; the agent may show or interpret any output |
| Always exit 0 | Catch every exception inside the hook command; log it to a file under the state directory |
| Return fast | Persist the minimum and spawn slow work as a detached process (`python -m <package> ...`, new session); never wait for it |
| Avoid recursion | Set an environment variable (`<TOOL>_HOOK=1`) in spawned processes and return immediately when it is present |

Placement follows the foundation: the payload model and the routing of an event to a
command are an anti-corruption layer of the receiving context, in its
`infrastructure/inbound/<agent>/`. The CLI hook command keeps only the process concerns:
read stdin, guard recursion, call the ACL, swallow and log failures.

```python
@hook_app.command("handle")
def handle_hook(context: typer.Context) -> None:
    """Read one agent hook event on stdin; print nothing; always exit 0."""
    if os.environ.get("<TOOL>_HOOK") == "1":
        return
    try:
        payload = HookPayload.model_validate_json(sys.stdin.read())
    except (json.JSONDecodeError, ValidationError):
        return
    try:
        asyncio.run(route_hook_event(payload, _handlers(context)))
    except Exception as error:  # a hook must never fail the agent
        log_hook_failure(cli_state(context), error)
```

## Integration Installers

A command that registers the tool with an agent (`<tool> integrate <agent> install`):

- previews the settings diff by default and writes only with `--yes`, keeping a timestamped
  backup;
- adds only its own entries and `uninstall` removes only those;
- is idempotent (`already up to date`);
- registers an absolute, stable command: the installed executable found on `PATH`, else
  `sys.executable -m <package>`, plus `--env-file` when one was used; it warns when that
  points into a development virtual environment;
- tells the user to restart agent sessions so they load the change.

## Review Checklist

- [ ] Every command supports `--json`, never prompts in automation, and documents itself in `--help`.
- [ ] Fixable errors carry concrete `next_steps`; agents can branch on stable codes listed in the guide.
- [ ] The installed skill is a stub that resolves the executable and runs `skills get`; guides ship as package data with the CLI.
- [ ] Hook commands read stdin with a tolerant model, print nothing, always exit 0, log failures, return fast, and guard against recursion.
- [ ] Hook payload parsing and routing live in the receiving context's inbound infrastructure, not in the CLI.
- [ ] Installers preview, back up, stay idempotent, and register a stable absolute command.
