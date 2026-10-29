---
name: zsh-shell
description: Create, change, or review zsh shell customisation that must work on macOS, Linux, and WSL: aliases, small functions, PATH and environment setup, and where secrets live. Use when the user asks to add or fix an alias, a shell function, or a `.zshrc` setting; not for bash scripts or non-zsh shells.
---

# zsh shell

Keep zsh customisation small, portable, and safe to commit to a dotfiles repository.

## Where things live

| What | File | Tracked in git |
|---|---|---|
| Aliases and functions | `~/.config/zsh/aliases.zsh` (override with `$ZSH_ALIASES_FILE`) | yes |
| Shell setup (`PATH`, plugins, prompt) | `~/.zshrc`, which sources the aliases file after the plugin framework | yes |
| Tokens and any secret | an untracked file such as `~/.zshenv.local`, sourced from `.zshrc` | never |

If the user's setup differs, read `~/.zshrc` first and follow what is there; do not move files unasked.

## Add an alias: use the script

Never edit the aliases file by hand for a plain alias. Run the helper:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/zsh-alias.sh add <name> '<command>'
${CLAUDE_PLUGIN_ROOT}/scripts/zsh-alias.sh remove <name>
${CLAUDE_PLUGIN_ROOT}/scripts/zsh-alias.sh list
```

It validates the name, refuses one that is already an alias, function, command, or builtin in the user's interactive zsh, quotes the command, checks the file with `zsh -n` before writing, and prints the reload hint. In Codex, resolve the plugin directory first and run its `scripts/zsh-alias.sh`.

- On exit code 1 (conflict) tell the user which kind of thing the name collides with and offer another name. Pass `--force` only after the user agrees to shadow it.
- Afterwards the user reloads with `source ~/.zshrc`; the current shell does not pick the alias up by itself.

## Alias or function

- Alias: a fixed command prefix, no logic (`alias gst='git status -sb'`).
- Function: arguments in the middle, conditionals, or several commands. Write it by hand in the same file, then run `zsh -n <file>`.

## Portability across macOS, Linux, and WSL

The same file is reused on every OS, so guard anything OS-specific:

```zsh
if [[ $OSTYPE == darwin* ]]; then
  alias o='open'
elif [[ -r /proc/version ]] && grep -qi microsoft /proc/version; then
  alias o='explorer.exe'
else
  alias o='xdg-open'
fi
```

Usual differences: `open` / `xdg-open` / `wslview`; clipboard `pbcopy` / `wl-copy` or `xclip` / `clip.exe`; `sed -i ''` on macOS versus `sed -i` on GNU; `ls -G` versus `ls --color`; package manager (`brew`, `pacman`, `apt`). Prefer POSIX options when a command exists on all three.

## Gotchas

- `.zshrc` is read only by interactive shells; GUI-launched and non-interactive processes will not see its aliases or exports.
- Aliases sourced after the plugin framework override its aliases of the same name.
- Never put a token in a tracked file; point the user to the untracked secrets file instead.
- An alias that expands inside another alias or function is resolved at definition time; use a function if it must be late-bound.

## Review Checklist

- [ ] Alias added through the script, not by hand, unless it needed a function.
- [ ] The script's output was read; any exit code 1 or 2 was explained to the user.
- [ ] No `--force` without the user's agreement.
- [ ] OS-specific commands are guarded or the alias is portable.
- [ ] `zsh -n` passes on every hand-edited file.
- [ ] No token or secret was written to a tracked file.
- [ ] The user was told to run `source ~/.zshrc`.
