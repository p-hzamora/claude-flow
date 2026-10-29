# omarchy-tools

Hyprland on Omarchy: inspect the running compositor before a change and validate it
after. Install only on Omarchy machines.

**Version:** 0.1.0
**Dependencies:** none. Soft: the built-in `omarchy` skill (what to edit) and the
`obsidian-vault` plugin (`vault-reader`, for personal notes under `os/omarchy/`).

Every shared skill has a task-specific `Review Checklist` that agents complete before
reporting applicable work done.

**Codex:** the skill is packaged through `../plugins/omarchy-tools/.codex-plugin/plugin.json`.
The helper needs a running Hyprland session and `jq`.

## Skills

| Skill | Path |
|---|---|
| `hyprland-workflow` | `skills/hyprland-workflow/SKILL.md`: add a binding without duplicate owners, read window classes for rules, check the monitor layout, and validate with reload plus `configerrors`. Defers to the built-in `omarchy` skill for which files to edit. |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/hypr-inspect.sh` | `bind <MODS> <KEY>`, `window`, `clients`, `monitors`, `check`. Read-only except the reload in `check`; exit 0 only when `configerrors` is empty. |
