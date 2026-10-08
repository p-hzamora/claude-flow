---
name: scaffold-catalog
description: Author a valid scaffold config.yaml and drive a project-template catalog's `scaffold` CLI safely: pick a template from the catalog, write a schema-conformant config, compare variants or verify properties in throwaway sandbox renders, then render the final project only after the output path is authorized. Use for any template in the catalog, whatever its language or pattern; never run Copier directly.
---

# Scaffold catalog

A **catalog** is a repository whose `scaffold` command (`uv run scaffold ...`) validates a strict YAML config and renders a project template. This skill holds the procedure; the catalog's own docs and the template's schema hold the facts. Neither is restated here: they change as templates are added, and a copy would drift.

## Sources of truth, in order

1. `<catalog>/docs/agent-usage.md` and `<catalog>/docs/scaffold-command-reference.md`: protocol, option placement, exit codes. Read both first; they override this skill.
2. `scaffold schema <id> --format json`: the only authority for fields, enums, defaults, patterns, and `required`. Read root `properties`, `required`, and `$defs`.
3. `scaffold describe <id> --json`: capabilities, vendored dependencies, lifecycle.
4. `<catalog>/docs/user-guide.md` and `<catalog>/examples/*.yaml`: intent behind each option and known-good shapes. Examples are a starting point, never a substitute for the schema.

Run every command as `env -u VIRTUAL_ENV uv run --directory <catalog> scaffold <leaf> ... --json`, with leaf options after the leaf. The catalog path comes from the caller; if absent, ask and do not search the machine.

## Hard rules

- Never run Copier, never pass ad-hoc answers, never edit the catalog or a generated project.
- Never guess a template ID or a field. Unknown in the schema means unsupported: tell the caller, do not invent a key.
- The config is closed. `data`, `answers_file`, and secret-bearing names (`password`, `token`, `secret`, `dsn`, `api_key`, `connection_url`, `credential`, `database_url`) are rejected anywhere. Never put a credential in a config or a URL.
- A value the schema does not default and the caller did not state is a question for the caller, not a guess. Defaults the schema supplies may be omitted.
- Check the exit status and the payload. Exit `2` carries `error_code` and `diagnostics` (`path`, `rule`, `message`); report them verbatim.
- Delete nothing except the sandbox directory you created with `mktemp -d` in this run.

## Author a config

1. `list`, pick the ID that matches the request (read `summary` and `capabilities`), then `describe` and `schema`.
2. Map each requested capability to schema fields. Write the smallest complete YAML: required fields plus only the options the request needs. Keep a short note of why each non-default option is on.
3. `validate`. On failure fix from the diagnostics, at most 2 rounds, then report what remains.
4. `render --dry-run`. It is the first command that checks `output_dir` (exists, writable, outside the catalog, final directory absent).

## Sandbox: compare variants or verify a property

Use when the caller wants to compare options, or to ensure something about the generated output before the real render.

1. `SANDBOX=$(mktemp -d)`. Put configs and a fresh `out/` inside it; set each config's `output_dir` to that absolute `out/`. The sandbox is outside the catalog and outside any real output directory.
2. One variant per config, differing in the fewest fields possible, each with a distinct project name/slug so renders do not collide. Change one axis at a time, or the comparison cannot attribute a difference.
3. `validate` and `render --dry-run` each variant. A dry run writes nothing, so it is enough when only validity or resolved paths are in question.
4. Real renders are needed only when the question is about generated files. A real render may initialize a virtualenv and sync dependencies inside the project, so it is slower and, with a remote package provider, needs network and credentials. Prefer the offline/local provider for sandbox renders unless the provider is what is being tested, and say so when you do not.
5. Compare with evidence: `diff -rq` between trees (exclude `.venv`, `.git`, caches), then `diff -u` or Grep on the specific files the question is about. Read the generated `scaffold-manifest.json`, `vendor-manifest.json`, and any boundaries/guide docs the template ships.
6. Report per question: the claim checked, the command, and the file/line or payload that proves it. A property you could not observe is `UNVERIFIED`, never passing.
7. Remove the sandbox you created when done, after listing its contents once so the caller can see what existed. If the caller wants to keep it, report the path instead.

## Final render

Proceed only when the prompt contains an explicit authorization naming the exact final output path (`<output_dir>/<slug>`).

1. Use the vetted config, with only `output_dir` changed to the authorized parent. Re-run `validate` and `render --dry-run` against it and confirm `output_path` equals the authorized path.
2. `render <config> --json` (no `--dry-run`). The runner refuses an existing destination; report that instead of working around it.
3. Read the generated `scaffold-manifest.json`, `vendor-manifest.json`, and the template's own guides; state what the project already provides.
4. Never claim a project exists unless the render payload says `dry_run: false` and the path is present.

## Output

End with a short block:

```
SCAFFOLD_RESULT
status: DRY-RUN OK, AWAITING AUTHORIZATION | COMPARED | RENDERED | BLOCKED
template: <id>   catalog_revision: <rev>
config: <absolute path>
output_path: <resolved path or n/a>
checks: <claim -> evidence, one per line; UNVERIFIED where unproven>
next: <one step>
```

## Review Checklist

- [ ] Template ID came from `list`; every field exists in the fetched schema.
- [ ] No secret, Copier control key, or credential-bearing URL in any config.
- [ ] Every non-default option traces to the request.
- [ ] Sandbox configs and renders stayed outside the catalog; only that sandbox was deleted.
- [ ] Each comparison changed one axis and cites file/line or payload evidence.
- [ ] Real render happened only after authorization naming the exact path.
- [ ] Runner errors quoted verbatim; nothing reported created that was not.
