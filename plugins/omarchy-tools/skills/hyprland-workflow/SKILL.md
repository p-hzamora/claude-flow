---
name: hyprland-workflow
description: Change Hyprland on an Omarchy system safely by inspecting live state first and validating after: find who owns a key binding before adding one, read a window's class for a rule, check the monitor layout, and reload with config-error checks. Use when adding or changing Hyprland bindings, window rules, monitors, or workspaces; defers to the built-in `omarchy` skill for what to edit.
---

# Hyprland workflow

The built-in `omarchy` skill says which file to edit and what never to touch
(`~/.local/share/omarchy/` is read-only). This skill adds how to inspect the running
compositor before a change and validate it after. Load `omarchy` first for any edit.

## Helper

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/hypr-inspect.sh <command>
```

| Command | Use it to |
|---|---|
| `bind <MODS> <KEY>` | see what a combo is bound to (e.g. `bind SUPER SHIFT B`) |
| `window` | read `class`, `initialClass`, `title` of the focused window, for rules |
| `clients` | list every window with its workspace |
| `monitors` | one line per monitor: mode, position, scale, transform, workspace |
| `check` | `hyprctl reload`, then `configerrors`; exit 0 only when clean |

It is read-only (apart from the reload in `check`) and needs a running Hyprland
session and `jq`. In Codex, resolve the plugin directory and run its `scripts/hypr-inspect.sh`.

## Adding a key binding

1. Run `bind <MODS> <KEY>`. "Free" exit 1 means nothing owns it.
2. If an Omarchy default owns it, put `unbind = <MODS>, <KEY>` before the new `bindd`
   in the user bindings file; a bare `bindd` would add a second action.
3. Edit the user file under `~/.config/hypr/`, never the defaults.
4. Run `check` and fix every error it prints before reporting done.

## Window rules

Get the real class and title with `window` (focus the window first) or `clients`. Copy
the rule syntax from `~/.local/share/omarchy/default/hypr/windows.conf`, which matches
the installed Hyprland; if unsure, check the official wiki for the installed version
(`hyprctl version`). Rule syntax changes between releases, so do not write it from memory.

## Monitors and workspaces

Run `monitors` before editing. A monitor turned 90° (`transform 1` or `3`) swaps its
width and height in the layout, so neighbours' x offsets shift by the difference.
Negative y is valid. Workspace-to-monitor binding is separate from position.

## Config order

`hyprland.conf` sources the Omarchy defaults first and the user files after, so a later
line wins. Override by redeclaring or `unbind` first, not by editing the defaults.

## Personal context

Facts about this machine (layout, drivers, past gotchas) belong in the notes vault, not
in this skill. When the `obsidian-vault` plugin is installed, ask its `vault-reader`
agent about `os/omarchy/<topic>` before a change, and carry on without it if Obsidian is
not running.

## Review Checklist

- [ ] The built-in `omarchy` skill was loaded and no file under `~/.local/share/omarchy/` was edited.
- [ ] For a new binding, `bind` was run first and any existing owner was `unbind`-ed.
- [ ] Window rules use a class or title read from `window` or `clients`, in the installed syntax.
- [ ] `check` ran after the last edit and printed `OK`.
- [ ] Any `configerrors` output was quoted verbatim and resolved or reported.
- [ ] No personal machine facts were copied into the skill.
